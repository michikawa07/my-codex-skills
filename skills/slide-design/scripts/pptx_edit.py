#!/usr/bin/env python3
"""Apply a specified edit to a PPTX and render the affected pages."""
import argparse
from contextlib import redirect_stdout
from io import StringIO
from os.path import commonprefix
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
from tempfile import TemporaryDirectory, mkdtemp
from xml.dom import minidom
from zipfile import BadZipFile, ZipFile

sys.dont_write_bytecode = True
from pptx_font_size import child, paragraph_text, points, set_size, text_shape
from pptx_grouping import LOCK_TYPES, slide_parts, write_copy


def replace_text(doc, args):
    if not args.text or any(char in args.text + args.new for char in "\r\n"):
        raise ValueError("Use single-line text for this edit.")
    shape_id, body = text_shape(doc, args)
    paragraphs = [node for node in body.childNodes if node.localName == "p"]
    if len(paragraphs) != 1:
        raise ValueError("Select a single-line native text shape.")
    pieces = []
    for node in paragraphs[0].childNodes:
        if node.localName in ("fld", "br"):
            raise ValueError("This shape contains a field or a line break.")
        if node.localName == "r":
            element = child(node, "t")
            if element is not None:
                pieces.append(element)
    if not pieces:
        raise ValueError("No editable run in the selected shape.")
    # Preserve both unchanged ends, including their formatting across runs.
    first = len(commonprefix([args.text, args.new]))
    tail = len(commonprefix([args.text[first:][::-1], args.new[first:][::-1]]))
    last = len(args.text) - tail
    middle = args.new[first:len(args.new) - tail]
    start = 0
    for i, element in enumerate(pieces):
        original = "".join(n.data for n in element.childNodes if n.nodeType == n.TEXT_NODE)
        end = start + len(original)
        insert = start <= first < end or (i == len(pieces) - 1 and first == end)
        value = original[:max(0, first - start)] + (middle if insert else "") + original[max(0, last - start):]
        if value != original:
            for node in list(element.childNodes):
                element.removeChild(node)
            element.appendChild(doc.createTextNode(value))
        start = end
    return shape_id


def slide_nodes(parent):
    return [node for node in parent.childNodes if node.localName == "sldId"]


def place_after(node, anchor):
    node.parentNode.removeChild(node)
    anchor.parentNode.insertBefore(node, anchor.nextSibling)


def reorder(doc, origin, after):
    main = slide_nodes(child(doc.documentElement, "sldIdLst"))
    if not 1 <= after <= len(main) or origin == after:
        raise ValueError("The destination must be a different existing page (numbered before the move).")
    node, anchor = main[origin - 1], main[after - 1]
    for sections in doc.getElementsByTagNameNS("*", "sectionLst"):
        entries = {}
        for section in [n for n in sections.childNodes if n.localName == "section"]:
            items = child(section, "sldIdLst")
            if items:
                entries.update((n.getAttribute("id"), n) for n in slide_nodes(items))
        if entries:
            if any(n.getAttribute("id") not in entries for n in (node, anchor)):
                raise ValueError("The section list does not identify both pages.")
            place_after(entries[node.getAttribute("id")], entries[anchor.getAttribute("id")])
    place_after(node, anchor)


def last_title_page(deck, parts, heading):
    key = unicodedata.normalize("NFKC", heading).strip().casefold()
    if not key:
        raise ValueError("Specify the beginning of a title.")
    found = None
    for page, part in enumerate(parts, 1):
        for shape in ET.fromstring(deck.read(part)).findall(".//{*}sp"):
            marker = shape.find("./{*}nvSpPr/{*}nvPr/{*}ph")
            if marker is None or marker.get("type") not in ("title", "ctrTitle"):
                continue
            text = "".join(t.text or "" for t in shape.findall("./{*}txBody//{*}t"))
            title = unicodedata.normalize("NFKC", text).strip().casefold()
            if title == key or (title.startswith(key) and not title[len(key)].isalnum()):
                found = page
                break
    if found is None:
        raise ValueError("No matching title placeholder. Use 'after' with the original page number.")
    return found


