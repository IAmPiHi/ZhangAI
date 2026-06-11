# -*- coding: utf-8 -*-
from _common import resolve

SKILL = {
    "name": "list_files",
    "desc": "List files and subfolders in a directory",
    "params": {"path": "directory path (empty = project root)"},
}


def run(args):
    folder = resolve(args.get("path", ""))
    if not folder.is_dir():
        return {"ok": False, "text": f"directory not found: {folder}"}
    rows = []
    for p in sorted(folder.iterdir()):
        tag = "[DIR]" if p.is_dir() else f"{p.stat().st_size:,} B"
        rows.append(f"{p.name}\t{tag}")
    return {"ok": True, "text": f"{folder}:\n" + ("\n".join(rows) or "(empty folder)"