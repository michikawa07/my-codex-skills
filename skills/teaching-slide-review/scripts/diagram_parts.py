"""Read native diagram review candidates from selected PowerPoint thumbnail positions.

Object keys contain the supplied deck alias, 1-based page and native group/shape IDs.
local_emu is [x, y, width, height] in the recorded parent frame. bbox_emu is
[left, top, right, bottom] on the slide. Sizes are in points (12,700 EMU per pt).
Only objects used by a review unit are exported. No order, grouping or size
comparison here establishes that objects serve the same instructional purpose.
"""

from collections import Counter, defaultdict
from math import cos, dist, isfinite, radians, sin
from pathlib import Path
import posixpath
import re
from runpy import run_path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


slide_parts = run_path(str(Path(__file__).resolve().parents[2] / "slide-design" /
                           "scripts" / "pptx_grouping.py"))["slide_parts"]
PT = 12700
KINDS = {"sp", "cxnSp", "grpSp", "pic", "graphicFrame", "contentPart"}


def tag(node):
    return node.tag.rsplit("}", 1)[-1]


def number(value):
    try:
        result = float(value)
        return result if isfinite(result) else None
    except (ValueError, TypeError):
        return None


def rect(xfrm, child=False):
    if xfrm is None:
        return None
    pos = xfrm.find("{*}chOff" if child else "{*}off")
    size = xfrm.find("{*}chExt" if child else "{*}ext")
    if pos is None or size is None:
        return None
    values = [number(e.get(k)) for e, k in ((pos, "x"), (pos, "y"), (size, "cx"), (size, "cy"))]
    return values if None not in values and min(values[2:]) >= 0 else None


def projection(xfrm, xywh, outer):
    """Map unit-square shape coordinates through flips, rotation and enclosing groups."""
    angle = number(xfrm.get("rot", "0")) if xfrm is not None else None
    if xywh is None or angle is None:
        return None
    x, y, w, h = xywh
    angle = radians(angle / 60000)
    c, s = cos(angle), sin(angle)
    sx = -w if xfrm.get("flipH") in ("1", "true") else w
    sy = -h if xfrm.get("flipV") in ("1", "true") else h

    def project(u, v):
        dx, dy = (u - .5) * sx, (v - .5) * sy
        return outer(x + w / 2 + c * dx - s * dy, y + h / 2 + s * dx + c * dy)

    return project


def paint(prop, ref):
    for elem in [] if prop is None else prop:
        kind = tag(elem)
        if not kind.endswith("Fill"):
            continue
        if kind == "noFill":
            return "none"
        color = next(iter(elem), None)
        if kind == "solidFill" and color is not None:
            alpha = color.find("{*}alpha")
            if alpha is not None and alpha.get("val") == "0":
                return "none"
            return f"{tag(color)} {color.get('val', '')}".strip()
        return kind
    if ref is not None:
        return "none" if ref.get("idx") == "0" else "theme style " + ref.get("idx", "?")
    return "unspecified"


def point_segment(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    squared = dx * dx + dy * dy
    if not squared:
        return dist(p, a)
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / squared))
    return dist(p, (a[0] + t * dx, a[1] + t * dy))


