# -*- coding: utf-8 -*-
import math

SKILL = {
    "name": "calc",
    "desc": "數學計算(支援 sin/cos/sqrt/log 等)",
    "params": {"expression": "數學運算式"},
}


def run(args):
    expr = args.get("expression", "")
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed.update({"abs": abs, "round": round, "min": min, "max": max})
    try:
        val = eval(expr, {"__builtins__": {}}, allowed)
        return {"ok": True, "text": f"{expr} = {val}"}
    except Exception as e:
        return {"ok": False, "text": f"計算失敗: {e}"}
