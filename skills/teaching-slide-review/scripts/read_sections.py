#!/usr/bin/env python3
"""List the review references' headings or print selected sections with their introductions."""

import argparse
from pathlib import Path
import re
import sys

SKILL = Path(__file__).resolve().parents[1]
DOCUMENTS = {
    "D": SKILL.parent / "slide-design" / "SKILL.md",
    "T": SKILL / "references" / "teaching-review.md",
}


def sections(prefix, path):
    lines = path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    headings = []
    fence = ""
    for pos, line in enumerate(lines):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if not fence:
                fence = token
            elif token.startswith(fence) and not line[marker.end():].strip():
                fence = ""
            continue
        heading = re.match(r"^(#{1,6}) +(.+?)\s*$", line)
        if heading and not fence:
            headings.append((pos, len(heading[1]), heading[2]))

    parents = []
    for i, (pos, level, title) in enumerate(headings):
        while parents and parents[-1][0] >= level:
            parents.pop()
        key = f"{prefix}{i}"
        end = headings[i + 1][0] if i + 1 < len(headings) else len(lines)
        text = "".join(lines[(pos if i else 0):end])
        yield key, level, title, text, [parent for _, parent in parents]
        parents.append((level, key))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sections", nargs="*", help="IDs from the outline, e.g. D2 T5")
    parser.add_argument("--criteria", action="store_true", help="Read all design and review criteria; source details can be opened by ID.")
    args = parser.parse_args()
    entries = {key: (level, title, text, parents)
               for prefix, path in DOCUMENTS.items()
               for key, level, title, text, parents in sections(prefix, path)}
    if args.criteria:
        if args.sections:
            parser.error("--criteria takes no section IDs")
        for _, title, body, _ in entries.values():
            if title.endswith("根拠資料と適用範囲"):
                body = "".join(line for line in body.splitlines(keepends=True)
                               if not re.match(r"^(?:\||\[S\d+\]:)", line))
            print(body, end="")
        return
    if not args.sections:
        for key, (level, title, _, _) in entries.items():
            print(f"{key:4} {'  ' * (level - 1)}{title}")
        print("S番号   引用した文献と，その適用範囲")
        return
    requested = set(args.sections)
    sources = {key for key in requested if re.fullmatch(r"S[0-9]+", key)}
    if sources:
        # Keep the section's common qualifications and the requested rows and links.
        tag = re.compile(r"^(?:\| |\[)(S[0-9]+)(?: \||\]:)")
        for key, (level, title, text, parents) in list(entries.items()):
            lines = text.splitlines(keepends=True)
            tags = [tag.match(line) for line in lines]
            found = {match[1] for match in tags if match} & sources
            if found:
                excerpt = "".join(line for line, match in zip(lines, tags)
                                  if not match or match[1] in found)
                if key not in requested:
                    entries[key] = (level, title, excerpt, parents)
                requested.difference_update(found)
                requested.add(key)
    unknown = requested - entries.keys()
    if unknown:
        parser.error("unknown section: " + ", ".join(sorted(unknown)))
    wanted = requested.copy()
    for key in requested:
        wanted.update(entries[key][3])
    for key, (_, _, text, _) in entries.items():
        if key in wanted:
            print(text, end="")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
