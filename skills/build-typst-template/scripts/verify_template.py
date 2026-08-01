#!/usr/bin/env python3
"""Fixed, manifest-driven acceptance checks for Typst templates.

This is deliberately not a command runner.  It only invokes Typst, Poppler,
and the sibling PDF comparator with arguments constructed by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Sequence

CONTRACT, INPUT, ENVIRONMENT, OUTPUT = 1, 2, 3, 4
ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
SHA = re.compile(r"^[0-9a-fA-F]{64}$")
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
DEFAULTS = {"scan_dpi": 150, "pixel_threshold_percent": 3.0, "geometry_tolerance_pt": 0.1}
EVIDENCE_ROLES = {"structural-source", "visual-reference", "review-record", "accepted-typst-baseline", "external-dependency"}

def keys(value: dict[str, Any], allowed: set[str], name: str, required: set[str] = set()) -> None:
    if set(value) - allowed or not required <= set(value): raise InputError(f"{name} has unsupported or missing keys")


class Error(RuntimeError):
    exit_code = ENVIRONMENT


class InputError(Error):
    exit_code = INPUT


class OutputError(Error):
    exit_code = OUTPUT


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def execute(argv: Sequence[str], accepted: tuple[int, ...] = (0,), cwd: Path | None = None) -> dict[str, Any]:
    try:
        p = subprocess.run(list(argv), text=True, encoding="utf-8", errors="replace",
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                           cwd=None if cwd is None else str(cwd))
    except OSError as e:
        raise Error(f"cannot execute {argv[0]}: {e}") from e
    result = {"command": list(argv), "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    if p.returncode not in accepted:
        raise Error(f"command failed ({p.returncode}): {' '.join(argv)}\n{(p.stderr or p.stdout).strip()}")
    return result


def require_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise InputError(f"{name} must be a non-empty string")
    return value


def require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise InputError(f"{name} must be an array")
    return value


def finite(value: Any, name: str, low: float, high: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise InputError(f"{name} must be a finite number")
    if value < low or (high is not None and value > high):
        raise InputError(f"{name} is outside its permitted range")
    return float(value)


def json_write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise InputError(f"manifest not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise InputError(f"invalid manifest JSON: {e}") from e
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise InputError("schema_version must be 1")
    keys(value, {"schema_version","project_root","font_paths","required_available_fonts","required_typst_version","comparison_settings","evidence","required_capabilities","fixtures"}, "manifest", {"schema_version","project_root","font_paths","required_available_fonts","evidence","required_capabilities","fixtures"})
    return value


def root_for(manifest: Path, value: Any) -> Path:
    raw = Path(require_str(value, "project_root"))
    if raw.is_absolute():
        raise InputError("project_root must be relative to the manifest")
    root = (manifest.parent / raw).resolve()
    if not root.is_dir():
        raise InputError(f"project_root is not a directory: {root}")
    return root


def within(root: Path, path: Path, name: str) -> Path:
    try:
        path.relative_to(root)
    except ValueError as e:
        raise InputError(f"{name} must resolve within project_root: {path}") from e
    return path


def project_file(root: Path, raw: Any, name: str) -> Path:
    text = require_str(raw, name)
    p = Path(text)
    if p.is_absolute() or ".." in p.parts:
        raise InputError(f"{name} must be root-relative without '..'")
    result = within(root, (root / p).resolve(), name)
    if not result.is_file():
        raise InputError(f"{name} not found: {result}")
    return result


def evidence_file(root: Path, raw: Any, name: str) -> Path:
    text = require_str(raw, name)
    declared = Path(text).expanduser()
    if declared.is_absolute():
        result = declared.resolve()
    else:
        if ".." in declared.parts:
            raise InputError(f"{name} relative path must not contain '..'")
        result = within(root, (root / declared).resolve(), name)
    if not result.is_file():
        raise InputError(f"{name} not found: {result}")
    return result


def output_dir(path: Path) -> Path:
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise OutputError(f"output must be new or empty: {path}")
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OutputError(f"cannot create output: {e}") from e
    return path.resolve()


def docx_inventory(path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(path) as z:
            entries = [i.filename for i in z.infolist()]
            names = [n for n in ("word/document.xml", "word/styles.xml", "word/fontTable.xml") if n in entries]
            xml = {n: ET.fromstring(z.read(n)) for n in names}
    except (OSError, zipfile.BadZipFile, ET.ParseError) as e:
        raise Error(f"cannot inspect DOCX {path}: {e}") from e
    document, styles, font_table = (xml.get("word/document.xml"), xml.get("word/styles.xml"), xml.get("word/fontTable.xml"))
    sections = []
    if document is not None:
        for section in document.findall(".//w:sectPr", NS):
            row: dict[str, Any] = {}
            for tag, key in (("w:pgSz", "pgSz"), ("w:pgMar", "pgMar"), ("w:cols", "cols")):
                node = section.find(tag, NS)
                row[key] = {} if node is None else {k.rsplit("}", 1)[-1]: v for k, v in node.attrib.items()}
            sections.append(row)
    style_fonts: set[str] = set()
    for tree in (document, styles):
        if tree is not None:
            for node in tree.findall(".//w:rFonts", NS):
                style_fonts.update(v for v in node.attrib.values() if v)
    declared_fonts = [] if font_table is None else sorted({node.attrib.get("{" + NS["w"] + "}name", "") for node in font_table.findall(".//w:font", NS)} - {""})
    return {
        "zip_entries": entries,
        "document": {
            "paragraph_count": 0 if document is None else len(document.findall(".//w:p", NS)),
            "table_count": 0 if document is None else len(document.findall(".//w:tbl", NS)),
            "w_br_count": 0 if document is None else len(document.findall(".//w:br", NS)),
            "w_cr_count": 0 if document is None else len(document.findall(".//w:cr", NS)),
            "sections": sections,
        },
        "styles": {"rFonts": sorted(style_fonts)}, "fontTable": {"font_names": declared_fonts},
    }


def tool_version(command: Sequence[str]) -> str:
    r = execute(command)
    return ((r["stdout"] or r["stderr"]).strip().splitlines() or ["unknown"])[0]


def fonts(font_paths: list[Path]) -> tuple[dict[str, Any], str]:
    for tool in ("typst", "pdfinfo", "pdffonts", "pdftotext", "pdftoppm"):
        if not shutil.which(tool):
            raise Error(f"required tool is unavailable: {tool}")
    command = ["typst", "fonts"]
    if font_paths:
        command += ["--font-path", os.pathsep.join(str(p) for p in font_paths)]
    listing = execute(command)["stdout"]
    typst_raw = tool_version(("typst", "--version"))
    match = re.search(r"\b(\d+\.\d+\.\d+)\b", typst_raw)
    return ({"typst": typst_raw, "typst_version": None if match is None else match.group(1), "pdfinfo": tool_version(("pdfinfo", "-v")),
             "pdffonts": tool_version(("pdffonts", "-v")), "pdftotext": tool_version(("pdftotext", "-v")),
             "font_paths": [str(p) for p in font_paths], "available_family_count": len([x for x in listing.splitlines() if x.strip()])}, listing)


def pdf_info(path: Path) -> dict[str, Any]:
    raw = execute(("pdfinfo", str(path)))["stdout"]
    pages = re.search(r"^Pages:\s+(\d+)\s*$", raw, re.M)
    if pages is None:
        raise Error(f"cannot read PDF page count: {path}")
    count = int(pages.group(1))
    detail = execute(("pdfinfo", "-box", "-f", "1", "-l", str(count), str(path)))["stdout"]
    sizes = {int(n): {"page": int(n), "width_pt": float(w), "height_pt": float(h)} for n, w, h in re.findall(r"^Page\s+(\d+)\s+size:\s+([0-9.+-]+)\s+x\s+([0-9.+-]+)\s+pts", detail, re.M)}
    rotations = {int(n): int(v) for n, v in re.findall(r"^Page\s+(\d+)\s+rot:\s+(-?\d+)", detail, re.M)}
    boxes: dict[int, dict[str, list[float]]] = {}
    for n, kind, a, b, c, d in re.findall(r"^Page\s+(\d+)\s+(MediaBox|CropBox):\s+([0-9.+-]+)\s+([0-9.+-]+)\s+([0-9.+-]+)\s+([0-9.+-]+)", detail, re.M):
        boxes.setdefault(int(n), {})[kind] = [float(a), float(b), float(c), float(d)]
    if len(sizes) != count:
        raise Error(f"cannot read per-page PDF geometry: {path}")
    geometry = []
    for page in range(1, count + 1):
        if page not in rotations:
            raise Error(f"cannot read page rotation: {path}")
        geometry.append({**sizes[page], "rotation": rotations[page], **boxes.get(page, {})})
    return {"pages": count, "page_geometry": geometry, "raw": detail}


def pdf_fonts(path: Path) -> dict[str, Any]:
    raw = execute(("pdffonts", str(path)))["stdout"]
    return {"font_names": [line.split()[0] for line in raw.splitlines()[2:] if line.split()], "raw": raw}


def text_of(pdf: Path, destination: Path) -> str:
    execute(("pdftotext", "-layout", str(pdf), str(destination)))
    return destination.read_text(encoding="utf-8", errors="replace")


def norm_font(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", re.sub(r"^[A-Z]{6}\+", "", value).casefold())


def evidence(manifest: dict[str, Any], root: Path, hash_file=digest) -> tuple[list[dict[str, Any]], dict[str, Path]]:
    rows, index, ids = [], {}, set()
    for item in require_list(manifest.get("evidence", []), "evidence"):
        if not isinstance(item, dict): raise InputError("evidence entries must be objects")
        keys(item, {"id","path","role","approved_sha256"}, "evidence", {"id","path","role"})
        name = require_str(item.get("id"), "evidence.id")
        if not ID.fullmatch(name) or name in ids: raise InputError(f"invalid or duplicate evidence id: {name}")
        ids.add(name); path = evidence_file(root, item.get("path"), f"evidence.{name}.path")
        role = require_str(item.get("role"), "evidence.role")
        if role not in EVIDENCE_ROLES: raise InputError(f"unsupported evidence role: {role}")
        row = {"id": name, "path": str(path), "role": role, "sha256": hash_file(path)}
        approved = item.get("approved_sha256")
        if approved is not None:
            if not isinstance(approved, str) or not SHA.fullmatch(approved): raise InputError("approved_sha256 must be a SHA-256")
            row["approved_sha256"] = approved.casefold(); row["approved_match"] = row["approved_sha256"] == row["sha256"]
        if path.suffix.casefold() == ".docx": row["docx_inventory"] = docx_inventory(path)
        if path.suffix.casefold() == ".pdf": row["pdf"] = {**pdf_info(path), "fonts": pdf_fonts(path)}
        rows.append(row); index[name] = path
    return rows, index


def index_evidence(rows: list[dict[str, Any]], out: Path, hash_file=digest) -> tuple[list[dict[str, Any]], list[Path]]:
    """Keep detailed source observations out of the root report."""
    directory = out / "details" / "evidence"
    directory.mkdir(parents=True, exist_ok=True)
    index, created = [], []
    for row in rows:
        detail = directory / f"{row['id']}.json"
        json_write(detail, row); created.append(detail)
        summary = {key: row[key] for key in ("id", "path", "role", "sha256")}
        if "approved_sha256" in row:
            summary["approved_match"] = row["approved_match"]
        if "pdf" in row:
            summary["pdf"] = {"pages": row["pdf"]["pages"], "font_count": len(row["pdf"]["fonts"]["font_names"])}
        if "docx_inventory" in row:
            document = row["docx_inventory"]["document"]
            summary["docx"] = {"paragraph_count": document["paragraph_count"], "table_count": document["table_count"], "section_count": len(document["sections"])}
        summary["detail"] = {"path": str(detail.relative_to(out)), "sha256": hash_file(detail)}
        index.append(summary)
    return index, created


def capabilities(manifest: dict[str, Any], fixtures: list[dict[str, Any]]) -> list[str]:
    raw = require_list(manifest.get("required_capabilities"), "required_capabilities")
    required: dict[str, bool] = {}
    for item in raw:
        if isinstance(item, str): name, diagnostic = item, False
        elif isinstance(item, dict):
            keys(item, {"id","require_diagnostic"}, "required_capability", {"id"})
            name = require_str(item.get("id"), "required_capabilities.id")
            diagnostic = item.get("require_diagnostic", False)
            if not isinstance(diagnostic, bool): raise InputError("required_capabilities.require_diagnostic must be boolean")
        else: raise InputError("required_capabilities entries must be strings or objects")
        if not ID.fullmatch(name) or name in required: raise InputError(f"invalid or duplicate capability: {name}")
        required[name] = diagnostic
    observed: dict[str, set[str]] = {name: set() for name in required}
    for fixture in fixtures:
        if not isinstance(fixture, dict): raise InputError("fixture must be an object")
        fixture_id = require_str(fixture.get("id"), "fixture.id")
        for cover in require_list(fixture.get("covers"), f"fixture.{fixture_id}.covers"):
            if not isinstance(cover, dict): raise InputError("coverage entries must be objects")
            keys(cover, {"capability","case"}, "coverage", {"capability","case"})
            name, case = require_str(cover.get("capability"), "covers.capability"), require_str(cover.get("case"), "covers.case")
            if name not in observed or case not in ("nominal", "boundary", "diagnostic"): raise InputError("coverage names/cases must be declared")
            role = fixture.get("role")
            if role == "diagnostic" and case != "diagnostic": raise InputError("diagnostic fixture may cover only diagnostic cases")
            if case == "diagnostic" and role != "diagnostic": raise InputError("diagnostic coverage requires diagnostic-role fixture")
            observed[name].add(case)
    failures = []
    for name, needs_diagnostic in required.items():
        for case in (("nominal", "boundary") + (("diagnostic",) if needs_diagnostic else ())):
            if case not in observed[name]: failures.append(f"capability {name} lacks {case} coverage")
    return failures


def text_contract(text: str, contract: Any) -> dict[str, Any]:
    if not isinstance(contract, dict): raise InputError("positive_text must be an object")
    keys(contract, {"required_text","ordered_text"}, "positive_text", {"required_text"})
    required = [require_str(x, "positive_text.required_text item") for x in require_list(contract.get("required_text"), "positive_text.required_text")]
    if not required: raise InputError("success fixture requires positive_text.required_text")
    ordered = [require_str(x, "positive_text.ordered_text item") for x in require_list(contract.get("ordered_text", []), "positive_text.ordered_text")]
    if len(set(ordered)) != len(ordered): raise InputError("positive_text.ordered_text must not contain duplicates")
    missing, out_of_order, at = [x for x in required if x not in text], [], 0
    for item in ordered:
        where = text.find(item, at)
        if where < 0: out_of_order.append(item)
        else: at = where + len(item)
    return {"required_text": required, "ordered_text": ordered, "missing": missing, "order_failures": out_of_order, "pass": not missing and not out_of_order}


def visual_settings(manifest: dict[str, Any]) -> dict[str, Any]:
    settings = dict(DEFAULTS); override = manifest.get("comparison_settings")
    if override is None: return settings
    if not isinstance(override, dict): raise InputError("comparison_settings must be an object")
    unknown = set(override) - (set(DEFAULTS) | {"reason"})
    if unknown: raise InputError("comparison_settings has unsupported keys")
    for key in DEFAULTS:
        if key in override: settings[key] = finite(override[key], f"comparison_settings.{key}", 0.0)
    changed = any(key in override and settings[key] != DEFAULTS[key] for key in DEFAULTS)
    if changed: require_str(override.get("reason"), "comparison_settings.reason")
    if settings["scan_dpi"] <= 0 or int(settings["scan_dpi"]) != settings["scan_dpi"]: raise InputError("comparison_settings.scan_dpi must be positive integer")
    if settings["pixel_threshold_percent"] > 100: raise InputError("pixel threshold must be <=100")
    return settings


def comparison_run(reference: Path, candidate: Path, comparison: dict[str, Any], target: Path,
                   settings: dict[str, Any], evidence_meta: dict[str, dict[str, Any]], hash_file=digest) -> tuple[dict[str, Any], list[Path], bool]:
    """Run the staged comparator and return only compact root-index data."""
    compare_id = require_str(comparison.get("id"), "comparison.id")
    keys(comparison, {"id","reference_evidence","purpose","basis","visual","inspection"}, "comparison", {"id","reference_evidence","purpose","basis","visual"})
    purpose = require_str(comparison.get("purpose"), f"comparison.{compare_id}.purpose")
    if purpose not in ("calibration", "regression"): raise InputError("comparison purpose must be calibration or regression")
    reference_id = require_str(comparison.get("reference_evidence"), "comparison.reference_evidence")
    if reference_id not in evidence_meta: raise InputError("comparison reference must name evidence")
    reference_record = evidence_meta[reference_id]
    if purpose == "calibration" and reference_record["role"] != "visual-reference": raise InputError("calibration reference must have visual-reference role")
    basis = comparison.get("basis")
    if not isinstance(basis, dict): raise InputError("comparison.basis must be an object")
    keys(basis, {"mode","evidence"}, "comparison.basis", {"mode","evidence"})
    basis_mode = require_str(basis.get("mode"), "comparison.basis.mode")
    basis_evidence = require_str(basis.get("evidence"), "comparison.basis.evidence")
    if basis_mode not in ("content-equivalent", "geometry-only"): raise InputError("invalid comparison basis mode")
    if basis_evidence not in evidence_meta: raise InputError("comparison.basis.evidence must reference a manifest evidence id")
    if evidence_meta[basis_evidence]["role"] not in {"structural-source","review-record","accepted-typst-baseline"}: raise InputError("comparison basis evidence has an invalid role")
    visual = comparison.get("visual")
    if not isinstance(visual, dict): raise InputError("comparison.visual must be an object")
    visual_mode = require_str(visual.get("mode"), "comparison.visual.mode")
    if visual_mode not in ("evidence", "zero", "approved-budget"): raise InputError("invalid visual mode")
    if purpose == "regression" and visual_mode != "zero": raise InputError("regression comparison requires zero visual mode")
    if visual_mode == "zero" and (reference_record["role"] != "accepted-typst-baseline" or reference_record.get("approved_match") is not True): raise InputError("zero reference must be an approved matching accepted-typst-baseline")
    evidence_visual_keys = {"mode", "pixel_threshold_percent", "pixel_threshold_reason", "geometry_tolerance_pt", "geometry_tolerance_reason"}
    gate_visual_keys = {"mode", "regions", "pixel_threshold_percent", "pixel_threshold_reason", "geometry_tolerance_pt", "geometry_tolerance_reason", "page_budgets"}
    allowed_visual_keys = evidence_visual_keys if visual_mode == "evidence" else gate_visual_keys
    if set(visual) - allowed_visual_keys: raise InputError(f"{visual_mode} visual contract has unsupported keys")
    if visual_mode == "evidence":
        threshold = finite(visual.get("pixel_threshold_percent", settings["pixel_threshold_percent"]), "comparison.visual.pixel_threshold_percent", 0.0, 100.0)
        tolerance = finite(visual.get("geometry_tolerance_pt", settings["geometry_tolerance_pt"]), "comparison.visual.geometry_tolerance_pt", 0.0)
        if "pixel_threshold_percent" in visual and threshold != 3.0: require_str(visual.get("pixel_threshold_reason"), "comparison.visual.pixel_threshold_reason")
        if "geometry_tolerance_pt" in visual and tolerance != 0.1: require_str(visual.get("geometry_tolerance_reason"), "comparison.visual.geometry_tolerance_reason")
    else:
        threshold = finite(visual.get("pixel_threshold_percent", 3.0), "comparison.visual.pixel_threshold_percent", 0.0, 100.0)
        tolerance = finite(visual.get("geometry_tolerance_pt", 0.1), "comparison.visual.geometry_tolerance_pt", 0.0)
        if threshold != 3.0: require_str(visual.get("pixel_threshold_reason"), "comparison.visual.pixel_threshold_reason")
        if tolerance != 0.1: require_str(visual.get("geometry_tolerance_reason"), "comparison.visual.geometry_tolerance_reason")
    if basis_mode == "geometry-only" and visual_mode != "evidence": raise InputError("geometry-only comparison must use evidence visual mode")
    if visual_mode == "zero" and purpose != "regression": raise InputError("zero visual mode is only valid for regression")
    inspection = comparison.get("inspection")
    if inspection is not None and (not isinstance(inspection, dict) or set(inspection) != {"status", "evidence"}): raise InputError("comparison.inspection must contain exactly status and evidence")
    approved_inspection = isinstance(inspection, dict) and inspection.get("status") == "approved" and inspection.get("evidence") in evidence_meta
    if isinstance(inspection, dict) and inspection.get("status") != "approved": raise InputError("comparison.inspection.status must be approved")
    if isinstance(inspection, dict) and inspection.get("evidence") not in evidence_meta: raise InputError("comparison.inspection.evidence must reference a manifest evidence id")
    if isinstance(inspection, dict):
        record = evidence_meta[inspection["evidence"]]
        if record["role"] != "review-record" or record.get("approved_match") is not True: raise InputError("inspection evidence must be an approved matching review-record")
    script = Path(__file__).with_name("compare_pdfs.py")
    if not script.is_file(): raise Error("bundled compare_pdfs.py is missing")
    scan_dir = target / "scan"
    command = [sys.executable, str(script), "scan", str(reference), str(candidate), str(scan_dir)]
    structural_scan = basis_mode == "geometry-only" or visual_mode in ("zero", "approved-budget")
    if structural_scan:
        command += ["--layers", "content,fonts,geometry", "--geometry-tolerance-pt", str(tolerance)]
    else:
        command += ["--dpi", str(int(settings["scan_dpi"])), "--pixel-threshold-percent", str(threshold), "--geometry-tolerance-pt", str(tolerance)]
    execute(command)
    index_path = scan_dir / "index.json"
    if not index_path.is_file(): raise Error("comparison scan did not create index.json")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    top = []
    for domain, findings in index.get("findings", {}).items():
        for finding in findings[:4]:
            top.append({"domain": domain, "id": finding.get("id"), "page": finding.get("page"), "measurement_kind": finding.get("measurement_kind"), "detail": finding.get("detail")})
            if len(top) >= 20: break
        if len(top) >= 20: break
    run_root = target.parents[2]
    scan_meaning = (
        "non-raster content/font/geometry preflight before the sole 300 dpi gate"
        if visual_mode in ("zero", "approved-budget")
        else "non-raster geometry-only evidence; no visual layout completion claim"
        if basis_mode == "geometry-only"
        else f"{int(settings['scan_dpi'])} dpi all-layer calibration evidence for human inspection"
    )
    page_count_equal = index.get("page_count", {}).get("equal") is True
    geometry_mismatch_count = index.get("geometry", {}).get("mismatch_count")
    geometry_pass = page_count_equal and geometry_mismatch_count == 0
    result: dict[str, Any] = {"id": compare_id, "purpose": purpose, "basis": {"mode": basis_mode, "evidence": basis_evidence}, "visual_mode": visual_mode, "scan": {"index": str(index_path.relative_to(run_root)), "sha256": hash_file(index_path), "layers": index.get("settings", {}).get("layers"), "meaning": scan_meaning, "differences_present": index.get("differences_present"), "finding_summary": index.get("finding_summary"), "geometry": {"pass": geometry_pass, "page_count_equal": page_count_equal, "mismatch_count": geometry_mismatch_count, "tolerance_pt": index.get("settings", {}).get("geometry_tolerance_pt")}, "top_findings": top}, "gate": None}
    if visual_mode == "evidence" and not geometry_pass:
        result["failure"] = "reference geometry differs at the effective scan tolerance"
    created = [index_path]
    requires_inspection = purpose == "calibration" or basis_mode == "geometry-only" or visual_mode == "approved-budget"
    pending = requires_inspection and not approved_inspection
    if visual_mode in ("zero", "approved-budget"):
        contract_path = target / "gate-contract.json"; json_write(contract_path, visual); created.append(contract_path)
        gate_dir = target / "gate"
        gate_record = execute((sys.executable, str(script), "gate", str(reference), str(candidate), str(contract_path), str(gate_dir)), (0, 1))
        gate_path = gate_dir / "gate.json"
        if not gate_path.is_file(): raise Error("comparison gate did not create gate.json")
        gate = json.loads(gate_path.read_text(encoding="utf-8")); created.append(gate_path)
        result["gate"] = {"path": str(gate_path.relative_to(run_root)), "sha256": hash_file(gate_path), "status": gate.get("status"), "failed_id_count": gate.get("failed_id_count"), "failed_ids": gate.get("failed_ids", [])[:20]}
        if gate_record["returncode"] != 0 or gate.get("status") != "pass": result["failure"] = "visual gate failed"
    if approved_inspection: result["inspection"] = inspection
    return result, created, pending


def starter() -> dict[str, Any]:
    caps = ["frontmatter", "presenter-marker", "heading", "inline-math", "display-equation", "image-sizing", "figure-grouping", "caption", "table", "list", "cross-reference", "manual-reference", "bibliography"]
    return {"schema_version": 1, "project_root": ".", "font_paths": [], "required_available_fonts": [], "comparison_settings": dict(DEFAULTS), "evidence": [{"id":"official-structure","path":"evidence/official.docx","role":"structural-source"},{"id":"official-visual","path":"evidence/official.pdf","role":"visual-reference"}], "required_capabilities": [{"id": c, "require_diagnostic": c in ("display-equation", "image-sizing", "caption")} for c in caps], "fixtures": [
        {"id": "standard-syntax-nominal", "source": "fixtures/standard-syntax-nominal.typ", "role": "official", "intent": "Verified regression targets: Japanese body references are 図1 and 表1, while English caption prefixes are Fig. 1 and Table 1; bibliography heading preceding space is preserved; captions are 9.5 pt. Pending visual inspection remains explicit for the presenter glyph and chapter default versus local override spacing.", "covers": [{"capability": c, "case": "nominal"} for c in caps], "positive_text": {"required_text": ["JAPANESE-BODY-FIGURE-REFERENCE-図1", "JAPANESE-BODY-TABLE-REFERENCE-表1", "ENGLISH-CAPTION-FIG-1", "ENGLISH-CAPTION-TABLE-1", "BIBLIOGRAPHY-SPACING-END", "NOMINAL-STANDARD-SYNTAX-END"]}, "comparisons": [{"id":"official-calibration","reference_evidence":"official-visual","purpose":"calibration","basis":{"mode":"content-equivalent","evidence":"official-structure"},"visual":{"mode":"evidence"}}]},
        {"id": "standard-syntax-boundary", "source": "fixtures/standard-syntax-boundary.typ", "role": "stress", "intent": "Verified regression target: preliminary 0/0 images survive sizing and retain following content. Exercise narrow/grouped figures, wrapped captions, page-crossing tables/lists/references and end markers. Nested figure/container usage remains an explicitly pending design/visual inspection item.", "covers": [{"capability": c, "case": "boundary"} for c in caps], "positive_text": {"required_text": ["ZERO-DIMENSION-IMAGE-END", "NESTED-FIGURE-PENDING-INSPECTION", "TABLE-END", "LIST-END", "REFERENCE-END", "BOUNDARY-STANDARD-SYNTAX-END"]}, "comparisons": []},
        {"id": "atomic-display-equation-diagnostic", "source": "fixtures/atomic-display-equation-diagnostic.typ", "role": "diagnostic", "intent": "An overwide or over-tall atomic display equation fails with an actionable diagnostic.", "covers": [{"capability": "display-equation", "case": "diagnostic"}], "required_diagnostic_text": ["ACTIONABLE DISPLAY EQUATION DIAGNOSTIC"]},
        {"id": "atomic-figure-diagnostic", "source": "fixtures/atomic-figure-diagnostic.typ", "role": "diagnostic", "intent": "An unsplittable figure body/caption that exceeds one page fails explicitly.", "covers": [{"capability": "image-sizing", "case": "diagnostic"}, {"capability": "caption", "case": "diagnostic"}], "required_diagnostic_text": ["ACTIONABLE FIGURE DIAGNOSTIC"]}
    ]}


def init(manifest: Path, profile: str) -> int:
    if profile != "academic-paper": raise InputError("only --profile academic-paper is supported")
    if manifest.exists(): raise OutputError(f"refusing to overwrite {manifest}")
    manifest.parent.mkdir(parents=True, exist_ok=True); json_write(manifest, starter()); print(f"created: {manifest}"); return 0


def inspect(manifest_path: Path, destination: Path) -> int:
    manifest_path = manifest_path.resolve(); manifest = load(manifest_path); root = root_for(manifest_path, manifest.get("project_root")); out = output_dir(destination)
    raw_paths = require_list(manifest.get("font_paths"), "font_paths")
    paths = []
    for raw in raw_paths:
        p = Path(require_str(raw, "font_paths item")); p = p.resolve() if p.is_absolute() else (root / p).resolve()
        if not p.is_dir(): raise Error(f"font path missing: {p}")
        paths.append(p)
    toolchain, listing = fonts(paths); rows, _ = evidence(manifest, root)
    (out / "details").mkdir(); (out / "text").mkdir()
    tool_detail = out / "details" / "toolchain.json"
    json_write(tool_detail, {"toolchain": toolchain, "typst_fonts_listing": listing})
    evidence_index, evidence_details = index_evidence(rows, out)
    text_artifacts: list[Path] = []
    for row in rows:
        if Path(row["path"]).suffix.casefold() == ".pdf":
            text_path = out / "text" / f"{row['id']}.txt"; value = text_of(Path(row["path"]), text_path)
            text_artifacts.append(text_path)
            summary = next(item for item in evidence_index if item["id"] == row["id"])
            summary["pdf_text"] = {"path": str(text_path.relative_to(out)), "sha256": digest(text_path), "page_character_counts": [len(x) for x in value.split("\f")]}
    observation = {"status": "observed", "manifest": {"path": str(manifest_path), "sha256": digest(manifest_path)}, "project_root": str(root), "toolchain": {"path": str(tool_detail.relative_to(out)), "sha256": digest(tool_detail), "typst_version": toolchain["typst_version"]}, "evidence": evidence_index, "artifacts": [{"path": str(path.relative_to(out)), "sha256": digest(path)} for path in [tool_detail, *evidence_details, *text_artifacts]]}
    json_write(out / "observation.json", observation); print("status: observed"); return 0


def run(manifest_path: Path, destination: Path) -> int:
    manifest_path = manifest_path.resolve(); manifest = load(manifest_path); root = root_for(manifest_path, manifest.get("project_root")); out = output_dir(destination)
    digest_cache: dict[Path, str] = {}
    def run_hash(path: Path) -> str:
        key = path.resolve()
        if key not in digest_cache: digest_cache[key] = digest(key)
        return digest_cache[key]
    font_paths = []
    for raw in require_list(manifest.get("font_paths"), "font_paths"):
        p = Path(require_str(raw, "font_paths item")); p = p.resolve() if p.is_absolute() else (root / p).resolve()
        if not p.is_dir(): raise Error(f"font path missing: {p}")
        font_paths.append(p)
    toolchain, listing = fonts(font_paths)
    required_version = manifest.get("required_typst_version")
    if required_version is not None and require_str(required_version, "required_typst_version") != toolchain["typst_version"]:
        raise Error(f"required Typst version {required_version} is unavailable (found {toolchain['typst_version']})")
    required_fonts = [require_str(x, "required_available_fonts item") for x in require_list(manifest.get("required_available_fonts"), "required_available_fonts")]
    available_families = {line.strip().casefold() for line in listing.splitlines() if line.strip()}
    missing_available = [x for x in required_fonts if x.casefold() not in available_families]
    if missing_available: raise Error("required available fonts missing: " + ", ".join(missing_available))
    fixtures = require_list(manifest.get("fixtures"), "fixtures")
    if not fixtures: raise InputError("fixtures must not be empty")
    common_fixture_keys = {"id","source","role","intent","covers","approved_external_dependencies"}
    success_fixture_keys = {"positive_text","comparisons","page_contract","required_embedded_fonts"}
    diagnostic_fixture_keys = {"required_diagnostic_text"}
    official_count = 0
    for fixture in fixtures:
        if not isinstance(fixture, dict): raise InputError("fixture must be an object")
        role = require_str(fixture.get("role"), "fixture.role")
        if role not in ("official", "stress", "diagnostic"): raise InputError("invalid fixture role")
        allowed = common_fixture_keys | (diagnostic_fixture_keys if role == "diagnostic" else success_fixture_keys)
        required = common_fixture_keys - {"approved_external_dependencies"}
        if role == "diagnostic": required |= diagnostic_fixture_keys
        else: required.add("positive_text")
        keys(fixture, allowed, "fixture", required)
        require_str(fixture.get("intent"), "fixture.intent")
        if role == "official":
            official_count += 1
            if not require_list(fixture.get("comparisons"), "official fixture comparisons"): raise InputError("every official fixture requires at least one comparison")
        if role == "diagnostic":
            required_diagnostic = [require_str(x, "required_diagnostic_text item") for x in require_list(fixture.get("required_diagnostic_text"), "required_diagnostic_text")]
            if not required_diagnostic: raise InputError("diagnostic requires required_diagnostic_text")
        else:
            page_contract = fixture.get("page_contract", {})
            if not isinstance(page_contract, dict): raise InputError("page_contract must be an object")
            keys(page_contract, {"minimum_pages"}, "page_contract")
    if official_count == 0: raise InputError("at least one official fixture is required")
    coverage_failures = capabilities(manifest, fixtures); settings = visual_settings(manifest)
    for name in ("pdf", "logs", "text", "deps", "comparison", "details"): (out / name).mkdir()
    report: dict[str, Any] = {"automation_status": "pass", "completion_state": "automation_pass", "manifest": {"path": str(manifest_path), "sha256": run_hash(manifest_path)}, "project_root": str(root), "settings": settings, "toolchain": {}, "evidence": [], "coverage_failures": coverage_failures, "fixtures": [], "failures": list(coverage_failures), "artifacts": []}
    seen = set()
    def artifact(path: Path) -> None:
        if not path.is_file(): raise Error(f"expected generated artifact missing: {path}")
        report["artifacts"].append({"path": str(path), "relative_path": str(path.relative_to(out)), "sha256": run_hash(path)})
    tool_detail = out / "details" / "toolchain.json"
    json_write(tool_detail, {"toolchain": toolchain, "typst_fonts_listing": listing}); artifact(tool_detail)
    report["toolchain"] = {"path": str(tool_detail.relative_to(out)), "sha256": run_hash(tool_detail), "typst_version": toolchain["typst_version"]}
    rows, evidence_index = evidence(manifest, root, run_hash)
    evidence_observations = {row["id"]: row for row in rows}
    compact_evidence, evidence_details = index_evidence(rows, out, run_hash)
    report["evidence"] = compact_evidence
    for detail in evidence_details: artifact(detail)
    for item in compact_evidence:
        if item.get("approved_match") is False: report["failures"].append(f"evidence {item['id']} SHA-256 differs from approved value")
    for fixture in fixtures:
        if not isinstance(fixture, dict): raise InputError("fixture must be an object")
        name = require_str(fixture.get("id"), "fixture.id")
        if not ID.fullmatch(name) or name in seen: raise InputError("fixture ids must be unique and safe")
        seen.add(name); source = project_file(root, fixture.get("source"), f"fixture.{name}.source")
        role = require_str(fixture.get("role"), "fixture.role")
        if "outcome" in fixture: raise InputError("fixture.outcome is redundant; outcome is derived from role")
        if role not in ("official", "stress", "diagnostic"): raise InputError("invalid fixture role")
        outcome = "diagnostic" if role == "diagnostic" else "success"
        pdf, deps, log = out / "pdf" / f"{name}.pdf", out / "deps" / f"{name}.json", out / "logs" / f"{name}.json"
        command = ["typst", "compile", "--root", str(root)]
        if font_paths: command += ["--font-path", os.pathsep.join(str(p) for p in font_paths)]
        command += ["--deps", str(deps), str(source), str(pdf)]
        compilation = execute(command, (0, 1), root); json_write(log, compilation); artifact(log)
        entry: dict[str, Any] = {"id": name, "role": role, "outcome": outcome, "source": {"path": str(source), "sha256": run_hash(source)}, "compile": {"returncode": compilation["returncode"], "log": str(log.relative_to(out)), "log_sha256": run_hash(log), "clean": None}, "failures": []}
        if outcome == "diagnostic":
            required = [require_str(x, "required_diagnostic_text item") for x in require_list(fixture.get("required_diagnostic_text"), "required_diagnostic_text")]
            if not required: raise InputError("diagnostic requires required_diagnostic_text")
            combined = compilation["stdout"] + "\n" + compilation["stderr"]; missing = [x for x in required if x not in combined]
            if compilation["returncode"] == 0 or missing: entry["failures"].append("diagnostic outcome/literals do not match")
        else:
            if compilation["returncode"] != 0 or not pdf.is_file(): entry["failures"].append("success fixture did not compile")
            else:
                entry["compile"]["clean"] = "warning:" not in (compilation["stdout"] + compilation["stderr"]).casefold()
                if not entry["compile"]["clean"]: entry["failures"].append("success fixture emitted warning")
                info, embedded = pdf_info(pdf), pdf_fonts(pdf); artifact(pdf)
                pdf_detail = out / "details" / f"{name}-pdf.json"; json_write(pdf_detail, {"pdf_info": info, "pdf_fonts": embedded}); artifact(pdf_detail)
                entry["pdf"] = {"path": str(pdf.relative_to(out)), "sha256": run_hash(pdf), "pages": info["pages"], "font_count": len(embedded["font_names"]), "detail": {"path": str(pdf_detail.relative_to(out)), "sha256": run_hash(pdf_detail)}}
                minimum = fixture.get("page_contract", {}).get("minimum_pages", 1) if isinstance(fixture.get("page_contract", {}), dict) else None
                if not isinstance(minimum, int) or minimum < 1: raise InputError("page_contract.minimum_pages must be positive integer")
                if info["pages"] < minimum: entry["failures"].append("page count below minimum")
                want_fonts = [require_str(x, "required_embedded_fonts item") for x in require_list(fixture.get("required_embedded_fonts", []), "required_embedded_fonts")]
                actual = [norm_font(x) for x in embedded["font_names"]]
                if any(norm_font(w) not in actual for w in want_fonts): entry["failures"].append("required embedded font missing")
                text_path = out / "text" / f"{name}.txt"; text = text_of(pdf, text_path); artifact(text_path); entry["text"] = text_contract(text, fixture.get("positive_text"));
                if not entry["text"]["pass"]: entry["failures"].append("positive text contract failed")
                comparison_results, comparison_ids = [], set()
                for comparison in require_list(fixture.get("comparisons", []), "fixture.comparisons"):
                    if not isinstance(comparison, dict): raise InputError("comparison must be an object")
                    comparison_id = require_str(comparison.get("id"), "comparison.id")
                    if not ID.fullmatch(comparison_id) or comparison_id in comparison_ids: raise InputError("comparison ids must be unique and safe")
                    comparison_ids.add(comparison_id)
                    ref_id = require_str(comparison.get("reference_evidence"), "comparison.reference_evidence")
                    if ref_id not in evidence_index or evidence_index[ref_id].suffix.casefold() != ".pdf": raise InputError("comparison reference_evidence must name PDF evidence")
                    # Reuse the one evidence inventory made at run start.
                    result, generated, pending = comparison_run(evidence_index[ref_id], pdf, comparison, out / "comparison" / name / comparison_id, settings, evidence_observations, run_hash)
                    for generated_path in generated: artifact(generated_path)
                    if result.get("failure"): entry["failures"].append(f"comparison {comparison_id}: {result['failure']}")
                    if pending: report["completion_state"] = "inspection_pending"
                    comparison_results.append(result)
                entry["comparisons"] = comparison_results
        if deps.is_file():
            try:
                data = json.loads(deps.read_text(encoding="utf-8")); inputs = data.get("inputs", []) if isinstance(data, dict) else []
                if not isinstance(inputs, list) or any(not isinstance(x, str) for x in inputs): raise ValueError
                external_ids = [require_str(x, "approved_external_dependencies item") for x in require_list(fixture.get("approved_external_dependencies", []), "approved_external_dependencies")]
                if len(set(external_ids)) != len(external_ids): raise InputError("approved_external_dependencies must not contain duplicates")
                for external_id in external_ids:
                    if external_id not in evidence_index or evidence_observations[external_id]["role"] != "external-dependency": raise InputError("approved external dependency must reference external-dependency evidence")
                    if evidence_observations[external_id].get("approved_match") is not True:
                        raise InputError("approved external dependency must have a matching approved_sha256")
                allowed_external = {evidence_index[x] for x in external_ids}
                hashes = []
                for raw in inputs:
                    p = Path(raw); p = p.resolve() if p.is_absolute() else (root / p).resolve()
                    try: within(root, p, "dependency")
                    except InputError:
                        if p not in allowed_external: raise
                    if not p.is_file(): raise Error(f"dependency missing: {p}")
                    hashes.append({"path": str(p), "sha256": run_hash(p)})
                artifact(deps)
                dependency_detail = out / "details" / f"{name}-dependencies.json"
                json_write(dependency_detail, {"deps_path": str(deps), "deps_sha256": run_hash(deps), "files": hashes}); artifact(dependency_detail)
                entry["dependencies"] = {"path": str(deps.relative_to(out)), "sha256": run_hash(deps), "count": len(hashes), "detail": {"path": str(dependency_detail.relative_to(out)), "sha256": run_hash(dependency_detail)}}
            except (OSError, json.JSONDecodeError, ValueError) as e: raise Error(f"invalid Typst dependency data: {deps}") from e
        if entry["failures"]: report["failures"].extend(f"{name}: {x}" for x in entry["failures"])
        report["fixtures"].append(entry)
    if report["failures"]: report["automation_status"] = "fail"; report["completion_state"] = "incomplete"
    summary = out / "summary.txt"; summary.write_text("\n".join([f"automation_status: {report['automation_status']}", f"completion_state: {report['completion_state']}"] + [f"- {x}" for x in report["failures"]]) + "\n", encoding="utf-8"); artifact(summary)
    report["artifacts"].append({"path": str(out / "run.json"), "relative_path": "run.json", "sha256": None, "note": "self hash is intentionally undefined"})
    json_write(out / "run.json", report); print((out / "summary.txt").read_text(encoding="utf-8")); return 0 if report["automation_status"] == "pass" else CONTRACT


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fixed Typst acceptance verifier")
    s = p.add_subparsers(dest="command", required=True)
    i = s.add_parser("init"); i.add_argument("manifest", type=Path); i.add_argument("--profile", default="academic-paper")
    q = s.add_parser("inspect"); q.add_argument("manifest", type=Path); q.add_argument("output", type=Path)
    r = s.add_parser("run"); r.add_argument("manifest", type=Path); r.add_argument("output", type=Path)
    return p.parse_args()


def main() -> int:
    a = args()
    try:
        return init(a.manifest, a.profile) if a.command == "init" else inspect(a.manifest, a.output) if a.command == "inspect" else run(a.manifest, a.output)
    except Error as e:
        print(f"error: {e}", file=sys.stderr); return e.exit_code
    except OSError as e:
        print(f"error: {e}", file=sys.stderr); return OUTPUT


if __name__ == "__main__": raise SystemExit(main())
