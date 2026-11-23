"""Select presentation pages in their existing order, keeping surviving package parts intact."""
from collections import defaultdict
from pathlib import PurePosixPath
import posixpath
from urllib.parse import unquote
from zipfile import ZipFile

from lxml import etree

from pptx_grouping import slide_parts, write_copy

PRESENTATION = "ppt/presentation.xml"
RELATIONSHIPS = "ppt/_rels/presentation.xml.rels"
TYPES = "[Content_Types].xml"


def relations(archive):
    """Yield source part, relationship ID/type and the resolved internal target."""
    for name in archive.namelist():
        if not name.endswith(".rels"):
            continue
        owner = posixpath.join(posixpath.dirname(posixpath.dirname(name)), posixpath.basename(name)[:-5])
        for rel in etree.fromstring(archive.read(name)):
            if rel.get("TargetMode") != "External":
                path = unquote(rel.get("Target").split("#", 1)[0])
                target = posixpath.normpath(posixpath.join(posixpath.dirname(owner), path)).lstrip("/") if path else owner
                yield owner, rel.get("Id"), rel.get("Type", "").rsplit("/", 1)[-1], target


def reachable(graph, omit=()):
    visited, pending = set(), [""]
    while pending:
        part = pending.pop()
        if part in visited:
            continue
        visited.add(part)
        pending.extend(target for target in graph[part] if part != PRESENTATION or target not in omit)
    return visited


def selection(first, ranges, length):
    numbers = {first}
    for term in ranges:
        left, sep, right = term.partition("-")
        a, b = int(left), int(right) if sep else int(left)
        if not 1 <= a <= b <= length:
            raise ValueError(f"Page range outside the presentation: {term}")
        numbers.update(range(a, b + 1))
    if not 1 <= first <= length:
        raise ValueError(f"Page {first} is outside the presentation.")
    return numbers


def update_properties(doc, original, kept, archive, lost):
    """Update existing presentation statistics and the localized slide-title list."""
    for tag, value in (("Slides", len(kept)),
                       ("HiddenSlides", sum(etree.fromstring(archive.read(original[i - 1])).get("show") in ("0", "false") for i in kept))):
        elem = doc.find("{*}" + tag)
        if elem is not None:
            elem.text = str(value)
    notes = doc.find("{*}Notes")
    if notes is not None and (notes.text or "").isdigit():
        removed_notes = sum(part.startswith("ppt/notesSlides/") and part.endswith(".xml") for part in lost)
        notes.text = str(max(0, int(notes.text) - removed_notes))
    titles = doc.find("{*}TitlesOfParts/{*}vector")
    groups = doc.findall("{*}HeadingPairs/{*}vector/{*}variant")
    if titles is None or len(groups) % 2:
        return
    start = 0
    for heading, count in zip(groups[::2], groups[1::2]):
        number = count.find("{*}i4")
        if number is None or not (number.text or "").isdigit():
            break
        size = int(number.text)
        label = "".join(heading.itertext()).strip().casefold()
        if label in ("slide titles", "スライド タイトル", "スライドのタイトル") and size == len(original) and start + size <= len(titles):
            for index, item in enumerate(list(titles)[start:start + size], 1):
                if index not in kept:
                    titles.remove(item)
            number.text, titles.attrib["size"] = str(len(kept)), str(len(titles))
            return
        start += size


def subset(args, stage):
    def pack(node):
        return etree.tostring(node, encoding="UTF-8", xml_declaration=True, standalone=True)

    with ZipFile(args.file) as archive:
        original = list(slide_parts(archive))
        chosen = selection(args.slide, args.pages, len(original))
        kept = [i for i in range(1, len(original) + 1) if (i in chosen) == (args.action == "keep")]
        if not kept:
            raise ValueError("Keep at least one slide.")
        kept_set = set(kept)
        expected = [original[i - 1] for i in kept]
        omit = set(original).difference(expected)
        graph = defaultdict(set)
        for owner, _, _, target in relations(archive):
            graph[owner].add(target)
        lost = reachable(graph) - reachable(graph, omit)
        if omit - lost:
            raise ValueError("A retained part links to an omitted slide. Resolve that link before removing the slide.")
        removed = set(lost)
        for part in lost:
            path = PurePosixPath(part)
            removed.add(str(path.parent / "_rels" / (path.name + ".rels")))
        changed = {}
        if omit:
            doc = etree.fromstring(archive.read(PRESENTATION))
            entries = doc.find("{*}sldIdLst")
            ids, rel_ids = set(), set()
            for i, entry in enumerate(list(entries), 1):
                if i not in kept_set:
                    ids.add(entry.get("id"))
                    rel_ids.add(next(v for k, v in entry.attrib.items() if k.endswith("}id")))
                    entries.remove(entry)
            for section in doc.iterfind(".//{*}sectionLst/{*}section/{*}sldIdLst"):
                for entry in list(section):
                    if entry.get("id") in ids:
                        section.remove(entry)
            for show in doc.iterfind(".//{*}custShow/{*}sldLst"):
                for entry in list(show):
                    if any(value in rel_ids for value in entry.attrib.values()):
                        show.remove(entry)
            for node in doc.iter():
                if any(key.endswith("}id") and value in rel_ids for key, value in node.attrib.items()):
                    raise ValueError("The presentation still uses a relationship to an omitted slide.")
            changed[PRESENTATION] = pack(doc)
            rels = etree.fromstring(archive.read(RELATIONSHIPS))
            for rel in list(rels):
                if rel.get("Id") in rel_ids:
                    rels.remove(rel)
            changed[RELATIONSHIPS] = pack(rels)
            types = etree.fromstring(archive.read(TYPES))
            for item in list(types):
                if unquote(item.get("PartName", "")).lstrip("/") in removed:
                    types.remove(item)
            changed[TYPES] = pack(types)
            if "docProps/app.xml" in archive.namelist():
                app = etree.fromstring(archive.read("docProps/app.xml"))
                update_properties(app, original, kept_set, archive, lost)
                changed["docProps/app.xml"] = pack(app)
        write_copy(archive, stage, changed, removed)
    with ZipFile(stage) as saved:
        if list(slide_parts(saved)) != expected or removed.intersection(saved.namelist()):
            raise ValueError("The saved pages do not match the selection.")
        if any(target in lost for _, _, _, target in relations(saved)):
            raise ValueError("A relationship in the saved presentation points to an omitted part.")
    # Show both sides of a cut, including the new first or last page for edge cuts.
    pages = [j for j, i in enumerate(kept, 1) if (i > 1 and i - 1 not in kept_set) or
             (i < len(original) and i + 1 not in kept_set)]
    return pages or [1]
