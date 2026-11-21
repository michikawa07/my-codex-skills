#!/usr/bin/env python3
"""Find terms in the saved text of PowerPoint shapes and table cells."""

import argparse
import re
import sys
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

if __name__ == "__main__":
    sys.dont_write_bytecode = True
from pptx_grouping import DRAWING_NS, slide_parts


def text_blocks(slide):
    tree = slide.find("{*}cSld/{*}spTree")
    if tree is None:
        raise ValueError("slide has no shape tree")
    p = tree.tag.rsplit("}", 1)[0] + "}"
    tags = {p + "sp", p + "cxnSp"} | {f"{{{ns}}}tc" for ns in DRAWING_NS}
    for element in tree.iter():
        if element.tag not in tags:
            continue
        lines = []
        for paragraph in element.findall("{*}txBody/{*}p"):
            parts = []
            for run in paragraph:
                if run.tag.endswith("}br"):
                    parts.append("\n")
                else:
                    parts.append(run.findtext("{*}t", default=""))
            lines.append("".join(parts))
        if lines:
            yield "\n".join(lines)


def search_pattern(term):
    # Manual breaks can split either two words or a single word. Formatting runs add no space.
    line_break = r"(?:[^\S\n]*\n\s*)?"
    words = [line_break.join(re.escape(char) for char in word) for word in term.split()]
    return re.compile(r"\s+".join(words), re.IGNORECASE)


def context(text, match):
    left = max(0, match.start() - 40)
    right = min(len(text), match.end() + 40)
    return ("…" if left else "") + text[left:right] + ("…" if right < len(text) else "")


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Matches are case-insensitive substrings within each shape or cell, including grouped shapes. "
        "Each term has its own non-overlapping occurrence count. Original line breaks appear as \\n in context. "
        "Image pixels, separate chart parts, masters and notes are outside the search. "
        "Review each occurrence in context. A completed search returns 0, including zero matches."
    ))
    parser.add_argument("file", help="saved PPTX to inspect")
    parser.add_argument("terms", metavar="TERM", nargs="+", help="literal text, with quotes around a phrase")
    args = parser.parse_args()
    if any(not term.strip() for term in args.terms):
        parser.error("each search term must contain text")
    patterns = {term: search_pattern(term) for term in args.terms}
    counts = dict.fromkeys(patterns, 0)
    try:
        with ZipFile(args.file) as archive:
            for page, part in enumerate(slide_parts(archive), 1):
                for block in text_blocks(ET.fromstring(archive.read(part))):
                    for term, pattern in patterns.items():
                        for match in pattern.finditer(block):
                            print(f"p{page}\t{term!r}\t{context(block, match)!r}")
                            counts[term] += 1
    except (OSError, BadZipFile, ET.ParseError, KeyError, RuntimeError, ValueError) as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")
    print("Occurrences")
    for term, count in counts.items():
        print(f"{term!r}\t{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
