#!/usr/bin/env python3
"""Replace exactly one Typst-to-TeX seed block with a TeX fragment."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def load_block_ids(block_ledger: Path | None) -> set[str]:
    if not block_ledger:
        return set()
    data = json.loads(block_ledger.read_text(encoding="utf-8"))
    return {str(block.get("id")) for block in data.get("blocks", []) if isinstance(block, dict)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_tex", type=Path)
    parser.add_argument("block_id")
    parser.add_argument("fragment_tex", type=Path)
    parser.add_argument("--block-ledger", type=Path, default=None)
    args = parser.parse_args()

    known_ids = load_block_ids(args.block_ledger)
    if known_ids and args.block_id not in known_ids:
        print(f"unknown block id: {args.block_id}", file=sys.stderr)
        return 2

    text = args.output_tex.read_text(encoding="utf-8")
    fragment = args.fragment_tex.read_text(encoding="utf-8").rstrip("\n")
    escaped = re.escape(args.block_id)
    pattern = re.compile(
        rf"(?ms)^% BEGIN typst-to-tex block id={escaped} [^\n]*\n"
        rf".*?"
        rf"^% END typst-to-tex block id={escaped}\s*$"
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        print(f"expected exactly one block {args.block_id}, found {len(matches)}", file=sys.stderr)
        return 1

    new_text = text[:matches[0].start()] + fragment + text[matches[0].end():]
    args.output_tex.write_text(new_text, encoding="utf-8")
    print(f"replaced={args.block_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
