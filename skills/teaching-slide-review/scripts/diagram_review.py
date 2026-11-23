#!/usr/bin/env python3
"""Prepare and finish a PowerPoint diagram review against the saved slides."""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile, TemporaryDirectory
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
from diagram_parts import inspect_deck


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def inventory(files, pages):
    objects, units, limits = {}, [], []
    for index, filename in enumerate(files, start=1):
        alias = f"D{index}"
        parts = inspect_deck(filename, pages, alias)
        objects.update(parts["objects"])
        units.extend(parts["units"])
        limits.extend(parts["limits"])
    return {"objects": objects, "units": units, "limits": limits}


def prepare(args):
    work = args.work.resolve()
    files = [p.resolve() for p in args.decks]
    pages = list(dict.fromkeys(args.pages))
    content = args.main.read_bytes() if args.main is not None else b""
    if args.main is not None and not content.strip():
        raise ValueError("empty main assessment")
    if args.main is not None:
        content.decode("utf-8-sig")
    inputs = {"decks": [{"path": str(p), "sha256": digest(p.read_bytes())} for p in files],
              "pages": pages, "main": str(args.main.resolve()) if args.main else None,
              "main_sha256": digest(content)}
    if work.exists():
        if not (work / "inputs.json").is_file() or read_json(work / "inputs.json") != inputs:
            raise ValueError("choose a new review directory for different materials or a changed assessment")
        print(f"Existing review: {work}")
        return
    data = inventory(files, pages)
    work.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=work.parent) as temp:
        complete = Path(temp) / "review"
        complete.mkdir()
        write_json(complete / "inputs.json", inputs)
        write_json(complete / "inventory.json", data)
        (complete / "content.md").write_bytes(content)
        observations = [{"ids": [unit["id"]], "evidence": [], "state": "", "observed": "",
                         "reader_cost": "", "editing": ""} for unit in data["units"]]
        write_json(complete / "observations.json", observations)
        (complete / "additional.md").touch()
        complete.rename(work)
    print(f"{len(data['units'])} items in {work / 'inventory.json'}; record what is visible in observations.json.")


def show(args):
    data = read_json(args.work / "inventory.json")
    for index, deck in enumerate(read_json(args.work / "inputs.json")["decks"], start=1):
        print(f"D{index} = {deck['path']}")
    for unit in data["units"]:
        if args.prefix and not any(unit["id"].startswith(p) for p in args.prefix):
            continue
        print(unit["id"], unit["kind"])
        original = not (args.work / "comparisons.json").exists()
        for fact in unit["facts"]:
            if not original or "chord" not in fact.lower():
                print(" ", fact)
        members = set(unit["members"])
        for key in dict.fromkeys(unit["members"] + unit["evidence"]):
            obj = data["objects"][key]
            label = " ".join(str(obj.get("text") or obj.get("name") or obj.get("geometry") or "").split())
            print("  *" if key in members else "   ", key, label[:75])
    for limit in data["limits"]:
        print(" ", limit)