def edit_deck(args, stage):
    if args.action in ("keep", "omit"):
        from pptx_page_subset import subset
        return subset(args, stage)
    if args.action == "size":
        args.output, args.preview = stage, None
        with redirect_stdout(StringIO()):
            set_size(args)
        return [args.slide]
    with ZipFile(args.file) as deck:
        parts = list(slide_parts(deck))
        if not 1 <= args.slide <= len(parts):
            raise ValueError("Page outside the presentation.")
        part = parts[args.slide - 1] if args.action == "text" else "ppt/presentation.xml"
        expected_order = parts.copy()
        with minidom.parseString(deck.read(part)) as doc:
            if args.action == "text":
                shape_id = replace_text(doc, args)
                pages, changed = [args.slide], args.text != args.new
            else:
                if args.action == "after-last-title":
                    args.after = last_title_page(deck, parts, args.heading)
                reorder(doc, args.slide, args.after)
                dest = args.after + (args.slide > args.after)
                expected_order.insert(dest - 1, expected_order.pop(args.slide - 1))
                pages = list(range(min(args.slide, dest), max(args.slide, dest) + 1))
                changed = dest != args.slide
            data = doc.toxml(encoding=doc.encoding or "utf-8", standalone=doc.standalone)
            write_copy(deck, stage, {part: data} if changed else {})
    with ZipFile(stage) as saved:
        if list(slide_parts(saved)) != expected_order:
            raise ValueError("The saved page order does not match the request.")
        if args.action == "text":
            args.id = shape_id
            with minidom.parseString(saved.read(part)) as doc:
                _, body = text_shape(doc, args)
                if paragraph_text(child(body, "p")) != args.new:
                    raise ValueError("The saved text does not match the request.")
    return pages


def publish(source, output, preview_dir, prepare):
    output = Path(output or source).resolve()
    if output.suffix.lower() != source.suffix.lower():
        raise ValueError("Keep the original PowerPoint file extension.")
    node_name = "node.exe" if os.name == "nt" else "node"
    bundled = Path(sys.executable).resolve().parents[1] / "node" / "bin" / node_name
    node = str(bundled) if bundled.is_file() else shutil.which("node")
    if not node:
        raise ValueError("Run with the Codex Python and Node runtime to render previews.")
    stamp = source.stat()
    with TemporaryDirectory(dir=output.parent) as folder:
        scratch = Path(folder)
        stage = scratch / output.name
        pages = list(dict.fromkeys(prepare(stage)))
        renderer = Path(__file__).with_name("render_pptx_page.mjs")
        image_args = [arg for p in pages for arg in (str(p), str(scratch / f"p{p}.png"))]
        subprocess.run([node, str(renderer), str(stage), *image_args], check=True, stdout=subprocess.DEVNULL)
        if output == source and (stamp.st_mtime_ns, stamp.st_size) != (output.stat().st_mtime_ns, output.stat().st_size):
            raise ValueError("The source changed during the edit.")
        images = Path(preview_dir or mkdtemp(prefix="pptx-pages-")).resolve()
        images.mkdir(parents=True, exist_ok=True)
        for page in pages:
            shutil.copy2(scratch / f"p{page}.png", images / f"p{page}.png")
        os.replace(stage, output)
    return output, [images / f"p{page}.png" for page in pages]


def edit_file(file, pages, write, check, *, preview_dir=None, output=None):
    """Use any editor in write(source, candidate). Return a true value from check(candidate)."""
    source = Path(file).resolve()
    pages = [pages] if isinstance(pages, int) else list(pages)
    if not pages:
        raise ValueError("Specify at least one page to preview in the saved presentation.")

    def prepare(stage):
        write(source, stage)
        if not check(stage):
            raise ValueError("The saved PowerPoint did not pass the requested check.")
        return pages

    saved, images = publish(source, output, preview_dir, prepare)
    print(saved, *images, sep="\n")
    return saved, images


def page_part(parts, page):
    if not 1 <= page <= len(parts):
        raise ValueError(f"Page {page} is outside the presentation.")
    return parts[page - 1]


def shape_xml(root, shape_id):
    """Find a native slide object by ID, including children of groups."""
    found = root.xpath(f'.//p:cNvPr[@id="{int(shape_id)}"]/../..')
    if len(found) != 1:
        raise ValueError(f"Expected one shape with ID {shape_id}, found {len(found)}.")
    return found[0]


