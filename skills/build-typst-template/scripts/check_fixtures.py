#!/usr/bin/env python3
"""Compile and check three project-declared Typst template fixtures."""
from __future__ import annotations

import argparse
from collections import Counter
import difflib
import hashlib
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Sequence

from inspect_evidence import (
    EvidenceError, execute, extract_pdf_text, pdf_fonts, pdf_info, sha256, tool_version,
)


ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
KINDS = {"official", "frontmatter", "body-flow"}
TOP_KEYS = {
    "project_root", "template_entry", "entry_symbol", "font_paths",
    "comparison_dpi", "bibliography_data", "bibliography_style_asset",
    "fixtures",
}
FIXTURE_KEYS = {
    "id", "kind", "source", "reference_pdf", "required_text",
    "required_text_file", "ordered_text", "minimum_pages", "page_flows",
    "geometry_tolerance_pt", "text_thresholds",
}
FLOW_KEYS = {"start", "end", "following"}
THRESHOLD_KEYS = {"reference_coverage", "candidate_precision", "ordered_similarity"}
MINIMUM_TEXT_THRESHOLDS = {
    "reference_coverage": 0.95,
    "candidate_precision": 0.95,
    "ordered_similarity": 0.90,
}
LAYOUT_ANCHOR_TOLERANCE_PT = 0.25
MINIMUM_WORD_ANCHOR_COVERAGE = 0.50
LAYOUT_VERTICAL_BANDS = 8
REPAIR_TARGET_LIMIT = 12
ABSOLUTE_DIMENSION_RE = re.compile(
    r"(?<![A-Za-z0-9_.])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:pt|mm|cm|in)(?![A-Za-z])"
)
LAYOUT_CONSTRUCT_RE = re.compile(
    r"#\s*(?:set\s+)?(align|place|move|rotate|scale|block|box|grid|columns|"
    r"pagebreak|colbreak|linebreak|v|h|text|par|image|table)\b"
)
LAYOUT_PROPERTY_RE = re.compile(
    r"\b(width|height|dx|dy|inset|outset|spacing|column-gutter|row-gutter|gutter|"
    r"leading|first-line-indent|font|size|margin|top|bottom|left|right|align|position)\s*:"
)


class CheckError(RuntimeError):
    pass


class InputError(CheckError):
    pass


def require_keys(value: dict[str, Any], allowed: set[str], required: set[str], label: str) -> None:
    unknown, missing = set(value) - allowed, required - set(value)
    if unknown or missing:
        details = []
        if unknown:
            details.append("unknown=" + ",".join(sorted(unknown)))
        if missing:
            details.append("missing=" + ",".join(sorted(missing)))
        raise InputError(f"{label} has invalid fields ({'; '.join(details)})")


def string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise InputError(f"{label} must be a nonempty string")
    return value


def string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        raise InputError(f"{label} must be an array")
    result = [string(item, f"{label} item") for item in value]
    if len(result) != len(set(result)):
        raise InputError(f"{label} must not contain duplicates")
    return result


