#!/usr/bin/env python3
"""Audit mechanical Typst-to-TeX conversion invariants.

Usage:
    audit_tex_conversion.py source.typ output.tex [--fix] [--tex-evidence sample.tex]

The optional --fix mode only applies local, syntax-preserving TeX fixes:
label/reference key unescaping and child-only \figref{...} repair when the
parent/child subfigure map is present in the TeX output.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


KEY_CMD_RE = re.compile(r"\\(label|ref|eqref|figref|tabref|secref|subref|cite)\{([^{}]*)\}")
FORBIDDEN_UNITS_RE = re.compile(r"\\(?:meter|per|degree|newton|radian|milli)\b")
ACTIVE_TYPST_RE = re.compile(r"(#(?:qty|unit|subpar_grid|figure)\b|(?<![\\A-Za-z0-9_.-])@[A-Za-z0-9][A-Za-z0-9_.:-]*|<[A-Za-z][A-Za-z0-9_:-]+>)")
FALLBACK_RE = re.compile(r"FIXME\s+typst-to-tex:")
CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
CJK_SUPPORT_RE = re.compile(r"CJKutf8|\\begin\{CJK|xeCJK|luatexja|pLaTeX|upLaTeX", re.I)
NOTE_RE = re.compile(r"#(?:l|r)note\[[^\]]*\]")
PACKAGE_RE = re.compile(r"\\usepackage(?:\[[^\]]*\])?\{([^{}]+)\}")
DOCUMENTCLASS_RE = re.compile(r"\\documentclass(?:\[[^\]]*\])?\{([^{}]+)\}")
RAW_TYPST_MATH_RE = re.compile(
    r"(?<!\\)\b(?:alpha|beta|gamma|delta|theta|omega|tau|pi)(?:_[A-Za-z]|\b)"
    r"|(?<!\\)\b(?:integral|dots|tilde\.eq|plus\.minus|dd)\b"
    r"|(?<!\\)\bmax\s*\("
)
STRAIGHT_CJK_QUOTE_RE = re.compile(r'[\u3040-\u30ff\u3400-\u9fff][^"\n]*"[^"\n]+"')
UNUSED_PACKAGE_RULES = {
    "algorithmic": re.compile(r"\\begin\{algorithmic\}"),
    "threeparttable": re.compile(r"\\begin\{threeparttable\}"),
    "ulem": re.compile(r"\\(?:uline|uuline|uwave|sout|xout)\b"),
}
DISPLAY_ENVS = ("align", "equation", "gather", "multline")


def active_part(line: str) -> str:
    """Return the part before an unescaped TeX comment marker."""
    for idx, char in enumerate(line):
        if char == "%" and (idx == 0 or line[idx - 1] != "\\"):
            return line[:idx]
    return line


def is_comment_line(line: str) -> bool:
    return line.lstrip().startswith("%")


def source_comment_texts(lines: list[str]) -> list[str]:
    comments: list[str] = []
    for line in lines:
        if "//" in line:
            comments.append(line.split("//", 1)[1].strip())
    return comments


def tex_comment_texts(lines: list[str]) -> list[str]:
    comments: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("%"):
            comments.append(stripped[1:].strip())
    return comments


def comment_buckets(lines: list[str], source: bool) -> dict[str, Counter[str]]:
    buckets: dict[str, Counter[str]] = defaultdict(Counter)
    current = "__preamble__"
    for line in lines:
        active = typst_active_part(line) if source else active_part(line)
        heading_match = (
            re.match(r"^\s*=+\s+(.+?)\s*$", active)
            if source
            else re.search(r"\\(?:section|subsection|subsubsection)\*?\{([^{}]*)\}", active)
        )
        if heading_match:
            current = normalize_heading(heading_match.group(1))
        if source:
            if "//" in line:
                text = line.split("//", 1)[1].strip()
                if text:
                    buckets[current][text] += 1
        elif line.lstrip().startswith("%"):
            text = line.lstrip()[1:].strip()
            if text:
                buckets[current][text] += 1
    return buckets


def typst_active_part(line: str) -> str:
    return line.split("//", 1)[0]


def source_active_labels(lines: list[str]) -> set[str]:
    labels: set[str] = set()
    for line in lines:
        labels.update(re.findall(r"<([A-Za-z][A-Za-z0-9_:-]+)>", typst_active_part(line)))
    return labels


def source_active_notes(lines: list[str]) -> list[str]:
    notes: list[str] = []
    for line in lines:
        notes.extend(NOTE_RE.findall(typst_active_part(line)))
    return notes


def source_math_let_definitions(lines: list[str]) -> set[str]:
    definitions: set[str] = set()
    for line in lines:
        active = typst_active_part(line)
        if re.match(r"\s*#let\s+[A-Za-z][A-Za-z0-9_]*\s*=", active):
            definitions.add(active.strip())
    return definitions


def source_multiline_caption_stats(lines: list[str]) -> tuple[int, int]:
    block_count = 0
    comment_count = 0
    idx = 0
    while idx < len(lines):
        active = typst_active_part(lines[idx])
        if re.search(r"caption\s*:\s*\[", active) and "]" not in active.split("[", 1)[1]:
            block_count += 1
            idx += 1
            while idx < len(lines):
                if "//" in lines[idx]:
                    comment_count += 1
                if "]" in typst_active_part(lines[idx]):
                    break
                idx += 1
        idx += 1
    return block_count, comment_count


def tex_multiline_caption_stats(lines: list[str]) -> tuple[int, int]:
    block_count = 0
    comment_count = 0
    in_caption = False
    brace_depth = 0
    for line in lines:
        active = active_part(line)
        if not in_caption:
            match = re.search(r"\\caption(?:\[[^\]]*\])?\{", active)
            if not match:
                continue
            tail = active[match.end():]
            brace_depth = 1 + tail.count("{") - tail.count("}")
            if brace_depth > 0:
                in_caption = True
                block_count += 1
            continue

        if is_comment_line(line):
            comment_count += 1
        brace_depth += active.count("{") - active.count("}")
        if brace_depth <= 0:
            in_caption = False
    return block_count, comment_count


def normalize_heading(text: str) -> str:
    text = re.sub(r"<[A-Za-z][A-Za-z0-9_:-]+>", "", text)
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", "", text)
    text = re.sub(r"[{}]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def source_headings(lines: list[str]) -> list[str]:
    headings: list[str] = []
    for line in lines:
        match = re.match(r"^\s*=+\s+(.+?)\s*$", typst_active_part(line))
        if match:
            headings.append(normalize_heading(match.group(1)))
    return headings


def tex_headings(lines: list[str]) -> list[str]:
    headings: list[str] = []
    for line in lines:
        if is_comment_line(line):
            continue
        for match in re.finditer(r"\\(?:section|subsection|subsubsection)\*?\{([^{}]*)\}", active_part(line)):
            headings.append(normalize_heading(match.group(1)))
    return headings


def tex_active_labels(lines: list[str]) -> set[str]:
    labels: set[str] = set()
    for line in lines:
        if not is_comment_line(line):
            labels.update(re.findall(r"\\label\{([^{}]+)\}", active_part(line)))
    return labels


def tex_active_text(lines: list[str]) -> str:
    return "\n".join(active_part(line) for line in lines if not is_comment_line(line))


def tex_active_body_text(lines: list[str]) -> str:
    body: list[str] = []
    in_body = False
    for line in lines:
        if r"\begin{document}" in line:
            in_body = True
        if in_body and not is_comment_line(line):
            body.append(active_part(line))
    return "\n".join(body)


def tex_full_text_without_comments(lines: list[str]) -> str:
    return "\n".join(active_part(line) for line in lines)


def documentclass_name(text: str) -> str | None:
    match = DOCUMENTCLASS_RE.search(text)
    return match.group(1) if match else None


def normalized_command(text: str, command: str) -> str | None:
    match = re.search(rf"\\{command}\s*(?:\{{[^{{}}]*\}}\s*){{2}}", text)
    if not match:
        return None
    args = re.findall(r"\{([^{}]*)\}", match.group(0))
    return "|".join(re.sub(r"\s+", " ", arg).strip() for arg in args)


def has_nonempty_command_arg(text: str, command: str) -> bool:
    return any(value.strip() for value in re.findall(rf"\\{command}\{{([^{{}}]*)\}}", text))


def has_empty_command_arg(text: str, command: str) -> bool:
    return bool(re.search(rf"\\{command}\{{\s*\}}", text))


def package_names(text: str) -> set[str]:
    names: set[str] = set()
    for match in PACKAGE_RE.finditer(text):
        names.update(name.strip() for name in match.group(1).split(","))
    return names


def grouped_citation_style(text: str) -> bool:
    return bool(re.search(r"\\cite\{[^{}]+,[^{}]+\}", text))


def display_env_counts(text: str) -> Counter[str]:
    return Counter(re.findall(r"\\begin\{(" + "|".join(DISPLAY_ENVS) + r")\}", text))


def source_math_let_names(lines: list[str]) -> set[str]:
    names: set[str] = set()
    for line in lines:
        match = re.match(r"^\s*#let\s+([A-Za-z][A-Za-z0-9_]*)\s*=\s*\$", typst_active_part(line))
        if match:
            names.add(match.group(1))
    return names


def subfigure_parent_map(lines: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    in_figure = False
    children: list[str] = []
    parent: str | None = None

    def flush() -> None:
        if parent:
            for child in children:
                mapping[child] = parent

    for raw in lines:
        line = active_part(raw)
        if r"\begin{figure" in line:
            in_figure = True
            children = []
            parent = None
        if in_figure:
            labels = re.findall(r"\\label\{([^{}]+)\}", line)
            if r"\subfloat" in line:
                children.extend(labels)
            else:
                for label in labels:
                    if label.startswith("fig:"):
                        parent = label
        if in_figure and r"\end{figure" in line:
            flush()
            in_figure = False
    return mapping


def fix_key_escapes(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(2).replace(r"\_", "_")
        return rf"\{match.group(1)}{{{key}}}"

    return KEY_CMD_RE.sub(repl, text)


def fix_child_figrefs(text: str, child_to_parent: dict[str, str]) -> str:
    for child, parent in child_to_parent.items():
        text = text.replace(rf"\figref{{{child}}}", rf"\figref{{{parent}}}\subref{{{child}}}")
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_typ", type=Path)
    parser.add_argument("output_tex", type=Path)
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--tex-evidence", type=Path, default=None)
    args = parser.parse_args()

    source_lines = args.source_typ.read_text(encoding="utf-8").splitlines()
    tex_text = args.output_tex.read_text(encoding="utf-8")

    if args.fix:
        tex_text = fix_key_escapes(tex_text)
        tex_text = fix_child_figrefs(tex_text, subfigure_parent_map(tex_text.splitlines()))
        args.output_tex.write_text(tex_text, encoding="utf-8")

    tex_lines = tex_text.splitlines()
    active_lines = [active_part(line) for line in tex_lines if not is_comment_line(line)]
    active_body = tex_active_body_text(tex_lines)

    failures: list[str] = []
    warnings: list[str] = []

    fallback_markers = [(idx + 1, line.strip()) for idx, line in enumerate(tex_lines) if FALLBACK_RE.search(line)]
    if fallback_markers:
        failures.append(f"unresolved fallback markers remain: {len(fallback_markers)}")
        warnings.extend(f"fallback marker line: {line_no}: {line}" for line_no, line in fallback_markers[:10])

    source_comments = [c for c in source_comment_texts(source_lines) if c]
    output_comments = tex_comment_texts(tex_lines)
    source_comment_counts = Counter(source_comments)
    output_comment_counts = Counter(output_comments)
    missing_comments = [
        c for c, count in source_comment_counts.items()
        if output_comment_counts[c] < count
    ]
    if missing_comments:
        failures.append(f"missing source comment lines: {len(missing_comments)} / {len(source_comments)}")
        warnings.extend(f"missing comment: {c}" for c in missing_comments[:10])

    duplicated_comments = [
        c for c, count in source_comment_counts.items()
        if output_comment_counts[c] > count
    ]
    if duplicated_comments:
        failures.append(f"duplicated source comment lines: {len(duplicated_comments)}")
        warnings.extend(f"duplicated comment: {c}" for c in duplicated_comments[:10])

    source_buckets = comment_buckets(source_lines, source=True)
    output_buckets = comment_buckets(tex_lines, source=False)
    misplaced_comments: list[str] = []
    for bucket, comments in source_buckets.items():
        for comment, count in comments.items():
            if output_buckets[bucket][comment] < count:
                misplaced_comments.append(f"{bucket}: {comment}")
    if misplaced_comments:
        failures.append(f"source comments missing from matching heading buckets: {len(misplaced_comments)}")
        warnings.extend(f"misplaced/missing bucket comment: {c}" for c in misplaced_comments[:10])

    source_notes = source_active_notes(source_lines)
    missing_notes = [
        note for note, count in Counter(source_notes).items()
        if output_comment_counts[note] < count
    ]
    if missing_notes:
        failures.append(f"missing active Typst note comments: {len(missing_notes)} / {len(source_notes)}")
        warnings.extend(f"missing note: {note}" for note in missing_notes[:10])

    output_source_notes = [comment for comment in output_comments if NOTE_RE.fullmatch(comment)]
    extra_notes = Counter(output_source_notes) - Counter(source_notes)
    if extra_notes:
        failures.append(f"extra Typst note comments not present as active source notes: {sum(extra_notes.values())}")
        warnings.extend(f"extra note comment: {note}" for note in list(extra_notes)[:10])

    source_lets = source_math_let_definitions(source_lines)
    output_let_notes = [comment for comment in output_comments if comment.startswith("Source-local definition converted")]
    if output_let_notes and not source_lets:
        failures.append("extra source-local-definition comment without source definition")
    elif output_let_notes:
        failures.append("source-local definitions should become TeX mechanisms, not explanatory output comments")

    source_heading_list = source_headings(source_lines)
    tex_heading_list = tex_headings(tex_lines)
    if source_heading_list != tex_heading_list:
        failures.append(f"heading sequence mismatch: source={len(source_heading_list)} output={len(tex_heading_list)}")
        for idx, (source_heading, tex_heading) in enumerate(zip(source_heading_list, tex_heading_list), start=1):
            if source_heading != tex_heading:
                warnings.append(f"heading mismatch {idx}: source={source_heading!r} output={tex_heading!r}")
                break

    source_labels = source_active_labels(source_lines)
    output_labels = tex_active_labels(tex_lines)
    missing_active_labels = sorted(source_labels - output_labels)
    if missing_active_labels:
        failures.append(f"missing active labels: {', '.join(missing_active_labels[:10])}")
    extra_active_labels = sorted(output_labels - source_labels)
    if extra_active_labels:
        failures.append(f"extra active labels not present in source: {', '.join(extra_active_labels[:10])}")

    active_typst = [(idx + 1, line.strip()) for idx, line in enumerate(active_lines) if ACTIVE_TYPST_RE.search(line)]
    if active_typst:
        failures.append(f"active Typst syntax remains: {len(active_typst)} line(s)")
        warnings.extend(f"active Typst line: {line_no}: {line}" for line_no, line in active_typst[:10])

    orphan_typst_delimiters = [
        (idx + 1, line.strip())
        for idx, line in enumerate(active_lines)
        if line.strip() in {")", "]", "},"}
    ]
    if orphan_typst_delimiters:
        failures.append(f"orphan Typst wrapper delimiters remain active: {len(orphan_typst_delimiters)}")
        warnings.extend(f"orphan delimiter line: {line_no}: {line}" for line_no, line in orphan_typst_delimiters[:10])

    escaped_keys = KEY_CMD_RE.findall("\n".join(active_lines))
    escaped_keys = [(cmd, key) for cmd, key in escaped_keys if r"\_" in key]
    if escaped_keys:
        failures.append(f"escaped label/reference keys: {len(escaped_keys)}")

    forbidden_units = FORBIDDEN_UNITS_RE.findall("\n".join(active_lines))
    if forbidden_units:
        failures.append(f"forbidden siunitx unit macros: {len(forbidden_units)}")

    degree_quantities = re.findall(r"\\SI\{[^{}]+\}\{deg\}", "\n".join(active_lines))
    if degree_quantities:
        failures.append(f"angle quantities should use \\ang, not raw deg SI: {len(degree_quantities)}")

    if "#bibliography" in "\n".join(source_lines):
        active_bib = re.search(r"^\s*\\bibliographystyle\{|^\s*\\bibliography\{", "\n".join(active_lines), re.M)
        if not active_bib:
            failures.append("active source bibliography has no active TeX bibliography commands")

    if CJK_RE.search("\n".join(source_lines)) and CJK_RE.search("\n".join(active_lines)) and not CJK_SUPPORT_RE.search(tex_text):
        failures.append("active CJK text present without explicit CJK engine/package support")

    if CJK_RE.search("\n".join(source_lines)) and "CJKutf8" in tex_text and r"\begin{CJK}{" in tex_text:
        failures.append("CJKutf8 output uses non-star CJK environment; use CJK* unless TeX evidence requires non-star CJK")

    child_to_parent = subfigure_parent_map(tex_lines)
    active_text = "\n".join(active_lines)
    child_only = [child for child in child_to_parent if re.search(rf"\\figref\{{{re.escape(child)}\}}", active_text)]
    if child_only:
        failures.append(f"child labels used as sole figure refs: {', '.join(child_only[:10])}")

    source_grouped = sum(1 for line in source_lines if "#subpar_grid" in line)
    active_subfloats = len(re.findall(r"\\subfloat", active_text))
    if source_grouped and active_subfloats == 0:
        failures.append("source grouped figures found, but no active TeX subfloat output")

    if active_subfloats and r"\captionsetup[subfloat]" not in tex_text:
        failures.append("active subfloat output lacks required subfloat caption setup")

    source_block_captions, source_block_caption_comments = source_multiline_caption_stats(source_lines)
    tex_block_captions, tex_block_caption_comments = tex_multiline_caption_stats(tex_lines)
    if source_block_captions and tex_block_captions != source_block_captions:
        failures.append(
            f"caption block line-shape mismatch: source_multiline={source_block_captions} output_multiline={tex_block_captions}"
        )
    if source_block_caption_comments and tex_block_caption_comments != source_block_caption_comments:
        failures.append(
            f"caption block comment placement mismatch: source_inside={source_block_caption_comments} output_inside={tex_block_caption_comments}"
        )

    active_escaped_math = re.findall(r"\b[A-Za-z]+\\_[A-Za-z0-9]+", active_text)
    if active_escaped_math:
        failures.append(f"escaped math identifiers in active text: {len(active_escaped_math)}")

    adjacent_cites = re.findall(r"\\cite\{[^{}]+\}\s*\\cite\{[^{}]+\}", active_body)
    if adjacent_cites:
        failures.append(f"adjacent citation commands should be grouped: {len(adjacent_cites)}")

    raw_typst_math = [(idx + 1, line.strip()) for idx, line in enumerate(active_body.splitlines()) if RAW_TYPST_MATH_RE.search(line)]
    if raw_typst_math:
        failures.append(f"raw Typst math tokens remain in active body: {len(raw_typst_math)} line(s)")
        warnings.extend(f"raw math token line: {line_no}: {line}" for line_no, line in raw_typst_math[:10])

    cases_with_rendered_commas = re.findall(r"\\begin\{cases\}.*?,\s*\\\\", active_body, flags=re.S)
    if "cases(" in "\n".join(source_lines) and cases_with_rendered_commas:
        failures.append(f"Typst case separators rendered as equation punctuation: {len(cases_with_rendered_commas)}")

    unresolved_math_lets = [
        name for name in sorted(source_math_let_names(source_lines))
        if re.search(rf"(?<!\\)\b{re.escape(name)}\b", active_body)
    ]
    if unresolved_math_lets:
        failures.append(f"source-local math definitions emitted as raw identifiers: {', '.join(unresolved_math_lets[:10])}")

    if r"\mathrm{" in active_body:
        failures.append("active body uses \\mathrm; use \\text for Typst math text fragments")

    if "vb(" in "\n".join(source_lines) and r"\usepackage{physics}" in tex_text and r"\mathbf{" in active_body:
        failures.append("Typst vector notation converted to raw \\mathbf despite physics package evidence")

    if r"\DeclareSIUnit" in tex_text:
        failures.append("custom siunitx unit macro defined; use raw units in \\SI/\\si")

    if r"\sisetup" in tex_text and (not args.tex_evidence or r"\sisetup" not in args.tex_evidence.read_text(encoding="utf-8", errors="replace")):
        failures.append("global \\sisetup added without TeX evidence")

    repeated_blank_runs = re.findall(r"\n[ \t]*\n[ \t]*\n", tex_text)
    if len(repeated_blank_runs) > 3:
        failures.append(f"excess repeated blank-line runs: {len(repeated_blank_runs)}")

    if "set enum(" in "\n".join(source_lines) and r"\renewcommand{\labelenumi}" in active_body:
        failures.append("Typst enum options converted by local label redefinition; use enumitem options when available")

    straight_cjk_quotes = [
        (idx + 1, line.strip())
        for idx, line in enumerate(active_body.splitlines())
        if STRAIGHT_CJK_QUOTE_RE.search(line)
    ]
    if straight_cjk_quotes:
        failures.append(f"straight double quotes remain in active CJK text: {len(straight_cjk_quotes)} line(s)")
        warnings.extend(f"straight quote line: {line_no}: {line}" for line_no, line in straight_cjk_quotes[:10])

    if args.tex_evidence:
        evidence_text = args.tex_evidence.read_text(encoding="utf-8", errors="replace")
        output_full_text = tex_full_text_without_comments(tex_lines)
        evidence_class = documentclass_name(evidence_text)
        output_class = documentclass_name(tex_text)
        if evidence_class and output_class and evidence_class != output_class:
            failures.append(f"documentclass differs from TeX evidence: output={output_class} evidence={evidence_class}")
        for command in ("markboth",):
            evidence_command = normalized_command(evidence_text, command)
            output_command = normalized_command(tex_text, command)
            if evidence_command and output_command and evidence_command != output_command:
                failures.append(f"reusable TeX scaffold command changed from evidence: \\{command}")

        if r"\documentclass{ieeeaccess}" in evidence_text and r"\documentclass{ieeeaccess}" in tex_text:
            scaffold_needles = [
                r"\AtBeginDocument{\DeclareMathVersion{bold}",
                r"\def\BibTeX",
                "%Your document starts from here ___________________________________________________",
            ]
            for needle in scaffold_needles:
                if needle in evidence_text and needle not in tex_text:
                    failures.append(f"missing reusable TeX scaffold from evidence: {needle}")

        for command in ("history", "doi"):
            if has_nonempty_command_arg(evidence_text, command) and has_empty_command_arg(tex_text, command):
                failures.append(f"empty \\{command} despite nonempty TeX evidence placeholder")

        output_packages = package_names(tex_text)
        active_output = "\n".join(active_lines)
        for package, usage_re in UNUSED_PACKAGE_RULES.items():
            if package in output_packages and not usage_re.search(active_output):
                failures.append(f"unused copied package: {package}")

        if "adjustbox" in output_packages and not re.search(r"\\(?:begin\{adjustbox\}|adjustbox\b|includegraphics\[[^]]*(?:valign|frame|margin))", active_output):
            failures.append("unused copied package: adjustbox")

        evidence_envs = display_env_counts(tex_full_text_without_comments(evidence_text.splitlines()))
        output_envs = display_env_counts(active_body)
        dominant_evidence_envs = [env for env, count in evidence_envs.items() if count > 0]
        if dominant_evidence_envs:
            preferred = evidence_envs.most_common(1)[0][0]
            for env, count in output_envs.items():
                if env != preferred and evidence_envs[env] == 0 and count > 0:
                    failures.append(f"display math environment differs from TeX evidence: {env} used, expected {preferred}")

        if grouped_citation_style(evidence_text) and adjacent_cites:
            failures.append("TeX evidence groups adjacent citations, but output keeps them split")

    print(f"source_headings={len(source_heading_list)} output_headings={len(tex_heading_list)}")
    print(f"source_comments={len(source_comments)} output_comment_lines={len(output_comments)}")
    print(f"active_subfloats={active_subfloats} child_parent_map={len(child_to_parent)}")
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"- {warning}")
    if failures:
        print("FAIL:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
