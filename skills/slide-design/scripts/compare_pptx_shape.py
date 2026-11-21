#!/usr/bin/env python3
"""Compare the stored drawing properties of one PowerPoint shape or connector."""

import argparse
import difflib
import posixpath
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile


def local(tag):
    return tag.rsplit("}", 1)[-1]


def slide_tree(filename, page):
    with ZipFile(filename) as pptx:
        presentation = ET.fromstring(pptx.read("ppt/presentation.xml"))
        slides = presentation.findall("{*}sldIdLst/{*}sldId")
        if not 1 <= page <= len(slides):
            raise ValueError(f"{filename}: slide {page} is outside 1..{len(slides)}")
        slide = slides[page - 1]
        rel_id = next((v for k, v in slide.attrib.items() if k.endswith("}id")), None)
        rels = ET.fromstring(pptx.read("ppt/_rels/presentation.xml.rels"))
        targets = {r.get("Id"): r.attrib["Target"] for r in rels if r.get("Type", "").endswith("/slide")}
        part = posixpath.normpath(posixpath.join("ppt", targets[rel_id])).lstrip("/")
        tree = ET.fromstring(pptx.read(part)).find("{*}cSld/{*}spTree")
        if tree is None:
            raise ValueError(f"{filename}: slide {page} has no shape tree")
        return slide.attrib["id"], tree


def shapes(group, transforms=()):
    for element in group:
        identity = element.find("*/{*}cNvPr")
        if identity is not None:
            yield identity, element, transforms
        if local(element.tag) == "grpSp":
            transform = element.find("{*}grpSpPr/{*}xfrm")
            yield from shapes(element, (*transforms, transform))


def select(tree, key, value, location):
    matches = [(info, shape, parents) for info, shape, parents in shapes(tree) if info.get(key) == value]
    if len(matches) > 1:
        ids = ", ".join(info.attrib["id"] for info, _, _ in matches)
        raise ValueError(f"{location}: ambiguous {key}={value!r} (shape IDs: {ids})")
    if matches:
        _, shape, transforms = matches[0]
        return shape, transforms
    return None


def property_lines(node, parent):
    path = f"{parent}/{local(node.tag)}"
    attributes = [f"{local(k)}={v!r}" for k, v in sorted(node.attrib.items())]
    yield " ".join([path, *attributes])
    for child in node:
        if local(child.tag) != "extLst":
            yield from property_lines(child, path)


def drawing_properties(shape, transforms):
    yield f"object {local(shape.tag)}"
    for depth, transform in enumerate(transforms, 1):
        if transform is not None:
            yield from property_lines(transform, f"group[{depth}]")
    for prop in shape.findall("{*}spPr/*"):
        if local(prop.tag) in {"xfrm", "prstGeom", "custGeom", "ln", "noFill", "solidFill", "gradFill", "pattFill", "blipFill", "grpFill"}:
            yield from property_lines(prop, "shape")
    for ref in shape.findall("{*}style/*"):
        if local(ref.tag) in {"lnRef", "fillRef"}:
            yield from property_lines(ref, "style")
    for endpoint in shape.findall("{*}nvCxnSpPr/{*}cNvCxnSpPr/*"):
        if local(endpoint.tag) in {"stCxn", "endCxn"}:
            yield from property_lines(endpoint, "connection")


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Compares stored transforms (including parent groups), geometry, fill, line, "
        "line/fill style references and connector endpoints. Text, inherited or linked "
        "content, theme definitions and rendered appearance are outside this comparison. "
        "Exit 0: compared properties match; 1: properties differ or target absent after "
        "the edit; 2: input or selection error."
    ))
    parser.add_argument("before", help="saved PPTX containing the original shape")
    parser.add_argument("after", help="edited, saved PPTX")
    parser.add_argument("--slide", required=True, type=int, help="1-based page in thumbnail order")
    parser.add_argument("--after-slide", type=int, help="corresponding page in AFTER if its order or slide ID changed")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--name", help="exact, unique Selection Pane name on the slide")
    selector.add_argument("--id", type=int, help="numeric shape ID on the slide")
    args = parser.parse_args()
    key, value = ("id", str(args.id)) if args.name is None else ("name", args.name)
    after_page = args.slide if args.after_slide is None else args.after_slide
    before_location = f"{args.before}, slide {args.slide}"
    after_location = f"{args.after}, slide {after_page}"
    try:
        before_id, tree = slide_tree(args.before, args.slide)
        before = select(tree, key, value, before_location)
        if before is None:
            raise ValueError(f"{before_location}: {key}={value!r} not found")
        if local(before[0].tag) not in {"sp", "cxnSp"}:
            raise ValueError(f"{before_location}: select a native shape or connector, including one inside a group")
        after_id, tree = slide_tree(args.after, after_page)
        if args.after_slide is None and before_id != after_id:
            raise ValueError("slide IDs differ at this position; identify the corresponding page with --after-slide")
        after = select(tree, key, value, after_location)
    except (OSError, BadZipFile, ET.ParseError, KeyError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")

    if after is None:
        print(f"{after_location}: {key}={value!r} not found")
        return 1
    original = list(drawing_properties(*before))
    edited = list(drawing_properties(*after))
    if original == edited:
        print(f"{key}={value!r}: compared drawing properties match")
        return 0
    for line in difflib.unified_diff(original, edited, before_location, after_location, n=1, lineterm=""):
        print(line)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