def edit_pages(file, pages, change, check, *, preview_dir=None, output=None):
    """Pass (page number, native slide XML) to change and, after saving, to check."""
    from lxml import etree
    from pptx.oxml import parse_xml

    pages = [pages] if isinstance(pages, int) else list(dict.fromkeys(pages))

    def write(source, stage):
        changed = {}
        with ZipFile(source) as archive:
            parts = list(slide_parts(archive))
            for page in pages:
                part = page_part(parts, page)
                root = parse_xml(archive.read(part))
                before = etree.tostring(root)
                change(page, root)
                if etree.tostring(root) != before:
                    changed[part] = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
            write_copy(archive, stage, changed)

    def check_saved(stage):
        with ZipFile(stage) as archive:
            parts = list(slide_parts(archive))
            return all(check(page, parse_xml(archive.read(page_part(parts, page)))) for page in pages)

    return edit_file(file, pages, write, check_saved, preview_dir=preview_dir, output=output)


def selected_elements(root, selector):
    from lxml import etree

    try:
        nodes = root.xpath(selector)
    except etree.XPathError as exc:
        raise ValueError(f"Invalid XPath: {exc}") from exc
    if not isinstance(nodes, list) or any(not isinstance(node, etree._Element) or not isinstance(node.tag, str) for node in nodes):
        raise ValueError("Use an XPath that selects XML elements.")
    return nodes


def element_label(node):
    for parent in (node, *node.iterancestors()):
        info = parent.find("./*/{*}cNvPr")
        if info is not None:
            label = f"#{info.get('id')} {info.get('name', '')} / {node.tag.rsplit('}', 1)[-1]}"
            groups = (group.find("./{*}nvGrpSpPr/{*}cNvPr") for group in parent.iterancestors("{*}grpSp"))
            names = [prop.get("name") for prop in groups if prop is not None and prop.get("name")]
            if names:
                label += " [" + " > ".join(reversed(names)) + "]"
            return label
    return node.tag.rsplit("}", 1)[-1]


def attributes(args):
    from pptx.oxml import parse_xml

    values = {}
    for pair in args.assignments:
        key, separator, value = pair.partition("=")
        if not separator or not key or key in values:
            raise ValueError("Use a separate name=value for each XML attribute.")
        values[key] = value
    if args.count is not None and args.count < 1:
        raise ValueError("Specify a positive match count.")

    if not values:
        with ZipFile(args.file) as archive:
            part = page_part(list(slide_parts(archive)), args.slide)
            nodes = selected_elements(parse_xml(archive.read(part)), args.xpath)
            print(f"p{args.slide}: {len(nodes)} match(es)")
            for node in nodes:
                print(element_label(node), dict(node.attrib))
        return

    paths, report = [], []

    def change(page, root):
        nodes = selected_elements(root, args.xpath)
        expected = args.count or 1
        if not nodes or (not args.all and len(nodes) != expected):
            raise ValueError(f"XPath matched {len(nodes)} element(s), expected {expected if not args.all else 'one or more'}. "
                             "Run the selector without assignments to inspect its matches.")
        tree = root.getroottree()
        for node in nodes:
            paths.append(tree.getelementpath(node))
            edits = [f"{key}={node.get(key, '(unset)')} -> {value}" for key, value in values.items()]
            report.append(f"p{page} {element_label(node)}: {', '.join(edits)}")
            for key, value in values.items():
                node.set(key, value)

    def check(page, root):
        # Changing an attribute can make the original XPath stop matching.
        for path in paths:
            node = root if path == "." else root.find(path)
            if node is None or any(node.get(key) != value for key, value in values.items()):
                return False
        return bool(paths)

    edit_pages(args.file, args.slide, change, check, preview_dir=args.preview_dir, output=args.output)
    print(*report, sep="\n")


def inspect_links(archive, parts, page):
    """Show the page order and its incoming and outgoing internal package relationships."""
    from pptx_page_subset import relations

    part = page_part(parts, page)
    lo, hi = max(0, page - 2), min(len(parts), page + 1)
    print("Page order:", len(parts), "pages;", ", ".join(f"p{i + 1}={parts[i]}" for i in range(lo, hi)))
    for owner, rel_id, kind, target in relations(archive):
        if owner == part or target == part:
            print(f"{owner or '/'}  {rel_id} ({kind})  ->  {target}")



