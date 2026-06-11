# -*- coding: utf-8 -*-
import re
import zipfile
from html import unescape
from _common import resolve

SKILL = {
    "name": "docx_read",
    "desc": "讀取 Word(.docx) 文件的文字內容",
    "params": {"path": "檔案路徑"},
}


def run(args):
    p = resolve(args.get("path", ""))
    if not p.is_file():
        return {"ok": False, "text": f"檔案不存在: {p}"}
    with zipfile.ZipFile(p) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    xml = xml.replace("</w:p>", "\n")
    text = unescape(re.sub(r"<[^>]+>", "", xml)).strip()
    return {"ok": True, "text": text[:8000] or "(文件無文字內容)"}
