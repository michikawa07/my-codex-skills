#!/usr/bin/env python3
"""Extract judgment-free facts from document-template evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Sequence


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
W = "{" + NS["w"] + "}"
TEXT_SUFFIXES = {".tex", ".sty", ".typ", ".md", ".txt", ".bib", ".yaml", ".yml", ".json"}


class EvidenceError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def execute(command: Sequence[str], *, cwd: Path | None = None) -> dict[str, Any]:
    try:
        process = subprocess.run(
            list(command), cwd=None if cwd is None else str(cwd), check=False,
            text=True, encoding="utf-8", errors="replace",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except OSError as error:
        raise EvidenceError(f"cannot execute {command[0]}: {error}") from error
    return {
        "command": list(command), "returncode": process.returncode,
        "stdout": process.stdout, "stderr": process.stderr,
    }


def checked(command: Sequence[str], *, cwd: Path | None = None) -> dict[str, Any]:
    result = execute(command, cwd=cwd)
    if result["returncode"] != 0:
        detail = (result["stderr"] or result["stdout"]).strip()
        raise EvidenceError(f"command failed ({result['returncode']}): {' '.join(command)}\n{detail}")
    return result


def tool_version(name: str, arguments: Sequence[str]) -> dict[str, Any]:
    executable = shutil.which(name)
    if executable is None:
        raise EvidenceError(f"required tool is unavailable: {name}")
    result = checked((name, *arguments))
    first = ((result["stdout"] or result["stderr"]).strip().splitlines() or ["unknown"])[0]
    path = Path(executable).resolve()
    return {"path": str(path), "sha256": sha256(path), "version": first}


def pdf_info(path: Path) -> dict[str, Any]:
    raw = checked(("pdfinfo", str(path)))["stdout"]
    page_match = re.search(r"^Pages:\s+(\d+)\s*$", raw, re.MULTILINE)
    if page_match is None:
        raise EvidenceError(f"cannot read PDF page count: {path}")
    count = int(page_match.group(1))
    detail = checked(("pdfinfo", "-box", "-f", "1", "-l", str(count), str(path)))["stdout"]
    sizes = {
        int(number): (float(width), float(height))
        for number, width, height in re.findall(
            r"^Page\s+(\d+)\s+size:\s+([0-9.+-]+)\s+x\s+([0-9.+-]+)\s+pts",
            detail, re.MULTILINE,
        )
    }
    rotations = {
        int(number): int(value)
        for number, value in re.findall(r"^Page\s+(\d+)\s+rot:\s+(-?\d+)", detail, re.MULTILINE)
    }
    boxes: dict[int, dict[str, list[float]]] = {}
    for number, kind, a, b, c, d in re.findall(
        r"^Page\s+(\d+)\s+(MediaBox|CropBox):\s+([0-9.+-]+)\s+([0-9.+-]+)\s+([0-9.+-]+)\s+([0-9.+-]+)",
        detail, re.MULTILINE,
    ):
        boxes.setdefault(int(number), {})[kind] = [float(a), float(b), float(c), float(d)]
    if len(sizes) != count or len(rotations) != count:
        raise EvidenceError(f"cannot read every PDF page geometry: {path}")
    geometry = []
    for page in range(1, count + 1):
        width, height = sizes[page]
        geometry.append({
            "page": page, "width_pt": width, "height_pt": height,
            "rotation": rotations[page], **boxes.get(page, {}),
        })
    fields = {}
    for key in ("Creator", "Producer"):
        match = re.search(rf"^{key}:\s*(.*)$", raw, re.MULTILINE)
        fields[key.casefold()] = None if match is None else match.group(1).strip()
    return {"pages": count, "geometry": geometry, **fields}


def pdf_fonts(path: Path) -> dict[str, Any]:
    raw = checked(("pdffonts", str(path)))["stdout"]
    names = [line.split()[0] for line in raw.splitlines()[2:] if line.split()]
    return {"font_names": names, "raw_sha256": hashlib.sha256(raw.encode()).hexdigest()}


def extract_pdf_text(path: Path, pages: int, destination: Path) -> list[dict[str, Any]]:
    destination.mkdir(parents=True, exist_ok=True)
    records, page_texts = [], []
    for page in range(1, pages + 1):
        target = destination / f"page-{page:03d}.txt"
        checked(("pdftotext", "-layout", "-f", str(page), "-l", str(page), str(path), str(target)))
        text = target.read_text(encoding="utf-8", errors="replace")
        page_texts.append(text)
        records.append({
            "page": page, "path": str(target), "sha256": sha256(target),
            "characters": len(text), "text": text,
        })
    (destination / "all.txt").write_text("\f\n".join(page_texts), encoding="utf-8")
    return records


def xml_attrs(node: ET.Element | None) -> dict[str, str]:
    if node is None:
        return {}
    return {
        name.rsplit("}", 1)[-1]: value
        for name, value in sorted(node.attrib.items())
    }


def child_attrs(parent: ET.Element | None, tag: str) -> dict[str, str] | None:
    node = None if parent is None else parent.find(f"w:{tag}", NS)
    return None if node is None else xml_attrs(node)


def on_off_fact(parent: ET.Element | None, tag: str) -> dict[str, Any] | None:
    node = None if parent is None else parent.find(f"w:{tag}", NS)
    if node is None:
        return None
    value = node.attrib.get(W + "val")
    return {
        "present": True,
        "value": True if value is None else value.casefold() not in {"0", "false", "off", "no"},
        "raw": xml_attrs(node),
    }


def divided_values(values: dict[str, str], divisor: float, names: Sequence[str]) -> dict[str, float]:
    result = {}
    for name in names:
        try:
            result[name] = float(values[name]) / divisor
        except (KeyError, ValueError):
            pass
    return result


def paragraph_property_facts(properties: ET.Element | None) -> dict[str, Any]:
    if properties is None:
        return {}
    facts: dict[str, Any] = {}
    for tag, key in (
        ("jc", "alignment"), ("textAlignment", "text_alignment"),
        ("spacing", "spacing"), ("ind", "indent"),
    ):
        value = child_attrs(properties, tag)
        if value is not None:
            facts[key] = value
    tabs = properties.find("w:tabs", NS)
    if tabs is not None:
        facts["tabs"] = [
            {"index": index, **xml_attrs(tab)}
            for index, tab in enumerate(tabs.findall("w:tab", NS), start=1)
        ]
    if "spacing" in facts:
        points = divided_values(facts["spacing"], 20, ("before", "after"))
        if facts["spacing"].get("lineRule") in {"exact", "atLeast"}:
            points.update(divided_values(facts["spacing"], 20, ("line",)))
        if points:
            facts["spacing_points"] = points
    if "indent" in facts:
        points = divided_values(facts["indent"], 20, ("left", "right", "start", "end", "firstLine", "hanging"))
        if points:
            facts["indent_points"] = points
    for tag, key in (
        ("keepNext", "keep_next"), ("keepLines", "keep_lines"),
        ("pageBreakBefore", "page_break_before"), ("widowControl", "widow_control"),
    ):
        value = on_off_fact(properties, tag)
        if value is not None:
            facts[key] = value
    return facts


def run_property_facts(properties: ET.Element | None) -> dict[str, Any]:
    if properties is None:
        return {}
    facts: dict[str, Any] = {}
    for tag, key in (
        ("rFonts", "fonts"), ("sz", "size_half_points"),
        ("szCs", "complex_script_size_half_points"), ("spacing", "tracking_twentieth_points"),
        ("w", "scale_percent"), ("vertAlign", "vertical_alignment"),
    ):
        value = child_attrs(properties, tag)
        if value is not None:
            facts[key] = value
    for tag, key in (("b", "bold"), ("bCs", "complex_script_bold"), ("i", "italic"), ("iCs", "complex_script_italic")):
        value = on_off_fact(properties, tag)
        if value is not None:
            facts[key] = value
    if "size_half_points" in facts:
        points = divided_values(facts["size_half_points"], 2, ("val",))
        if "val" in points:
            facts["size_points"] = points["val"]
    if "complex_script_size_half_points" in facts:
        points = divided_values(facts["complex_script_size_half_points"], 2, ("val",))
        if "val" in points:
            facts["complex_script_size_points"] = points["val"]
    if "tracking_twentieth_points" in facts:
        points = divided_values(facts["tracking_twentieth_points"], 20, ("val",))
        if "val" in points:
            facts["tracking_points"] = points["val"]
    return facts


def edge_facts(properties: ET.Element | None, container: str) -> dict[str, Any] | None:
    node = None if properties is None else properties.find(f"w:{container}", NS)
    if node is None:
        return None
    return {
        child.tag.rsplit("}", 1)[-1]: xml_attrs(child)
        for child in node
    }


def table_property_facts(properties: ET.Element | None) -> dict[str, Any]:
    if properties is None:
        return {}
    facts: dict[str, Any] = {}
    for tag, key in (
        ("tblStyle", "style"), ("tblW", "width"), ("jc", "alignment"),
        ("tblInd", "indent"), ("tblLayout", "layout"),
    ):
        value = child_attrs(properties, tag)
        if value is not None:
            facts[key] = value
    for tag, key in (("tblCellMar", "cell_margins"), ("tblBorders", "borders")):
        value = edge_facts(properties, tag)
        if value is not None:
            facts[key] = value
    if "width" in facts:
        width = facts["width"]
        if width.get("type") == "dxa":
            facts["width_normalized"] = {"unit": "pt", **divided_values(width, 20, ("w",))}
        elif width.get("type") == "pct":
            facts["width_normalized"] = {"unit": "percent", **divided_values(width, 50, ("w",))}
    return facts


def cell_property_facts(properties: ET.Element | None) -> dict[str, Any]:
    if properties is None:
        return {}
    facts: dict[str, Any] = {}
    for tag, key in (
        ("tcW", "width"), ("gridSpan", "grid_span"), ("vMerge", "vertical_merge"),
        ("vAlign", "vertical_alignment"),
    ):
        value = child_attrs(properties, tag)
        if value is not None:
            facts[key] = value
    for tag, key in (("tcMar", "cell_margins"), ("tcBorders", "borders")):
        value = edge_facts(properties, tag)
        if value is not None:
            facts[key] = value
    if "width" in facts:
        width = facts["width"]
        if width.get("type") == "dxa":
            facts["width_normalized"] = {"unit": "pt", **divided_values(width, 20, ("w",))}
        elif width.get("type") == "pct":
            facts["width_normalized"] = {"unit": "percent", **divided_values(width, 50, ("w",))}
    return facts


def merge_property_facts(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Apply the documented limited style rule: a direct property replaces its ancestor."""
    return {**base, **overlay}


