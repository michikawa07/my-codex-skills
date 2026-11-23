#!/usr/bin/env python3
"""Change one native diagram part in a new PPTX for a visual comparison."""

import argparse
import re
import sys
from pathlib import Path
from xml.dom import minidom
from xml.etree import ElementTree as ET
from xml.parsers import expat
from zipfile import BadZipFile, ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "slide-design" / "scripts"))
from pptx_grouping import DRAWING_NS, slide_parts, write_copy


def children(node):
    return [c for c in node.childNodes if c.nodeType == c.ELEMENT_NODE]


def drawing(node, name):
    if node is None:
        return None
    return next((c for c in children(node) if c.localName == name and c.namespaceURI in DRAWING_NS), None)


def compact(shape, props):
    preset = drawing(props, "prstGeom")
    text_box = any(n.getAttribute("txBox") in ("1", "true")
                   for n in shape.getElementsByTagNameNS(shape.namespaceURI, "cNvSpPr"))
    if shape.localName != "sp" or text_box or preset is None or preset.getAttribute("prst") != "rect":
        raise ValueError("compact requires a native rectangle")
    transform = drawing(props, "xfrm")
    if drawing(transform, "off") is None or drawing(transform, "ext") is None:
        raise ValueError("rectangle needs an explicit position and size")
    new = transform.cloneNode(True)
    off, ext = drawing(new, "off"), drawing(new, "ext")
    for axis in ("x", "y"):
        size = int(ext.getAttribute("c" + axis))
        inset = round(size * 0.075)  # Equal insets keep the centre exact to the stored unit.
        if inset == 0 or size <= 0:
            raise ValueError("rectangle is too small to compact")
        off.setAttribute(axis, str(int(off.getAttribute(axis)) + inset))
        ext.setAttribute("c" + axis, str(size - 2 * inset))
    return transform, new


def straighten(shape, props):
    preset = drawing(props, "prstGeom")
    if preset is not None and shape.localName == "cxnSp":
        if not re.fullmatch(r"(?:bent|curved)Connector[2-5]", preset.getAttribute("prst")):
            raise ValueError("select a bent or curved connector")
        # All these presets run from (left, top) to (right, bottom) before the same transform.
        new = preset.cloneNode(False)  # The old preset's adjustments do not apply.
        new.setAttribute("prst", "straightConnector1")
        return preset, new

    paths = drawing(drawing(props, "custGeom"), "pathLst")
    path = drawing(paths, "path")
    if path is None or len(children(paths)) != 1:
        raise ValueError("select a bent/curved connector or one open custom stroke")
    if drawing(drawing(props, "ln"), "noFill") is not None or path.getAttribute("stroke") in ("0", "false"):
        raise ValueError("custom path needs a visible stroke")
    if path.getAttribute("fill") != "none" and drawing(props, "noFill") is None:
        raise ValueError("custom path must be explicitly unfilled")
    ops = children(path)
    if len(ops) < 2 or ops[0].localName != "moveTo" or (len(ops) == 2 and ops[1].localName == "lnTo"):
        raise ValueError("custom path needs one move followed by a curve or multiple segments")
    counts = {"lnTo": 1, "quadBezTo": 2, "cubicBezTo": 3}
    for i, op in enumerate(ops):
        pts = children(op)
        expected = 1 if i == 0 else counts.get(op.localName)
        if op.namespaceURI != path.namespaceURI or len(pts) != expected or any(
            p.localName != "pt" or p.namespaceURI != path.namespaceURI for p in pts
        ):
            raise ValueError("only open line, quadratic and cubic path segments are supported")
    first, last = children(ops[0])[0], children(ops[-1])[-1]
    coords = [tuple(int(p.getAttribute(a)) for a in ("x", "y")) for p in (first, last)]
    if coords[0] == coords[1]:
        raise ValueError("start and end of the custom path coincide")
    prefix = path.prefix + ":" if path.prefix else ""
    line = shape.ownerDocument.createElementNS(path.namespaceURI, prefix + "lnTo")
    end = shape.ownerDocument.createElementNS(path.namespaceURI, prefix + "pt")
    for axis in ("x", "y"):
        end.setAttribute(axis, last.getAttribute(axis))
    line.appendChild(end)
    new = path.cloneNode(False)
    new.appendChild(ops[0].cloneNode(True))
    new.appendChild(line)
    return path, new


