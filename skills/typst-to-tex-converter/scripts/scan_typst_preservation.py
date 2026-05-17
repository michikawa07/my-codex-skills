#!/usr/bin/env python3
"""Scan Typst source for conversion-preservation items.

The default path invokes the bundled Rust scanner based on typst-syntax. The
legacy lexical scanner remains available only as an explicit fallback for
diagnosing scanner failures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path


NOTE_RE = re.compile(r"#(?:l|r)note\[[^\]]*\]")
LABEL_RE = re.compile(r"<([^>\s]+)>")
REFERENCE_RE = re.compile(r"(?<![\\A-Za-z0-9_.-])@([A-Za-z0-9][A-Za-z0-9_.:-]*)")
COMMAND_RE = re.compile(r"#([A-Za-z_][A-Za-z0-9_.-]*)")
QTY_RE = re.compile(r"#(?:qty|unit)\s*\(")
LET_RE = re.compile(r"^\s*#let\s+([A-Za-z][A-Za-z0-9_]*)\s*=")


def active_part(line: str) -> str:
    return line.split("//", 1)[0]


def stable_id(kind: str, line: int, text: str) -> str:
    digest = hashlib.sha1(f"{kind}\0{line}\0{text}".encode("utf-8")).hexdigest()[:12]
    return f"{kind}:{line}:{digest}"


def make_item(kind: str, line: int, text: str, **extra: object) -> dict[str, object]:
    item: dict[str, object] = {
        "id": stable_id(kind, line, text),
        "source": "source-scan",
        "kind": kind,
        "line": line,
        "text": text,
    }
    item.update(extra)
    return item


def find_caption_block(lines: list[str], start_index: int) -> tuple[int, int, int] | None:
    active = active_part(lines[start_index])
    caption_index = active.find("caption")
    bracket_index = active.find("[", caption_index)
    if bracket_index == -1:
        return None
    if "]" in active[bracket_index + 1:]:
        return (start_index + 1, start_index + 1, 0)

    comments = 0
    for idx in range(start_index + 1, len(lines)):
        if "//" in lines[idx]:
            comments += 1
        if "]" in active_part(lines[idx]):
            return (start_index + 1, idx + 1, comments)
    return (start_index + 1, len(lines), comments)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_typ", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--lexical-fallback",
        action="store_true",
        help="Use the legacy lexical scanner only if the typst-syntax AST scanner cannot run.",
    )
    parser.add_argument(
        "--force-lexical",
        action="store_true",
        help="Force the legacy lexical scanner. This is not the default conversion path.",
    )
    args = parser.parse_args()

    if not args.force_lexical:
        manifest = Path(__file__).resolve().parent / "typst_ast_scanner" / "Cargo.toml"
        cargo = shutil.which("cargo")
        if cargo and manifest.exists():
            cmd = [
                cargo,
                "run",
                "--quiet",
                "--manifest-path",
                str(manifest),
                "--",
                str(args.source_typ),
            ]
            if args.output:
                cmd.extend(["--output", str(args.output)])
            completed = subprocess.run(cmd, check=False)
            if completed.returncode == 0 or not args.lexical_fallback:
                return completed.returncode
        elif not args.lexical_fallback:
            print("cargo or typst_ast_scanner/Cargo.toml not found; AST scan unavailable", file=sys.stderr)
            return 2

    lines = args.source_typ.read_text(encoding="utf-8").splitlines()
    items: list[dict[str, object]] = []
    caption_starts: set[int] = set()

    for idx, line in enumerate(lines):
        line_no = idx + 1
        active = active_part(line)

        if "//" in line:
            comment = line.split("//", 1)[1].strip()
            if comment:
                items.append(make_item("comment", line_no, comment, raw=line))

        for note in NOTE_RE.findall(active):
            items.append(make_item("note", line_no, note, raw=line))

        for label in LABEL_RE.findall(active):
            items.append(make_item("label", line_no, label, raw=line))

        if not active.lstrip().startswith("#import"):
            for target in REFERENCE_RE.findall(active):
                items.append(make_item("reference", line_no, target, raw=line))

        if QTY_RE.search(active):
            items.append(make_item("qty_or_unit", line_no, active.strip(), raw=line))

        if "#subpar_grid" in active:
            items.append(make_item("subpar_grid", line_no, active.strip(), raw=line))

        let_match = LET_RE.match(active)
        if let_match:
            items.append(make_item("source_let", line_no, active.strip(), name=let_match.group(1), raw=line))

        if "caption" in active and ":" in active:
            block = find_caption_block(lines, idx)
            if block and block[0] not in caption_starts:
                start, end, comments = block
                caption_starts.add(start)
                kind = "caption_block" if end > start else "caption_inline"
                items.append(make_item(kind, start, lines[idx].strip(), end_line=end, comments_inside=comments, raw=line))

        for command in COMMAND_RE.findall(active):
            items.append(make_item("active_command", line_no, command, raw=line))

        if re.search(r"#[A-Za-z_][A-Za-z0-9_.-]*\s*\(", active) and active.count("(") > active.count(")"):
            items.append(make_item("multiline_command", line_no, active.strip(), raw=line))

    summary = Counter(str(item["kind"]) for item in items)
    result = {
        "schema": "typst-to-tex-source-scan-v1",
        "source": str(args.source_typ),
        "items": items,
        "summary": dict(sorted(summary.items())),
    }

    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"source_scan={args.output}")
        print(f"items={len(items)}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
