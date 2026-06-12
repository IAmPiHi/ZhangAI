# TODO / Roadmap

## Near-term

- [ ] **Set up Stable Diffusion WebUI (A1111) for the `gen_image` skill**
      Install [AUTOMATIC1111 WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui),
      launch with `--api` on port 7860, then `/skill generate an image of ...` works end-to-end.
      Consider adding a setup script like `setup_sd.bat`.
- [x] Add remaining screenshots to README (`/think` debate panel, `/search` flow) → `docs/`
- [ ] Test `start.sh` + `setup_llama.sh` on a real macOS machine

## Ideas / Backlog

- [ ] More built-in skills (xlsx read/write, pdf text extraction, clipboard)
- [ ] Optional TTS / voice input
- [ ] Per-chat system prompt override
- [ ] Export conversation as Markdown
- [ ] One-click portable package (embed Python runtime)

Contributions welcome — pick an item and open a PR! (see [README](README.md#-contributing))