def stroke_paths(preset, custom, xywh):
    """Return (description, normalized polyline or None, probe, sampled curve) per open subpath."""
    if custom is None:
        name = preset.get("prst", "") if preset is not None else ""
        if name in ("line", "straightConnector1", "lineInv"):
            pts = [(0, 1), (1, 0)] if name == "lineInv" else [(0, 0), (1, 1)]
            return [(name, pts, False, False)]
        match = re.fullmatch(r"(bent|curved)Connector([2-5])", name)
        if not match:
            return []
        count = int(match[2])
        if match[1] == "curved":
            return [(name + " (endpoints only)", [(0, 0), (1, 1)], True, True)]
        adj = {g.get("name"): g.get("fmla", "") for g in preset.findall("{*}avLst/{*}gd")}
        values = []
        for i in range(1, count - 1):
            formula = adj.get(f"adj{i}", "val 50000").split()
            value = number(formula[1]) if len(formula) == 2 and formula[0] == "val" else None
            if value is None:
                return [(name + " (unresolved adjustment)", None, True, False)]
            values.append(value / 100000)
        if count == 2:
            pts = [(1, 0)]
        elif count == 3:
            pts = [(values[0], 0), (values[0], 1)]
        elif count == 4:
            x, y = values
            pts = [(x, 0), (x, y), (1, y)]
        else:
            x, y, xx = values
            pts = [(x, 0), (x, y), (xx, y), (xx, 1)]
        return [(f"{name} ({count - 1} nominal bends)", [(0, 0), *pts, (1, 1)], True, False)]

    result = []
    for path in custom.findall("{*}pathLst/{*}path"):
        if path.get("stroke") in ("0", "false"):
            continue
        w = number(path.get("w", xywh[2] if xywh else None))
        h = number(path.get("h", xywh[3] if xywh else None))
        subpaths = []
        for cmd in path:
            if tag(cmd) == "moveTo" or not subpaths:
                subpaths.append([])
            subpaths[-1].append(cmd)
        for commands in subpaths:
            ops = [tag(cmd) for cmd in commands]
            if "close" in ops or len(ops) < 2:
                continue
            curved = any(op in ("quadBezTo", "cubicBezTo", "arcTo") for op in ops)
            points = []
            for cmd in commands:
                op = tag(cmd)
                coords = [(number(p.get("x")), number(p.get("y"))) for p in cmd.findall("{*}pt")]
                arity = {"moveTo": 1, "lnTo": 1, "quadBezTo": 2, "cubicBezTo": 3}.get(op)
                if not w or not h or arity != len(coords) or any(None in pt for pt in coords):
                    points = None
                    break
                controls = [(x / w, y / h) for x, y in coords]
                if arity == 1:
                    points.extend(controls)
                elif points:
                    start = points[-1]
                    for step in range(1, 17):
                        t = step / 16
                        level = [start, *controls]
                        while len(level) > 1:
                            level = [((1-t)*a[0]+t*b[0], (1-t)*a[1]+t*b[1]) for a, b in zip(level, level[1:])]
                        points.append(level[0])
                else:
                    points = None
                    break
            result.append(("open custom path " + " / ".join(ops), points, curved or len(ops) > 2, curved))
    return result


def title_band(archive, part, slide, slide_height):
    """Use an actual top title placeholder to recognize compact groups in its vertical band."""
    def bottom(doc):
        for shape in doc.findall("./{*}cSld/{*}spTree/{*}sp"):
            ph = shape.find("./{*}nvSpPr/{*}nvPr/{*}ph")
            box = rect(shape.find("./{*}spPr/{*}xfrm"))
            if ph is not None and ph.get("type") in ("title", "ctrTitle") and box:
                edge = box[1] + box[3]
                if 0 < edge <= slide_height / 3:
                    return edge
        return 0
    edge = bottom(slide)
    if edge:
        return edge
    directory, filename = posixpath.split(part)
    try:
        rels = ET.fromstring(archive.read(posixpath.join(directory, "_rels", filename + ".rels")))
        layout = next((r.get("Target") for r in rels if r.get("Type", "").endswith("/slideLayout")
                       and r.get("TargetMode") != "External"), None)
        if layout:
            return bottom(ET.fromstring(archive.read(posixpath.normpath(posixpath.join(directory, layout)).lstrip("/"))))
    except (KeyError, ET.ParseError):
        pass
    return 0


