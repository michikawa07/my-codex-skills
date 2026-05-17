#!/usr/bin/env python3
"""Normalize indentation for converted TeX without changing content."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


BEGIN_RE = re.compile(r"\\begin\{([^{}]+)\}")
END_RE = re.compile(r"\\end\{([^{}]+)\}")
SECTION_RE = re.compile(r"\\(?:section|subsection|subsubsection)\*?\{")


def leading_closes(line: str) -> int:
    stripped = line.lstrip()
    count = 0
    while stripped.startswith("}"):
        count += 1
        stripped = stripped[1:].lstrip()
    return count


def net_brace_delta(line: str) -> int:
    active = line.split("%", 1)[0]
    return active.count("{") - active.count("}")


def format_lines(lines: list[str], indent: str = "\t") -> list[str]:
    formatted: list[str] = []
    level = 0

    for raw in lines:
        content = raw.lstrip(" \t")
        stripped = content.strip()
        if not content:
            formatted.append("")
            continue

        if SECTION_RE.search(stripped):
            level = 0

        end_count = len(END_RE.findall(stripped))
        close_count = leading_closes(stripped)
        current_level = max(0, level - end_count - close_count)
        formatted.append(f"{indent * current_level}{content}")

        begin_count = len(BEGIN_RE.findall(stripped))
        level = max(0, level + begin_count - end_count + net_brace_delta(stripped))

    return formatted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tex", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--indent", default="\t")
    args = parser.parse_args()

    original = args.tex.read_text(encoding="utf-8")
    formatted = "\n".join(format_lines(original.splitlines(), args.indent)) + "\n"
    if args.check:
        if formatted != original:
            print(f"indentation differs: {args.tex}")
            return 1
        return 0
    args.tex.write_text(formatted, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
