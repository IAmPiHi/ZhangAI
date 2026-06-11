# -*- coding: utf-8 -*-
import re
import zipfile
from _common import resolve

SKILL = {
    "name": "docx_replace",
    "desc": "在 Word(.docx) 文件中尋找並取代文字",
    "params": {"path": "檔案路徑", "find": "要找的文字", "replace": "取代為"},
}


def run(args):
    p = resolve(args.get("path", ""))
    find, repl = args.get("find", ""), args.get("replace", "")
    if not p.is_file():
        return {"ok": False, "text": f"檔案不存在: {p}"}
    if not find:
        return {"ok": False, "text": "缺少 find 參數"}
    with zipfile.ZipFile(p) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    count = [0]

    def sub(m):
        count[0] += m.group(2).count(find)
        return m.group(1) + m.group(2).replace(find, repl) + m.group(3)

    new_xml = re.sub(r"(<w:t[^>]*>)(.*?)(</w:t>)", sub, xml, flags=re.S)
    with zipfile.ZipFile(p) as zin:
        items = [(i.filename, zin.read(i.filename)) for i in zin.infolist()]
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in items:
            zout.writestr(name, new_xml.encode("utf-8") if name == "word/document.xml" else data)
    note = "" if count[0] else "(注意: 0 處,若文字被 Word 拆成多段格式可能找不到)"
    return {"ok": True, "text": f"已取代 {count[0]} 處 {note},檔案: {p}"}
