#!/usr/bin/env python3
"""Print the next unresolved Typst-to-TeX block from a block ledger."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("block_ledger", type=Path)
    parser.add_argument("output_tex", type=Path)
    args = parser.parse_args()

    ledger = json.loads(args.block_ledger.read_text(encoding="utf-8"))
    tex = args.output_tex.read_text(encoding="utf-8", errors="replace")
    pending_ids = set(re.findall(r"% BEGIN typst-to-tex block id=([^ ]+)", tex))

    for block in ledger.get("blocks", []):
        ident = str(block.get("id", ""))
        if ident not in pending_ids:
            continue
        print(f"id: {ident}")
        print(f"kind: {block.get('kind')}")
        print(f"heading: {block.get('heading')}")
        print(f"lines: {block.get('start_line')}-{block.get('end_line')}")
        print("source:")
        print(block.get("source", ""))
        return 1

    print("no pending blocks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
