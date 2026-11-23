#!/usr/bin/env python3
"""Set the point size of one existing PowerPoint text shape and verify the saved result."""

import argparse
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from xml.dom import minidom
from zipfile import BadZipFile, ZipFile

sys.dont_write_bytecode = True
from pptx_grouping import DRAWING_NS, slide_parts, write_copy


def points(value):
    try:
        size = Decimal(value)
        if size.is_finite() and 1 <= size <= 4000 and size * 100 == int(size * 100):
            return str(int(size * 100))
    except InvalidOperation:
        pass
    raise argparse.ArgumentTypeError("use 1–4000 points, with at most two decimal places")


def child(node, name):
    return next((c for c in node.childNodes if c.localName == name), None)


def paragraph_text(paragraph):
    pieces = []
    for node in paragraph.childNodes:
        if node.localName == "br":
            pieces.append("\n")
        elif node.localName in ("r", "fld"):
            text = child(node, "t")
            if text is not None:
                pieces.extend(n.data for n in text.childNodes if n.nodeType in (n.TEXT_NODE, n.CDATA_SECTION_NODE))
    return "".join(pieces)


def text_shape(doc, args):
    matches = []
    ns = doc.documentElement.namespaceURI
    for shape in doc.getElementsByTagNameNS(ns, "sp"):
        body = child(shape, "txBody")
        if body is None:
            continue
        info = child(shape, "nvSpPr")
        identity = child(info, "cNvPr")
        shape_id = identity.getAttribute("id")
        if args.title:
            selected = any(ph.getAttribute("type") in ("title", "ctrTitle")
                           for ph in info.getElementsByTagNameNS(ns, "ph"))
        elif args.id is not None:
            selected = shape_id == str(args.id)
        else:
            paragraphs = [c for c in body.childNodes if c.localName == "p" and c.namespaceURI in DRAWING_NS]
            text = "\n".join(paragraph_text(p) for p in paragraphs)
            selected = text == args.text
        if selected:
            matches.append((shape_id, body))
    if len(matches) != 1:
        ids = ", ".join(key for key, _ in matches)
        raise ValueError(f"expected one text shape on slide {args.slide}; found {len(matches)} {ids}".rstrip())
    return matches[0]


def ensure(parent, name, before):
    node = child(parent, name)
    if node is None:
        qualified = f"{parent.prefix}:{name}" if parent.prefix else name
        node = parent.ownerDocument.createElementNS(parent.namespaceURI, qualified)
        parent.insertBefore(node, before)
    return node


def font_properties(body, create=False):
    for p in body.childNodes:
        if p.localName != "p" or p.namespaceURI not in DRAWING_NS:
            continue
        props = ensure(p, "pPr", p.firstChild) if create else child(p, "pPr")
        default = (ensure(props, "defRPr", child(props, "extLst")) if create
                   else child(props, "defRPr") if props is not None else None)
        if default is None:
            raise ValueError("missing saved paragraph font size")
        yield default
        for name in ("rPr", "endParaRPr"):
            yield from p.getElementsByTagNameNS(p.namespaceURI, name)


def set_size(args):
    output = (args.output or args.file).resolve()
    if args.preview and args.preview.suffix.lower() != ".png":
        raise ValueError("preview output must be a PNG")
    source = args.file.resolve()
    if args.preview and args.preview.resolve() in (source, output):
        raise ValueError("use a separate file for the page preview")
    stamp = source.stat()
    with TemporaryDirectory(dir=output.parent) as tmp:
        stage = Path(tmp) / "edited.pptx"
        with ZipFile(source) as archive:
            parts = list(slide_parts(archive))
            if not 1 <= args.slide <= len(parts):
                raise ValueError(f"slide outside 1..{len(parts)}")
            part = parts[args.slide - 1]
            with minidom.parseString(archive.read(part)) as doc:
                shape_id, body = text_shape(doc, args)
                changed = False
                for prop in font_properties(body, create=True):
                    if prop.getAttribute("sz") != args.points:
                        prop.setAttribute("sz", args.points)
                        changed = True
                data = doc.toxml(encoding=doc.encoding or "utf-8", standalone=doc.standalone)
            write_copy(archive, stage, {part: data} if changed else {})
        with ZipFile(stage) as saved, minidom.parseString(saved.read(part)) as doc:
            _, body = text_shape(doc, args)
            sizes = {p.getAttribute("sz") for p in font_properties(body)}
            if sizes != {args.points}:
                raise ValueError("saved point size did not match the request")
        if source == output and (source.stat().st_mtime_ns, source.stat().st_size) != (stamp.st_mtime_ns, stamp.st_size):
            raise ValueError("the original changed during the edit")
        os.replace(stage, output)
    print(f"Verified slide {args.slide}, shape {shape_id}, {int(args.points) / 100:g} pt in {output}", flush=True)
    if args.preview:
        renderer = Path(__file__).with_name("render_pptx_page.mjs")
        subprocess.run(["node", str(renderer), str(output), str(args.slide), str(args.preview)], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--slide", type=int, required=True, help="1-based page in thumbnail order")
    select = parser.add_mutually_exclusive_group(required=True)
    select.add_argument("--title", action="store_true", help="native title placeholder")
    select.add_argument("--text", help="exact text of a native shape; join paragraphs with a newline")
    select.add_argument("--id", type=int, help="native shape ID on this slide")
    parser.add_argument("--points", type=points, required=True)
    parser.add_argument("--output", type=Path, help="save to this path; defaults to the input file")
    parser.add_argument("--preview", type=Path, help="render the saved page as a PNG using the Codex Node runtime")
    try:
        set_size(parser.parse_args())
    except (OSError, ValueError, BadZipFile, subprocess.CalledProcessError) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")


if __name__ == "__main__":
    main()
