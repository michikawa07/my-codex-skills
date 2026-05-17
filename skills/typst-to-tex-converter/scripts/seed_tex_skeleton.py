#!/usr/bin/env python3
"""Create a block-marker TeX seed from TeX evidence and Typst source.

The seed is intentionally incomplete. It preserves TeX scaffold evidence,
Typst heading order, source comments/notes in local order, and inserts one
local marker for each active Typst source span that still needs conversion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


HEADING_RE = re.compile(r"^(\s*)(=+)\s+(.+?)\s*$")
NOTE_RE = re.compile(r"#(?:l|r)note\[[^\]]*\]")
LABEL_RE = re.compile(r"\s*<([A-Za-z][A-Za-z0-9_:-]+)>\s*$")
STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')


def typst_active_part(line: str) -> str:
    return line.split("//", 1)[0]


def has_active_content(line: str) -> bool:
    return bool(typst_active_part(line).strip())


def heading_command(level: int) -> str:
    if level <= 1:
        return "section"
    if level == 2:
        return "subsection"
    return "subsubsection"


def split_heading(raw: str) -> tuple[str, str | None]:
    label_match = LABEL_RE.search(raw)
    label = label_match.group(1) if label_match else None
    title = LABEL_RE.sub("", raw).strip()
    return title, label


def block_id(kind: str, start_line: int, end_line: int, text: str) -> str:
    digest = hashlib.sha1(f"{kind}\0{start_line}\0{end_line}\0{text}".encode("utf-8")).hexdigest()[:10]
    return f"{kind}-{start_line}-{end_line}-{digest}"


def evidence_preamble(evidence: Path | None) -> str:
    if not evidence:
        return "\\documentclass{article}\n"
    text = evidence.read_text(encoding="utf-8", errors="replace")
    marker = r"\begin{document}"
    preamble = text.split(marker, 1)[0].rstrip() if marker in text else text.rstrip()
    return preamble + "\n"


def evidence_placeholder_commands(evidence: Path | None) -> list[str]:
    if not evidence:
        return []
    text = evidence.read_text(encoding="utf-8", errors="replace")
    commands: list[str] = []
    for command in ("history", "doi"):
        match = re.search(rf"\\{command}\{{[^{{}}]*\}}", text)
        if match:
            commands.append(match.group(0))
    return commands


def line_excerpt(lines: list[str], start_line: int, end_line: int) -> str:
    return "\n".join(lines[start_line - 1:end_line]).strip()


def make_body_block(
    out: list[str],
    blocks: list[dict[str, object]],
    lines: list[str],
    kind: str,
    start_line: int,
    end_line: int,
    heading: str | None,
) -> None:
    if start_line > end_line:
        return
    source = line_excerpt(lines, start_line, end_line)
    if not source:
        return
    ident = block_id(kind, start_line, end_line, source)
    out.append(f"% BEGIN typst-to-tex block id={ident} lines={start_line}-{end_line} kind={kind}")
    out.append(f"% FIXME typst-to-tex: convert source lines {start_line}-{end_line} here.")
    out.append(f"% END typst-to-tex block id={ident}")
    blocks.append(
        {
            "id": ident,
            "kind": kind,
            "heading": heading,
            "start_line": start_line,
            "end_line": end_line,
            "source": source,
            "status": "pending",
        }
    )


def emit_comment_and_notes(out: list[str], line: str) -> None:
    if "//" in line:
        out.append(f"%{line.split('//', 1)[1].rstrip()}")
    for note in NOTE_RE.findall(typst_active_part(line)):
        out.append(f"% {note}")


def bracket_delta(active: str) -> int:
    scrubbed = STRING_RE.sub('""', active)
    opens = scrubbed.count("(") + scrubbed.count("[") + scrubbed.count("{")
    closes = scrubbed.count(")") + scrubbed.count("]") + scrubbed.count("}")
    return opens - closes


def emit_source_region(
    out: list[str],
    blocks: list[dict[str, object]],
    lines: list[str],
    start_line: int,
    end_line: int,
    heading: str | None,
    kind: str,
) -> None:
    pending_start: int | None = None
    pending_end: int | None = None
    depth = 0

    def flush() -> None:
        nonlocal pending_start, pending_end, depth
        if pending_start is not None and pending_end is not None:
            make_body_block(out, blocks, lines, kind, pending_start, pending_end, heading)
        pending_start = None
        pending_end = None
        depth = 0

    for line_no in range(start_line, end_line + 1):
        line = lines[line_no - 1]
        active = typst_active_part(line)

        if active.strip():
            if pending_start is None:
                pending_start = line_no
            pending_end = line_no
            depth = max(0, depth + bracket_delta(active))
            continue

        if pending_start is not None and depth > 0:
            pending_end = line_no
            continue

        if "//" in line or NOTE_RE.search(active):
            if pending_start is not None:
                flush()
            emit_comment_and_notes(out, line)
        elif not active.strip():
            flush()
    flush()


def seed_lines(source: Path, evidence: Path | None) -> tuple[list[str], list[dict[str, object]]]:
    lines = source.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    blocks: list[dict[str, object]] = []
    out.extend(evidence_preamble(evidence).splitlines())

    first_heading = next(
        (idx + 1 for idx, line in enumerate(lines) if HEADING_RE.match(typst_active_part(line))),
        None,
    )

    if first_heading and first_heading > 1:
        emit_source_region(out, blocks, lines, 1, first_heading - 1, "__metadata__", "metadata")
        out.append("")

    out.append(r"\begin{document}")
    out.extend(evidence_placeholder_commands(evidence))
    out.append("")

    heading_positions: list[tuple[int, int, str, str | None]] = []
    for line_no, line in enumerate(lines, start=1):
        heading = HEADING_RE.match(typst_active_part(line))
        if not heading:
            continue
        level = len(heading.group(2))
        title, label = split_heading(heading.group(3))
        heading_positions.append((line_no, level, title, label))

    for idx, (line_no, level, title, label) in enumerate(heading_positions):
        cmd = heading_command(level)
        if label:
            out.append(rf"\{cmd}{{{title}}}\label{{{label}}}")
        else:
            out.append(rf"\{cmd}{{{title}}}")
        emit_comment_and_notes(out, lines[line_no - 1])

        region_start = line_no + 1
        region_end = heading_positions[idx + 1][0] - 1 if idx + 1 < len(heading_positions) else len(lines)
        emit_source_region(out, blocks, lines, region_start, region_end, title, "body")
        out.append("")

    out.append(r"\end{document}")
    return out, blocks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_typ", type=Path)
    parser.add_argument("output_tex", type=Path)
    parser.add_argument("--tex-evidence", type=Path, default=None)
    parser.add_argument("--block-ledger", type=Path, default=None)
    args = parser.parse_args()

    out, blocks = seed_lines(args.source_typ, args.tex_evidence)
    args.output_tex.parent.mkdir(parents=True, exist_ok=True)
    args.output_tex.write_text("\n".join(out) + "\n", encoding="utf-8")

    if args.block_ledger:
        ledger = {
            "schema": "typst-to-tex-block-ledger-v1",
            "source": str(args.source_typ),
            "output": str(args.output_tex),
            "blocks": blocks,
            "pending_blocks": len(blocks),
        }
        args.block_ledger.parent.mkdir(parents=True, exist_ok=True)
        args.block_ledger.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"block_ledger={args.block_ledger}")

    print(f"seed_tex={args.output_tex}")
    print(f"blocks={len(blocks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
