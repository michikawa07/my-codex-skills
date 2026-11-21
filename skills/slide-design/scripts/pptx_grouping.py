#!/usr/bin/env python3
"""Find explicit PowerPoint grouping locks or release selected locks in a new file."""

import argparse
import posixpath
import re
from collections import defaultdict
from pathlib import Path
from xml.dom import minidom
from xml.etree import ElementTree as ET
from xml.parsers import expat
from xml.sax.saxutils import quoteattr
from zipfile import BadZipFile, ZipFile


LOCK_TYPES = {
    "sp": "spLocks", "grpSp": "grpSpLocks", "cxnSp": "cxnSpLocks",
    "pic": "picLocks", "graphicFrame": "graphicFrameLocks",
}
DRAWING_NS = {
    "http://schemas.openxmlformats.org/drawingml/2006/main",
    "http://purl.oclc.org/ooxml/drawingml/main",
}
ATTRIBUTE = re.compile(r'''\s+([^\s=/>]+)\s*=\s*(?:"[^"]*"|'[^']*')''')


def slide_parts(archive):
    presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
    rels = ET.fromstring(archive.read("ppt/_rels/presentation.xml.rels"))
    targets = {r.get("Id"): r.attrib["Target"] for r in rels if r.get("Type", "").endswith("/slide")}
    for slide in presentation.findall("{*}sldIdLst/{*}sldId"):
        rel_id = next((v for k, v in slide.attrib.items() if k.endswith("}id")), None)
        yield posixpath.normpath(posixpath.join("ppt", targets[rel_id])).lstrip("/")


def slide_shapes(doc):
    p = doc.documentElement.namespaceURI
    trees = doc.getElementsByTagNameNS(p, "spTree")
    if len(trees) != 1:
        raise ValueError("slide has no unique shape tree")
    for info in trees[0].getElementsByTagNameNS(p, "cNvPr"):
        nonvisual = info.parentNode
        shape = nonvisual.parentNode
        kind = shape.localName
        if shape.namespaceURI != p or kind not in LOCK_TYPES:
            continue
        placeholder = bool(nonvisual.getElementsByTagNameNS(p, "ph"))
        locks = [lock for lock in nonvisual.getElementsByTagNameNS("*", LOCK_TYPES[kind])
                 if lock.parentNode.parentNode is nonvisual and lock.namespaceURI in DRAWING_NS
                 and lock.getAttribute("noGrp").strip() in ("1", "true")]
        yield int(info.getAttribute("id")), kind, info.getAttribute("name"), placeholder, locks


def target(value):
    parts = value.split(":")
    if len(parts) != 2 or not all(part.isdecimal() for part in parts) or int(parts[0]) < 1:
        raise argparse.ArgumentTypeError("use PAGE:ID, with pages numbered from 1")
    return tuple(map(int, parts))


def edit_attribute(data, doc, selected, name, value):
    """Set an attribute on the selected DOM elements, or remove it when value is None."""
    # Expat gives the byte offset of each real start tag, also in DOM preorder.
    # Splice only the selected attribute. This preserves prefixes, character references and all other XML bytes.
    offsets = []
    parser = expat.ParserCreate()
    parser.StartElementHandler = lambda name, attrs: offsets.append(parser.CurrentByteIndex)
    parser.Parse(data, True)
    offsets.append(len(data))
    encoding = doc.encoding or "utf-8"
    if data.startswith((b"\xff\xfe", b"<\0")):
        encoding = "utf-16-le"
    elif data.startswith((b"\xfe\xff", b"\0<")):
        encoding = "utf-16-be"
    replacement = b"" if value is None else f" {name}={quoteattr(value)}".encode(encoding)
    pieces = []
    last = 0
    for node, start, end in zip(doc.getElementsByTagName("*"), offsets, offsets[1:]):
        if node not in selected:
            continue
        fragment = data[start:end].decode(encoding)
        if node.hasAttribute(name):
            attr = next((m for m in ATTRIBUTE.finditer(fragment) if m[1] == name), None)
            if attr is None:
                raise ValueError(f"cannot locate the selected {name} attribute")
            left, right = attr.span()
        elif value is None:
            raise ValueError(f"cannot locate the selected {name} attribute")
        else:
            left = right = re.match(r"<[^\s/>]+", fragment).end()
        pieces.append(data[last:start + len(fragment[:left].encode(encoding))] + replacement)
        last = start + len(fragment[:right].encode(encoding))
    if len(pieces) != len(selected):
        raise ValueError(f"cannot locate all selected elements for {name}")
    return b"".join([*pieces, data[last:]])


def write_copy(archive, output, changed):
    stream = output.open("xb")
    try:
        with stream, ZipFile(stream, "w") as result:
            result.comment = archive.comment
            for part in archive.infolist():
                payload = changed[part.filename] if part.filename in changed else archive.read(part)
                result.writestr(part, payload)
    except BaseException:
        output.unlink()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Scan lists PAGE:ID, shape type and Selection Pane name for locked slide objects, "
        "excluding placeholders. Choose the objects the author intends to group. "
        "Scan returns 0 for no candidates, 1 for candidates, and 2 for an error. "
        "A successful repair returns 0. Only explicit noGrp locks on selected objects are removed."
    ))
    parser.add_argument("file", type=Path, help="saved PPTX to inspect")
    parser.add_argument("--allow", type=target, nargs="+", metavar="PAGE:ID", help="selected locked objects in slide thumbnail order")
    parser.add_argument("--output", type=Path, metavar="NEW.pptx", help="new PPTX for the selected changes")
    args = parser.parse_args()
    if bool(args.allow) != bool(args.output):
        parser.error("use --allow and --output together")

    requested = defaultdict(set)
    for page, shape_id in args.allow or ():
        requested[page].add(shape_id)
    found = 0
    changed = {}
    try:
        with ZipFile(args.file) as archive:
            parts = list(slide_parts(archive))
            if requested and max(requested) > len(parts):
                raise ValueError(f"page {max(requested)} is outside 1..{len(parts)}")
            for page, part in enumerate(parts, 1):
                if requested and page not in requested:
                    continue
                data = archive.read(part)
                with minidom.parseString(data) as doc:
                    matches = defaultdict(list)
                    for shape_id, kind, name, placeholder, locks in slide_shapes(doc):
                        if requested:
                            matches[shape_id].append((placeholder, locks))
                        elif locks and not placeholder:
                            print(f"{page}:{shape_id}\t{kind}\t{name}")
                            found += 1
                    if not requested:
                        continue
                    selected = set()
                    for shape_id in sorted(requested[page]):
                        objects = matches[shape_id]
                        if len(objects) != 1:
                            raise ValueError(f"{page}:{shape_id} matches {len(objects)} objects")
                        placeholder, locks = objects[0]
                        if placeholder or not locks:
                            raise ValueError(f"{page}:{shape_id} is a placeholder or has no explicit grouping lock")
                        selected.update(locks)
                    changed[part] = edit_attribute(data, doc, selected, "noGrp", None)
            if args.output:
                write_copy(archive, args.output, changed)
                print(f"Saved {args.output}")
                return 0
    except (OSError, ValueError, KeyError, BadZipFile, expat.ExpatError, ET.ParseError, RuntimeError) as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")
    print(f"{found} locked non-placeholder candidate(s)")
    return int(bool(found))


if __name__ == "__main__":
    raise SystemExit(main())
