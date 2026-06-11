# ZHANGAI · Local AI Console

English | **[繁體中文](README.zh-TW.md)**

> A local LLM console with a cooler interface — like Ollama, but with built-in vision, tool calling, multi-AI debate, web search, and long-term memory.
> Pure llama.cpp + Python standard library + a single-file frontend. No frameworks, no database, zero cloud dependencies.

![main](docs/main.png)

## ✨ Features

- **Dark neon UI** — particle-network background, shimmering logo, rainbow border while generating, token-by-token streaming with live tok/s stats. Interface switchable between English / 中文
- **Vision model support** — drag & drop / paste / upload images; with an mmproj projector the model can see
- **`/skill` tool mode** — the AI can call local tools in `skills/` (read/write DOCX, file ops, math, Stable Diffusion image gen…). Drop in a `.py` file and it becomes a new tool
- **`/think` Super Think** — 4 AI personas (logic / creative / critic / pragmatist) each give their view, then a moderator delivers a Consensus / Disagreement / Final-answer verdict
- **`/search` web search** — headless Chrome searches Google (Bing/DDG fallback); the AI decides whether snippets suffice and only reads full pages when needed, answering with cited sources
- **Long-term memory** — optionally let the AI save facts about you to `memory.json` after each chat, remembered across conversations
- **Chat management** — every conversation auto-saves to `chats/<number>/chat.json`; edit, resend, regenerate, or open another chat in a new window while generating
- **Three model sources** — local llama.cpp / Gemini API / DeepSeek API, switchable in settings
- Command menu (type `/`, Tab to complete), tunable params, system prompt, all settings persisted

## 🚀 Quick Start

Requirements: **Python 3.8+** (Chrome browser additionally needed for `/search`)

```
1. Run setup_llama.bat (Windows) or ./setup_llama.sh (macOS/Linux)
   → auto-detects your GPU (CUDA / Vulkan / CPU / Metal) and downloads the matching llama.cpp

2. Get a model — either:
   a) Run download_model.bat / ./download_model.sh
      → pick a quantization interactively; downloads the default model
        (Qwen3.6-35B, vision-capable, apache-2.0)
   b) Bring your own GGUF, place it in model/ and rename:
      model/main.gguf      ← language model (required)
      model/mmproj.gguf    ← vision projector (optional; no images without it)

3. Run start.bat (Windows) or ./start.sh (macOS/Linux)
   → open http://localhost:8080 in your browser
     (everything runs in one terminal; llama-server is spawned
      automatically on :8090 with its native web UI disabled)
```

### Swapping models

Rename any GGUF to `main.gguf` and drop it into `model/`. Context length and GPU layers are the `CTX` / `NGL` variables at the top of `start.bat` / `start.sh`.

Quantization guide for the default model [HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive](https://huggingface.co/HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive) (selectable in the download script):

| Quant | Size | Suggested VRAM |
|---|---|---|
| IQ2_M | 11.7 GB | ~12 GB (minimum) |
| IQ3_M | 15.4 GB | ~16 GB (recommended) |
| IQ4_XS | 18.7 GB | ~20 GB |
| Q4_K_M | 21.2 GB | ~24 GB |
| Q5_K_P | 28 GB | ~32 GB |

> ⚠️ **About the default model:** it is an *uncensored* community finetune with very few built-in refusals — it may produce content that mainstream assistants would decline. It is intended for local, personal use; **you are solely responsible for how you use it and for complying with your local laws.** Prefer a safety-tuned model? Just drop any standard GGUF into `model/main.gguf` instead.

## 🗂 Project Layout

```
front/index.html   frontend (single file, no build step, built-in EN/ZH i18n)
server.py          backend (Python stdlib: static serving, chat storage, LLM proxy, search, memory)
skills/*.py        tool modules — each file = one tool the AI can call
skills/skills.json tool manifest (auto-generated at startup)
model/             your GGUF models
llama/             llama.cpp engine (auto-downloaded by the setup script)
chats/             conversation history (numbered folders + chat.json)
memory.json        long-term user memory
```

## 🔧 Write Your Own Skill

Drop a `.py` into `skills/` defining `SKILL` and `run()`, restart, done:

```python
SKILL = {
    "name": "hello",
    "desc": "Demo tool: say hello",
    "params": {"name": "who to greet"},
}

def run(args):
    return {"ok": True, "text": f"Hello, {args.get('name','world')}!"}
```

## 🖼 Screenshots

![main](docs/main.png)

*(more screenshots — /think debate, /search — coming soon, see [TODO](TODO.md))*

## 🤝 Contributing

[Issues](../../issues) and [Pull Requests](../../pulls) are welcome — in English or Chinese:

1. Fork the repo and create a branch
2. Commit your changes (please describe what changed and how you tested it)
3. Open a PR — contributions are licensed under the project license

## 📄 License

[ZNC-1.0](LICENSE) — fr