def inspect_page(file, page, ids, links=False):
    from lxml import etree
    from pptx.oxml import parse_xml

    with ZipFile(file) as archive:
        parts = list(slide_parts(archive))
        part = page_part(parts, page)
        root = parse_xml(archive.read(part))
        if links:
            inspect_links(archive, parts, page)
    print(f"p{page}  {part}")
    if ids:
        for shape_id in ids:
            print(etree.tostring(shape_xml(root, shape_id), encoding="unicode", pretty_print=True))
        return
    for prop in root.xpath(".//p:cNvPr"):
        obj = prop.getparent().getparent()
        kind = etree.QName(obj).localname
        if kind in LOCK_TYPES:
            words = [] if kind == "grpSp" else obj.xpath(".//a:t/text()")
            depth = len(obj.xpath("ancestor::p:grpSp"))
            print(f"{'  ' * depth}{prop.get('id')}  {kind}  {prop.get('name', '')}  {''.join(words)[:96]}")


def save_with_previews(args):
    output, images = publish(args.file, args.output, args.preview_dir, lambda stage: edit_deck(args, stage))
    if args.action in ("keep", "omit"):
        result = f"{args.action} original pages: {args.slide} {' '.join(args.pages)}".rstrip()
    elif args.action == "size":
        result = f"Slide {args.slide}: {args.text!r}, {int(args.points) / 100:g} pt"
    elif args.action == "text":
        result = f"Slide {args.slide}: {args.new!r}"
    else:
        result = f"Original slide {args.slide} now at {args.after + (args.slide > args.after)}, after original slide {args.after}"
    print(f"Verified: {result}", output, *images, sep="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("slide", type=int, help="1-based page in thumbnail order")
    parser.add_argument("--output", type=Path, help="defaults to editing the named file")
    parser.add_argument("--preview-dir", type=Path, help="defaults to a new temporary folder")
    parser.set_defaults(title=False, id=None)
    actions = parser.add_subparsers(dest="action", required=True)
    inspect = actions.add_parser("inspect", help="list page objects in group order, or show the XML for selected IDs")
    inspect.add_argument("ids", type=int, nargs="*")
    inspect.add_argument("--links", action="store_true", help="also show page order and related package parts")
    attrs = actions.add_parser("attrs", help="inspect or set attributes on elements selected by native slide XPath")
    attrs.add_argument("xpath", help="XPath using PowerPoint p: and a: namespaces")
    attrs.add_argument("assignments", nargs="*", metavar="NAME=VALUE")
    count = attrs.add_mutually_exclusive_group()
    count.add_argument("--count", type=int, help="required number of matches when editing; default 1")
    count.add_argument("--all", action="store_true", help="change all matches, requiring at least one")
    size = actions.add_parser("size", help="font size of an existing text shape")
    size.add_argument("text", help="exact shape text")
    size.add_argument("points", type=points)
    wording = actions.add_parser("text", help="replace a single-line shape's text")
    wording.add_argument("text", help="current exact shape text")
    wording.add_argument("new")
    order = actions.add_parser("after", help="move the page immediately after another")
    order.add_argument("after", type=int, help="destination's original page number")
    by_title = actions.add_parser("after-last-title", help="move after the last matching native slide title")
    by_title.add_argument("heading", help="complete title or its first words")
    subset_ops = []
    for name, help_text in (("omit", "remove the selected original pages"), ("keep", "retain just the selected original pages")):
        operation = actions.add_parser(name, help=help_text)
        operation.add_argument("pages", nargs="*", help="additional page numbers or ranges, e.g. 7 9-12")
        subset_ops.append(operation)
    for operation in (attrs, size, wording, order, by_title, *subset_ops):
        operation.add_argument("--output", type=Path, default=argparse.SUPPRESS)
        operation.add_argument("--preview-dir", type=Path, default=argparse.SUPPRESS)
    args = parser.parse_args()
    args.file = args.file.resolve()
    try:
        if args.action == "inspect":
            inspect_page(args.file, args.slide, args.ids, args.links)
        elif args.action == "attrs":
            attributes(args)
        else:
            save_with_previews(args)
    except (OSError, ValueError, BadZipFile, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