def native_shapes(tree, page, title_bottom, page_width):
    shapes, limits = {}, Counter()

    def visit(parent, frame, outer, space, in_header=False):
        for i, elem in enumerate(parent, 1):
            kind = tag(elem)
            if kind not in KINDS:
                if kind == "AlternateContent":
                    limits["unsupported alternate-content branches"] += 1
                continue
            info = elem.find("./{*}*/{*}cNvPr")
            if info is not None and info.get("hidden") in ("1", "true"):
                continue
            native_id = info.get("id") if info is not None else None
            obj = f"{frame}/{native_id or 'slot' + str(i)}"
            if obj in shapes:
                obj += f"~slot{i}"
            name = info.get("name", "") if info is not None else ""
            ph = elem.find("./{*}*/{*}nvPr/{*}ph")
            if ph is not None:
                continue
            prop = elem.find("{*}grpSpPr" if kind == "grpSp" else "{*}spPr")
            xfrm = prop.find("{*}xfrm") if prop is not None else elem.find("{*}xfrm")
            xywh = rect(xfrm)
            project = projection(xfrm, xywh, outer)
            corners = [project(u, v) for u, v in ((0, 0), (1, 0), (1, 1), (0, 1))] if project else []
            box, sizes, area = None, None, None
            if corners:
                xx, yy = zip(*corners)
                box = [min(xx), min(yy), max(xx), max(yy)]
                a, b, _, d = corners
                sizes = [round(dist(a, b) / PT, 2), round(dist(a, d) / PT, 2)]
                area = abs((b[0]-a[0])*(d[1]-a[1]) - (b[1]-a[1])*(d[0]-a[0]))
            else:
                limits["objects without a usable numeric transform"] += 1
            preset = prop.find("{*}prstGeom") if prop is not None else None
            custom = prop.find("{*}custGeom") if prop is not None else None
            geom = preset.get("prst", "?") if preset is not None else ("custom" if custom is not None else kind)
            line = prop.find("{*}ln") if prop is not None else None
            fill = paint(prop, elem.find("./{*}style/{*}fillRef"))
            ink = paint(line, elem.find("./{*}style/{*}lnRef"))
            paras = ["".join(n.text or "" if tag(n) == "t" else "\n" for n in p.iter() if tag(n) in ("t", "br"))
                     for p in elem.findall("./{*}txBody/{*}p")]
            text = "\n".join(paras).strip()
            paths = stroke_paths(preset, custom, xywh) if ink != "none" else []
            open_geom = bool(stroke_paths(preset, None, xywh)) if custom is None else bool(paths)
            closed_custom = custom is not None and custom.find("./{*}pathLst/{*}path/{*}close") is not None
            surface = (kind == "sp" and (not open_geom or closed_custom) and geom != "sp"
                       and (fill not in ("none", "unspecified") or ink not in ("none", "unspecified")))
            strokes = []
            for desc, points, probe, curved in paths:
                projected = [project(*pt) for pt in points] if project and points else []
                endpoints_only = "(endpoints only)" in desc
                deviation = (max(point_segment(p, projected[0], projected[-1]) for p in projected)
                             if len(projected) > 1 and not endpoints_only else None)
                if deviation is not None and deviation <= 1:  # allow EMU rounding in degenerate paths
                    probe = False
                if endpoints_only and xywh and min(xywh[2:]) == 0:
                    probe = False
                if probe and (not projected or endpoints_only):
                    limits["open paths with unresolved interior geometry"] += 1
                strokes.append((desc, projected, probe, curved, endpoints_only, deviation))
            attached = [(tag(c), c.get("id"), c.get("idx")) for c in elem.findall("./{*}*/{*}cNvCxnSpPr/*")
                        if tag(c) in ("stCxn", "endCxn")]
            data = dict(name=name, text=text, label=text or name or geom, geometry=geom, fill=fill, line=ink,
                        frame=frame, local_emu=[round(v) for v in xywh] if xywh else None,
                        bbox_emu=[round(v) for v in box] if box and space == page else None,
                        size_pt=sizes, comparison_frame=space, _kind=kind, _id=native_id, _box=box,
                        _area=area, _surface=surface, _paths=strokes, _attach=attached, _header=in_header)
            if line is not None:
                ends = {tag(end): end.get("type") for end in line if tag(end) in ("headEnd", "tailEnd")}
                if ends:
                    data["arrowheads"] = ends
            shapes[obj] = data
            if kind == "grpSp":
                decoration = (in_header or bool(box and space == page and box[3] <= title_bottom
                                                and box[2] - box[0] <= page_width / 2))
                data["_header"] = decoration
                if decoration and not in_header:
                    limits["compact groups in the title band omitted from peer comparisons"] += 1
                child = rect(xfrm, child=True)
                if project and child and min(child[2:]) > 0:
                    cx, cy, cw, ch = child
                    visit(elem, obj, lambda x, y: project((x-cx)/cw, (y-cy)/ch), space, decoration)
                else:
                    limits["groups with an unresolved child coordinate frame"] += 1
                    visit(elem, obj, lambda x, y: (x, y), obj, decoration)
            elif kind in ("pic", "graphicFrame", "contentPart"):
                limits["pictures, graphic frames or external content with uninspected interiors"] += 1
            elif kind == "cxnSp" and not strokes and ink != "none":
                limits["connectors without recognized path geometry"] += 1
    visit(tree, page, lambda x, y: (x, y), page)
    return shapes, limits


