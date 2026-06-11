# -*- coding: utf-8 -*-
from _common import resolve

SKILL = {
    "name": "read_text",
    "desc": "讀取文字檔(txt/md/csv/py 等)內容",
    "params": {"path": "檔案路徑"},
}


def run(args):
    p = resolve(args.get("path", ""))
    if not p.is_file():
        return {"ok": False, "text": f"檔案不存在: {p}"}
    return {"ok": True, "text": p.read_text(encoding="utf-8", errors="replace")[:6000]}