def span(data, doc, target):
    """Locate one element so surrounding slide XML stays byte-for-byte intact."""
    nodes = iter(doc.getElementsByTagName("*"))
    stack, bounds = [], []
    parser = expat.ParserCreate()

    def start(name, attrs):
        stack.append(next(nodes))
        if stack[-1] is target:
            bounds.append(parser.CurrentByteIndex)

    def end(name):
        if stack.pop() is target:
            bounds.append(parser.CurrentByteIndex)

    parser.StartElementHandler, parser.EndElementHandler = start, end
    parser.Parse(data, True)
    encoding = doc.encoding or "utf-8"
    if data.startswith((b"\xff\xfe", b"<\0")):
        encoding = "utf-16-le"
    elif data.startswith((b"\xfe\xff", b"\0<")):
        encoding = "utf-16-be"
    if not target.hasChildNodes() and data[bounds[0]:bounds[1]].endswith("/>".encode(encoding)):
        return bounds[0], bounds[1], encoding
    marker = ">".encode(encoding)
    return bounds[0], data.index(marker, bounds[1]) + len(marker), encoding


def edit(data, ident, action):
    with minidom.parseString(data) as doc:
        p = doc.documentElement.namespaceURI
        tree, = doc.getElementsByTagNameNS(p, "spTree")
        shapes = [info.parentNode.parentNode for info in tree.getElementsByTagNameNS(p, "cNvPr")
                  if info.getAttribute("id") == str(ident)]
        if len(shapes) != 1 or shapes[0].localName not in ("sp", "cxnSp"):
            raise ValueError(f"ID {ident} must identify one native shape or connector")
        shape = shapes[0]
        props = next((c for c in children(shape) if c.namespaceURI == p and c.localName == "spPr"), None)
        if props is None or shape.getElementsByTagNameNS(p, "ph"):
            raise ValueError("select a non-placeholder with explicit drawing properties")
        target, new = action(shape, props)
        start, end, encoding = span(data, doc, target)
        return data[:start] + new.toxml().encode(encoding) + data[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Straighten holds both stored endpoints fixed. Custom strokes require one open, unfilled "
        "path with numeric endpoints and line or Bezier segments. Compact scales a rectangle to "
        "85% about its centre. Text, formatting and stored connections are retained. Render both "
        "versions at the same size to assess the effect."
    ))
    parser.add_argument("deck", type=Path)
    parser.add_argument("--page", type=int, required=True, help="page in thumbnail order, starting at 1")
    parser.add_argument("--id", type=int, required=True, help="numeric shape ID on that page")
    parser.add_argument("--action", choices=("straighten", "compact"), required=True)
    parser.add_argument("--output", type=Path, required=True, metavar="NEW.pptx")
    args = parser.parse_args()
    try:
        if args.deck.suffix.lower() != ".pptx" or args.output.suffix.lower() != ".pptx":
            raise ValueError("input and output must be .pptx files")
        with ZipFile(args.deck) as archive:
            parts = list(slide_parts(archive))
            if not 1 <= args.page <= len(parts):
                raise ValueError(f"page {args.page} is outside 1..{len(parts)}")
            part = parts[args.page - 1]
            action = {"straighten": straighten, "compact": compact}[args.action]
            data = edit(archive.read(part), args.id, action)
            write_copy(archive, args.output, {part: data})  # opens the destination exclusively
        print(f"Saved {args.output} (page {args.page}, ID {args.id}, {args.action})")
    except (OSError, BadZipFile, ValueError, KeyError, expat.ExpatError, ET.ParseError, RuntimeError) as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()