def drawing_facts(drawing: ET.Element, drawing_id: str) -> dict[str, Any]:
    container = drawing.find("wp:inline", NS)
    kind = "inline"
    if container is None:
        container = drawing.find("wp:anchor", NS)
        kind = "anchor"
    if container is None:
        return {"id": drawing_id, "kind": "unresolved", "extent": None, "doc_properties": None, "blips": []}
    extent = None if container.find("wp:extent", NS) is None else xml_attrs(container.find("wp:extent", NS))
    extent_points = {}
    if extent is not None:
        raw_points = divided_values(extent, 12700, ("cx", "cy"))
        extent_points = {
            key: raw_points[source] for key, source in (("width", "cx"), ("height", "cy"))
            if source in raw_points
        }
    return {
        "id": drawing_id, "kind": kind,
        "extent": extent, "extent_points": extent_points,
        "doc_properties": (
            None if container.find("wp:docPr", NS) is None else xml_attrs(container.find("wp:docPr", NS))
        ),
        "blips": [xml_attrs(blip) for blip in container.findall(".//a:blip", NS)],
    }


def docx_inventory(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as archive:
            entries = sorted(item.filename for item in archive.infolist())
            trees = {}
            for name in ("word/document.xml", "word/styles.xml", "word/fontTable.xml"):
                if name in entries:
                    trees[name] = ET.fromstring(archive.read(name))
    except (OSError, zipfile.BadZipFile, ET.ParseError) as error:
        raise EvidenceError(f"cannot inspect DOCX {path}: {error}") from error
    document = trees.get("word/document.xml")
    styles = trees.get("word/styles.xml")
    font_table = trees.get("word/fontTable.xml")
    for name, tree in trees.items():
        namespace = tree.tag.partition("}")[0].lstrip("{") if "}" in tree.tag else ""
        if namespace and namespace != NS["w"]:
            raise EvidenceError(f"unsupported WordprocessingML namespace in {name}: {namespace}")
    sections = []
    section_elements = [] if document is None else document.findall(".//w:sectPr", NS)
    section_ids = {id(section): f"sect{index:04d}" for index, section in enumerate(section_elements, start=1)}
    if document is not None:
        for index, section in enumerate(section_elements, start=1):
            columns = section.find("w:cols", NS)
            record = {
                "id": section_ids[id(section)], "index": index,
                "page_size": child_attrs(section, "pgSz") or {},
                "margins": child_attrs(section, "pgMar") or {},
                "columns": {
                    **({} if columns is None else xml_attrs(columns)),
                    "items": [] if columns is None else [
                        {"index": item_index, **xml_attrs(column)}
                        for item_index, column in enumerate(columns.findall("w:col", NS), start=1)
                    ],
                },
                "headers": [xml_attrs(node) for node in section.findall("w:headerReference", NS)],
                "footers": [xml_attrs(node) for node in section.findall("w:footerReference", NS)],
                "document_grid": child_attrs(section, "docGrid"),
            }
            record["normalized_points"] = {
                "page_size": divided_values(record["page_size"], 20, ("w", "h")),
                "margins": divided_values(
                    record["margins"], 20,
                    ("top", "right", "bottom", "left", "header", "footer", "gutter"),
                ),
                "columns": [
                    {"index": item["index"], **divided_values(item, 20, ("w", "space"))}
                    for item in record["columns"]["items"]
                ],
            }
            sections.append(record)

    defaults = {"paragraph": {}, "run": {}}
    style_records: list[dict[str, Any]] = []
    if styles is not None:
        paragraph_default = styles.find("w:docDefaults/w:pPrDefault/w:pPr", NS)
        run_default = styles.find("w:docDefaults/w:rPrDefault/w:rPr", NS)
        defaults = {
            "paragraph": paragraph_property_facts(paragraph_default),
            "run": run_property_facts(run_default),
        }
        for index, style in enumerate(styles.findall("w:style", NS), start=1):
            style_records.append({
                "index": index, "style_id": style.attrib.get(W + "styleId"),
                "name": (child_attrs(style, "name") or {}).get("val"),
                "type": style.attrib.get(W + "type"),
                "based_on": (child_attrs(style, "basedOn") or {}).get("val"),
                "next": (child_attrs(style, "next") or {}).get("val"),
                "link": (child_attrs(style, "link") or {}).get("val"),
                "default": style.attrib.get(W + "default"),
                "direct": {
                    "paragraph": paragraph_property_facts(style.find("w:pPr", NS)),
                    "run": run_property_facts(style.find("w:rPr", NS)),
                    "table": table_property_facts(style.find("w:tblPr", NS)),
                    "cell": cell_property_facts(style.find("w:tcPr", NS)),
                },
            })
    style_by_id = {
        record["style_id"]: record for record in style_records if record["style_id"] is not None
    }
    for record in style_records:
        chain, seen, cursor = [], set(), record["style_id"]
        unresolved, cycle = None, None
        while cursor is not None:
            if cursor in seen:
                cycle = cursor
                break
            seen.add(cursor)
            current = style_by_id.get(cursor)
            if current is None:
                unresolved = cursor
                break
            chain.append(cursor)
            cursor = current["based_on"]
        ordered_chain = list(reversed(chain))
        effective = {
            "paragraph": dict(defaults["paragraph"]), "run": dict(defaults["run"]),
            "table": {}, "cell": {},
        }
        for style_id in ordered_chain:
            direct = style_by_id[style_id]["direct"]
            for kind in effective:
                effective[kind] = merge_property_facts(effective[kind], direct[kind])
        record["resolved"] = {
            "method": "docDefaults then exact basedOn chain; direct child property replacement",
            "scope": "observed style properties, not fully rendered Word formatting",
            "chain": ordered_chain, "unresolved_based_on": unresolved, "cycle_at": cycle,
            **effective,
        }

    paragraph_elements = [] if document is None else document.findall(".//w:p", NS)
    paragraph_ids = {
        id(paragraph): f"p{index:04d}" for index, paragraph in enumerate(paragraph_elements, start=1)
    }
    paragraphs = []
    if document is not None:
        for index, paragraph in enumerate(paragraph_elements, start=1):
            paragraph_id = paragraph_ids[id(paragraph)]
            properties = paragraph.find("w:pPr", NS)
            section_break = None if properties is None else properties.find("w:sectPr", NS)
            style_id = (child_attrs(properties, "pStyle") or {}).get("val")
            resolved = style_by_id.get(style_id, {}).get("resolved", {})
            runs = []
            run_elements = paragraph.findall(".//w:r", NS)
            run_ids = {id(run): f"{paragraph_id}-run-{run_index:03d}" for run_index, run in enumerate(run_elements, start=1)}
            for run_index, run in enumerate(run_elements, start=1):
                run_properties = run.find("w:rPr", NS)
                runs.append({
                    "id": run_ids[id(run)], "index": run_index,
                    "text": "".join(node.text or "" for node in run.findall(".//w:t", NS)),
                    "style_id": (child_attrs(run_properties, "rStyle") or {}).get("val"),
                    "direct": run_property_facts(run_properties),
                })
            drawing_elements = paragraph.findall(".//w:drawing", NS)
            drawing_ids = {
                id(drawing): f"{paragraph_id}-drawing-{drawing_index:03d}"
                for drawing_index, drawing in enumerate(drawing_elements, start=1)
            }
            drawings = [
                drawing_facts(drawing, drawing_ids[id(drawing)]) for drawing in drawing_elements
            ]
            math_elements = paragraph.findall(".//m:oMath", NS)
            math_ids = {
                id(math_node): f"{paragraph_id}-math-{math_index:03d}"
                for math_index, math_node in enumerate(math_elements, start=1)
            }
            inline_events = []
            for node in paragraph.iter():
                if node.tag == W + "r" and id(node) in run_ids:
                    inline_events.append({
                        "kind": "run", "id": run_ids[id(node)],
                        "text": "".join(text.text or "" for text in node.findall(".//w:t", NS)),
                    })
                elif node.tag == W + "drawing" and id(node) in drawing_ids:
                    inline_events.append({"kind": "drawing", "id": drawing_ids[id(node)]})
                elif node.tag == "{" + NS["m"] + "}oMath" and id(node) in math_ids:
                    inline_events.append({"kind": "math", "id": math_ids[id(node)]})
            for event_index, event in enumerate(inline_events, start=1):
                event["index"] = event_index
            paragraphs.append({
                "id": paragraph_id, "index": index, "style_id": style_id,
                "section_break_id": None if section_break is None else section_ids.get(id(section_break)),
                "text": "".join(node.text or "" for node in paragraph.findall(".//w:t", NS)),
                "text_method": "concatenated w:t in XML order",
                "direct": {
                    "paragraph": paragraph_property_facts(properties),
                    "paragraph_mark_run": run_property_facts(
                        None if properties is None else properties.find("w:rPr", NS)
                    ),
                },
                "resolved_style": {
                    key: resolved.get(key, {}) for key in ("paragraph", "run")
                },
                "runs": runs,
                "math_count": len(math_elements), "drawing_count": len(drawing_elements),
                "drawings": drawings, "inline_events": inline_events,
            })

    table_elements = [] if document is None else document.findall(".//w:tbl", NS)
    table_ids = {id(table): f"tbl{index:04d}" for index, table in enumerate(table_elements, start=1)}
    tables = []
    if document is not None:
        for table_index, table in enumerate(table_elements, start=1):
            properties = table.find("w:tblPr", NS)
            style_id = (child_attrs(properties, "tblStyle") or {}).get("val")
            resolved = style_by_id.get(style_id, {}).get("resolved", {})
            rows = []
            for row_index, row in enumerate(table.findall("w:tr", NS), start=1):
                row_properties = row.find("w:trPr", NS)
                row_facts = {
                    "height": child_attrs(row_properties, "trHeight"),
                    "repeat_header": on_off_fact(row_properties, "tblHeader"),
                    "cannot_split": on_off_fact(row_properties, "cantSplit"),
                }
                cells = []
                for cell_index, cell in enumerate(row.findall("w:tc", NS), start=1):
                    cells.append({
                        "index": cell_index,
                        "text": "".join(node.text or "" for node in cell.findall(".//w:t", NS)),
                        "direct": cell_property_facts(cell.find("w:tcPr", NS)),
                        "paragraph_ids": [
                            paragraph_ids[id(paragraph)] for paragraph in cell.findall(".//w:p", NS)
                        ],
                    })
                rows.append({
                    "index": row_index,
                    "direct": {key: value for key, value in row_facts.items() if value is not None},
                    "cells": cells,
                })
            tables.append({
                "id": table_ids[id(table)], "index": table_index, "style_id": style_id,
                "grid": [
                    {"index": grid_index, **xml_attrs(column)}
                    for grid_index, column in enumerate(table.findall("w:tblGrid/w:gridCol", NS), start=1)
                ],
                "grid_points": [
                    {"index": grid_index, **divided_values(xml_attrs(column), 20, ("w",))}
                    for grid_index, column in enumerate(table.findall("w:tblGrid/w:gridCol", NS), start=1)
                ],
                "direct": table_property_facts(properties),
                "resolved_style": {
                    "table": resolved.get("table", {}), "cell": resolved.get("cell", {}),
                    "scope": "basedOn properties only; conditional table style regions remain unresolved",
                },
                "rows": rows,
            })
    body_order = []
    if document is not None:
        body = document.find("w:body", NS)
        if body is not None:
            for node in body:
                kind, item_id = None, None
                if node.tag == W + "p":
                    kind, item_id = "paragraph", paragraph_ids.get(id(node))
                elif node.tag == W + "tbl":
                    kind, item_id = "table", table_ids.get(id(node))
                elif node.tag == W + "sectPr":
                    kind, item_id = "section", section_ids.get(id(node))
                if kind and item_id:
                    body_order.append({"index": len(body_order) + 1, "kind": kind, "id": item_id})
                    if kind == "paragraph":
                        section = node.find("w:pPr/w:sectPr", NS)
                        section_id = None if section is None else section_ids.get(id(section))
                        if section_id:
                            body_order.append({
                                "index": len(body_order) + 1,
                                "kind": "section_boundary", "id": section_id,
                            })
    used_fonts: set[str] = set()
    for tree in (document, styles):
        if tree is not None:
            for node in tree.findall(".//w:rFonts", NS):
                used_fonts.update(value for value in node.attrib.values() if value)
    declared_fonts = set()
    if font_table is not None:
        key = "{" + NS["w"] + "}name"
        declared_fonts = {node.attrib.get(key, "") for node in font_table.findall(".//w:font", NS)} - {""}
    return {
        "zip_entry_count": len(entries),
        "paragraph_count": 0 if document is None else len(document.findall(".//w:p", NS)),
        "table_count": 0 if document is None else len(document.findall(".//w:tbl", NS)),
        "explicit_break_count": 0 if document is None else (
            len(document.findall(".//w:br", NS)) + len(document.findall(".//w:cr", NS))
        ),
        "sections": sections,
        "unit_legend": {
            "section.pgSz/pgMar/cols, paragraph.ind/before/after, row.height, table.gridCol": "dxa, 1/20 pt",
            "paragraph.spacing.line": "lineRule=auto: 1/240 line; lineRule=exact or atLeast: dxa; otherwise unresolved",
            "run.size": "half-points", "run.tracking": "1/20 pt", "run.scale": "percent",
            "table/cell.width": "type=dxa: 1/20 pt; type=pct: 1/50 percent; other types unresolved",
            "border.size": "1/8 pt", "drawing.extent.cx/cy": "EMU, 1/12700 pt",
        },
        "style_resolution_scope": (
            "docDefaults and exact basedOn only; theme substitution, numbering, linked styles, "
            "conditional table styles, and final Word rendering remain unresolved"
        ),
        "style_defaults": defaults, "styles": style_records,
        "body_order": body_order,
        "paragraphs": paragraphs, "tables": tables,
        "used_fonts": sorted(used_fonts),
        "declared_fonts": sorted(declared_fonts),
    }


def text_inventory(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    tex_definitions = set(re.findall(r"\\(?:newcommand|renewcommand)\*?\s*\{?\\([A-Za-z@]+)", text))
    tex_definitions.update(re.findall(r"\\(?:long\s*)?def\s*\\([A-Za-z@]+)", text))
    typst_definitions = set(re.findall(r"(?m)^\s*#let\s+([_A-Za-z][A-Za-z0-9_-]*)", text))
    return {
        "line_count": len(text.splitlines()), "character_count": len(text),
        "tex_definitions": sorted(tex_definitions),
        "typst_definitions": sorted(typst_definitions),
    }


def new_output(path: Path) -> Path:
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise EvidenceError(f"output must be new or empty: {path}")
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def safe_id(path: Path, used: set[str]) -> str:
    base = re.sub(r"[^A-Za-z0-9_-]+", "-", path.stem).strip("-") or "evidence"
    candidate, counter = base, 2
    while candidate in used:
        candidate, counter = f"{base}-{counter}", counter + 1
    used.add(candidate)
    return candidate


def inspect(paths: Sequence[Path], output: Path) -> dict[str, Any]:
    output = new_output(output)
    resolved = [path.expanduser().resolve() for path in paths]
    for path in resolved:
        if not path.is_file():
            raise EvidenceError(f"evidence file not found: {path}")
    suffixes = {path.suffix.casefold() for path in resolved}
    tools = {}
    if ".pdf" in suffixes:
        tools = {
            "pdfinfo": tool_version("pdfinfo", ("-v",)),
            "pdffonts": tool_version("pdffonts", ("-v",)),
            "pdftotext": tool_version("pdftotext", ("-v",)),
        }
    records, used = [], set()
    for path in resolved:
        evidence_id = safe_id(path, used)
        record: dict[str, Any] = {
            "id": evidence_id, "path": str(path), "sha256": sha256(path),
            "bytes": path.stat().st_size, "suffix": path.suffix.casefold(),
        }
        if path.suffix.casefold() == ".pdf":
            information = pdf_info(path)
            text_records = extract_pdf_text(path, information["pages"], output / "text" / evidence_id)
            record["pdf"] = {
                **information, "fonts": pdf_fonts(path),
                "text_pages": [
                    {key: value for key, value in item.items() if key != "text"}
                    for item in text_records
                ],
                "text_all": {
                    "path": str(output / "text" / evidence_id / "all.txt"),
                    "sha256": sha256(output / "text" / evidence_id / "all.txt"),
                },
            }
        elif path.suffix.casefold() == ".docx":
            record["docx"] = docx_inventory(path)
        elif path.suffix.casefold() in TEXT_SUFFIXES:
            record["text"] = text_inventory(path)
        records.append(record)
    report = {
        "kind": "document-template-evidence", "observation_only": True,
        "tools": tools, "evidence": records,
    }
    target = output / "evidence.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"evidence_json: {target}")
    print(f"evidence_count: {len(records)}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract facts from document-template evidence")
    parser.add_argument("output", type=Path)
    parser.add_argument("inputs", nargs="+", type=Path)
    arguments = parser.parse_args()
    try:
        inspect(arguments.inputs, arguments.output)
        return 0
    except EvidenceError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
