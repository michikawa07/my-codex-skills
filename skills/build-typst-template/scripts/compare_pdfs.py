#!/usr/bin/env python3
"""Measure PDF differences without registration, rescaling, or OCR normalization.

``scan`` records broad evidence, ``detail`` renders one selected area at high
resolution, and ``gate`` applies an explicit acceptance contract.  None of the
subcommands compiles documents or executes caller-provided commands.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


EXIT_DIFFERENT = 1
EXIT_INPUT = 2
EXIT_DEPENDENCY = 3
EXIT_EXECUTION = 4
EXIT_OUTPUT = 5
DEFAULT_LAYERS = ("content", "fonts", "geometry", "ink", "pixels")
REGION_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
PAGE_COUNT_RE = re.compile(r"^Pages:\s+(\d+)\s*$", re.MULTILINE)
PAGE_SIZE_RE = re.compile(r"^Page\s+(\d+)\s+size:\s+([0-9.+-]+)\s+x\s+([0-9.+-]+)\s+pts", re.MULTILINE)
PAGE_ROT_RE = re.compile(r"^Page\s+(\d+)\s+rot:\s+(-?\d+)\s*$", re.MULTILINE)
PAGE_BOX_RE = re.compile(r"^Page\s+(\d+)\s+(MediaBox|CropBox):\s+([0-9.+-]+)\s+([0-9.+-]+)\s+([0-9.+-]+)\s+([0-9.+-]+)\s*$", re.MULTILINE)
PDF_FIELD_RE = re.compile(r"^(Creator|Producer):\s*(.*)$", re.MULTILINE)
SUBSET_FONT_RE = re.compile(r"^[A-Z]{6}\+")


class CompareError(RuntimeError):
    exit_code = EXIT_EXECUTION


class InputError(CompareError):
    exit_code = EXIT_INPUT


class DependencyError(CompareError):
    exit_code = EXIT_DEPENDENCY


class OutputError(CompareError):
    exit_code = EXIT_OUTPUT


@dataclass(frozen=True)
class ImageMagick:
    compare: tuple[str, ...]
    convert: tuple[str, ...]
    identify: tuple[str, ...]
    version: tuple[str, ...]


def run(command: Sequence[str], *, accepted_codes: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(list(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", check=False)
    if result.returncode not in accepted_codes:
        detail = (result.stderr or result.stdout).strip()
        raise CompareError(f"command failed ({result.returncode}): {' '.join(command)}" + (f"\n{detail}" if detail else ""))
    return result


def run_bytes(command: Sequence[str]) -> bytes:
    result = subprocess.run(list(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise CompareError(f"command failed ({result.returncode}): {' '.join(command)}\n" + result.stderr.decode(errors="replace"))
    return result.stdout


def find_imagemagick() -> ImageMagick:
    if shutil.which("magick"):
        return ImageMagick(("magick", "compare"), ("magick",), ("magick", "identify"), ("magick", "-version"))
    missing = [name for name in ("compare", "convert", "identify") if not shutil.which(name)]
    if missing:
        raise DependencyError("missing ImageMagick commands: " + ", ".join(missing))
    return ImageMagick(("compare",), ("convert",), ("identify",), ("convert", "-version"))


def require_dependencies(*, content: bool, fonts: bool, render: bool) -> ImageMagick | None:
    required = ["pdfinfo"]
    if render:
        required.append("pdftoppm")
    if content:
        required.append("pdftotext")
    if fonts:
        required.append("pdffonts")
    missing = [name for name in required if not shutil.which(name)]
    if missing:
        raise DependencyError("missing required commands: " + ", ".join(missing))
    return find_imagemagick() if render else None


def tool_version(command: Sequence[str]) -> str:
    result = run(command)
    text = (result.stdout or result.stderr).strip()
    return text.splitlines()[0] if text else "unknown"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_pdf(path: Path) -> Path:
    path = path.expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise InputError(f"PDF not found or not a .pdf file: {path}")
    return path


def prepare_output(path: Path) -> Path:
    path = path.expanduser().resolve()
    if path.exists() and not path.is_dir():
        raise OutputError(f"output path exists and is not a directory: {path}")
    if path.exists() and any(path.iterdir()):
        raise OutputError(f"output directory is not empty: {path}")
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise OutputError(f"cannot prepare output directory {path}: {error}") from error
    return path


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path, label: str) -> Any:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise InputError(f"{label} not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InputError(f"could not read {label}: {error}") from error


def inspect_pdf(path: Path) -> dict[str, Any]:
    basic = run(("pdfinfo", "-box", "-f", "1", "-l", "999999", str(path))).stdout
    match = PAGE_COUNT_RE.search(basic)
    if not match:
        raise CompareError(f"could not read page count from: {path}")
    count = int(match.group(1))
    detailed = basic
    pages = {page: {"page": page, "width_pt": None, "height_pt": None, "rotation": None} for page in range(1, count + 1)}
    for item in PAGE_SIZE_RE.finditer(detailed):
        pages[int(item.group(1))].update(width_pt=float(item.group(2)), height_pt=float(item.group(3)))
    for item in PAGE_ROT_RE.finditer(detailed):
        pages[int(item.group(1))]["rotation"] = int(item.group(2))
    for item in PAGE_BOX_RE.finditer(detailed):
        pages[int(item.group(1))][item.group(2)] = [float(item.group(i)) for i in range(3, 7)]
    missing = [page for page, value in pages.items() if value["width_pt"] is None or value["height_pt"] is None]
    if missing:
        raise CompareError(f"missing page geometry for {path}: {missing}")
    metadata = {match.group(1).lower(): match.group(2).strip() for match in PDF_FIELD_RE.finditer(basic)}
    return {"path": str(path), "sha256": sha256(path), "pages": count, "page_geometry": list(pages.values()), "render_origin": metadata}


def visual_size(geometry: dict[str, Any]) -> tuple[float, float]:
    rotation = int(geometry["rotation"] or 0) % 360
    if rotation in (0, 180):
        return float(geometry["width_pt"]), float(geometry["height_pt"])
    if rotation in (90, 270):
        return float(geometry["height_pt"]), float(geometry["width_pt"])
    raise CompareError(f"unsupported page rotation: {geometry['rotation']}")


def geometry_equal(left: dict[str, Any], right: dict[str, Any], tolerance: float) -> bool:
    if left["rotation"] != right["rotation"]:
        return False
    for key in ("width_pt", "height_pt"):
        if abs(left[key] - right[key]) > tolerance:
            return False
    for key in ("MediaBox", "CropBox"):
        if (key in left) != (key in right):
            return False
        if key in left and any(abs(a - b) > tolerance for a, b in zip(left[key], right[key])):
            return False
    return True


def render_page(pdf: Path, page: int, dpi: int, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    prefix = target.with_suffix("")
    run(("pdftoppm", "-png", "-r", str(dpi), "-f", str(page), "-l", str(page), "-singlefile", str(pdf), str(prefix)))
    if not target.is_file():
        raise CompareError(f"rasterizer did not create: {target}")
    return target


def render_pages(pdf: Path, count: int, dpi: int, output: Path, label: str) -> dict[int, Path]:
    if count <= 0: return {}
    prefix = output / f".scan-{label}"
    run(("pdftoppm", "-png", "-r", str(dpi), "-f", "1", "-l", str(count), str(pdf), str(prefix)))
    rendered: dict[int, Path] = {}
    for page in range(1, count + 1):
        source = Path(f"{prefix}-{page}.png")
        if not source.is_file(): raise CompareError(f"batch rasterizer did not create page {page}: {source}")
        target = output / "pages" / f"{page:03d}" / f"{label}.png"
        target.parent.mkdir(parents=True, exist_ok=True); source.replace(target); rendered[page] = target
    return rendered


def image_size(im: ImageMagick, path: Path) -> tuple[int, int]:
    try:
        with path.open("rb") as stream:
            header = stream.read(24)
        if header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR":
            return struct.unpack(">II", header[16:24])
    except OSError as error:
        raise CompareError(f"could not read image dimensions: {path}") from error
    raise CompareError(f"expected PNG image: {path}")


def create_visuals(im: ImageMagick, reference: Path, candidate: Path, directory: Path) -> dict[str, Path]:
    paths = {"reference": reference, "candidate": candidate, "abs": directory / "abs.png", "highlight": directory / "highlight.png", "overlay": directory / "overlay.png", "side_by_side": directory / "side-by-side.png"}
    if not paths["abs"].is_file():
        run((*im.convert, str(reference), str(candidate), "-compose", "difference", "-composite", str(paths["abs"])))
    run((*im.compare, str(reference), str(candidate), str(paths["highlight"])), accepted_codes=(0, 1))
    run((*im.convert, str(reference), str(candidate), "-evaluate-sequence", "mean", str(paths["overlay"])))
    run((*im.convert, str(reference), str(candidate), "+append", str(paths["side_by_side"])))
    return paths


def ae_metric(im: ImageMagick, reference: Path, candidate: Path) -> int:
    result = run((*im.compare, "-metric", "AE", str(reference), str(candidate), "null:"), accepted_codes=(0, 1))
    return int(float(result.stderr.strip().splitlines()[-1]))


def rmse_metric(im: ImageMagick, reference: Path, candidate: Path) -> tuple[float, float]:
    result = run((*im.compare, "-metric", "RMSE", str(reference), str(candidate), "null:"), accepted_codes=(0, 1))
    match = re.search(r"([0-9.eE+-]+)\s+\(([0-9.eE+-]+)\)", result.stderr.strip().splitlines()[-1])
    if not match:
        raise CompareError("could not parse RMSE metric")
    return float(match.group(1)), float(match.group(2))


def difference_ratio(im: ImageMagick, abs_diff: Path, threshold: float) -> float:
    text = run((*im.convert, str(abs_diff), "-colorspace", "Gray", "-threshold", f"{threshold}%", "-format", "%[fx:mean]", "info:")).stdout.strip()
    try:
        return float(text)
    except ValueError as error:
        raise CompareError(f"could not parse changed ratio: {text}") from error


def thresholded_bbox(im: ImageMagick, image: Path, threshold: float, *, invert: bool) -> str | None:
    command = [*im.convert, str(image), "-colorspace", "Gray"]
    if invert:
        command.append("-negate")
    command.extend(("-threshold", f"{threshold}%", "-format", "%[fx:mean]|%@", "info:"))
    text = run(command, accepted_codes=(0, 1)).stdout.strip()
    try:
        fraction, bbox = text.split("|", maxsplit=1)
        return bbox or None if float(fraction) > 0 else None
    except ValueError as error:
        raise CompareError(f"could not parse bounding box: {text}") from error


def crop(im: ImageMagick, source: Path, target: Path, box: tuple[int, int, int, int]) -> Path:
    x, y, width, height = box
    run((*im.convert, str(source), "-crop", f"{width}x{height}+{x}+{y}", "+repage", str(target)))
    if not target.is_file():
        raise CompareError(f"crop did not create: {target}")
    return target


def projection_features(im: ImageMagick, image: Path, threshold: float, *, limit: int = 8) -> dict[str, Any]:
    width, height = image_size(im, image)
    raw = run_bytes((*im.convert, str(image), "-colorspace", "Gray", "-negate", "-threshold", f"{threshold}%", "-depth", "8", "gray:-"))
    if len(raw) != width * height:
        raise CompareError("unexpected grayscale raster size")
    rows = [sum(raw[y * width:(y + 1) * width]) / (255 * width) for y in range(height)]
    columns = [sum(raw[x::width]) / (255 * height) for x in range(width)]
    total = sum_x = sum_y = 0.0
    for index, byte in enumerate(raw):
        if byte:
            value = byte / 255
            total += value; sum_x += (index % width) * value; sum_y += (index // width) * value
    centroid = None if total == 0 else {"x": sum_x / total, "y": sum_y / total}
    def bands(values: Sequence[float], cutoff: float) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        start: int | None = None
        for index, value in enumerate((*values, 0.0)):
            if value >= cutoff and start is None: start = index
            if value < cutoff and start is not None:
                segment = values[start:index]
                found.append({"start": start, "end": index, "coverage": max(segment)})
                start = None
        return sorted(found, key=lambda item: (item["coverage"], item["end"] - item["start"]), reverse=True)[:limit]
    return {"ink_bbox": bbox_measurement(thresholded_bbox(im, image, threshold, invert=True)), "centroid": centroid, "horizontal_bands": bands(rows, 0.35), "vertical_bands": bands(columns, 0.35), "long_horizontal_rules": bands(rows, 0.75), "long_vertical_rules": bands(columns, 0.75), "feature_limit": limit}


def text_page(pdf: Path, page: int, target: Path) -> str:
    run(("pdftotext", "-layout", "-f", str(page), "-l", str(page), str(pdf), str(target)))
    return target.read_text(encoding="utf-8", errors="replace")


def extract_text_pages(pdf: Path, count: int, target: Path) -> list[str]:
    run(("pdftotext", "-layout", str(pdf), str(target)))
    parts = target.read_text(encoding="utf-8", errors="replace").split("\f")
    if parts and not parts[-1]: parts.pop()
    if len(parts) != count: raise CompareError(f"text extractor returned {len(parts)} pages for a {count}-page PDF")
    return parts


def font_set(pdf: Path) -> list[str]:
    text = run(("pdffonts", str(pdf))).stdout.splitlines()
    if len(text) < 3:
        return []
    return sorted({line.split()[0] for line in text[2:] if line.split()})


def normalized_fonts(fonts: Sequence[str]) -> list[str]:
    return sorted({SUBSET_FONT_RE.sub("", font) for font in fonts})


def parse_layers(value: str | None) -> set[str]:
    values = set(DEFAULT_LAYERS if value is None else (item.strip() for item in value.split(",") if item.strip()))
    unknown = values - set(DEFAULT_LAYERS)
    if unknown or not values:
        raise InputError("--layers must be a nonempty subset of " + ",".join(DEFAULT_LAYERS))
    return values


def finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise InputError(f"{label} must be a finite number")
    return float(value)


def parse_box(values: Sequence[float], geometry: dict[str, Any], label: str) -> tuple[float, float, float, float]:
    if len(values) != 4:
        raise InputError(f"{label} requires X Y W H")
    x, y, width, height = (finite_number(value, label) for value in values)
    visual_width, visual_height = visual_size(geometry)
    if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > visual_width or y + height > visual_height:
        raise InputError(f"{label} is outside the visual page bounds")
    return x, y, width, height


def pixels_for_box(box: tuple[float, float, float, float], geometry: dict[str, Any], raster: tuple[int, int]) -> tuple[int, int, int, int]:
    x, y, width, height = box
    visual_width, visual_height = visual_size(geometry)
    left = round(x / visual_width * raster[0])
    top = round(y / visual_height * raster[1])
    right = round((x + width) / visual_width * raster[0])
    bottom = round((y + height) / visual_height * raster[1])
    result = left, top, right - left, bottom - top
    if result[2] <= 0 or result[3] <= 0 or left < 0 or top < 0 or right > raster[0] or bottom > raster[1]:
        raise InputError("requested box rounds outside the raster")
    return result


def metric_record(im: ImageMagick, reference: Path, candidate: Path, abs_diff: Path, *, threshold: float, ink_threshold: float, include_ink: bool = True, buffers: tuple[int, int, bytes, bytes | None, bytes | None] | None = None) -> dict[str, Any]:
    if buffers is None:
        width, height = image_size(im, reference)
        if image_size(im, candidate) != (width, height): raise CompareError("reference and candidate raster dimensions differ")
    else:
        width, height = buffers[:2]
    changed = ae_metric(im, reference, candidate)
    absolute, normalized = rmse_metric(im, reference, candidate)
    pixels = width * height
    if buffers is None:
        _, _, changed_mask = threshold_mask(im, abs_diff, threshold, invert=False)
        ref_mask = threshold_mask(im, reference, ink_threshold, invert=True)[2] if include_ink else None
        cand_mask = threshold_mask(im, candidate, ink_threshold, invert=True)[2] if include_ink else None
    else:
        buffer_width, buffer_height, changed_mask, ref_mask, cand_mask = buffers
        if (buffer_width, buffer_height) != (width, height): raise CompareError("metric buffer dimensions differ")
    whole = (0, 0, width, height)
    thresholded = sum(bool(value) for value in changed_mask)
    ratio = thresholded / pixels
    result = {
        "pixels": [width, height], "raw_changed_pixels": changed, "raw_changed_ratio": changed / pixels,
        "thresholded_changed_pixels": thresholded, "thresholded_changed_ratio": ratio,
        "rmse_absolute": absolute, "rmse_normalized": normalized,
        "diff_bbox": mask_measurement(changed_mask, width, whole),
    }
    if include_ink:
        if ref_mask is None or cand_mask is None: raise CompareError("ink metrics require ink buffers")
        result["ink_bbox_reference"] = mask_measurement(ref_mask, width, whole)
        result["ink_bbox_candidate"] = mask_measurement(cand_mask, width, whole)
    return result


def threshold_mask(im: ImageMagick, image: Path, threshold: float, *, invert: bool, size: tuple[int, int] | None = None) -> tuple[int, int, bytes]:
    width, height = size if size is not None else image_size(im, image)
    command = [*im.convert, str(image), "-colorspace", "Gray"]
    if invert: command.append("-negate")
    command.extend(("-threshold", f"{threshold}%", "-depth", "8", "gray:-"))
    raw = run_bytes(command)
    if len(raw) != width * height: raise CompareError("unexpected threshold raster size")
    return width, height, raw


def threshold_masks_batch(im: ImageMagick, specifications: Sequence[tuple[Path, float, bool]], size: tuple[int, int]) -> list[bytes]:
    width, height = size
    command: list[str] = [*im.convert]
    for image, threshold, invert in specifications:
        command.extend(("(", str(image), "-colorspace", "Gray"))
        if invert: command.append("-negate")
        command.extend(("-threshold", f"{threshold}%", ")"))
    command.extend(("-depth", "8", "gray:-"))
    raw = run_bytes(command); frame_size = width * height
    if len(raw) != frame_size * len(specifications): raise CompareError("unexpected batched threshold raster size")
    return [raw[index * frame_size:(index + 1) * frame_size] for index in range(len(specifications))]


def mask_measurement(raw: bytes, image_width: int, box: tuple[int, int, int, int]) -> dict[str, Any] | None:
    x, y, width, height = box
    count = sum_x = sum_y = 0
    left, right, top, bottom = width, -1, height, -1
    for row in range(height):
        base = (y + row) * image_width + x
        for column, value in enumerate(raw[base:base + width]):
            if value:
                count += 1; sum_x += column; sum_y += row
                left, right, top, bottom = min(left, column), max(right, column), min(top, row), max(bottom, row)
    if count == 0: return None
    return {"x": left, "y": top, "width": right - left + 1, "height": bottom - top + 1, "center_x": sum_x / count, "center_y": sum_y / count}


def local_rule_bands(
    raw: bytes, image_width: int, box: tuple[int, int, int, int], *, horizontal: bool,
) -> list[dict[str, Any]]:
    """Return dense local row/column bands as coarse rule/image structure."""
    x, y, width, height = box
    values = []
    if horizontal:
        for row in range(height):
            base = (y + row) * image_width + x
            segment = raw[base:base + width]
            values.append((width - segment.count(0)) / width)
    else:
        for column in range(width):
            start = y * image_width + x + column
            segment = raw[start:start + height * image_width:image_width]
            values.append((height - segment.count(0)) / height)
    bands, start = [], None
    for index, coverage in enumerate((*values, 0.0)):
        if coverage >= 0.5 and start is None:
            start = index
        if coverage < 0.5 and start is not None:
            bands.append({
                "start": start, "end": index,
                "maximum_coverage": max(values[start:index]),
            })
            start = None
    return bands


def tile_measurements(buffers: tuple[int, int, bytes | None, bytes | None, bytes | None], geometry: dict[str, Any], columns: int, rows: int, page: int) -> list[dict[str, Any]]:
    width, height, changed_mask, ref_mask, cand_mask = buffers
    if columns > width or rows > height: raise InputError("tile grid exceeds raster dimensions and would create zero-width tiles")
    result = []
    visual_width, visual_height = visual_size(geometry)
    for row in range(rows):
        for column in range(columns):
            left, right = round(column * width / columns), round((column + 1) * width / columns)
            top, bottom = round(row * height / rows), round((row + 1) * height / rows)
            tile = (left, top, right - left, bottom - top)
            changed = sum(bool(changed_mask[(top + dy) * width + left + dx]) for dy in range(tile[3]) for dx in range(tile[2])) if changed_mask is not None else None
            ratio = changed / (tile[2] * tile[3]) if changed is not None else None
            ref_ink = mask_measurement(ref_mask, width, tile) if ref_mask is not None else None
            cand_ink = mask_measurement(cand_mask, width, tile) if cand_mask is not None else None
            x_pt, y_pt = tile[0] / width * visual_width, tile[1] / height * visual_height
            w_pt, h_pt = tile[2] / width * visual_width, tile[3] / height * visual_height
            item: dict[str, Any] = {"id": f"p{page:03d}-r{row + 1:03d}-c{column + 1:03d}-tile", "page": page, "measurement_kind": "tile-observation", "row": row + 1, "column": column + 1, "box_pt": [x_pt, y_pt, w_pt, h_pt]}
            if changed is not None: item["pixel"] = {"thresholded_changed_ratio": ratio, "thresholded_changed_pixels": changed}
            if ref_mask is not None and cand_mask is not None:
                item["ink"] = {
                    "reference": ref_ink, "candidate": cand_ink,
                    "displacement": ink_displacement(ref_ink, cand_ink),
                    "structure": {
                        "reference": {
                            "horizontal_bands": local_rule_bands(ref_mask, width, tile, horizontal=True),
                            "vertical_bands": local_rule_bands(ref_mask, width, tile, horizontal=False),
                        },
                        "candidate": {
                            "horizontal_bands": local_rule_bands(cand_mask, width, tile, horizontal=True),
                            "vertical_bands": local_rule_bands(cand_mask, width, tile, horizontal=False),
                        },
                        "coverage_cutoff": 0.5,
                    },
                }
            result.append(item)
    return result


def thresholded_bbox_crop(im: ImageMagick, image: Path, box: tuple[int, int, int, int], threshold: float) -> str | None:
    x, y, width, height = box
    command = [*im.convert, str(image), "-crop", f"{width}x{height}+{x}+{y}", "+repage", "-colorspace", "Gray", "-negate", "-threshold", f"{threshold}%", "-format", "%[fx:mean]|%@", "info:"]
    text = run(command, accepted_codes=(0, 1)).stdout.strip()
    try:
        fraction, bbox = text.split("|", maxsplit=1)
        return bbox or None if float(fraction) > 0 else None
    except ValueError as error:
        raise CompareError(f"could not parse tile ink box: {text}") from error


def bbox_measurement(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    match = re.fullmatch(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", value)
    if not match:
        return {"raw": value}
    width, height, x, y = (float(match.group(index)) for index in range(1, 5))
    return {"x": x, "y": y, "width": width, "height": height, "center_x": x + width / 2, "center_y": y + height / 2}


def ink_displacement(reference: dict[str, Any] | None, candidate: dict[str, Any] | None) -> dict[str, float] | None:
    if reference is None and candidate is None: return None
    if reference is None or candidate is None: return {"presence_change": 1.0, "center_dx": 0.0, "center_dy": 0.0, "width_delta": 0.0, "height_delta": 0.0, "magnitude": 1_000_000.0}
    if "raw" in reference or "raw" in candidate: return None
    center = math.hypot(candidate["center_x"] - reference["center_x"], candidate["center_y"] - reference["center_y"])
    width_delta, height_delta = candidate["width"] - reference["width"], candidate["height"] - reference["height"]
    return {
        "presence_change": 0.0,
        "center_dx": candidate["center_x"] - reference["center_x"],
        "center_dy": candidate["center_y"] - reference["center_y"],
        "width_delta": width_delta,
        "height_delta": height_delta,
        "magnitude": max(center, abs(width_delta), abs(height_delta)),
    }


def source_record(path: Path) -> dict[str, str]:
    return {"path": str(path), "sha256": sha256(path)}


def scan(args: argparse.Namespace) -> int:
    layers = parse_layers(args.layers)
    render = bool(layers & {"ink", "pixels"})
    im = require_dependencies(content="content" in layers, fonts="fonts" in layers, render=render)
    reference, candidate, output = validate_pdf(args.reference), validate_pdf(args.candidate), prepare_output(args.output)
    ref_info, cand_info = inspect_pdf(reference), inspect_pdf(candidate)
    tools = {"pdfinfo": tool_version(("pdfinfo", "-v"))}
    if "content" in layers: tools["pdftotext"] = tool_version(("pdftotext", "-v"))
    if "fonts" in layers: tools["pdffonts"] = tool_version(("pdffonts", "-v"))
    if render:
        assert im is not None
        tools.update(pdftoppm=tool_version(("pdftoppm", "-v")), imagemagick=tool_version(im.version))
    index: dict[str, Any] = {"kind": "pdf-difference-scan", "comparability": {}, "inputs": {"reference": source_record(reference), "candidate": source_record(candidate)}, "settings": {"dpi": args.dpi, "layers": sorted(layers), "pixel_threshold_percent": args.pixel_threshold_percent, "ink_threshold_percent": args.ink_threshold_percent, "geometry_tolerance_pt": args.geometry_tolerance_pt, "tile_columns": args.tile_columns, "tile_rows": args.tile_rows, "top_findings_per_domain": args.top_hotspots}, "tools": tools, "render_origin": {"reference": ref_info["render_origin"], "candidate": cand_info["render_origin"]}, "page_count": {"reference": ref_info["pages"], "candidate": cand_info["pages"], "equal": ref_info["pages"] == cand_info["pages"]}, "fonts": {}, "content_full_diff": None, "findings": {"page_count": [], "fonts": [], "geometry": [], "content": [], "hotspots": []}, "finding_summary": {}, "pages": [], "differences_present": False, "measurement_note": "Measurements report evidence only; they do not classify causes."}
    index["coordinate_system"] = "top-left page points after page rotation"
    if "pixels" not in layers: index["settings"].pop("pixel_threshold_percent")
    if "ink" not in layers: index["settings"].pop("ink_threshold_percent")
    if "fonts" in layers:
        ref_fonts, cand_fonts = font_set(reference), font_set(candidate)
        index["fonts"] = {"reference_normalized": normalized_fonts(ref_fonts), "candidate_normalized": normalized_fonts(cand_fonts)}
        if index["fonts"]["reference_normalized"] != index["fonts"]["candidate_normalized"]:
            index["differences_present"] = True
            index["findings"]["fonts"].append({"id": "document-font-set", "measurement_kind": "font-set", "detail": "index.json"})
    if ref_info["pages"] != cand_info["pages"]:
        index["differences_present"] = True
        index["findings"]["page_count"].append({"id": "page-count", "measurement_kind": "page-count", "detail": "index.json"})
    full_diff: list[str] = []
    common = min(ref_info["pages"], cand_info["pages"])
    all_hotspots: list[dict[str, Any]] = []
    ref_text_pages = extract_text_pages(reference, ref_info["pages"], output / "reference-content.txt") if "content" in layers else []
    cand_text_pages = extract_text_pages(candidate, cand_info["pages"], output / "candidate-content.txt") if "content" in layers else []
    ref_rasters = render_pages(reference, common, args.dpi, output, "reference") if render else {}
    cand_rasters = render_pages(candidate, common, args.dpi, output, "candidate") if render else {}
    for page in range(1, common + 1):
        page_dir = output / "pages" / f"{page:03d}"
        page_dir.mkdir(parents=True, exist_ok=True)
        ref_geometry, cand_geometry = ref_info["page_geometry"][page - 1], cand_info["page_geometry"][page - 1]
        geometry_matches = geometry_equal(ref_geometry, cand_geometry, args.geometry_tolerance_pt)
        record: dict[str, Any] = {"page": page, "detail": str((page_dir / "scan.json").relative_to(output))}
        if "geometry" in layers: record.update(geometry_equal=geometry_matches, geometry={"reference": ref_geometry, "candidate": cand_geometry})
        if "geometry" in layers and not geometry_matches:
            index["differences_present"] = True
            index["findings"]["geometry"].append({"id": f"p{page:03d}-geometry", "page": page, "measurement_kind": "geometry", "detail": record["detail"]})
        if "content" in layers:
            ref_text, cand_text = ref_text_pages[page - 1], cand_text_pages[page - 1]
            (page_dir / "reference.txt").write_text(ref_text, encoding="utf-8")
            (page_dir / "candidate.txt").write_text(cand_text, encoding="utf-8")
            diff = list(difflib.unified_diff(ref_text.splitlines(keepends=True), cand_text.splitlines(keepends=True), fromfile=f"reference/page-{page}", tofile=f"candidate/page-{page}"))
            (page_dir / "content.diff").write_text("".join(diff), encoding="utf-8")
            full_diff.extend(diff)
            record["content"] = {"equal": ref_text == cand_text, "changed_lines": sum(1 for line in diff if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))), "diff": str((page_dir / "content.diff").relative_to(output))}
            if not record["content"]["equal"]:
                index["differences_present"] = True
                index["findings"]["content"].append({"id": f"p{page:03d}-content", "page": page, "measurement_kind": "content", "detail": record["detail"]})
        if "pixels" in layers or "ink" in layers:
            assert im is not None
            ref_png, cand_png = ref_rasters[page], cand_rasters[page]
            ref_size, cand_size = image_size(im, ref_png), image_size(im, cand_png)
            sizes_equal = ref_size == cand_size
            record["raster_dimensions_equal"] = sizes_equal
            if not sizes_equal:
                index["differences_present"] = True
                record["measurement_error"] = "raster_dimensions_mismatch"
            else:
                abs_path = page_dir / "abs.png"
                run((*im.convert, str(ref_png), str(cand_png), "-compose", "difference", "-composite", str(abs_path)))
                width, height = ref_size
                specifications: list[tuple[Path, float, bool]] = []
                if "pixels" in layers: specifications.append((abs_path, args.pixel_threshold_percent, False))
                if "ink" in layers: specifications.extend(((ref_png, args.ink_threshold_percent, True), (cand_png, args.ink_threshold_percent, True)))
                masks = iter(threshold_masks_batch(im, specifications, ref_size))
                changed_mask = next(masks) if "pixels" in layers else None
                ref_mask, cand_mask = (next(masks), next(masks)) if "ink" in layers else (None, None)
                buffers = (width, height, changed_mask, ref_mask, cand_mask)
                if "pixels" in layers:
                    assert changed_mask is not None
                    changed = sum(bool(value) for value in changed_mask); pixels = width * height
                    metrics = {"pixels": [width, height], "thresholded_changed_pixels": changed, "thresholded_changed_ratio": changed / pixels, "diff_bbox": mask_measurement(changed_mask, width, (0, 0, width, height))}
                    record["pixels"] = metrics
                    if changed: index["differences_present"] = True
                if "ink" in layers:
                    assert ref_mask is not None and cand_mask is not None
                    whole = (0, 0, width, height)
                    ref_ink, cand_ink = mask_measurement(ref_mask, width, whole), mask_measurement(cand_mask, width, whole)
                    record["ink"] = {"reference": ref_ink, "candidate": cand_ink, "displacement": ink_displacement(ref_ink, cand_ink), "changed_pixels": sum(a != b for a, b in zip(ref_mask, cand_mask))}
                    if ref_mask != cand_mask: index["differences_present"] = True
                tiles = tile_measurements(buffers, ref_geometry, args.tile_columns, args.tile_rows, page)
                record["tiles"] = tiles
                all_hotspots.extend(tiles)
        write_json(page_dir / "scan.json", record)
        rank_score = record.get("pixels", {}).get("thresholded_changed_ratio", (record.get("ink", {}).get("displacement") or {}).get("magnitude", 0.0))
        index["pages"].append({"page": page, "detail": record["detail"], "rank_score": rank_score, "geometry_equal": geometry_matches})
    for page in range(common + 1, max(ref_info["pages"], cand_info["pages"]) + 1):
        page_dir = output / "pages" / f"{page:03d}"; page_dir.mkdir(parents=True)
        reference_only = page <= ref_info["pages"]
        detail = str((page_dir / "scan.json").relative_to(output))
        record = {"page": page, "detail": detail, "page_presence": {"reference": reference_only, "candidate": not reference_only}, "findings": []}
        if "geometry" in layers:
            record.update(geometry_equal=False, geometry={"reference": ref_info["page_geometry"][page - 1] if reference_only else None, "candidate": cand_info["page_geometry"][page - 1] if not reference_only else None})
            index["findings"]["geometry"].append({"id": f"p{page:03d}-geometry", "page": page, "measurement_kind": "missing-page-geometry", "detail": detail})
            record["findings"].append({"id": f"p{page:03d}-geometry", "measurement_kind": "missing-page-geometry"})
        if "content" in layers:
            ref_text = ref_text_pages[page - 1] if reference_only else ""; cand_text = cand_text_pages[page - 1] if not reference_only else ""
            (page_dir / "reference.txt").write_text(ref_text, encoding="utf-8"); (page_dir / "candidate.txt").write_text(cand_text, encoding="utf-8")
            diff = list(difflib.unified_diff(ref_text.splitlines(keepends=True), cand_text.splitlines(keepends=True), fromfile=f"reference/page-{page}", tofile=f"candidate/page-{page}"))
            (page_dir / "content.diff").write_text("".join(diff), encoding="utf-8"); full_diff.extend(diff)
            record["content"] = {"equal": False, "changed_lines": sum(1 for line in diff if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))), "diff": str((page_dir / "content.diff").relative_to(output))}
            index["findings"]["content"].append({"id": f"p{page:03d}-content", "page": page, "measurement_kind": "missing-page-content", "detail": detail})
            record["findings"].append({"id": f"p{page:03d}-content", "measurement_kind": "missing-page-content"})
        write_json(page_dir / "scan.json", record)
        index["pages"].append({"page": page, "detail": detail, "rank_score": 0.0, "geometry_equal": False})
    if "content" in layers:
        (output / "content.diff").write_text("".join(full_diff), encoding="utf-8")
        index["content_full_diff"] = "content.diff"
    ratio_rank = sorted((item for item in all_hotspots if "pixel" in item and item["pixel"]["thresholded_changed_pixels"] > 0), key=lambda item: item["pixel"]["thresholded_changed_ratio"], reverse=True)[:args.top_hotspots]
    ink_rank = sorted((item for item in all_hotspots if "ink" in item and (item["ink"].get("displacement") or {}).get("magnitude", 0.0) > 0), key=lambda item: (item["ink"].get("displacement") or {}).get("magnitude", 0.0), reverse=True)[:args.top_hotspots]
    hotspot_union = {item["id"]: item for item in ratio_rank + ink_rank}
    index["findings"]["hotspots"].extend({**item, "detail": f"pages/{item['page']:03d}/scan.json"} for item in hotspot_union.values())
    for domain in ("geometry", "content"):
        index["findings"][domain] = index["findings"][domain][:args.top_hotspots]
    page_details = index.pop("pages")
    geometry_mismatch_count = sum(not item["geometry_equal"] for item in page_details)
    ranked_pages = sorted(page_details, key=lambda item: item["rank_score"], reverse=True)[:args.top_hotspots]
    index["page_ranking"] = [{key: value for key, value in item.items() if key != "geometry_equal" or "geometry" in layers} for item in ranked_pages]
    index["geometry"] = {
        "enabled": True,
        "equal_page_count": len(page_details) - sum(not item["geometry_equal"] for item in page_details),
        "mismatch_pages": [item["page"] for item in page_details if not item["geometry_equal"]][:args.top_hotspots],
        "mismatch_count": geometry_mismatch_count,
        "detail_directory": "pages",
    } if "geometry" in layers else {"enabled": False}
    page_records = [read_json(output / item["detail"], "page scan") for item in page_details]
    index["comparability"] = {
        "content": {"enabled": True, "equal_pages": sum(record.get("content", {}).get("equal", False) for record in page_records), "different_pages": sum(not record.get("content", {}).get("equal", True) for record in page_records), "full_diff": index["content_full_diff"]} if "content" in layers else {"enabled": False},
        "page_correspondence": index["page_count"],
        "fonts": {"enabled": "fonts" in layers, "equal": index["fonts"].get("reference_normalized") == index["fonts"].get("candidate_normalized") if "fonts" in layers else None},
        "geometry": {"enabled": True, "equal_pages": index["geometry"]["equal_page_count"], "mismatch_count": index["geometry"]["mismatch_count"]} if "geometry" in layers else {"enabled": False},
        "render_origin": index["render_origin"],
        "render": {"enabled": render, "dpi": args.dpi if render else None, "auto_registration": False, "rescaling": False},
    }
    index["finding_summary"] = {domain: {"reported": len(items), "limit": args.top_hotspots * 2 if domain == "hotspots" else args.top_hotspots} for domain, items in index["findings"].items()}
    write_json(output / "index.json", index)
    print(f"scan status=ok differences={str(index['differences_present']).lower()} pages={len(page_details)} findings={sum(len(items) for items in index['findings'].values())}")
    return 0


def resolve_scan_input(scan_dir: Path) -> tuple[dict[str, Any], Path, Path]:
    index = read_json(scan_dir / "index.json", "scan index")
    if not isinstance(index, dict) or index.get("kind") != "pdf-difference-scan":
        raise InputError("not a scan index")
    try:
        ref = validate_pdf(Path(index["inputs"]["reference"]["path"]))
        cand = validate_pdf(Path(index["inputs"]["candidate"]["path"]))
        if sha256(ref) != index["inputs"]["reference"]["sha256"] or sha256(cand) != index["inputs"]["candidate"]["sha256"]:
            raise InputError("scan input SHA-256 no longer matches")
    except (KeyError, TypeError) as error:
        raise InputError("scan index input record is invalid") from error
    return index, ref, cand


def detail(args: argparse.Namespace) -> int:
    index, reference, candidate = resolve_scan_input(args.scan_dir.expanduser().resolve())
    layers = parse_layers(args.layers if args.layers is not None else ",".join(index.get("settings", {}).get("layers", DEFAULT_LAYERS)))
    render = bool(layers & {"ink", "pixels"})
    im = require_dependencies(content="content" in layers, fonts="fonts" in layers, render=render)
    ref_info, cand_info = inspect_pdf(reference), inspect_pdf(candidate)
    output = prepare_output(args.output)
    finding = None
    if args.finding:
        if args.box is not None:
            raise InputError("--finding and --box describe competing targets")
        finding = next((item for items in index.get("findings", {}).values() for item in items if item.get("id") == args.finding), None)
        if finding is None or "page" not in finding:
            raise InputError("--finding must name a page-level hotspot in the scan index")
        page = finding["page"]
        box = tuple(finding["box_pt"]) if "box_pt" in finding else None
    else:
        page = args.page
        if page is None:
            raise InputError("provide --finding or --page")
        box = tuple(args.box) if args.box else None
    if not isinstance(page, int) or page <= 0 or page > min(ref_info["pages"], cand_info["pages"]):
        raise InputError("requested page is unavailable in both PDFs")
    ref_geometry, cand_geometry = ref_info["page_geometry"][page - 1], cand_info["page_geometry"][page - 1]
    if render and not geometry_equal(ref_geometry, cand_geometry, index["settings"]["geometry_tolerance_pt"]):
        raise InputError("detail requires matching page geometry")
    if box is None:
        width, height = visual_size(ref_geometry)
        box = (0.0, 0.0, width, height)
    box = parse_box(box, ref_geometry, "detail box")
    if args.context_pt:
        visual_width, visual_height = visual_size(ref_geometry)
        x, y, width, height = box
        left, top = max(0.0, x - args.context_pt), max(0.0, y - args.context_pt)
        right, bottom = min(visual_width, x + width + args.context_pt), min(visual_height, y + height + args.context_pt)
        box = (left, top, right - left, bottom - top)
    result: dict[str, Any] = {"kind": "pdf-difference-detail", "scan_dir": str(args.scan_dir.expanduser().resolve()), "finding": args.finding, "page": page, "box_pt": list(box), "context_pt": args.context_pt, "layers": sorted(layers)}
    result["coordinate_system"] = "top-left page points after page rotation"
    if "geometry" in layers:
        result["geometry"] = {"reference": ref_geometry, "candidate": cand_geometry, "equal": geometry_equal(ref_geometry, cand_geometry, index["settings"]["geometry_tolerance_pt"])}
    if "fonts" in layers:
        ref_fonts, cand_fonts = font_set(reference), font_set(candidate)
        result["fonts"] = {"reference_raw": ref_fonts, "candidate_raw": cand_fonts, "reference_normalized": normalized_fonts(ref_fonts), "candidate_normalized": normalized_fonts(cand_fonts)}
    if render:
        assert im is not None
        ref_png, cand_png = render_page(reference, page, args.dpi, output / "page-reference.png"), render_page(candidate, page, args.dpi, output / "page-candidate.png")
        if image_size(im, ref_png) != image_size(im, cand_png):
            raise CompareError("detail requires matching raster dimensions")
        pixel_box = pixels_for_box(box, ref_geometry, image_size(im, ref_png))
        ref_crop, cand_crop = crop(im, ref_png, output / "reference.png", pixel_box), crop(im, cand_png, output / "candidate.png", pixel_box)
        result.update(pixel_crop=list(pixel_box), render_source="rerendered at requested DPI after scan input SHA-256 revalidation")
        if "pixels" in layers:
            paths = create_visuals(im, ref_crop, cand_crop, output)
            result["artifacts"] = {key: str(value.name) for key, value in paths.items()}
            result["pixels"] = metric_record(im, ref_crop, cand_crop, paths["abs"], threshold=index["settings"]["pixel_threshold_percent"], ink_threshold=index["settings"].get("ink_threshold_percent", 3.0), include_ink=False)
        if "ink" in layers:
            result["ink"] = {"reference": projection_features(im, ref_crop, index["settings"]["ink_threshold_percent"]), "candidate": projection_features(im, cand_crop, index["settings"]["ink_threshold_percent"])}
    if "content" in layers:
        ref_text, cand_text = text_page(reference, page, output / "reference.txt"), text_page(candidate, page, output / "candidate.txt")
        (output / "content.diff").write_text("".join(difflib.unified_diff(ref_text.splitlines(keepends=True), cand_text.splitlines(keepends=True), fromfile="reference", tofile="candidate")), encoding="utf-8")
        result["content"] = {"equal": ref_text == cand_text, "diff": "content.diff"}
    write_json(output / "detail.json", result)
    print(f"detail status=ok page={page} finding={args.finding or '-'} layers={','.join(sorted(layers))}")
    return 0


def parse_budget(item: Any, label: str) -> dict[str, Any]:
    required = {"max_changed_ratio", "max_changed_pixels", "cause", "scope", "approval"}
    if not isinstance(item, dict) or set(item) != required:
        raise InputError(f"{label} must contain exactly: {', '.join(sorted(required))}")
    ratio, pixels = finite_number(item["max_changed_ratio"], f"{label}.max_changed_ratio"), finite_number(item["max_changed_pixels"], f"{label}.max_changed_pixels")
    if not 0 <= ratio <= 1 or pixels < 0 or not pixels.is_integer() or any(not isinstance(item[key], str) or not item[key] for key in ("cause", "scope", "approval")):
        raise InputError(f"{label} has invalid limits or provenance")
    return {**item, "max_changed_ratio": ratio, "max_changed_pixels": int(pixels)}


def parse_region(item: Any, label: str, *, approved: bool) -> dict[str, Any]:
    required = {"id", "page", "x_pt", "y_pt", "width_pt", "height_pt"}
    allowed = required | ({"budget"} if approved else set())
    if not isinstance(item, dict) or set(item) - allowed or not required <= set(item):
        raise InputError(f"{label} has unsupported or missing keys")
    if not isinstance(item["id"], str) or not REGION_ID_RE.fullmatch(item["id"]):
        raise InputError(f"{label}.id is unsafe")
    if not isinstance(item["page"], int) or isinstance(item["page"], bool) or item["page"] <= 0:
        raise InputError(f"{label}.page must be a positive integer")
    result = {"id": item["id"], "page": item["page"], "x_pt": finite_number(item["x_pt"], label), "y_pt": finite_number(item["y_pt"], label), "width_pt": finite_number(item["width_pt"], label), "height_pt": finite_number(item["height_pt"], label)}
    result["budget"] = parse_budget(item["budget"], f"{label}.budget") if "budget" in item else None
    return result


def parse_contract(path: Path) -> dict[str, Any]:
    contract = read_json(path, "gate contract")
    if not isinstance(contract, dict):
        raise InputError("gate contract must be an object")
    allowed = {"mode", "regions", "pixel_threshold_percent", "pixel_threshold_reason", "geometry_tolerance_pt", "geometry_tolerance_reason", "page_budgets"}
    if set(contract) - allowed or "mode" not in contract:
        raise InputError("gate contract has unsupported or missing keys")
    mode = contract["mode"]
    if mode not in ("zero", "approved-budget"):
        raise InputError("contract mode must be zero or approved-budget")
    if mode == "zero" and ("pixel_threshold_percent" in contract or "pixel_threshold_reason" in contract):
        raise InputError("zero mode uses raw pixel equality and does not accept a pixel threshold")
    threshold = 0.0 if mode == "zero" else finite_number(contract.get("pixel_threshold_percent", 3.0), "pixel_threshold_percent")
    tolerance = finite_number(contract.get("geometry_tolerance_pt", 0.1), "geometry_tolerance_pt")
    if not 0 <= threshold <= 100 or tolerance < 0:
        raise InputError("contract thresholds are out of range")
    if mode == "approved-budget" and threshold != 3.0 and (not isinstance(contract.get("pixel_threshold_reason"), str) or not contract.get("pixel_threshold_reason")):
        raise InputError("pixel threshold override requires pixel_threshold_reason")
    if tolerance != 0.1 and (not isinstance(contract.get("geometry_tolerance_reason"), str) or not contract.get("geometry_tolerance_reason")):
        raise InputError("geometry tolerance override requires geometry_tolerance_reason")
    raw_page_budgets = contract.get("page_budgets", {})
    if not isinstance(raw_page_budgets, dict): raise InputError("page_budgets must be an object")
    if mode == "zero" and raw_page_budgets: raise InputError("zero contract has zero budget for every target")
    page_budgets: dict[int, dict[str, Any]] = {}
    for key, value in raw_page_budgets.items():
        if not isinstance(key, str) or not key.isdigit() or int(key) <= 0: raise InputError("page budget keys must be positive page numbers")
        page_budgets[int(key)] = parse_budget(value, f"page_budgets.{key}")
    regions = [parse_region(item, f"regions[{index}]", approved=mode == "approved-budget") for index, item in enumerate(contract.get("regions", []))]
    if len({item["id"] for item in regions}) != len(regions):
        raise InputError("region ids must be unique")
    if mode == "approved-budget" and not page_budgets and not any(region["budget"] is not None for region in regions):
        raise InputError("approved-budget requires at least one explicit page or region budget")
    return {"mode": mode, "pixel_threshold_percent": threshold, "geometry_tolerance_pt": tolerance, "page_budgets": page_budgets, "regions": regions}


def gate_target(im: ImageMagick, ref_png: Path, cand_png: Path, geometry: dict[str, Any], page: int, box: tuple[float, float, float, float], work: Path, output: Path, threshold: float, budget: dict[str, Any] | None, label: str, *, exact: bool) -> dict[str, Any]:
    work.mkdir(parents=True, exist_ok=True)
    if image_size(im, ref_png) != image_size(im, cand_png):
        return {"id": label, "status": "fail", "error": "raster_dimensions_mismatch"}
    pixels = pixels_for_box(box, geometry, image_size(im, ref_png))
    raster_size = image_size(im, ref_png)
    if pixels == (0, 0, raster_size[0], raster_size[1]):
        ref_crop, cand_crop = ref_png, cand_png
    else:
        ref_crop, cand_crop = crop(im, ref_png, work / "reference.png", pixels), crop(im, cand_png, work / "candidate.png", pixels)
    ratio_limit = budget["max_changed_ratio"] if budget else 0.0
    pixel_limit = budget["max_changed_pixels"] if budget else 0
    if exact:
        raw_changed = ae_metric(im, ref_crop, cand_crop)
        observed = {"raw_changed_pixels": raw_changed}
        if raw_changed == 0:
            return {"id": label, "page": page, "status": "pass", "box_pt": list(box), "budget": {"max_changed_ratio": 0.0, "max_changed_pixels": 0}, "observed": observed, "artifacts": {}}
        status = "fail"
        abs_path = work / "abs.png"
        run((*im.convert, str(ref_crop), str(cand_crop), "-compose", "difference", "-composite", str(abs_path)))
    else:
        abs_path = work / "abs.png"
        run((*im.convert, str(ref_crop), str(cand_crop), "-compose", "difference", "-composite", str(abs_path)))
        width, height = image_size(im, abs_path)
        changed_mask = threshold_mask(im, abs_path, threshold, invert=False, size=(width, height))[2]
        changed = sum(bool(value) for value in changed_mask); ratio = changed / (width * height)
        observed = {"thresholded_changed_pixels": changed, "thresholded_changed_ratio": ratio}
        status = "pass" if ratio <= ratio_limit and changed <= pixel_limit else "fail"
    artifacts: dict[str, str] = {}
    metrics = None
    if status == "fail":
        metrics = metric_record(im, ref_crop, cand_crop, abs_path, threshold=threshold, ink_threshold=3.0, include_ink=False)
        output.mkdir(parents=True, exist_ok=True)
        public_reference, public_candidate, public_abs = output / "reference.png", output / "candidate.png", output / "abs.png"
        shutil.copy2(ref_crop, public_reference); shutil.copy2(cand_crop, public_candidate); shutil.copy2(abs_path, public_abs)
        paths = create_visuals(im, public_reference, public_candidate, output)
        artifacts = {key: value.name for key, value in paths.items()}
    result = {"id": label, "page": page, "status": status, "box_pt": list(box), "budget": budget or {"max_changed_ratio": 0.0, "max_changed_pixels": 0}, "observed": observed, "artifacts": artifacts}
    if metrics is not None: result["diagnostic_metrics"] = metrics
    return result


def gate(args: argparse.Namespace) -> int:
    contract = parse_contract(args.contract)
    im = require_dependencies(content=False, fonts=False, render=True)
    assert im is not None
    reference, candidate = validate_pdf(args.reference), validate_pdf(args.candidate)
    ref_info, cand_info = inspect_pdf(reference), inspect_pdf(candidate)
    common = min(ref_info["pages"], cand_info["pages"])
    # Region geometry is a contract property and is validated before artifacts are produced.
    for region in contract["regions"]:
        if region["page"] > common: raise InputError(f"region {region['id']} page is unavailable in both PDFs")
        parse_box((region["x_pt"], region["y_pt"], region["width_pt"], region["height_pt"]), ref_info["page_geometry"][region["page"] - 1], f"region {region['id']}")
    if any(page > common for page in contract["page_budgets"]): raise InputError("page_budgets names an unavailable page")
    output = prepare_output(args.output)
    failed = ref_info["pages"] != cand_info["pages"]
    failed_ids: list[str] = ["page-count"] if failed else []
    page_counts, region_counts = {"pass": 0, "fail": 0}, {"pass": 0, "fail": 0}
    temporary = tempfile.TemporaryDirectory(prefix="compare-pdfs-gate-")
    work_root = Path(temporary.name)
    ref_cache = render_pages(reference, common, 300, work_root, "reference")
    cand_cache = render_pages(candidate, common, 300, work_root, "candidate")
    cache = {page: (ref_cache[page], cand_cache[page]) for page in range(1, common + 1)}
    for page in range(1, common + 1):
        ref_geometry, cand_geometry = ref_info["page_geometry"][page - 1], cand_info["page_geometry"][page - 1]
        page_dir = output / "pages" / f"{page:03d}"
        page_dir.mkdir(parents=True, exist_ok=True)
        if not geometry_equal(ref_geometry, cand_geometry, contract["geometry_tolerance_pt"]):
            record = {"id": f"page-{page}", "page": page, "status": "fail", "error": "geometry_mismatch"}
        else:
            width, height = visual_size(ref_geometry)
            ref_png, cand_png = cache[page]
            record = gate_target(im, ref_png, cand_png, ref_geometry, page, (0.0, 0.0, width, height), work_root / "pages" / f"{page:03d}", page_dir, contract["pixel_threshold_percent"], contract["page_budgets"].get(page), f"page-{page}", exact=contract["mode"] == "zero")
        write_json(page_dir / "gate.json", record)
        page_counts[record["status"]] += 1
        if record["status"] != "pass": failed_ids.append(record["id"])
        failed |= record["status"] != "pass"
    for region in contract["regions"]:
        region_dir = output / "regions" / region["id"]
        geometry = ref_info["page_geometry"][region["page"] - 1]
        candidate_geometry = cand_info["page_geometry"][region["page"] - 1]
        if not geometry_equal(geometry, candidate_geometry, contract["geometry_tolerance_pt"]):
            record = {"id": region["id"], "page": region["page"], "status": "fail", "error": "geometry_mismatch"}
        else:
            box = parse_box((region["x_pt"], region["y_pt"], region["width_pt"], region["height_pt"]), geometry, f"region {region['id']}")
            ref_png, cand_png = cache[region["page"]]
            record = gate_target(im, ref_png, cand_png, geometry, region["page"], box, work_root / "regions" / region["id"], region_dir, contract["pixel_threshold_percent"], region["budget"], region["id"], exact=contract["mode"] == "zero")
        region_dir.mkdir(parents=True, exist_ok=True)
        write_json(region_dir / "gate.json", record)
        region_counts[record["status"]] += 1
        if record["status"] != "pass": failed_ids.append(record["id"])
        failed |= record["status"] != "pass"
    root = {"kind": "pdf-difference-gate", "status": "fail" if failed else "pass", "mode": contract["mode"], "mode_purpose": "approved Typst baseline regression" if contract["mode"] == "zero" else "target-specific current evidence budgets", "inputs": {"reference": source_record(reference), "candidate": source_record(candidate), "contract": source_record(args.contract.expanduser().resolve())}, "settings": {"dpi": 300, "pixel_threshold_percent": contract["pixel_threshold_percent"], "geometry_tolerance_pt": contract["geometry_tolerance_pt"]}, "tools": {"pdfinfo": tool_version(("pdfinfo", "-v")), "pdftoppm": tool_version(("pdftoppm", "-v")), "imagemagick": tool_version(im.version)}, "page_count": {"reference": ref_info["pages"], "candidate": cand_info["pages"]}, "target_counts": {"pages": page_counts, "regions": region_counts}, "failed_id_count": len(failed_ids), "failed_ids": failed_ids[:100], "failed_ids_truncated": len(failed_ids) > 100, "details": {"pages": "pages/<page>/gate.json", "regions": "regions/<id>/gate.json"}, "render_cache_pages": len(cache)}
    root["coordinate_system"] = "top-left page points after page rotation"
    temporary.cleanup()
    write_json(output / "gate.json", root)
    print(f"gate status={root['status']} pages={sum(page_counts.values())} regions={sum(region_counts.values())} failed={len(failed_ids)}")
    return EXIT_DIFFERENT if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Measure PDF differences without registration or rescaling.")
    sub = parser.add_subparsers(dest="command", required=True)
    scan_parser = sub.add_parser("scan")
    scan_parser.add_argument("reference", type=Path); scan_parser.add_argument("candidate", type=Path); scan_parser.add_argument("output", type=Path)
    scan_parser.add_argument("--layers"); scan_parser.add_argument("--dpi", type=int, default=150); scan_parser.add_argument("--pixel-threshold-percent", type=float, default=3.0); scan_parser.add_argument("--ink-threshold-percent", type=float, default=3.0); scan_parser.add_argument("--geometry-tolerance-pt", type=float, default=0.1); scan_parser.add_argument("--tile-columns", type=int, default=4); scan_parser.add_argument("--tile-rows", type=int, default=12); scan_parser.add_argument("--top-hotspots", type=int, default=12); scan_parser.set_defaults(handler=scan)
    detail_parser = sub.add_parser("detail")
    detail_parser.add_argument("scan_dir", type=Path); detail_parser.add_argument("output", type=Path); group = detail_parser.add_mutually_exclusive_group(required=True); group.add_argument("--finding"); group.add_argument("--page", type=int); detail_parser.add_argument("--box", nargs=4, type=float); detail_parser.add_argument("--context-pt", type=float, default=0.0); detail_parser.add_argument("--layers"); detail_parser.add_argument("--dpi", type=int, default=300); detail_parser.set_defaults(handler=detail)
    gate_parser = sub.add_parser("gate")
    gate_parser.add_argument("reference", type=Path); gate_parser.add_argument("candidate", type=Path); gate_parser.add_argument("contract", type=Path); gate_parser.add_argument("output", type=Path); gate_parser.set_defaults(handler=gate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    for name in ("dpi", "tile_columns", "tile_rows", "top_hotspots"):
        if hasattr(args, name) and getattr(args, name) <= 0:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    for name in ("pixel_threshold_percent", "ink_threshold_percent"):
        if hasattr(args, name) and (not math.isfinite(getattr(args, name)) or not 0 <= getattr(args, name) <= 100):
            parser.error(f"--{name.replace('_', '-')} must be between 0 and 100")
    if hasattr(args, "geometry_tolerance_pt") and (not math.isfinite(args.geometry_tolerance_pt) or args.geometry_tolerance_pt < 0):
        parser.error("--geometry-tolerance-pt must be a nonnegative finite number")
    if hasattr(args, "context_pt") and (not math.isfinite(args.context_pt) or args.context_pt < 0):
        parser.error("--context-pt must be a nonnegative finite number")
    try:
        return args.handler(args)
    except CompareError as error:
        print(f"error: {error}", file=sys.stderr)
        return error.exit_code
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_OUTPUT


if __name__ == "__main__":
    raise SystemExit(main())
