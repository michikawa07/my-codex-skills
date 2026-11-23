"""Read completed human messages from a named local Codex rollout."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re


@dataclass(frozen=True)
class Message:
    id: str
    text: str
    words: tuple[str, ...]
    start: int
    end: int
    timestamp: str


def locate(thread_id, history_root):
    """Return the one selected rollout. An explicitly supplied JSONL can be a fixture."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", thread_id):
        raise ValueError(f"Invalid thread ID: {thread_id!r}")
    root = Path(history_root).expanduser()
    if root.is_file() and root.suffix.lower() == ".jsonl":
        path = root
    else:
        dirs = [d for d in (root / "sessions", root / "archived_sessions") if d.is_dir()]
        names = (f"-{thread_id}.jsonl", f"_{thread_id}.jsonl")
        paths = [p for d in (dirs or [root]) for p in d.rglob(f"*{thread_id}.jsonl")
                 if p.name == f"{thread_id}.jsonl" or
                 (p.name.startswith("rollout-") and p.name.endswith(names))]
        if len(paths) != 1:
            raise ValueError(f"Found {len(paths)} local rollouts for {thread_id} in {root}.")
        path = paths[0]
    with path.open("rb") as f:
        first = json.loads(f.readline())
    p = first.get("payload", {})
    if first.get("type") == "session_meta":
        actual = p.get("session_id") or p.get("id")
        if p.get("thread_source", "user") != "user" or isinstance(p.get("source"), dict):
            raise ValueError(f"{thread_id} is not a human conversation.")
    elif root.is_file() and first.get("type") == "event_msg":
        actual = p.get("thread_id")  # A single-file fixture may omit session metadata.
    else:
        raise ValueError(f"Unsupported rollout header in {path}.")
    if actual is not None and actual != thread_id:
        raise ValueError(f"Expected {thread_id}, found {actual} in {path}.")
    return path


REQUEST = re.compile(r"^#{1,3} (?:My request(?: for Codex)?|My comment|User request):[ \t]*\r?(?:\n|$)",
                     re.MULTILINE | re.IGNORECASE)
ANNOTATIONS = re.compile(r"<response-annotations>(.*?)</response-annotations>", re.DOTALL)
AMBIENT = re.compile(r"<in-app-browser-context\b[^>]*>.*?</in-app-browser-context>", re.DOTALL)
QUOTED = re.compile(
    r"^(?:[ \t]{0,3}>[^\n]*(?:\n|$))+|^[ ]{0,3}(?P<fence>\x60{3,}|~{3,})[^\n]*\n"
    r"[\s\S]*?^[ ]{0,3}(?P=fence)[ \t]*\r?(?:\n|$)", re.MULTILINE)
CONTEXT_HEADINGS = ("# response annotations:", "# files mentioned by the user:", "# selected text",
                    "# context from my ide setup:", "<response-annotations>", "<in-app-browser-context")
AUTOMATIC = ("# AGENTS.md instructions", "<environment_context>", "<skill>", "<permissions instructions>",
             "<external_codex_apps_open_page>", "<subagent_notification>", "<codex_delegation>",
             "<turn_aborted>", "<goal_context>")


def _own_words(text):
    start = 0
    for quote in QUOTED.finditer(text):
        if text[start:quote.start()].strip():
            yield text[start:quote.start()]
        start = quote.end()
    if text[start:].strip():
        yield text[start:]