def inside(p, b):
    return b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]


def cuts(a, b, box, margin=0):
    """Segment intersects an axis-aligned box; positive margin expands it."""
    lo, hi = 0., 1.
    for i in range(2):
        v = b[i] - a[i]
        low, high = box[i] - margin, box[i+2] + margin
        if low > high:
            return False
        if v:
            u, w = sorted(((low-a[i])/v, (high-a[i])/v))
            lo, hi = max(lo, u), min(hi, w)
        elif not low <= a[i] <= high:
            return False
    return lo <= hi


def edge_distance(p, obj):
    if obj["_paths"]:
        segments = [(a, b) for _, pts, _, _, ends_only, _ in obj["_paths"] if not ends_only
                    for a, b in zip(pts, pts[1:])]
        return min((point_segment(p, a, b) for a, b in segments), default=float("inf"))
    l, t, r, b = obj["_box"]
    return min(point_segment(p, a, z) for a, z in [((l,t),(r,t)), ((r,t),(r,b)), ((r,b),(l,b)), ((l,b),(l,t))])


def route_units(shapes, tolerance):
    by_id = defaultdict(list)
    for key, obj in shapes.items():
        by_id[obj["_id"]].append(key)
    for key, obj in shapes.items():
        for i, (desc, pts, probe, curved, ends_only, deviation) in enumerate(obj["_paths"], 1):
            if not probe:
                continue
            evidence = [key]
            facts = [desc]
            links = []
            for side, native, site in obj["_attach"]:
                matches = by_id.get(native, [])
                target = matches[0] if len(matches) == 1 else f"unresolved native ID {native}"
                if len(matches) == 1:
                    evidence.append(target)
                links.append(f"{side}={target} (site {site})")
            facts.append("Stored endpoint records: " + (", ".join(links) or "none"))
            if len(pts) > 1:
                start, end = pts[0], pts[-1]
                points = [p for j, p in enumerate(pts) if j == 0 or dist(p, pts[j-1]) > 1]
                if deviation is not None:
                    if not curved:
                        turns = sum(point_segment(b, a, c) > 1 for a, b, c in zip(points, points[1:], points[2:]))
                        facts.append(f"{turns} direction change(s) from the stored numeric path.")
                    facts.append(f"Maximum {'sampled ' if curved else ''}offset from the endpoint chord: {deviation/PT:.1f} pt.")
                pool = {k: o for k, o in shapes.items() if k != key and not o["_header"] and o["_box"]
                        and o["comparison_frame"] == obj["comparison_frame"] and (o["_surface"] or o["text"] or o["_paths"])}
                for side, tip in (("start", start), ("end", end)):
                    nearby = sorted((edge_distance(tip, o), k) for k, o in pool.items())
                    hits = [(d, k) for d, k in nearby[:3] if d <= tolerance]
                    if hits:
                        facts.append(f"Near {side} by border/stroke distance: " + ", ".join(f"{k} ({d/PT:.1f} pt)" for d,k in hits))
                        evidence.extend(k for _, k in hits)
                crossed = [k for k, o in pool.items() if not o["_paths"] and not inside(start, o["_box"])
                           and not inside(end, o["_box"]) and cuts(start, end, o["_box"], -1)]
                facts.append("Other box interiors intersecting the direct endpoint chord: " + (", ".join(crossed) or "none found"))
                evidence.extend(crossed)
                if not ends_only:
                    labels = [k for k, o in pool.items() if o["text"] and not o["_surface"] and
                              any(cuts(a, b, o["_box"], tolerance) for a,b in zip(pts, pts[1:]))]
                    if labels:
                        facts.append(f"Text boxes within {tolerance/PT:.1f} pt of the path bounds test: " + ", ".join(labels))
                        evidence.extend(labels)
            else:
                facts.append("No resolved path coordinates. Inspect the rendering.")
            suffix = f"/path{i}" if len(obj["_paths"]) > 1 else ""
            yield dict(id=f"route/{key}{suffix}", kind="route", members=[key],
                       evidence=list(dict.fromkeys(evidence)), facts=facts)


