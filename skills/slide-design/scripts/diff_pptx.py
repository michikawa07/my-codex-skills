#!/usr/bin/env python3
"""List changed PowerPoint pages, their text edits and changed shared resources."""

import argparse
import difflib
import hashlib
import posixpath
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZipFile

if __name__ == "__main__":
    sys.dont_write_bytecode = True
    sys.stdout.reconfigure(encoding="utf-8")
from find_pptx_text import text_blocks
from pptx_grouping import DRAWING_NS, slide_parts


PAGE_NUMBER_FIELDS = {f"{{{ns}}}fld" for ns in DRAWING_NS}
CREATION_IDS = {
    "{http://schemas.microsoft.com/office/drawing/2014/main}creationId": "id",
    "{http://schemas.microsoft.com/office/powerpoint/2010/main}creationId": "val",
}


def snapshot(archive):
    parts, links, bindings = {}, {}, {}
    for name in archive.namelist():
        if not name.endswith(".rels"):
            continue
        owner = name.replace("/_rels/", "/").removesuffix(".rels")
        related = [name]
        targets = {}
        for rel in ET.fromstring(archive.read(name)):
            kind, target = rel.attrib["Type"], rel.attrib["Target"]
            mode = rel.get("TargetMode", "Internal")
            targets[rel.attrib["Id"]] = (kind, target, mode)
            # A slide link and a master's list of child layouts are not inherited content.
            if mode == "External" or kind.endswith("/slide") or (kind.endswith("/slideLayout") and "/slideMasters/" in owner):
                continue
            related.append(posixpath.normpath(posixpath.join(posixpath.dirname(owner), target)).lstrip("/"))
        parts[name] = sorted(targets.values())
        bindings[owner], links[owner] = targets, related

    for name in archive.namelist():
        if name in parts or name.endswith("/") or name in ("docProps/core.xml", "docProps/app.xml") or name.startswith("docProps/thumbnail."):
            continue
        data = archive.read(name)
        if name.endswith(".xml"):
            root = ET.fromstring(data)
            targets = bindings.get(name, {})
            for node in root.iter():
                # Exporters regenerate these IDs even when an unchanged slide is saved.
                if node.tag in CREATION_IDS:
                    node.attrib.pop(CREATION_IDS[node.tag], None)
                elif node.tag in PAGE_NUMBER_FIELDS and node.get("type") == "slidenum":
                    node.attrib.pop("id", None)
                for key, value in node.attrib.items():
                    if "/relationships}" in key and value in targets:
                        node.set(key, repr(targets[value]))
            data = ET.tostring(root)
        parts[name] = hashlib.sha256(data).digest()

    pages = {}
    for number, part in enumerate(slide_parts(archive), 1):
        dependencies = set()
        pending = [part]
        while pending:
            item = pending.pop()
            if item not in dependencies:
                dependencies.add(item)
                pending.extend(links.get(item, ()))
        blocks = text_blocks(ET.fromstring(archive.read(part)))
        lines = [line for block in blocks for line in block.splitlines() if line.strip()]
        pages[part] = (number, dependencies, lines)
    return parts, pages


def compare(reviewed, candidate):
    versions = []
    for label, path in (("Reviewed", reviewed), ("Candidate", candidate)):
        with path.open("rb") as stream:
            digest = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
            print(f"{label} SHA-256: {digest.hexdigest()}")
            with ZipFile(stream) as archive:
                versions.append(snapshot(archive))
    (old, before), (new, after) = versions
    changed = {name for name in old.keys() | new.keys() if old.get(name) != new.get(name)}
    unassigned = changed.copy()
    for part in dict.fromkeys([*before, *after]):
        old_page, old_deps, old_text = before.get(part, (None, set(), []))
        new_page, new_deps, new_text = after.get(part, (None, set(), []))
        hits = changed.intersection(old_deps | new_deps)
        unassigned.difference_update(hits)
        if old_page == new_page and not hits:
            continue
        left = f"p{old_page}" if old_page else "(added)"
        right = f"p{new_page}" if new_page else "(removed)"
        print(f"{left} -> {right}", ", ".join(sorted(hits)), sep="  ")
        for line in difflib.unified_diff(old_text, new_text, n=0, lineterm=""):
            print(line)
    if unassigned:
        print("Deck-level changes (check scope against the rendered pages):", ", ".join(sorted(unassigned)))
    if not changed and list(before) == list(after):
        print("No slide or related package content changed.")
        return 0
    return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Use a separate, unmodified copy of the file actually reviewed. "
        "Exit 0: no compared content changed; 1: review differences; 2: input error."
    ))
    parser.add_argument("reviewed", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    try:
        if args.reviewed.samefile(args.candidate):
            parser.error("use the saved review copy and a separate submission candidate")
        return compare(args.reviewed, args.candidate)
    except (OSError, BadZipFile, ET.ParseError, KeyError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
