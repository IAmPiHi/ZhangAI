# -*- coding: utf-8 -*-
import base64
import json
import time
import urllib.request
from _common import GEN_DIR

SD_API = "http://127.0.0.1:7860"   # Stable Diffusion WebUI (A1111), start with --api

SKILL = {
    "name": "gen_image",
    "desc": "Generate an image with Stable Diffusion (requires A1111 WebUI running with --api)",
    "params": {"prompt": "image description in English", "negative_prompt": "(optional)",
               "width": "(optional)", "height": "(optional)"},
}


def run(args):
    prompt = args.get("prompt", "")
    if not prompt:
        return {"ok": False, "text": "missing 'prompt'"}
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
        return {"ok": True, "text": f"image generated: generated/{name}",
                "image_url": f"/generated/{name}"}
    except Exception as e:
        return {"ok": False,
                "text": f"cannot reach Stable Diffusion WebUI ({SD_API}). "
                        f"Install A1111 and start it with --api. Error: {e}"}