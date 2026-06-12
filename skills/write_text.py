# -*- coding: utf-8 -*-
from _common import resolve

SKILL = {
    "name": "write_text",
    "desc": "Write/create a text file",
    "params": {"path": "file path", "content": "text content"},
}


def run(args):
    p = resolve(args.get("path", ""))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(args.get("content", ""), encoding="utf-8")
    return {"ok": True, "text": f"written: {p}"}