def validate(units, records):
    if not isinstance(records, list):
        raise ValueError("observations.json must be a list")
    lookup = {unit["id"]: unit for unit in units}
    covered = set()
    errors = []
    for number, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            errors.append(f"row {number}: expected an object")
            continue
        ids = record.get("ids")
        evidence = record.get("evidence")
        if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids):
            errors.append(f"row {number}: list the item IDs")
            continue
        if not isinstance(evidence, list) or not all(isinstance(i, str) for i in evidence):
            errors.append(f"row {number}: list the supporting object IDs")
            continue
        known = [lookup[i] for i in ids if i in lookup]
        invalid = (set(ids) - lookup.keys()) | (set(ids) & covered)
        if invalid or len(ids) != len(set(ids)):
            errors.append(f"row {number}: unknown or repeated items: {', '.join(sorted(invalid or ids))}")
        covered.update(ids)
        if len({unit["kind"] for unit in known}) > 1:
            errors.append(f"row {number}: only group observations of the same kind")
        if record.get("state") not in {"clear", "issue", "open"} or not nonempty(record.get("observed")):
            errors.append(f"{', '.join(ids)}: record the state and what is visible in the original")
        if record.get("state") == "issue" and not nonempty(record.get("reader_cost")):
            errors.append(f"{', '.join(ids)}: identify the difficulty in reading the original")
        if record.get("editing") and not isinstance(record["editing"], str):
            errors.append(f"{', '.join(ids)}: editing observations must be text")
        cited = set(evidence)
        allowed = set()
        for unit in known:
            members = set(unit["members"])
            context = set(unit["evidence"]) | members
            allowed.update(context)
            if unit["kind"] == "peers" and len(cited & members) < 2:
                errors.append(f"{unit['id']}: cite two members of this same group")
            if unit["kind"] == "route":
                if not members <= cited:
                    errors.append(f"{unit['id']}: cite the route itself")
                if context - members and not cited & (context - members):
                    errors.append(f"{unit['id']}: cite an endpoint or nearby object from the inventory")
        if cited - allowed:
            errors.append(f"row {number}: evidence outside these items: {', '.join(sorted(cited - allowed))}")
    missing = lookup.keys() - covered
    if missing:
        errors.append("unreviewed items: " + ", ".join(sorted(missing)))
    if errors:
        raise ValueError("\n".join(errors))


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def compare(args):
    work = args.work.resolve()
    inventory = read_json(work / "inventory.json")
    raw = (work / "observations.json").read_bytes()
    records = json.loads(raw.decode("utf-8-sig"))
    validate(inventory["units"], records)
    comparisons = {r["ids"][0]: {"result": "", "observed": ""} for r in records if r["state"] == "issue"}
    path = work / "comparisons.json"
    if path.exists():
        if read_json(path).get("observations_sha256") != digest(raw):
            raise ValueError("original observations changed; start a new comparison before using an alternative")
        print(f"Existing comparisons: {path}")
        return
    with path.open("x", encoding="utf-8") as f:
        json.dump({"observations_sha256": digest(raw), "items": comparisons}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{len(comparisons)} observations of a reading difficulty to compare in {path}.")


def location(ids, units, files):
    pages = {}
    for key in ids:
        alias, page, _ = units[key]["members"][0].split("/", 2)
        name = files[int(alias[1:]) - 1].name
        if name not in pages.setdefault(page, []):
            pages[page].append(name)
    return "、".join(f"{page}（{'・'.join(names)}）" for page, names in pages.items())


def evidence_links(text, origin, output_dir):
    """Keep links to local evidence usable when the figures and report have different directories."""
    if origin == output_dir:
        return text

    def relocate(match):
        target = match.group("target")
        uri = urlsplit(target[1:-1] if target.startswith("<") else target)
        if uri.scheme or uri.netloc or not uri.path or Path(uri.path).is_absolute():
            return target
        path = (origin / unquote(uri.path)).resolve()
        if not path.is_file():
            return target
        try:
            destination = Path(os.path.relpath(path, output_dir)).as_posix()
        except ValueError:  # Different Windows drives.
            destination = path.as_posix()
        destination = destination.replace("%", "%25").replace("#", "%23").replace("?", "%3F")
        if uri.query:
            destination += "?" + uri.query
        if uri.fragment:
            destination += "#" + uri.fragment
        return f"<{destination}>"

    return re.sub(r"(?<=\]\()(?P<target><[^>\n]+>|(?:[^()\s]|\([^()\n]*\))+)(?=\s|\))", relocate, text)


def finish(args):
    work = args.work.resolve()
    output = args.output.resolve()
    inputs = read_json(work / "inputs.json")
    files = [Path(d["path"]) for d in inputs["decks"]]
    protected = files + ([Path(inputs["main"])] if inputs["main"] else [])
    attached = args.main.resolve() if args.main else None
    if attached is not None:
        if inputs["main"] and attached != Path(inputs["main"]).resolve():
            raise ValueError("this review already has a different saved main assessment")
        protected.append(attached)
    protected.extend(work / name for name in ("inputs.json", "inventory.json", "content.md", "observations.json", "comparisons.json", "additional.md"))
    if output in protected:
        raise ValueError("the output must be separate from all input files")
    for file, source in zip(files, inputs["decks"]):
        if digest(file.read_bytes()) != source["sha256"]:
            raise ValueError(f"source changed: {file}; prepare a review of the current version")
    content = (work / "content.md").read_bytes()
    if inputs["main"] and Path(inputs["main"]).read_bytes() != content:
        raise ValueError("the input assessment differs from the saved assessment")
    if digest(content) != inputs["main_sha256"]:
        raise ValueError("the saved main assessment has changed")
    if attached is not None and not inputs["main"]:
        content = attached.read_bytes()
        if not content.decode("utf-8-sig").strip():
            raise ValueError("empty main assessment")
    data = inventory(files, inputs["pages"])
    if json.loads(json.dumps(data)) != read_json(work / "inventory.json"):
        raise ValueError("the inventory no longer matches the source slides")
    raw = (work / "observations.json").read_bytes()
    records = json.loads(raw.decode("utf-8-sig"))
    validate(data["units"], records)
    checks = read_json(work / "comparisons.json")
    if checks.get("observations_sha256") != digest(raw):
        raise ValueError("original observations changed after the comparison started")
    comparisons = checks["items"]
    expected = {r["ids"][0] for r in records if r["state"] == "issue"}
    if not isinstance(comparisons, dict) or set(comparisons) != expected:
        raise ValueError("compare precisely the original observations that recorded a reading difficulty")
    units = {u["id"]: u for u in data["units"]}
    sections = {"修正する箇所": [], "保つ箇所": [], "PowerPointでの編集": [], "判断を保留した箇所": []}
    for item in records:
        where = location(item["ids"], units, files)
        def line(heading, words):
            sections[heading].append(f"- {where}　{words.strip()}")
        if item.get("editing"):
            line("PowerPointでの編集", item["editing"])
        if item["state"] == "issue":
            check = comparisons[item["ids"][0]]
            if (not isinstance(check, dict) or check.get("result") not in {"better", "same", "worse", "open"}
                    or not nonempty(check.get("observed"))):
                raise ValueError(f"{item['ids'][0]}: record the reading result of the alternative")
            result = check["result"]
            if result == "better":
                line("修正する箇所", item["reader_cost"] + " " + check["observed"])
            elif result == "open":
                line("判断を保留した箇所", item["observed"] + " " + check["observed"])
            elif item.get("highlight") is True:
                line("保つ箇所", check["observed"])
        elif item["state"] == "open":
            line("判断を保留した箇所", item["observed"])
        elif item.get("highlight") is True:
            line("保つ箇所", item["observed"])
    lines = ["## 図の校閲"]
    for heading, items in sections.items():
        if items:
            lines.extend(["### " + heading, "\n".join(items)])
    if not data["units"]:
        lines.append("選択したページには自動で起票できる項目がありません。画像の中の図は表示を確認してください。")
    elif len(lines) == 1:
        lines.append("図の形は現行のまま使えます。")
    extra = work / "additional.md"
    if extra.is_file() and (notes := extra.read_text(encoding="utf-8-sig").strip()):
        lines.extend(["### 図全体・そのほかの要素", notes])
    report = evidence_links("\n\n".join(lines) + "\n", work.parent, output.parent)
    text = (b"\n\n" if content else b"") + report.encode("utf-8")
    if args.check:
        submitted = output.read_bytes()
        if not submitted.startswith(content):
            raise ValueError("submitted main differs from the reviewed assessment")
        if submitted != content + text:
            raise ValueError("submitted figure assessment differs from the reviewed observations or notes")
        print(f"Verified the submitted report against its reviewed inputs: {output}")
        return
    temp = NamedTemporaryFile(dir=output.parent, delete=False)
    try:
        with temp:
            temp.write(content + text)
        os.replace(temp.name, output)
    finally:
        Path(temp.name).unlink(missing_ok=True)
    print(f"Recorded decisions for {len(data['units'])} diagram items; saved {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    collect = commands.add_parser("prepare", help="save the main assessment and inventory the diagrams")
    collect.add_argument("work", type=Path)
    collect.add_argument("decks", nargs="+", type=Path)
    collect.add_argument("--pages", nargs="+", type=int, required=True)
    collect.add_argument("--main", type=Path, help="already reviewed UTF-8 text to preserve")
    display = commands.add_parser("show", help="display diagram items, evidence and local facts")
    display.add_argument("work", type=Path)
    display.add_argument("prefix", nargs="*", help="optional prefixes of item IDs")
    review = commands.add_parser("compare", help="freeze original observations and open a comparison for each reading difficulty")
    review.add_argument("work", type=Path)
    submit = commands.add_parser("finish", help="check coverage and write the combined review")
    submit.add_argument("work", type=Path)
    submit.add_argument("output", type=Path)
    submit.add_argument("--main", type=Path, help="attach a separately reviewed UTF-8 assessment verbatim")
    submit.add_argument("--check", action="store_true", help="verify the submitted report without changing it")
    args = parser.parse_args()
    try:
        {"prepare": prepare, "show": show, "compare": compare, "finish": finish}[args.command](args)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()
