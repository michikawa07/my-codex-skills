#!/usr/bin/env python3
"""Read new slide-project comments and keep the sources of the decisions adopted from them."""

import argparse
from contextlib import closing
from itertools import islice
import json
import os
from pathlib import Path
import sqlite3
import sys

if __name__ == "__main__":
    sys.dont_write_bytecode = True
from feedback_source import locate, messages, validate


STATE = ".slide-feedback.sqlite3"
SKILLS = Path(__file__).resolve().parents[2]


def database(project, create):
    path = project / STATE
    if not create and not path.is_file():
        raise ValueError(f"No registered slide threads in {project}.")
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    if create:
        db.executescript("""
          CREATE TABLE IF NOT EXISTS threads (
            thread TEXT PRIMARY KEY, starting_after TEXT, cursor TEXT,
            start INTEGER NOT NULL, end INTEGER NOT NULL, quiet_size INTEGER, quiet_mtime INTEGER);
          CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY, thread TEXT NOT NULL, message TEXT NOT NULL,
            quote TEXT NOT NULL, place TEXT NOT NULL, file TEXT, rule TEXT,
            question TEXT, resolved_by INTEGER, example TEXT);
        """)
    def has_examples():
        return db.execute("SELECT 1 FROM pragma_table_info('decisions') WHERE name='example'").fetchone()
    if not has_examples():
        with db:
            db.execute("BEGIN IMMEDIATE")
            if not has_examples():
                db.execute("ALTER TABLE decisions ADD COLUMN example TEXT")
    return db


def watch(db, args, path):
    prior = db.execute("SELECT * FROM threads WHERE thread=?", (args.thread,)).fetchone()
    if prior:
        if args.after and args.after != prior["starting_after"]:
            raise ValueError("This thread is already registered with a different starting point.")
        return {"thread": args.thread, "starting_after": prior["starting_after"], "cursor": prior["cursor"]}
    first = None
    if args.from_now or args.after:
        for message in messages(path):
            if args.from_now or message.id == args.after:
                first = message
                if args.after:
                    break
        if args.after and first is None:
            raise ValueError(f"Starting message not found: {args.after}")
    anchor = first.id if first else None
    with db:
        db.execute("INSERT INTO threads (thread,starting_after,cursor,start,end) VALUES (?,?,?,?,?)",
                   (args.thread, anchor, anchor, first.start if first else 0, first.end if first else 0))
    return {"thread": args.thread, "starting_after": anchor, "cursor": anchor}


def after_cursor(path, row):
    cursor = row["cursor"]
    if not cursor:
        return messages(path)
    if validate(path, row["start"], row["end"], cursor):
        return messages(path, row["end"])
    for message in messages(path):
        if message.id == cursor:
            return messages(path, message.end)
    raise ValueError(f"Last confirmed user message is missing from {row['thread']}: {cursor}")


def get_thread(db, key):
    row = db.execute("SELECT * FROM threads WHERE thread=?", (key,)).fetchone()
    if not row:
        raise ValueError(f"Unregistered source: {key}")
    return row


def pending(db):
    return [dict(row) for row in db.execute(
        "SELECT id,thread,message,quote,place,question FROM decisions "
        "WHERE question IS NOT NULL AND resolved_by IS NULL ORDER BY id")]


def scan(db, args):
    if args.limit < 1:
        raise ValueError("--limit must be positive")
    sources = ([get_thread(db, key) for key in dict.fromkeys(args.threads)] if args.threads
               else db.execute("SELECT * FROM threads ORDER BY thread").fetchall())
    batches, unavailable = [], []
    for row in sources:
        try:
            path = locate(row["thread"], args.history_root)
            stat = path.stat()
            if (stat.st_size, stat.st_mtime_ns) == (row["quiet_size"], row["quiet_mtime"]):
                continue
            page = list(islice(after_cursor(path, row), args.limit + 1))
        except (OSError, ValueError) as error:
            unavailable.append({"thread": row["thread"], "error": str(error)})
            continue
        if not page:
            with db:
                db.execute("UPDATE threads SET quiet_size=?, quiet_mtime=? WHERE thread=? AND cursor IS ?",
                           (stat.st_size, stat.st_mtime_ns, row["thread"], row["cursor"]))
        else:
            batches.append({"thread": row["thread"], "after": row["cursor"],
                            "more": len(page) > args.limit, "messages": [
                                {"id": m.id, "text": m.text, "decisions": None} for m in page[:args.limit]
                            ]})
    return {"open": pending(db), "batches": batches, "unavailable": unavailable}


def required(data, key):
    if not isinstance(data, dict):
        raise ValueError("A decision must be a JSON object.")
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing {key!r} in a decision.")
    return value


