# -*- coding: utf-8 -*-
import base64
import json
import time
import urllib.request
from _common import GEN_DIR

SD_API = "http://127.0.0.1:7860"   # Stable Diffusion WebUI (A1111), start with --api

SKILL = {
    "name": "gen_image",
    "desc": "用 Stable Diffusion 生成圖片(需另外安裝 A1111 WebUI 並以 --api 啟動)",
    "params": {"prompt": "英文圖片描述", "negative_prompt": "(選填)",
               "width": "(選填)", "height": "(選填)"},
}


def run(args):
    prompt = args.get("prompt", "")
    if not prompt:
        return {"ok": False, "text": "缺少 prompt"}
    payload = json.dumps({
        "prompt": prompt,
        "negative_prompt": args.get("negative_prompt", ""),
        "steps": int(args.get("steps", 25)),
        "width": int(args.get("width", 768)),
        "height": int(args.get("height", 768)),
    }).encode("utf-8")
    req = urllib.request.Request(SD_API + "/sdapi/v1/txt2img", data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            data = json.loads(r.read().decode("utf-8"))
        img = base64.b64decode(data["images"][0])
        name = f"img-{int(time.time())}.png"
        (GEN_DIR / name).write_bytes(img)
        return {"ok": True, "text": f"圖片已生成並存於 generated/{name}",
                "image_url": f"/generated/{name}"}
    except Exception as e:
        return {"ok": False,
                "text": f"無法連到 Stable Diffusion WebUI ({SD_API})。"
                        f"請先安裝並以 --api 參數啟動 A1111。錯誤: {e}"}