def peer_units(shapes, page):
    faces = {k: o for k, o in shapes.items() if o["_surface"] and not o["_header"]}
    owners = {}
    for key, obj in faces.items():
        b = obj["_box"]
        parents = [(outer["_area"], k) for k, outer in faces.items()
                   if b and outer["_box"] and obj["comparison_frame"] == outer["comparison_frame"]
                   and outer["_area"] > obj["_area"] and inside(b[:2], outer["_box"]) and inside(b[2:], outer["_box"])]
        owners[key] = min(parents)[1] if parents else obj["frame"]
    containers = set(owners.values())
    pools = defaultdict(list)
    for key, owner in owners.items():
        if owner == page and key not in containers:
            continue  # unrelated loose objects on a slide do not form a cohort
        geom = faces[key]["geometry"]
        family = "rectangles" if re.fullmatch(r"(?:rect|(?:round|snip)\w*Rect)", geom) else geom
        pools[owner, family].append(key)
    for (owner, family), members in pools.items():
        if len(members) < 2:
            continue
        owner_type = "top-level enclosing surfaces" if owner == page else (
            "same smallest enclosing bounding box" if owner in faces else "same native group")
        facts = [f"{owner_type}: {owner}. Geometry family: {family}."]
        for key in members:
            obj = faces[key]
            if obj["size_pt"]:
                w, h = obj["size_pt"]
                facts.append(f"{key}: {w:g} × {h:g} pt; {obj['fill']}.")
        known = [faces[k] for k in members if faces[k]["_area"]]
        if len(known) == len(members) and len({o["comparison_frame"] for o in known}) == 1:
            areas = [o["_area"] for o in known]
            facts.append(f"Largest/smallest transformed rectangular area: {max(areas)/min(areas):.2f}×.")
        evidence = [*members, owner] if owner in shapes else members[:]
        yield dict(id=f"peers/{owner}/{family}", kind="peers", members=members, evidence=evidence, facts=facts)


def inspect_deck(path: Path, pages: list[int], alias: str) -> dict:
    """Inspect only requested 1-based thumbnail positions and their title layout bounds."""
    objects, units = {}, []
    limits = ["Only native slide objects are indexed. Theme appearance, master artwork and bitmap interiors require the rendering.",
              "Bounds and segment intersections are geometric hints. Stored endpoint records are reported separately from proximity.",
              "Bezier paths are sampled. Preset curved interiors, symbolic guides and arcs can require visual tracing.",
              "Sizes use each object's comparison frame. A group without a usable transform retains its own coordinate frame."]
    with ZipFile(path) as archive:
        parts = list(slide_parts(archive))
        requested = set(pages)
        if any(not isinstance(p, int) or p < 1 or p > len(parts) for p in requested):
            raise ValueError(f"page outside presentation positions 1..{len(parts)}")
        size = ET.fromstring(archive.read("ppt/presentation.xml")).find("{*}sldSz")
        width = number(size.get("cx")) if size is not None else None
        height = number(size.get("cy")) if size is not None else None
        for p in sorted(requested):
            part, page = parts[p-1], f"{alias}/p{p}"
            slide = ET.fromstring(archive.read(part))
            tree = slide.find("./{*}cSld/{*}spTree")
            if tree is None:
                limits.append(f"{page}: no native shape tree.")
                continue
            shapes, counts = native_shapes(tree, page, title_band(archive, part, slide, height or 0), width or 0)
            found = [*route_units(shapes, (height or 7200000) * .025), *peer_units(shapes, page)]
            for key in dict.fromkeys(k for u in found for k in u["evidence"]):
                objects[key] = {field: value for field, value in shapes[key].items() if not field.startswith("_")}
            units.extend(found)
            limits.extend(f"{page}: {n} {issue}." for issue, n in counts.items())
    return dict(objects=objects, units=units, limits=limits)
