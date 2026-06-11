# -*- coding: utf-8 -*-
from _common import resolve

SKILL = {
    "name": "list_files",
    "desc": "列出資料夾中的檔案與子資料夾",
    "params": {"path": "資料夾路徑(留空=E:\\MODEL)"},
}


def run(args):
    folder = resolve(args.get("path", ""))
    if not folder.is_dir():
        return {"ok": False, "text": f"資料夾不存在: {folder}"}
    rows = []
    for p in sorted(folder.iterdir()):
        tag = "[DIR]" if p.is_dir() else f"{p.stat().st_size:,} B"
        rows.append(f"{p.name}\t{tag}")
    return {"ok": True, "text": f"{folder}:\n" + ("\n".join(rows) or "(空資料夾)")}
