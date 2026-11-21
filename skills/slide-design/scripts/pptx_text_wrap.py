#!/usr/bin/env python3
"""Inspect shape text wrapping, or explicitly enable it on selected slides in a new PPTX."""

import argparse
import sys
from collections import Counter
from pathlib import Path
from xml.dom import minidom
from xml.etree import ElementTree as ET
from xml.parsers import expat
from zipfile import BadZipFile, ZipFile

if __name__ == "__main__":
    sys.dont_write_bytecode = True
from pptx_grouping import DRAWING_NS, edit_attribute, slide_parts, write_copy


def frames(doc):
    p = doc.documentElement.namespaceURI
    trees = doc.getElementsByTagNameNS(p, "spTree")
    if len(trees) != 1:
        raise ValueError("slide has no unique shape tree")
    for body in trees[0].getElementsByTagNameNS(p, "txBody"):
        shape = body.parentNode
        if shape.namespaceURI != p or shape.localName not in ("sp", "cxnSp"):
            continue
        props = [child for child in body.childNodes if child.localName == "bodyPr" and child.namespaceURI in DRAWING_NS]
        if len(props) != 1:
            raise ValueError("native shape text frame has no unique bodyPr")
        identity = shape.getElementsByTagNameNS(p, "cNvPr")
        if not identity:
            raise ValueError("native shape text frame has no shape ID")
        yield identity[0], props[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Includes existing native shape text frames, even when empty, grouped or in a slide placeholder. "
        "Excludes table cells, charts, notes, masters, layouts and shapes without a text frame. "
        "Scan returns 0 if every inspected frame explicitly says square, 1 if any says none or omits wrap, "
        "and 2 on error. Unspecified reports the stored attribute. A successful copy returns 0."
    ))
    parser.add_argument("file", type=Path, help="saved PPTX to inspect")
    parser.add_argument("--slides", type=int, nargs="+", metavar="N", help="1-based pages in thumbnail order (default: all)")
    parser.add_argument("--output", type=Path, metavar="NEW.pptx", help="new copy with wrapping explicitly enabled")
    args = parser.parse_args()
    counts = Counter()
    changed = {}
    try:
        with ZipFile(args.file) as archive:
            parts = list(slide_parts(archive))
            pages = set(args.slides or range(1, len(parts) + 1))
            if any(page < 1 or page > len(parts) for page in pages):
                raise ValueError(f"page outside 1..{len(parts)}")
            for page, part in enumerate(parts, 1):
                if page not in pages:
                    continue
                data = archive.read(part)
                with minidom.parseString(data) as doc:
                    selected = set()
                    for info, prop in frames(doc):
                        state = "unspecified"
                        if prop.hasAttribute("wrap"):
                            state = prop.getAttribute("wrap")
                            if state not in ("square", "none"):
                                raise ValueError(f"slide {page}: invalid wrap={state!r}")
                        counts[state] += 1
                        print(f"{page}:{info.getAttribute('id')}\t{state}\t{info.getAttribute('name')}")
                        if state != "square":
                            selected.add(prop)
                    if args.output and selected:
                        changed[part] = edit_attribute(data, doc, selected, "wrap", "square")
            if args.output:
                write_copy(archive, args.output, changed)
    except (OSError, ValueError, KeyError, BadZipFile, expat.ExpatError, ET.ParseError, RuntimeError) as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")
    print(f"Input frames: square={counts['square']} none={counts['none']} unspecified={counts['unspecified']}")
    if args.output:
        print(f"Saved {args.output}")
        return 0
    return int(bool(counts["none"] or counts["unspecified"]))


if __name__ == "__main__":
    raise SystemExit(main())