def ratio(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise InputError(f"{label} must be a finite number")
    if not 0 <= value <= 1:
        raise InputError(f"{label} must be between zero and one")
    return float(value)


def project_file(root: Path, value: Any, label: str) -> Path:
    raw = Path(string(value, label))
    if raw.is_absolute() or ".." in raw.parts:
        raise InputError(f"{label} must be project-relative without '..'")
    result = (root / raw).resolve()
    try:
        result.relative_to(root)
    except ValueError as error:
        raise InputError(f"{label} resolves outside project_root") from error
    if not result.is_file():
        raise InputError(f"{label} not found: {result}")
    return result


def read_required_text(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]


def load_config(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise InputError(f"checks file not found: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InputError(f"invalid checks JSON: {error}") from error
    if not isinstance(raw, dict):
        raise InputError("checks JSON must be an object")
    require_keys(raw, TOP_KEYS, {"template_entry", "entry_symbol", "fixtures"}, "checks")
    project_raw = Path(raw.get("project_root", "."))
    if project_raw.is_absolute() or ".." in project_raw.parts:
        raise InputError("project_root must be relative without '..'")
    root = (path.parent / project_raw).resolve()
    if not root.is_dir():
        raise InputError(f"project_root is not a directory: {root}")
    template = project_file(root, raw["template_entry"], "template_entry")
    symbol = string(raw["entry_symbol"], "entry_symbol")
    if not IDENTIFIER.fullmatch(symbol) or symbol.startswith("_"):
        raise InputError("entry_symbol must be a public Typst identifier")
    font_paths = []
    for index, item in enumerate(raw.get("font_paths", [])):
        value = Path(string(item, f"font_paths[{index}]")).expanduser()
        resolved = value.resolve() if value.is_absolute() else (root / value).resolve()
        if not resolved.is_dir():
            raise InputError(f"font path is not a directory: {resolved}")
        font_paths.append(resolved)
    bibliography_data = (
        project_file(root, raw["bibliography_data"], "bibliography_data")
        if "bibliography_data" in raw else None
    )
    bibliography_style = (
        project_file(root, raw["bibliography_style_asset"], "bibliography_style_asset")
        if "bibliography_style_asset" in raw else None
    )
    if bibliography_style is not None and bibliography_data is None:
        raise InputError("bibliography_style_asset requires bibliography_data")
    dpi = raw.get("comparison_dpi", 300)
    if isinstance(dpi, bool) or not isinstance(dpi, int) or not 300 <= dpi <= 1200:
        raise InputError("comparison_dpi must be an integer from 300 to 1200")
    fixture_items = raw["fixtures"]
    if not isinstance(fixture_items, list) or len(fixture_items) != 3:
        raise InputError("fixtures must contain exactly three project-declared fixtures")
    fixtures, ids, kinds = [], set(), set()
    for index, item in enumerate(fixture_items):
        label = f"fixtures[{index}]"
        if not isinstance(item, dict):
            raise InputError(f"{label} must be an object")
        require_keys(item, FIXTURE_KEYS, {"id", "kind", "source"}, label)
        fixture_id = string(item["id"], f"{label}.id")
        if not ID.fullmatch(fixture_id) or fixture_id in ids:
            raise InputError(f"{label}.id must be unique and safe")
        ids.add(fixture_id)
        kind = string(item["kind"], f"{label}.kind")
        if kind not in KINDS or kind in kinds:
            raise InputError("fixtures must contain one unique official, frontmatter, and body-flow kind")
        kinds.add(kind)
        source = project_file(root, item["source"], f"{label}.source")
        required_text = string_list(item.get("required_text", []), f"{label}.required_text")
        required_file = None
        if "required_text_file" in item:
            required_file = project_file(root, item["required_text_file"], f"{label}.required_text_file")
            required_text.extend(read_required_text(required_file))
        ordered_text = string_list(item.get("ordered_text", []), f"{label}.ordered_text")
        minimum_pages = item.get("minimum_pages", 1)
        if isinstance(minimum_pages, bool) or not isinstance(minimum_pages, int) or minimum_pages < 1:
            raise InputError(f"{label}.minimum_pages must be a positive integer")
        raw_flows = item.get("page_flows", [])
        if not isinstance(raw_flows, list):
            raise InputError(f"{label}.page_flows must be an array")
        flows = []
        for flow_index, flow in enumerate(raw_flows):
            flow_label = f"{label}.page_flows[{flow_index}]"
            if not isinstance(flow, dict):
                raise InputError(f"{flow_label} must be an object")
            require_keys(flow, FLOW_KEYS, FLOW_KEYS, flow_label)
            parsed = {key: string(flow[key], f"{flow_label}.{key}") for key in FLOW_KEYS}
            if len(set(parsed.values())) != 3:
                raise InputError(f"{flow_label} markers must be distinct")
            flows.append(parsed)
        fixture: dict[str, Any] = {
            "id": fixture_id, "kind": kind, "source": source,
            "required_text": required_text, "required_text_file": required_file,
            "ordered_text": ordered_text, "minimum_pages": minimum_pages,
            "page_flows": flows,
        }
        official_only = {"reference_pdf", "geometry_tolerance_pt", "text_thresholds"}
        present_official = official_only & set(item)
        if kind == "official":
            if present_official != official_only:
                raise InputError(f"{label} official fixture requires reference_pdf, geometry_tolerance_pt, and text_thresholds")
            if not required_text:
                raise InputError(f"{label} official fixture requires locked required text")
            fixture["reference_pdf"] = project_file(root, item["reference_pdf"], f"{label}.reference_pdf")
            tolerance = item["geometry_tolerance_pt"]
            if (isinstance(tolerance, bool) or not isinstance(tolerance, (int, float))
                    or not math.isfinite(tolerance) or not 0 <= tolerance <= 0.1):
                raise InputError(f"{label}.geometry_tolerance_pt must be between 0 and 0.1")
            thresholds = item["text_thresholds"]
            if not isinstance(thresholds, dict):
                raise InputError(f"{label}.text_thresholds must be an object")
            require_keys(thresholds, THRESHOLD_KEYS, THRESHOLD_KEYS, f"{label}.text_thresholds")
            fixture["geometry_tolerance_pt"] = float(tolerance)
            fixture["text_thresholds"] = {
                key: ratio(thresholds[key], f"{label}.text_thresholds.{key}")
                for key in THRESHOLD_KEYS
            }
            for key, minimum in MINIMUM_TEXT_THRESHOLDS.items():
                if fixture["text_thresholds"][key] < minimum:
                    raise InputError(f"{label}.text_thresholds.{key} must be at least {minimum}")
        elif present_official:
            raise InputError(f"{label} uses official-only comparison fields")
        if kind == "frontmatter" and len(ordered_text) < 2:
            raise InputError(f"{label} frontmatter fixture requires at least two ordered markers")
        if kind == "body-flow" and (minimum_pages < 2 or len(flows) < 2):
            raise InputError(f"{label} body-flow fixture requires minimum_pages >= 2 and at least two page_flows")
        fixtures.append(fixture)
    if kinds != KINDS:
        raise InputError("fixtures must contain official, frontmatter, and body-flow")
    if len({fixture["source"] for fixture in fixtures}) != 3:
        raise InputError("fixture sources must be distinct")
    return {
        "path": path, "root": root, "template": template, "entry_symbol": symbol,
        "font_paths": font_paths, "bibliography_data": bibliography_data,
        "bibliography_style_asset": bibliography_style,
        "comparison_dpi": dpi, "fixtures": fixtures,
    }


def strip_comments(text: str) -> str:
    result, index, block_depth, quoted = [], 0, 0, False
    while index < len(text):
        if quoted:
            character = text[index]
            result.append(character)
            if character == "\\" and index + 1 < len(text):
                result.append(text[index + 1]); index += 2; continue
            if character == '"':
                quoted = False
            index += 1; continue
        if block_depth:
            if text.startswith("/*", index):
                block_depth += 1; result.extend("  "); index += 2
            elif text.startswith("*/", index):
                block_depth -= 1; result.extend("  "); index += 2
            else:
                result.append("\n" if text[index] == "\n" else " "); index += 1
            continue
        if text.startswith("//", index):
            end = text.find("\n", index)
            if end < 0:
                result.extend(" " * (len(text) - index)); break
            result.extend(" " * (end - index)); result.append("\n"); index = end + 1; continue
        if text.startswith("/*", index):
            block_depth = 1; result.extend("  "); index += 2; continue
        if text[index] == '"':
            quoted = True
        result.append(text[index]); index += 1
    return "".join(result)


def token_pattern(name: str) -> str:
    return rf"(?<![A-Za-z0-9_-]){re.escape(name)}(?![A-Za-z0-9_-])"


def strip_strings(text: str) -> str:
    """Blank quoted strings while retaining offsets and line structure."""
    result, index, quoted = [], 0, False
    while index < len(text):
        character = text[index]
        if quoted:
            if character == "\\" and index + 1 < len(text):
                result.extend("  "); index += 2; continue
            if character == '"':
                quoted = False
            result.append("\n" if character == "\n" else " "); index += 1; continue
        if character == '"':
            quoted = True; result.append(" "); index += 1; continue
        result.append(character); index += 1
    return "".join(result)


def source_layout_inventory(path: Path) -> dict[str, Any]:
    """Record layout-sensitive source observations without assigning ownership."""
    text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    records = []
    for number, line in enumerate(text.splitlines(), start=1):
        constructs = sorted(set(LAYOUT_CONSTRUCT_RE.findall(line)))
        properties = sorted(set(LAYOUT_PROPERTY_RE.findall(line)))
        dimensions = ABSOLUTE_DIMENSION_RE.findall(line)
        if constructs or properties or dimensions:
            records.append({
                "line": number,
                "constructs": constructs,
                "properties": properties,
                "absolute_dimensions": dimensions,
                "evidence": line.strip()[:300],
            })
    return {
        "path": str(path.resolve()),
        "observation_only": True,
        "records": records,
        "record_count": len(records),
        "absolute_dimension_count": sum(len(item["absolute_dimensions"]) for item in records),
    }


def bibliography_semantics(path: Path) -> dict[str, Any]:
    """Inventory standard Typst citation and bibliography syntax with line evidence."""
    text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    citations, bibliographies = [], []
    for number, line in enumerate(text.splitlines(), start=1):
        citation_keys = re.findall(r"(?<![\\A-Za-z0-9_-])@([A-Za-z0-9_:.+-]+)", line)
        cite_calls = len(re.findall(r"#\s*cite\s*\(", line))
        bibliography_calls = len(re.findall(r"#\s*bibliography\s*\(", line))
        if citation_keys or cite_calls:
            citations.append({
                "line": number, "keys": citation_keys, "cite_calls": cite_calls,
                "evidence": line.strip()[:300],
            })
        if bibliography_calls:
            bibliographies.append({
                "line": number, "calls": bibliography_calls, "evidence": line.strip()[:300],
            })
    return {
        "has_citation": bool(citations), "has_bibliography": bool(bibliographies),
        "citations": citations, "bibliographies": bibliographies,
    }


def standard_structure_inventory(path: Path) -> dict[str, Any]:
    """Observe standard display-equation and figure/caption syntax."""
    text = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    display_equations, figures, captions = [], [], []
    display_pattern = re.compile(r"#\s*math\.equation\s*\(|\$\s+.*?\s+\$", re.DOTALL)
    for match in display_pattern.finditer(text):
        display_equations.append({
            "line": text.count("\n", 0, match.start()) + 1,
            "evidence": match.group(0).replace("\n", " ")[:300],
        })
    for number, line in enumerate(text.splitlines(), start=1):
        if re.search(r"#\s*figure\s*\(", line):
            figures.append({"line": number, "evidence": line.strip()[:300]})
        if re.search(r"\bcaption\s*:", line):
            captions.append({"line": number, "evidence": line.strip()[:300]})
    return {
        "has_display_equation": bool(display_equations),
        "has_figure": bool(figures), "has_figure_caption": bool(figures and captions),
        "display_equations": display_equations, "figures": figures, "captions": captions,
    }


def lint_source(template: Path, fixture: Path, entry_symbol: str) -> dict[str, Any]:
    if template.resolve() == fixture.resolve():
        raise InputError("template_entry and fixture source must be distinct")
    template_text = strip_comments(template.read_text(encoding="utf-8", errors="replace"))
    fixture_text = strip_comments(fixture.read_text(encoding="utf-8", errors="replace"))
    if not re.search(rf"#let\s+{token_pattern(entry_symbol)}\s*(?:\(|=)", template_text):
        raise InputError(f"template does not export declared entry_symbol: {entry_symbol}")
    if re.search(rf"#let\s*(?:{token_pattern(entry_symbol)}|\([^)]*{token_pattern(entry_symbol)}[^)]*\))", fixture_text):
        raise InputError(f"fixture shadows declared entry_symbol: {entry_symbol}")
    imports = []
    pattern = re.compile(r'#import\s+"([^"]+)"\s*:\s*(\([^)]*\)|[^\n]+)', re.MULTILINE)
    for match in pattern.finditer(fixture_text):
        raw_path, imported = match.group(1), match.group(2)
        declared = Path(raw_path)
        resolved = declared.resolve() if declared.is_absolute() else (fixture.parent / declared).resolve()
        if resolved == template.resolve() and ("*" in imported or re.search(token_pattern(entry_symbol), imported)):
            imports.append((match.start(), match.end(), raw_path, imported))
    if not imports:
        raise InputError("fixture does not import the declared entry_symbol from template_entry")
    without_imports = fixture_text
    for start, end, _, _ in reversed(imports):
        without_imports = without_imports[:start] + " " * (end - start) + without_imports[end:]
    code = strip_strings(without_imports)
    wrapper_uses = (
        rf"#\s*{token_pattern(entry_symbol)}\s*(?:\(|\.\s*with\s*\()",
        rf"#show\s*:\s*{token_pattern(entry_symbol)}(?:\s*\.\s*with\s*\(|\s*(?:\n|$))",
        rf"#show\s*:[^=\n]*=>\s*(?:\{{\s*)?{token_pattern(entry_symbol)}\s*\(",
    )
    if not any(re.search(pattern, code) for pattern in wrapper_uses):
        raise InputError(f"fixture imports but does not call/show entry_symbol: {entry_symbol}")
    private_symbols = sorted(set(re.findall(r"#let\s+(_[A-Za-z][A-Za-z0-9_-]*)", template_text)))
    used_private = []
    for private in private_symbols:
        call = rf"(?:#\s*{re.escape(private)}|{token_pattern(private)}\s*(?:\(|\.with\b)|[:=]\s*{token_pattern(private)})"
        if re.search(call, code):
            used_private.append(private)
    if used_private:
        raise InputError("fixture uses private template symbol(s): " + ", ".join(used_private))
    return {
        "template": str(template.resolve()), "fixture": str(fixture.resolve()),
        "entry_symbol": entry_symbol, "matching_imports": len(imports),
        "private_symbol_count": len(private_symbols),
    }


def normalize_text(value: str) -> str:
    return "".join(character for character in unicodedata.normalize("NFKC", value) if not character.isspace())


def intersection_metrics(reference: str, candidate: str) -> dict[str, Any]:
    reference_count, candidate_count = len(reference), len(candidate)
    matched = sum((Counter(reference) & Counter(candidate)).values())
    coverage = matched / reference_count if reference_count else (1.0 if not candidate_count else 0.0)
    precision = matched / candidate_count if candidate_count else (1.0 if not reference_count else 0.0)
    ordered = 1.0 if reference == candidate else difflib.SequenceMatcher(
        None, reference, candidate, autojunk=False,
    ).ratio()
    return {
        "reference_characters": reference_count, "candidate_characters": candidate_count,
        "matched_characters": matched, "reference_coverage": coverage,
        "candidate_precision": precision, "ordered_similarity": ordered,
    }


def text_metrics(reference_pages: Sequence[str], candidate_pages: Sequence[str]) -> dict[str, Any]:
    page_count = max(len(reference_pages), len(candidate_pages))
    per_page = []
    for index in range(page_count):
        reference = normalize_text(reference_pages[index]) if index < len(reference_pages) else ""
        candidate = normalize_text(candidate_pages[index]) if index < len(candidate_pages) else ""
        per_page.append({"page": index + 1, **intersection_metrics(reference, candidate)})
    return {
        "normalization": "NFKC-remove-whitespace-v1",
        **intersection_metrics(
            normalize_text("".join(reference_pages)), normalize_text("".join(candidate_pages)),
        ),
        "per_page": per_page,
    }


def geometry_metrics(reference: dict[str, Any], candidate: dict[str, Any], tolerance: float) -> dict[str, Any]:
    pages = max(reference["pages"], candidate["pages"])
    records, passed = [], reference["pages"] == candidate["pages"]
    for index in range(pages):
        left = reference["geometry"][index] if index < reference["pages"] else None
        right = candidate["geometry"][index] if index < candidate["pages"] else None
        if left is None or right is None:
            records.append({"page": index + 1, "pass": False, "reference": left, "candidate": right})
            passed = False; continue
        width_delta = right["width_pt"] - left["width_pt"]
        height_delta = right["height_pt"] - left["height_pt"]
        box_results = {}
        for box_name in ("MediaBox", "CropBox"):
            left_box, right_box = left.get(box_name), right.get(box_name)
            if left_box is None and right_box is None:
                continue
            if left_box is None or right_box is None:
                box_results[box_name] = {"pass": False, "deltas_pt": None}
            else:
                deltas = [candidate_value - reference_value for reference_value, candidate_value in zip(left_box, right_box)]
                box_results[box_name] = {"pass": all(abs(value) <= tolerance for value in deltas), "deltas_pt": deltas}
        page_pass = (
            abs(width_delta) <= tolerance and abs(height_delta) <= tolerance
            and right["rotation"] == left["rotation"]
            and all(result["pass"] for result in box_results.values())
        )
        passed &= page_pass
        records.append({
            "page": index + 1, "pass": page_pass,
            "width_delta_pt": width_delta, "height_delta_pt": height_delta,
            "rotation_equal": right["rotation"] == left["rotation"],
            "boxes": box_results,
        })
    return {"pass": passed, "tolerance_pt": tolerance, "pages": records}


def positive_text_checks(pages: Sequence[str], required: Sequence[str], ordered: Sequence[str]) -> dict[str, Any]:
    document = normalize_text("".join(pages))
    missing = [item for item in required if normalize_text(item) not in document]
    order_failures, position = [], 0
    for item in ordered:
        marker = normalize_text(item)
        found = document.find(marker, position)
        if found < 0:
            order_failures.append(item)
        else:
            position = found + len(marker)
    return {"pass": not missing and not order_failures, "missing": missing, "order_failures": order_failures}


def locked_required_text_checks(
    reference_pages: Sequence[str], candidate_pages: Sequence[str], required: Sequence[str],
) -> dict[str, Any]:
    reference = positive_text_checks(reference_pages, required, [])
    candidate = positive_text_checks(candidate_pages, required, [])
    return {"pass": reference["pass"] and candidate["pass"], "reference": reference, "candidate": candidate}


def page_flow_checks(pages: Sequence[str], flows: Sequence[dict[str, str]]) -> dict[str, Any]:
    normalized_pages = [normalize_text(page) for page in pages]
    document = "".join(normalized_pages)
    results, failures = [], []
    for index, flow in enumerate(flows):
        record: dict[str, Any] = {"index": index, **flow}
        positions, page_numbers = {}, {}
        flow_failures = []
        for key in ("start", "end", "following"):
            marker = normalize_text(flow[key])
            count = document.count(marker)
            positions[key] = document.find(marker)
            hits = [page + 1 for page, text in enumerate(normalized_pages) if marker in text]
            page_numbers[key] = hits[0] if len(hits) == 1 else None
            if count != 1:
                flow_failures.append(f"{key} marker count is {count}, expected 1")
        if not flow_failures:
            if not page_numbers["start"] < page_numbers["end"]:
                flow_failures.append("start and end do not cross pages in order")
            if not positions["end"] < positions["following"]:
                flow_failures.append("end does not precede following content")
        record.update({"pages": page_numbers, "positions": positions, "pass": not flow_failures, "failures": flow_failures})
        results.append(record)
        failures.extend(f"page_flow[{index}]: {failure}" for failure in flow_failures)
    return {"pass": not failures, "flows": results, "failures": failures}


def normalize_font(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = re.sub(r"^[A-Za-z]{6}\+", "", normalized)
    return "".join(character for character in normalized.casefold() if character.isalnum())


def font_family_match(required: str, embedded: str) -> bool:
    wanted, actual = normalize_font(required), normalize_font(embedded)
    return bool(wanted and wanted == actual)


def embedded_font_comparison(reference: Sequence[str], candidate: Sequence[str]) -> dict[str, Any]:
    """Compare embedded PDF face names after conservative spelling normalization."""
    def inventory(values: Sequence[str]) -> dict[str, list[str]]:
        result: dict[str, set[str]] = {}
        for value in values:
            key = normalize_font(value)
            if key:
                result.setdefault(key, set()).add(re.sub(r"^[A-Za-z]{6}\+", "", value))
        return {key: sorted(names) for key, names in sorted(result.items())}

    reference_inventory, candidate_inventory = inventory(reference), inventory(candidate)
    reference_keys, candidate_keys = set(reference_inventory), set(candidate_inventory)
    missing_keys, extra_keys = sorted(reference_keys - candidate_keys), sorted(candidate_keys - reference_keys)
    return {
        "pass": not missing_keys and not extra_keys,
        "normalization": "NFKC, subset-prefix removal, case-fold, alphanumeric exact match",
        "reference": reference_inventory,
        "candidate": candidate_inventory,
        "missing_reference_faces": [reference_inventory[key] for key in missing_keys],
        "extra_candidate_faces": [candidate_inventory[key] for key in extra_keys],
        "equivalences": [],
    }


def pdf_word_boxes(path: Path) -> dict[str, Any]:
    result = execute(("pdftotext", "-bbox-layout", str(path), "-"))
    if result["returncode"] != 0:
        detail = (result["stderr"] or result["stdout"]).strip()
        raise EvidenceError(f"pdftotext bbox extraction failed for {path}: {detail}")
    try:
        root = ET.fromstring(result["stdout"])
    except ET.ParseError as error:
        raise EvidenceError(f"invalid pdftotext bbox XML for {path}: {error}") from error
    records, page_sizes = [], []
    pages = [element for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "page"]
    for page_number, page in enumerate(pages, start=1):
        try:
            page_sizes.append({"width_pt": float(page.attrib["width"]), "height_pt": float(page.attrib["height"])})
        except (KeyError, ValueError) as error:
            raise EvidenceError(f"invalid page box in pdftotext output for {path}") from error
        line_number = 0
        for line in page.iter():
            if line.tag.rsplit("}", 1)[-1] != "line":
                continue
            line_number += 1
            for word in line.iter():
                if word.tag.rsplit("}", 1)[-1] != "word":
                    continue
                normalized = normalize_text("".join(word.itertext()))
                if not normalized:
                    continue
                try:
                    left, top = float(word.attrib["xMin"]), float(word.attrib["yMin"])
                    right, bottom = float(word.attrib["xMax"]), float(word.attrib["yMax"])
                except (KeyError, ValueError) as error:
                    raise EvidenceError(f"invalid word box in pdftotext output for {path}") from error
                records.append({
                    "page": page_number, "line": line_number, "text": normalized,
                    "left_pt": left, "top_pt": top, "right_pt": right, "bottom_pt": bottom,
                    "center_x_pt": (left + right) / 2, "center_y_pt": (top + bottom) / 2,
                })
    return {"page_count": len(pages), "page_sizes": page_sizes, "words": records}


def coherent_anchor_clusters(
    matched_blocks: Sequence[Sequence[tuple[dict[str, Any], dict[str, Any]]]],
) -> list[dict[str, Any]]:
    """Summarize only contextual, same-line, coherently displaced token runs."""
    clusters = []
    coherence_pt = 2 * LAYOUT_ANCHOR_TOLERANCE_PT

    def add(segment: list[tuple[dict[str, Any], dict[str, Any]]]) -> None:
        if len(segment) < 3:
            return
        per_pair = [{
            "left_dx_pt": candidate["left_pt"] - reference["left_pt"],
            "center_dx_pt": candidate["center_x_pt"] - reference["center_x_pt"],
            "top_dy_pt": candidate["top_pt"] - reference["top_pt"],
        } for reference, candidate in segment]
        if any(
            max(item[name] for item in per_pair) - min(item[name] for item in per_pair) > coherence_pt
            for name in ("left_dx_pt", "top_dy_pt")
        ):
            return
        reference_words, candidate_words = zip(*segment)
        reference = {
            "left_pt": statistics.median(item["left_pt"] for item in reference_words),
            "center_x_pt": statistics.median(item["center_x_pt"] for item in reference_words),
            "top_pt": statistics.median(item["top_pt"] for item in reference_words),
        }
        candidate = {
            "left_pt": statistics.median(item["left_pt"] for item in candidate_words),
            "center_x_pt": statistics.median(item["center_x_pt"] for item in candidate_words),
            "top_pt": statistics.median(item["top_pt"] for item in candidate_words),
        }
        deltas = {
            name: statistics.median(item[name] for item in per_pair)
            for name in ("left_dx_pt", "center_dx_pt", "top_dy_pt")
        }
        texts = [item["text"] for item in reference_words]
        clusters.append({
            "page": reference_words[0]["page"],
            "reference_line": reference_words[0]["line"],
            "candidate_line": candidate_words[0]["line"],
            "token_count": len(segment), "tokens": texts[:12],
            "tokens_truncated": len(texts) > 12,
            "reference": reference, "candidate": candidate, "deltas": deltas,
            "coherence_spread_pt": {
                name: max(item[name] for item in per_pair) - min(item[name] for item in per_pair)
                for name in ("left_dx_pt", "top_dy_pt")
            },
        })

    for block in matched_blocks:
        segment: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for pair in block:
            left, right = pair
            left_dx, top_dy = right["left_pt"] - left["left_pt"], right["top_pt"] - left["top_pt"]
            same_lines = not segment or (
                left["line"] == segment[-1][0]["line"]
                and right["line"] == segment[-1][1]["line"]
            )
            coherent = not segment or (
                max([candidate["left_pt"] - reference["left_pt"] for reference, candidate in segment] + [left_dx])
                - min([candidate["left_pt"] - reference["left_pt"] for reference, candidate in segment] + [left_dx])
                <= coherence_pt
                and max([candidate["top_pt"] - reference["top_pt"] for reference, candidate in segment] + [top_dy])
                - min([candidate["top_pt"] - reference["top_pt"] for reference, candidate in segment] + [top_dy])
                <= coherence_pt
            )
            if not same_lines or not coherent:
                add(segment)
                segment = []
            segment.append(pair)
        add(segment)
    return clusters


def line_layout_preflight(reference_pdf: Path, candidate_pdf: Path) -> dict[str, Any]:
    """Reject >0.25 pt drift of content-aligned word anchors on every official page."""
    reference, candidate = pdf_word_boxes(reference_pdf), pdf_word_boxes(candidate_pdf)
    violations, pages, maximum = [], [], {"left_dx_pt": 0.0, "center_dx_pt": 0.0, "top_dy_pt": 0.0}
    all_sufficient = reference["page_count"] == candidate["page_count"]
    for page_number in range(1, max(reference["page_count"], candidate["page_count"]) + 1):
        reference_words = [item for item in reference["words"] if item["page"] == page_number]
        candidate_words = [item for item in candidate["words"] if item["page"] == page_number]
        matcher = difflib.SequenceMatcher(
            None,
            [item["text"] for item in reference_words],
            [item["text"] for item in candidate_words],
            autojunk=False,
        )
        matched_blocks = [
            [(reference_words[left + offset], candidate_words[right + offset]) for offset in range(size)]
            for left, right, size in matcher.get_matching_blocks() if size
        ]
        pairs = [pair for block in matched_blocks for pair in block]
        reference_coverage = len(pairs) / len(reference_words) if reference_words else 0.0
        candidate_coverage = len(pairs) / len(candidate_words) if candidate_words else 0.0
        occupied_bands, anchored_bands = set(), set()
        if page_number <= reference["page_count"]:
            page_height = reference["page_sizes"][page_number - 1]["height_pt"]
            for word in reference_words:
                occupied_bands.add(min(LAYOUT_VERTICAL_BANDS - 1, int(word["center_y_pt"] / page_height * LAYOUT_VERTICAL_BANDS)))
            for word, _ in pairs:
                anchored_bands.add(min(LAYOUT_VERTICAL_BANDS - 1, int(word["center_y_pt"] / page_height * LAYOUT_VERTICAL_BANDS)))
        page_sufficient = (
            bool(pairs)
            and reference_coverage >= MINIMUM_WORD_ANCHOR_COVERAGE
            and candidate_coverage >= MINIMUM_WORD_ANCHOR_COVERAGE
            and occupied_bands <= anchored_bands
        )
        all_sufficient &= page_sufficient
        page_violation_count = 0
        page_violation_records = []
        for left, right in pairs:
            deltas = {
                "left_dx_pt": right["left_pt"] - left["left_pt"],
                "center_dx_pt": right["center_x_pt"] - left["center_x_pt"],
                "top_dy_pt": right["top_pt"] - left["top_pt"],
            }
            for name, value in deltas.items():
                if abs(value) > abs(maximum[name]):
                    maximum[name] = value
            if any(abs(value) > LAYOUT_ANCHOR_TOLERANCE_PT for value in deltas.values()):
                page_violation_count += 1
                violation = {
                    "page": page_number, "text": left["text"][:160], "deltas": deltas,
                    "reference": {name: left[name] for name in ("left_pt", "top_pt", "right_pt", "bottom_pt")},
                    "candidate": {name: right[name] for name in ("left_pt", "top_pt", "right_pt", "bottom_pt")},
                }
                page_violation_records.append(violation)
                violations.append(violation)
        diagnostic_first = min(page_violation_records, key=lambda item: (
            item["reference"]["top_pt"], item["reference"]["left_pt"], item["text"],
        ), default=None)
        diagnostic_maximum = min(page_violation_records, key=lambda item: (
            -max(abs(value) for value in item["deltas"].values()),
            item["reference"]["top_pt"], item["reference"]["left_pt"], item["text"],
        ), default=None)
        coherent = [
            cluster for cluster in coherent_anchor_clusters(matched_blocks)
            if any(abs(value) > LAYOUT_ANCHOR_TOLERANCE_PT for value in cluster["deltas"].values())
        ]
        earliest_coherent = min(coherent, key=lambda item: (
            item["reference"]["top_pt"], item["reference"]["left_pt"], item["tokens"],
        ), default=None)
        maximum_coherent = min(coherent, key=lambda item: (
            -max(abs(value) for value in item["deltas"].values()),
            item["reference"]["top_pt"], item["reference"]["left_pt"], item["tokens"],
        ), default=None)
        pages.append({
            "page": page_number, "reference_words": len(reference_words),
            "candidate_words": len(candidate_words), "matched_anchors": len(pairs),
            "reference_anchor_coverage": reference_coverage,
            "candidate_anchor_coverage": candidate_coverage,
            "occupied_vertical_bands": sorted(occupied_bands),
            "anchored_vertical_bands": sorted(anchored_bands),
            "sufficient_anchors": page_sufficient,
            "violation_count": page_violation_count,
            "diagnostic_first_violation": diagnostic_first,
            "diagnostic_maximum_violation": diagnostic_maximum,
            "coherent_violation_count": len(coherent),
            "earliest_coherent_divergence": earliest_coherent,
            "maximum_coherent_divergence": maximum_coherent,
        })
    return {
        "pass": all_sufficient and not violations,
        "method": "per-page ordered NFKC word anchors from pdftotext -bbox-layout",
        "scope": "structural text placement preflight; not pixel identity or aesthetic acceptance",
        "tolerance_pt": LAYOUT_ANCHOR_TOLERANCE_PT,
        "minimum_word_anchor_coverage": MINIMUM_WORD_ANCHOR_COVERAGE,
        "vertical_bands_per_page": LAYOUT_VERTICAL_BANDS,
        "all_pages_sufficient": all_sufficient,
        "pages": pages,
        "maximum_displacement": maximum,
        "violation_count": len(violations),
        "violations": violations[:100],
        "violations_truncated": len(violations) > 100,
    }


def equation_anchor_preflight(
    reference_pdf: Path, candidate_pdf: Path, expected_equations: int,
) -> dict[str, Any]:
    """Compare right-side equation numbers and their y-band math-body left edges."""
    if expected_equations <= 0:
        return {
            "pass": True, "applicable": False, "expected_equations": 0,
            "scope": "no display equations observed in official fixture source",
        }
    reference, candidate = pdf_word_boxes(reference_pdf), pdf_word_boxes(candidate_pdf)
    number_pattern = re.compile(r"\([0-9]+\)\Z")

    def equation_numbers(layout: dict[str, Any]) -> list[dict[str, Any]]:
        numbered = [word for word in layout["words"] if number_pattern.fullmatch(word["text"])]
        rightmost = sorted(numbered, key=lambda word: word["left_pt"], reverse=True)[:expected_equations]
        return sorted(rightmost, key=lambda word: (word["page"], word["top_pt"], word["left_pt"]))

    def body_left(layout: dict[str, Any], number: dict[str, Any]) -> float | None:
        height = number["bottom_pt"] - number["top_pt"]
        candidates = [
            word for word in layout["words"]
            if word["page"] == number["page"]
            and word["right_pt"] < number["left_pt"] - LAYOUT_ANCHOR_TOLERANCE_PT
            and word["bottom_pt"] >= number["top_pt"] - height
            and word["top_pt"] <= number["bottom_pt"] + height
            and not number_pattern.fullmatch(word["text"])
        ]
        return min((word["left_pt"] for word in candidates), default=None)

    reference_numbers, candidate_numbers = equation_numbers(reference), equation_numbers(candidate)
    sufficient = len(reference_numbers) == expected_equations and len(candidate_numbers) == expected_equations
    records, violations = [], []
    for index, (left, right) in enumerate(zip(reference_numbers, candidate_numbers), start=1):
        left_body, right_body = body_left(reference, left), body_left(candidate, right)
        deltas = {
            "number_left_dx_pt": right["left_pt"] - left["left_pt"],
            "number_top_dy_pt": right["top_pt"] - left["top_pt"],
            "body_left_dx_pt": None if left_body is None or right_body is None else right_body - left_body,
        }
        record = {
            "index": index, "reference_number": left["text"], "candidate_number": right["text"],
            "reference_page": left["page"], "candidate_page": right["page"],
            "reference_number_left_pt": left["left_pt"],
            "candidate_number_left_pt": right["left_pt"],
            "reference_number_top_pt": left["top_pt"],
            "candidate_number_top_pt": right["top_pt"],
            "reference_body_left_pt": left_body, "candidate_body_left_pt": right_body,
            "deltas": deltas,
        }
        failed = (
            left["text"] != right["text"] or left["page"] != right["page"]
            or left_body is None or right_body is None
            or any(
                value is not None and abs(value) > LAYOUT_ANCHOR_TOLERANCE_PT
                for value in deltas.values()
            )
        )
        record["pass"] = not failed
        records.append(record)
        if failed:
            violations.append(record)
    if not sufficient:
        violations.append({
            "reason": "numbered display-equation anchor count differs from source observation",
            "reference_numbers": len(reference_numbers), "candidate_numbers": len(candidate_numbers),
        })
    return {
        "pass": sufficient and not violations, "applicable": True,
        "method": "rightmost source-counted (n) word boxes plus leftmost math text box in each number y-band",
        "scope": "numbered display-equation structure; not math semantics or aesthetic acceptance",
        "tolerance_pt": LAYOUT_ANCHOR_TOLERANCE_PT,
        "expected_equations": expected_equations,
        "records": records, "violation_count": len(violations), "violations": violations,
    }


def local_ink_structure_gate(index_path: Path) -> dict[str, Any]:
    """Gate local ink extents from an all-page comparator scan in point units."""
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CheckError(f"invalid comparator index for structure gate: {error}") from error
    if index.get("kind") != "pdf-difference-scan":
        raise CheckError("structure gate requires a pdf-difference-scan index")
    try:
        dpi = int(index["settings"]["dpi"])
        columns = int(index["settings"]["tile_columns"])
        rows = int(index["settings"]["tile_rows"])
    except (KeyError, TypeError, ValueError) as error:
        raise CheckError("comparator index lacks tile settings") from error
    if dpi < math.ceil(72 / LAYOUT_ANCHOR_TOLERANCE_PT):
        raise CheckError("structure gate scan resolution cannot resolve the 0.25 pt tolerance")
    points_per_pixel = 72 / dpi
    pages, violations = [], []
    page_files = sorted((index_path.parent / "pages").glob("*/scan.json"))
    for page_file in page_files:
        try:
            page = json.loads(page_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CheckError(f"invalid comparator page scan: {page_file}: {error}") from error
        page_number = int(page["page"])
        comparable = page_violations = 0
        page_violation_records = []
        for tile in page.get("tiles", []):
            ink = tile.get("ink", {})
            reference, candidate = ink.get("reference"), ink.get("candidate")
            if reference is None and candidate is None:
                continue
            comparable += 1
            displacement = ink.get("displacement")
            record = {
                "page": page_number, "tile": tile.get("id"),
                "box_pt": tile.get("box_pt"), "failures": [],
            }
            if reference is None or candidate is None or not isinstance(displacement, dict):
                record["failures"].append("ink presence or measurement changed")
            else:
                deltas = {
                    name + "_pt": float(displacement[name]) * points_per_pixel
                    for name in ("center_dx", "center_dy", "width_delta", "height_delta")
                }
                record["reference"] = {"ink": reference}
                record["candidate"] = {"ink": candidate}
                record["deltas"] = deltas
                if any(abs(value) > LAYOUT_ANCHOR_TOLERANCE_PT for value in deltas.values()):
                    record["failures"].append("local ink centroid or extent moved")
            structure = ink.get("structure")
            if not isinstance(structure, dict):
                record["failures"].append("local rule/image structure signature is missing")
            else:
                structure_failures = []
                structure_deltas = []
                for direction in ("horizontal_bands", "vertical_bands"):
                    left_bands = structure.get("reference", {}).get(direction)
                    right_bands = structure.get("candidate", {}).get(direction)
                    if not isinstance(left_bands, list) or not isinstance(right_bands, list):
                        structure_failures.append(f"{direction} signature is invalid")
                        continue
                    if len(left_bands) != len(right_bands):
                        structure_failures.append(
                            f"{direction} count differs ({len(left_bands)} vs {len(right_bands)})"
                        )
                        continue
                    for band_index, (left_band, right_band) in enumerate(zip(left_bands, right_bands)):
                        for edge in ("start", "end"):
                            delta = (float(right_band[edge]) - float(left_band[edge])) * points_per_pixel
                            structure_deltas.append({
                                "direction": direction, "band": band_index, "edge": edge,
                                "reference_pt": float(left_band[edge]) * points_per_pixel,
                                "candidate_pt": float(right_band[edge]) * points_per_pixel,
                                "delta_pt": delta,
                            })
                            if abs(delta) > LAYOUT_ANCHOR_TOLERANCE_PT:
                                structure_failures.append(
                                    f"{direction}[{band_index}].{edge} moved {delta:.6f} pt"
                                )
                if structure_failures:
                    record["failures"].append("local dense row/column structure differs")
                    record["structure_failures"] = structure_failures[:20]
                    record["structure_failures_truncated"] = len(structure_failures) > 20
                    record["structure_deltas"] = [
                        item for item in structure_deltas
                        if abs(item["delta_pt"]) > LAYOUT_ANCHOR_TOLERANCE_PT
                    ][:20]
                if "reference" in record and "candidate" in record:
                    record["reference"]["structure"] = structure.get("reference")
                    record["candidate"]["structure"] = structure.get("candidate")
            if not record["failures"]:
                continue
            page_violations += 1
            page_violation_records.append(record)
            violations.append(record)
        sufficient = comparable > 0
        if not sufficient:
            violations.append({"page": page_number, "reason": "no comparable local ink tiles"})
        def violation_magnitude(item: dict[str, Any]) -> float:
            numeric = [
                abs(float(value)) for value in item.get("deltas", {}).values()
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            ]
            numeric.extend(
                abs(float(value["delta_pt"])) for value in item.get("structure_deltas", [])
                if isinstance(value.get("delta_pt"), (int, float))
            )
            return max(numeric, default=math.inf)

        representative_violation = min(page_violation_records, key=lambda item: (
            -violation_magnitude(item), str(item.get("tile", "")),
        ), default=None)
        pages.append({
            "page": page_number, "comparable_tiles": comparable,
            "violation_count": page_violations + (0 if sufficient else 1),
            "sufficient": sufficient,
            "representative_violation": representative_violation,
        })
    page_count_equal = bool(index.get("page_count", {}).get("equal"))
    all_pages_present = len(page_files) == index.get("page_count", {}).get("reference")
    return {
        "pass": page_count_equal and all_pages_present and bool(pages) and not violations,
        "method": "fixed all-page comparator tiles; binary-ink centroid/extents and dense row/column bands",
        "scope": "local raster structure preflight; not pixel identity or aesthetic acceptance",
        "tolerance_pt": LAYOUT_ANCHOR_TOLERANCE_PT,
        "dpi": dpi, "tile_columns": columns, "tile_rows": rows,
        "page_count_equal": page_count_equal, "all_pages_present": all_pages_present,
        "pages": pages, "violation_count": len(violations),
        "violations": violations[:100], "violations_truncated": len(violations) > 100,
    }


def correction_vector(deltas: dict[str, Any]) -> dict[str, float]:
    """Return the signed candidate correction needed to reach the reference."""
    return {
        name: -float(value)
        for name, value in deltas.items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }


def correction_words(deltas: dict[str, Any]) -> str:
    horizontal_values = [
        float(deltas[name])
        for name in ("left_dx_pt", "center_dx_pt", "number_left_dx_pt", "body_left_dx_pt")
        if isinstance(deltas.get(name), (int, float)) and not isinstance(deltas.get(name), bool)
        and abs(float(deltas[name])) > 0
    ]
    vertical_values = [
        float(deltas[name])
        for name in ("top_dy_pt", "number_top_dy_pt", "center_dy_pt")
        if isinstance(deltas.get(name), (int, float)) and not isinstance(deltas.get(name), bool)
        and abs(float(deltas[name])) > 0
    ]
    horizontal = max(horizontal_values, key=abs, default=None)
    vertical = max(vertical_values, key=abs, default=None)
    parts = []
    if horizontal is not None:
        parts.append(f"move candidate {'left' if horizontal > 0 else 'right'} {abs(horizontal):.3f} pt")
    if vertical is not None:
        parts.append(f"move candidate {'up' if vertical > 0 else 'down'} {abs(vertical):.3f} pt")
    return "; ".join(parts) if parts else "move candidate measurements toward the reference values"


def structure_correction(observation: dict[str, Any]) -> str:
    delta = observation["delta"]
    metric = str(observation.get("metric", ""))
    if metric in {"center_dx_pt"} or metric.startswith("vertical_bands"):
        return f"move candidate {'left' if delta > 0 else 'right'} {abs(delta):.3f} pt"
    if metric in {"center_dy_pt"} or metric.startswith("horizontal_bands"):
        return f"move candidate {'up' if delta > 0 else 'down'} {abs(delta):.3f} pt"
    if metric == "width_delta_pt":
        return f"make candidate {abs(delta):.3f} pt {'narrower' if delta > 0 else 'wider'}"
    if metric == "height_delta_pt":
        return f"make candidate {abs(delta):.3f} pt {'shorter' if delta > 0 else 'taller'}"
    return "move the candidate band/ink measurement to the reference value"


def build_repair_targets(report: dict[str, Any], limit: int = REPAIR_TARGET_LIMIT) -> tuple[list[dict[str, Any]], bool]:
    """Turn existing official measurements into a short, deterministic repair queue."""
    official_fixture = next(
        (item for item in report.get("fixtures", []) if item.get("kind") == "official"), None,
    )
    official = official_fixture.get("official", {}) if isinstance(official_fixture, dict) else {}
    targets: list[dict[str, Any]] = []

    fonts = official.get("embedded_fonts", {})
    if isinstance(fonts, dict) and not fonts.get("pass", True):
        targets.append({
            "id": "fonts", "kind": "font_inventory", "page": None,
            "signature": "reference-derived embedded face set",
            "reference": fonts.get("reference", {}), "candidate": fonts.get("candidate", {}),
            "delta": {
                "missing_reference_faces": fonts.get("missing_reference_faces", []),
                "extra_candidate_faces": fonts.get("extra_candidate_faces", []),
            },
            "correction_direction": "add/replace missing faces and remove unexplained fallback faces until the candidate set equals the reference set",
            "governing_rule": "affected element font/show rule and fallback chain",
        })

    layout = official.get("layout_preflight", {})
    layout_by_page: dict[int, list[dict[str, Any]]] = {}
    for page_record in layout.get("pages", []) if isinstance(layout, dict) else []:
        if not isinstance(page_record, dict) or not isinstance(page_record.get("page"), int):
            continue
        records = [
            item for item in (
                page_record.get("earliest_coherent_divergence"),
                page_record.get("maximum_coherent_divergence"),
            )
            if isinstance(item, dict) and isinstance(item.get("deltas"), dict)
        ]
        if records:
            layout_by_page[page_record["page"]] = records
    for page, violations in sorted(layout_by_page.items()):
        first = min(violations, key=lambda item: (
            float(item.get("reference", {}).get("top_pt", math.inf)),
            float(item.get("reference", {}).get("left_pt", math.inf)),
            str(item.get("text", "")),
        ))
        maximum = min(violations, key=lambda item: (
            -max((abs(float(value)) for value in item["deltas"].values() if value is not None), default=0.0),
            float(item.get("reference", {}).get("top_pt", math.inf)),
            float(item.get("reference", {}).get("left_pt", math.inf)),
            str(item.get("text", "")),
        ))

        def anchor(item: dict[str, Any]) -> dict[str, Any]:
            return {
                "tokens": item.get("tokens"), "token_count": item.get("token_count"),
                "reference_line": item.get("reference_line"), "candidate_line": item.get("candidate_line"),
                "reference": item.get("reference"),
                "candidate": item.get("candidate"), "delta": item.get("deltas"),
                "correction_to_reference": correction_vector(item.get("deltas", {})),
                "correction_direction": correction_words(item.get("deltas", {})),
            }

        targets.append({
            "id": f"layout-page-{page:03d}", "kind": "text_anchor", "page": page,
            "signature": "earliest and maximum same-line coherent token-cluster median displacement",
            "earliest": anchor(first), "maximum": anchor(maximum),
            "correction_direction": correction_words(maximum["deltas"]),
            "governing_rule": "earliest shared wrapper alignment/inset or leading/block-spacing rule",
        })

    equations = official.get("equation_preflight", {})
    equations_by_page: dict[int, list[dict[str, Any]]] = {}
    qualitative_equation_failure = False
    for violation in equations.get("violations", []) if isinstance(equations, dict) else []:
        if not isinstance(violation, dict) or not isinstance(violation.get("deltas"), dict):
            qualitative_equation_failure = True
            continue
        page = violation.get("reference_page")
        if isinstance(page, int):
            equations_by_page.setdefault(page, []).append(violation)
    for page, violations in sorted(equations_by_page.items()):
        observations = []
        for item in sorted(violations, key=lambda value: int(value.get("index", 0))):
            observations.append({
                "index": item.get("index"),
                "reference": {
                    "number": item.get("reference_number"), "page": item.get("reference_page"),
                    "number_left_pt": item.get("reference_number_left_pt"),
                    "number_top_pt": item.get("reference_number_top_pt"),
                    "body_left_pt": item.get("reference_body_left_pt"),
                },
                "candidate": {
                    "number": item.get("candidate_number"), "page": item.get("candidate_page"),
                    "number_left_pt": item.get("candidate_number_left_pt"),
                    "number_top_pt": item.get("candidate_number_top_pt"),
                    "body_left_pt": item.get("candidate_body_left_pt"),
                },
                "delta": item.get("deltas"),
                "correction_to_reference": correction_vector(item.get("deltas", {})),
            })
        maximum = max(
            observations,
            key=lambda item: max((abs(float(value)) for value in item["delta"].values() if value is not None), default=0.0),
        )
        targets.append({
            "id": f"equations-page-{page:03d}", "kind": "equation_anchor", "page": page,
            "signature": "display-equation body-left and right-side number anchors",
            "equations": observations,
            "correction_direction": correction_words(maximum["delta"]),
            "governing_rule": "template math.equation/block alignment, indent, and number placement",
        })
    if qualitative_equation_failure and not equations_by_page:
        targets.append({
            "id": "equations-unmatched", "kind": "equation_anchor", "page": None,
            "signature": "source-counted display-equation anchor correspondence",
            "reference": equations.get("expected_equations"), "candidate": "unmatched anchor count",
            "delta": None,
            "correction_direction": "restore one standard numbered display-equation structure per source-observed equation",
            "governing_rule": "template math.equation numbering and standard equation structure",
        })

    structure = official.get("comparison", {}).get("structure_gate", {})
    structure_by_page: dict[int, list[dict[str, Any]]] = {}
    for page_record in structure.get("pages", []) if isinstance(structure, dict) else []:
        violation = page_record.get("representative_violation") if isinstance(page_record, dict) else None
        if isinstance(violation, dict) and isinstance(page_record.get("page"), int):
            structure_by_page[page_record["page"]] = [violation]
    if not structure_by_page:
        for violation in structure.get("violations", []) if isinstance(structure, dict) else []:
            if isinstance(violation, dict) and isinstance(violation.get("page"), int):
                structure_by_page.setdefault(violation["page"], []).append(violation)
    points_per_pixel = 72 / float(structure.get("dpi", 300)) if isinstance(structure, dict) else 0.24
    for page, violations in sorted(structure_by_page.items()):
        observations = []
        for item in sorted(violations, key=lambda value: str(value.get("tile", ""))):
            reference_ink = item.get("reference", {}).get("ink")
            candidate_ink = item.get("candidate", {}).get("ink")
            mappings = {
                "center_dx_pt": "center_x", "center_dy_pt": "center_y",
                "width_delta_pt": "width", "height_delta_pt": "height",
            }
            for metric, source_key in mappings.items():
                delta = item.get("deltas", {}).get(metric)
                if delta is None or not isinstance(reference_ink, dict) or not isinstance(candidate_ink, dict):
                    continue
                observations.append({
                    "tile": item.get("tile"), "box_pt": item.get("box_pt"), "metric": metric,
                    "reference": float(reference_ink[source_key]) * points_per_pixel,
                    "candidate": float(candidate_ink[source_key]) * points_per_pixel,
                    "delta": float(delta), "unit": "pt", "source": "ink extent/centroid",
                })
            for band in item.get("structure_deltas", []):
                observations.append({
                    "tile": item.get("tile"), "box_pt": item.get("box_pt"),
                    "metric": f"{band['direction']}[{band['band']}].{band['edge']}",
                    "reference": band["reference_pt"], "candidate": band["candidate_pt"],
                    "delta": band["delta_pt"], "unit": "pt", "source": "dense structure band",
                })
        if observations:
            representative = min(observations, key=lambda item: (
                -abs(item["delta"]), str(item.get("tile", "")), str(item.get("metric", "")),
            ))
            representative["correction_to_reference"] = -representative["delta"]
            direction = structure_correction(representative)
        else:
            item = min(violations, key=lambda value: str(value.get("tile", "")))
            representative = {
                "tile": item.get("tile"), "box_pt": item.get("box_pt"),
                "reference": "ink/dense-band signature present in reference",
                "candidate": item.get("failures", []) + item.get("structure_failures", []),
                "delta": None,
            }
            direction = "restore the reference ink/dense-band presence and extent"
        targets.append({
            "id": f"structure-page-{page:03d}", "kind": "local_structure", "page": page,
            "signature": "representative local dense-band or ink delta on the page",
            "representative": representative, "correction_direction": direction,
            "governing_rule": "figure/image sizing and alignment, table/rule stroke placement, or their shared block rule",
        })

    kind_rank = {"font_inventory": 0, "equation_anchor": 1, "text_anchor": 2, "local_structure": 3}
    targets.sort(key=lambda target: (
        kind_rank.get(target.get("kind"), 99),
        target.get("page") if isinstance(target.get("page"), int) else 0,
        str(target.get("id", "")),
    ))
    truncated = len(targets) > limit
    selected = targets[:limit]
    for priority, target in enumerate(selected, start=1):
        target["priority"] = priority
    return selected, truncated


def repair_target_summary(target: dict[str, Any]) -> str:
    page = f" p{target['page']}" if target.get("page") is not None else ""
    kind = target.get("kind")
    measurement = ""
    if kind == "font_inventory":
        delta = target.get("delta", {})
        measurement = (
            f"missing={len(delta.get('missing_reference_faces', []))} "
            f"extra={len(delta.get('extra_candidate_faces', []))}"
        )
    elif kind == "text_anchor":
        maximum = target.get("maximum", {})
        deltas = maximum.get("delta", {})
        numeric = [(name, value) for name, value in deltas.items() if isinstance(value, (int, float))]
        if numeric:
            metric, delta = max(numeric, key=lambda item: abs(item[1]))
            reference_box, candidate_box = maximum.get("reference", {}), maximum.get("candidate", {})
            if metric == "left_dx_pt":
                reference, candidate = reference_box.get("left_pt"), candidate_box.get("left_pt")
            elif metric == "center_dx_pt":
                reference = reference_box.get("center_x_pt")
                candidate = candidate_box.get("center_x_pt")
                if reference is None or candidate is None:
                    reference = (reference_box.get("left_pt", 0) + reference_box.get("right_pt", 0)) / 2
                    candidate = (candidate_box.get("left_pt", 0) + candidate_box.get("right_pt", 0)) / 2
            else:
                reference, candidate = reference_box.get("top_pt"), candidate_box.get("top_pt")
            measurement = f"{metric}={reference:.3f}->{candidate:.3f} ({delta:+.3f} pt)"
    elif kind == "equation_anchor":
        choices = []
        mapping = {
            "number_left_dx_pt": "number_left_pt", "number_top_dy_pt": "number_top_pt",
            "body_left_dx_pt": "body_left_pt",
        }
        for equation in target.get("equations", []):
            for metric, delta in equation.get("delta", {}).items():
                key = mapping.get(metric)
                reference, candidate = equation.get("reference", {}).get(key), equation.get("candidate", {}).get(key)
                if key and isinstance(delta, (int, float)) and isinstance(reference, (int, float)) and isinstance(candidate, (int, float)):
                    choices.append((abs(delta), metric, reference, candidate, delta))
        if choices:
            _, metric, reference, candidate, delta = max(choices)
            measurement = f"{metric}={reference:.3f}->{candidate:.3f} ({delta:+.3f} pt)"
    elif kind == "local_structure":
        representative = target.get("representative", {})
        if all(isinstance(representative.get(name), (int, float)) for name in ("reference", "candidate", "delta")):
            measurement = (
                f"{representative.get('metric', 'structure')}="
                f"{representative['reference']:.3f}->{representative['candidate']:.3f} "
                f"({representative['delta']:+.3f} pt)"
            )
        else:
            measurement = "presence/signature mismatch"
    return (
        f"* [{target.get('kind', 'repair')}{page}] {measurement} -> "
        f"{target.get('correction_direction', 'move toward reference')}"
    )


def new_output(path: Path) -> Path:
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise InputError(f"output must be new or empty: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dependency_records(path: Path, project_root: Path) -> tuple[list[dict[str, Any]], set[Path]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CheckError(f"invalid Typst dependency file: {path}: {error}") from error
    inputs = value.get("inputs") if isinstance(value, dict) else None
    if not isinstance(inputs, list) or any(not isinstance(item, str) for item in inputs):
        raise CheckError(f"invalid Typst dependency data: {path}")
    records, resolved = [], set()
    for item in inputs:
        raw = Path(item)
        dependency = raw.resolve() if raw.is_absolute() else (project_root / raw).resolve()
        if not dependency.is_file():
            raise CheckError(f"dependency not found: {dependency}")
        resolved.add(dependency)
        records.append({"path": str(dependency), "sha256": sha256(dependency)})
    return records, resolved


def run(config_path: Path, output_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    output = new_output(output_path)
    for name in ("pdf", "logs", "deps", "text", "details"):
        (output / name).mkdir()
    tools = {
        "typst": tool_version("typst", ("--version",)),
        "pdfinfo": tool_version("pdfinfo", ("-v",)),
        "pdffonts": tool_version("pdffonts", ("-v",)),
        "pdftotext": tool_version("pdftotext", ("-v",)),
        "pdftoppm": tool_version("pdftoppm", ("-v",)),
    }
    font_command = ["typst", "fonts"]
    if config["font_paths"]:
        font_command += ["--font-path", os.pathsep.join(map(str, config["font_paths"]))]
    font_result = execute(font_command, cwd=config["root"])
    if font_result["returncode"] != 0:
        raise CheckError("typst fonts failed: " + (font_result["stderr"] or font_result["stdout"]).strip())
    available_fonts = [line.strip() for line in font_result["stdout"].splitlines() if line.strip()]
    failures: list[str] = []
    bibliography_record = None
    if config["bibliography_data"] is not None:
        bibliography_record = {
            "data": {
                "path": str(config["bibliography_data"]),
                "sha256": sha256(config["bibliography_data"]),
            },
            "style_asset": None if config["bibliography_style_asset"] is None else {
                "path": str(config["bibliography_style_asset"]),
                "sha256": sha256(config["bibliography_style_asset"]),
            },
        }
    report: dict[str, Any] = {
        "kind": "typst-template-fixture-check", "status": "pass",
        "checks": {"path": str(config["path"]), "sha256": sha256(config["path"])},
        "project_root": str(config["root"]),
        "template": {
            "path": str(config["template"]), "sha256": sha256(config["template"]),
            "source_inventory": source_layout_inventory(config["template"]),
        },
        "entry_symbol": config["entry_symbol"], "tools": tools,
        "fonts": {
            "paths": [str(path) for path in config["font_paths"]],
            "available_count": len(available_fonts),
            "listing_sha256": hashlib.sha256(font_result["stdout"].encode()).hexdigest(),
        },
        "bibliography": bibliography_record,
        "fixtures": [], "failures": failures,
    }
    structure_by_kind = {
        fixture["kind"]: standard_structure_inventory(fixture["source"])
        for fixture in config["fixtures"]
    }
    official_structures = structure_by_kind["official"]
    body_structures = structure_by_kind["body-flow"]
    for fixture in config["fixtures"]:
        fixture_id, source = fixture["id"], fixture["source"]
        pdf = output / "pdf" / f"{fixture_id}.pdf"
        deps = output / "deps" / f"{fixture_id}.json"
        log = output / "logs" / f"{fixture_id}.json"
        item: dict[str, Any] = {
            "id": fixture_id, "kind": fixture["kind"],
            "source": {"path": str(source), "sha256": sha256(source)},
            "source_inventory": source_layout_inventory(source),
            "bibliography_semantics": bibliography_semantics(source),
            "standard_structures": structure_by_kind[fixture["kind"]],
            "failures": [],
        }
        if fixture["kind"] == "body-flow":
            if official_structures["has_display_equation"] and not body_structures["has_display_equation"]:
                item["failures"].append(
                    "body-flow fixture must exercise a standard display equation present in the official source"
                )
            if official_structures["has_figure_caption"] and not body_structures["has_figure_caption"]:
                item["failures"].append(
                    "body-flow fixture must exercise a standard figure/caption present in the official source"
                )
        semantics = item["bibliography_semantics"]
        if (semantics["has_citation"] or semantics["has_bibliography"]) and config["bibliography_data"] is None:
            item["failures"].append("fixture uses citation/bibliography semantics but bibliography_data is undeclared")
        if fixture["kind"] in {"official", "body-flow"} and config["bibliography_data"] is not None:
            if not semantics["has_citation"] or not semantics["has_bibliography"]:
                item["failures"].append(
                    f"{fixture['kind']} fixture must exercise standard citation and bibliography semantics"
                )
        try:
            item["source_lint"] = lint_source(config["template"], source, config["entry_symbol"])
        except InputError as error:
            item["failures"].append(f"source lint: {error}")
        command = ["typst", "compile", "--root", str(config["root"])]
        if config["font_paths"]:
            command += ["--font-path", os.pathsep.join(map(str, config["font_paths"]))]
        command += ["--deps", str(deps), str(source), str(pdf)]
        compilation = execute(command, cwd=config["root"])
        write_json(log, compilation)
        combined = compilation["stdout"] + "\n" + compilation["stderr"]
        clean = compilation["returncode"] == 0 and "warning:" not in combined.casefold()
        item["compile"] = {
            "command": command, "returncode": compilation["returncode"], "clean": clean,
            "log": str(log.relative_to(output)), "log_sha256": sha256(log),
        }
        if compilation["returncode"] != 0 or not pdf.is_file():
            item["failures"].append("fixture did not compile successfully")
        elif not clean:
            item["failures"].append("fixture emitted a compiler warning")
        dependency_paths: set[Path] = set()
        if deps.is_file():
            try:
                dependency_files, dependency_paths = dependency_records(deps, config["root"])
                consumed = config["template"].resolve() in dependency_paths
                item["dependencies"] = {
                    "path": str(deps.relative_to(output)), "sha256": sha256(deps),
                    "files": dependency_files, "template_consumed": consumed,
                }
                if not consumed:
                    item["failures"].append("Typst dependency graph does not contain template_entry")
            except CheckError as error:
                item["failures"].append(str(error))
        else:
            item["failures"].append("Typst dependency file is missing")
        if config["bibliography_data"] is not None:
            data_consumed = config["bibliography_data"].resolve() in dependency_paths
            style_consumed = (
                None if config["bibliography_style_asset"] is None
                else config["bibliography_style_asset"].resolve() in dependency_paths
            )
            item["bibliography_dependencies"] = {
                "data_consumed": data_consumed, "style_asset_consumed": style_consumed,
            }
            if fixture["kind"] in {"official", "body-flow"} and not data_consumed:
                item["failures"].append(f"{fixture['kind']} fixture did not consume bibliography_data")
            if fixture["kind"] in {"official", "body-flow"} and style_consumed is False:
                item["failures"].append(f"{fixture['kind']} fixture did not consume bibliography_style_asset")
        if pdf.is_file() and compilation["returncode"] == 0:
            information, embedded = pdf_info(pdf), pdf_fonts(pdf)
            candidate_text_records = extract_pdf_text(pdf, information["pages"], output / "text" / fixture_id / "candidate")
            candidate_pages = [record["text"] for record in candidate_text_records]
            item["pdf"] = {
                "path": str(pdf.relative_to(output)), "sha256": sha256(pdf),
                "pages": information["pages"], "geometry": information["geometry"],
                "fonts": embedded["font_names"],
            }
            if information["pages"] < fixture["minimum_pages"]:
                item["failures"].append(
                    f"page count {information['pages']} is below minimum {fixture['minimum_pages']}"
                )
            item["positive_text"] = positive_text_checks(
                candidate_pages, fixture["required_text"], fixture["ordered_text"],
            )
            if not item["positive_text"]["pass"]:
                item["failures"].append("required or ordered text check failed")
            item["page_flow"] = page_flow_checks(candidate_pages, fixture["page_flows"])
            if not item["page_flow"]["pass"]:
                item["failures"].extend(item["page_flow"]["failures"])
            if fixture["required_text_file"] is not None:
                item["required_text_file"] = {
                    "path": str(fixture["required_text_file"]),
                    "sha256": sha256(fixture["required_text_file"]),
                }
            if fixture["kind"] == "official":
                reference = fixture["reference_pdf"]
                reference_info = pdf_info(reference)
                reference_text_records = extract_pdf_text(
                    reference, reference_info["pages"], output / "text" / fixture_id / "reference",
                )
                reference_pages = [record["text"] for record in reference_text_records]
                locked_text = locked_required_text_checks(reference_pages, candidate_pages, fixture["required_text"])
                geometry = geometry_metrics(reference_info, information, fixture["geometry_tolerance_pt"])
                metrics = text_metrics(reference_pages, candidate_pages)
                reference_embedded = pdf_fonts(reference)
                embedded_fonts = embedded_font_comparison(
                    reference_embedded["font_names"], embedded["font_names"],
                )
                layout_preflight = line_layout_preflight(reference, pdf)
                equation_preflight = equation_anchor_preflight(
                    reference, pdf, len(item["standard_structures"]["display_equations"]),
                )
                threshold_pass = all(
                    metrics[name] >= threshold for name, threshold in fixture["text_thresholds"].items()
                )
                item["official"] = {
                    "reference": {"path": str(reference), "sha256": sha256(reference)},
                    "geometry": geometry, "text_metrics": metrics,
                    "locked_required_text": locked_text,
                    "text_thresholds": fixture["text_thresholds"],
                    "text_thresholds_pass": threshold_pass,
                    "embedded_fonts": embedded_fonts,
                    "layout_preflight": layout_preflight,
                    "equation_preflight": equation_preflight,
                    "risk_structures": item["standard_structures"],
                }
                if not locked_text["reference"]["pass"]:
                    item["failures"].append("official required text is absent from the reference PDF")
                if not geometry["pass"]:
                    item["failures"].append("official page geometry or correspondence differs")
                if not threshold_pass:
                    item["failures"].append("official normalized text metrics are below declared thresholds")
                if not embedded_fonts["pass"]:
                    item["failures"].append(
                        "official embedded font faces differ from the reference PDF"
                    )
                if not layout_preflight["pass"]:
                    item["failures"].append(
                        "official structural text-placement preflight failed"
                    )
                if not equation_preflight["pass"]:
                    item["failures"].append(
                        "official numbered display-equation preflight failed"
                    )
                comparison = output / "comparison"
                comparison_dpi = max(config["comparison_dpi"], 300)
                compare_command = [
                    sys.executable, str(Path(__file__).with_name("compare_pdfs.py")), "scan",
                    str(reference), str(pdf), str(comparison), "--dpi", str(comparison_dpi),
                ]
                compare_result = execute(compare_command, cwd=config["root"])
                compare_log = output / "logs" / "official-comparison.json"
                write_json(compare_log, compare_result)
                item["official"]["comparison"] = {
                    "command": compare_command, "returncode": compare_result["returncode"],
                    "log": str(compare_log.relative_to(output)), "log_sha256": sha256(compare_log),
                }
                index = comparison / "index.json"
                if compare_result["returncode"] != 0 or not index.is_file():
                    item["failures"].append("official all-page comparator scan failed")
                else:
                    structure_gate = local_ink_structure_gate(index)
                    item["official"]["comparison"].update({
                        "index": str(index.relative_to(output)), "index_sha256": sha256(index),
                        "structure_gate": structure_gate,
                    })
                    if not structure_gate["pass"]:
                        item["failures"].append("official local raster structure preflight failed")
        if item["failures"]:
            failures.extend(f"{fixture_id}: {failure}" for failure in item["failures"])
        report["fixtures"].append(item)
    report["failures"] = failures
    report["status"] = "pass" if not failures else "fail"
    report["repair_targets"], report["repair_targets_truncated"] = build_repair_targets(report)
    report_path = output / "report.json"
    write_json(report_path, report)
    summary = [f"status: {report['status']}", f"fixtures: {len(report['fixtures'])}"]
    summary.extend(f"- {failure}" for failure in failures)
    summary.append(f"repair_targets: {len(report['repair_targets'])}")
    summary.extend(repair_target_summary(target) for target in report["repair_targets"])
    if report["repair_targets_truncated"]:
        summary.append(f"* additional targets omitted after limit {REPAIR_TARGET_LIMIT}")
    summary_path = output / "summary.txt"
    summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(summary_path.read_text(encoding="utf-8"), end="")
    print(f"report_json: {report_path}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check three project-declared Typst fixtures")
    parser.add_argument("checks", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    try:
        report = run(arguments.checks, arguments.output)
        return 0 if report["status"] == "pass" else 1
    except (InputError, CheckError, EvidenceError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
