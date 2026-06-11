# -*- coding: utf-8 -*-
from _common import resolve

SKILL = {
    "name": "write_text",
    "desc": "寫入/建立文字檔",
    "params": {"path": "檔案路徑", "content": "內容"},
}


def run(args):
    p = resolve(args.get("path", ""))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(args.get("content", ""), encoding="utf-8")
    return {"ok": True, "text": f"已寫入 {p}"}