def save_decision(db, project, thread, message, choice):
    quote = required(choice, "quote")
    if not any(quote in part for part in message.words):
        raise ValueError(f"{message.id}: quote the user's own words verbatim.")
    place = required(choice, "place")
    file, rule, question, example = None, None, None, None
    resolutions = choice.get("resolves", [])
    if not isinstance(resolutions, list) or any(type(i) is not int for i in resolutions):
        raise ValueError("resolves must list open decision IDs.")
    mode = [k for k in ("file", "example", "question", "local_only") if k in choice]
    if len(mode) != 1:
        raise ValueError("Choose a rule file, a historical example, an open question, or local_only to resolve a question.")
    if mode[0] == "file":
        file = required(choice, "file")
        rule = required(choice, "rule")
        root, relative = (SKILLS, file[6:]) if file.startswith("skill:") else (project, file)
        target = (root / relative).resolve()
        if Path(relative).is_absolute() or not target.is_relative_to(root.resolve()):
            raise ValueError(f"Use a rule path relative to its project or skill: {file}")
        if rule not in target.read_text(encoding="utf-8-sig"):
            raise ValueError(f"Adopted wording is missing from {target}: {rule!r}")
    elif mode[0] == "example":
        example = required(choice, "example")
    elif mode[0] == "question":
        question = required(choice, "question")
    elif choice["local_only"] is not True or not resolutions:
        raise ValueError("Use [] for a one-time instruction; local_only closes an open question.")
    decision_id = db.execute(
        "INSERT INTO decisions (thread,message,quote,place,file,rule,question,example) VALUES (?,?,?,?,?,?,?,?)",
        (thread, message.id, quote, place, file, rule, question, example)).lastrowid
    for key in resolutions:
        if key == decision_id or db.execute(
            "UPDATE decisions SET resolved_by=? WHERE id=? AND question IS NOT NULL AND resolved_by IS NULL",
            (decision_id, key)).rowcount != 1:
            raise ValueError(f"No open question with ID {key}.")


def apply(db, args):
    request = json.loads(args.batch.read_text(encoding="utf-8-sig"))
    saved = []
    with db:
        db.execute("BEGIN IMMEDIATE")
        for batch in request["batches"]:
            thread = batch["thread"]
            row = get_thread(db, thread)
            if row["cursor"] != batch["after"]:
                raise ValueError(f"{thread}: another review advanced this thread; read the remaining messages.")
            path = locate(thread, args.history_root)
            current = after_cursor(path, row)
            last = None
            for item in batch["messages"]:
                message = next(current, None)
                if message is None or item["id"] != message.id:
                    raise ValueError(f"{thread}: each reviewed message must follow the previous one.")
                choices = item["decisions"]
                if not isinstance(choices, list):
                    raise ValueError(f"{message.id}: review this message before advancing.")
                for choice in choices:
                    save_decision(db, args.project, thread, message, choice)
                last = message
            if last:
                db.execute("UPDATE threads SET cursor=?, start=?, end=?, quiet_size=NULL, quiet_mtime=NULL WHERE thread=?",
                           (last.id, last.start, last.end, thread))
                saved.append({"thread": thread, "through": last.id, "count": len(batch["messages"])})
    return {"reviewed": saved, "open": pending(db)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, help="project root; defaults to the nearest enrolled project")
    parser.add_argument("--history-root", type=Path, default=Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex"))
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("watch", help="register an agreed human production or review thread")
    add.add_argument("thread")
    starts = add.add_mutually_exclusive_group()
    starts.add_argument("--after", help="start just after this real user message")
    starts.add_argument("--from-now", action="store_true", help="include only future user messages")
    read = commands.add_parser("scan", help="read unreviewed user messages and any open questions")
    read.add_argument("threads", nargs="*")
    read.add_argument("--limit", type=int, default=12, help="maximum messages per thread in this batch")
    read.add_argument("--output", type=Path, help="write a working batch to a temporary JSON file")
    record = commands.add_parser("apply", help="record completed decisions and advance the reviewed position")
    record.add_argument("batch", type=Path)
    history = commands.add_parser("history", help="inspect provenance for a decision or rule file")
    lookup = history.add_mutually_exclusive_group()
    lookup.add_argument("--file", help="rule destination as registered")
    lookup.add_argument("--id", type=int, help="decision number")
    lookup.add_argument("--find", help="search a phrase in the original quote, place, decision or example")
    args = parser.parse_args()
    if args.project is None:
        cwd = Path.cwd()
        args.project = next((p for p in (cwd, *cwd.parents) if (p / STATE).is_file()), cwd)
    try:
        source = locate(args.thread, args.history_root) if args.command == "watch" else None
        if getattr(args, "output", None) and args.output.suffix.lower() != ".json":
            raise ValueError("Write the temporary batch to a separate .json file.")
        with closing(database(args.project, args.command == "watch")) as db:
            if args.command == "watch":
                result = watch(db, args, source)
            elif args.command == "scan":
                result = scan(db, args)
            elif args.command == "apply":
                result = apply(db, args)
            else:
                sql, params = "SELECT * FROM decisions", ()
                if args.id is not None:
                    sql, params = sql + " WHERE id=?", (args.id,)
                elif args.file:
                    sql, params = sql + " WHERE file=?", (args.file,)
                elif args.find:
                    sql += " WHERE instr(quote,?) OR instr(place,?) OR instr(rule,?) OR instr(example,?) OR instr(question,?)"
                    params = (args.find,) * 5
                result = {
                    "threads": [dict(row) for row in db.execute(
                        "SELECT thread,starting_after,cursor FROM threads ORDER BY thread")],
                    "decisions": [dict(row) for row in db.execute(sql + " ORDER BY id", params)],
                }
        if result.get("unavailable"):
            print("Some registered histories could not be read; see unavailable. Their positions were kept.", file=sys.stderr)
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if getattr(args, "output", None):
            args.output.write_text(output + "\n", encoding="utf-8")
            print(args.output)
        else:
            print(output)
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"{parser.prog}: {error}\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