def _render(parts):
    display, words = [], []

    def user(label, text):
        if isinstance(text, str) and text.strip():
            display.append(f"【{label}】\n{text.strip(chr(13) + chr(10))}")
            words.extend(_own_words(text))

    for part in parts:
        if part.get("type") in ("local_image", "image"):
            asset = part.get("path")
            if asset and not any(asset.replace("\\", "/") in s.replace("\\", "/") for s in display):
                display.append(f"【添付ファイル】\n{asset}")
            continue
        if part.get("type") != "text":
            continue
        raw = part.get("text", "")
        text = raw.strip()
        if not text or text.startswith(AUTOMATIC):
            continue
        if text.startswith("<send_user_message_question_reply>"):
            match = re.fullmatch(r"<send_user_message_question_reply>(.*?)</send_user_message_question_reply>",
                                 text, re.DOTALL)
            if not match:
                raise ValueError("Incomplete async question reply in a user event.")
            for item in json.loads(match[1]):
                if item.get("question"):
                    display.append(f"【Codex の質問】\n{item['question']}")
                user("ユーザーの回答", item["answer"])
            continue
        request = REQUEST.search(raw)
        if not text.lower().startswith(CONTEXT_HEADINGS) and not REQUEST.match(text):
            user("ユーザー", raw)
            continue
        context = raw[:request.start()] if request else raw
        annotations = ANNOTATIONS.search(context)
        if annotations:
            for item in json.loads(annotations[1]):
                if item.get("text"):
                    display.append(f"【選択された文章】\n{item['text']}")
                refs = {k: v for k, v in item.items() if k not in ("text", "annotation")}
                if refs:
                    display.append("【注釈の参照先】\n" + json.dumps(refs, ensure_ascii=False))
                user("ユーザーの注釈", item.get("annotation"))
            context = context[annotations.end():]
        elif "<response-annotations>" in context or text.lower().startswith("# response annotations:"):
            raise ValueError("Incomplete response annotations in a user event.")
        context = AMBIENT.sub("", context).strip()
        if context.lower().startswith("# files mentioned by the user:"):
            for file in re.findall(r"^## (.+)$", context, re.MULTILINE):
                display.append(f"【添付ファイル】\n{file.rstrip()}")
        elif context:
            if not request and annotations:
                user("ユーザー", context)
            else:
                display.append(f"【参照箇所】\n{context}")
        if request:
            user("ユーザーの依頼", raw[request.end():])
    return "\n\n".join(display), tuple(words)


def _item(row, raw, start, end):
    if row.get("type") != "event_msg":
        return None
    p = row["payload"]
    if p.get("type") == "item_completed" and p.get("item", {}).get("type") == "UserMessage":
        record = p["item"]
        parts = record["content"]
    elif p.get("type") == "user_message":
        record = p
        parts = [{"type": "text", "text": p["message"]}]
        parts.extend({"type": "local_image", "path": path} for path in p.get("local_images", []))
    else:
        return None
    text, words = _render(parts)
    identifier = record.get("id") or f"legacy-{start}-{hashlib.sha256(raw).hexdigest()[:20]}"
    return Message(identifier, text, words, start, end, row.get("timestamp", ""))


def readable_end(path):
    """Return the end of the last complete JSONL line, even during an append."""
    with Path(path).open("rb") as f:
        edge = f.seek(0, 2)
        while edge:
            begin = max(0, edge - 65536)
            f.seek(begin)
            index = f.read(edge - begin).rfind(b"\n")
            if index >= 0:
                return begin + index + 1
            edge = begin
    return 0


def _at_boundary(f, offset):
    if offset == 0:
        return True
    f.seek(offset - 1)
    return f.read(1) == b"\n"


def _response_user(row):
    """Detect a raw model-input mirror so an event-less backend cannot appear empty."""
    p = row.get("payload", {})
    if row.get("type") != "response_item" or p.get("type") != "message" or p.get("role") != "user":
        return False
    kinds = (p.get("internal_chat_message_metadata_passthrough") or {}).get("content_item_kinds")
    if kinds is not None:
        return "user.text" in kinds or "user.image" in kinds
    return any(c.get("type") == "input_text" and c.get("text", "").strip() and
               not c["text"].lstrip().startswith(AUTOMATIC) for c in p.get("content", []))


def messages(path, start=0, stop=None):
    """Read user events at byte boundaries in [start, stop), once per actual user input."""
    stop = readable_end(path) if stop is None else stop
    with Path(path).open("rb") as f:
        if not 0 <= start <= stop or not _at_boundary(f, start) or not _at_boundary(f, stop):
            raise ValueError(f"Invalid rollout byte interval [{start}, {stop}).")
        f.seek(start)
        pending = False
        while start < stop:
            raw = f.readline(stop - start)
            if not raw.endswith(b"\n"):
                raise ValueError(f"Rollout changed during read at byte {start}.")
            end = start + len(raw)
            if raw.strip():
                row = json.loads(raw)
                item = _item(row, raw, start, end)
                if item:
                    pending = False
                    if item.text:
                        yield item
                elif _response_user(row):
                    if pending:
                        raise ValueError("Rollout has user input without matching completed user events.")
                    pending = True
            start = end
        if pending:
            raise ValueError("User input lacks a completed user event. Retry an active thread or check its format.")


def validate(path, start, end, message_id):
    """Check the specific saved record, without reading the conversation before or after it."""
    if not 0 <= start < end:
        return False
    with Path(path).open("rb") as f:
        if not _at_boundary(f, start):
            return False
        f.seek(start)
        raw = f.readline(end - start)
    if len(raw) != end - start or not raw.endswith(b"\n"):
        return False
    try:
        item = _item(json.loads(raw), raw, start, end)
    except (ValueError, KeyError, TypeError):
        return False
    return bool(item and item.text and item.id == message_id)
