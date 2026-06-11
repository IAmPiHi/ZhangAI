#!/usr/bin/env bash
# ============================================================
#  ZHANGAI - Local AI Console launcher (macOS / Linux)
#  server.py serves the UI on :8080 and spawns llama-server
#  on :8090 with its native web UI disabled. All logs in this
#  single terminal.
#
#  Folder layout:
#    llama/llama-server        inference engine
#    model/main.gguf           language model  (swap freely)
#    model/mmproj.gguf         vision projector (optional)
#    front/index.html          web UI
#    server.py                 backend
# ============================================================
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

export ZHANGAI_LLAMA="$DIR/llama/llama-server"
export ZHANGAI_MODEL="$DIR/model/main.gguf"
export ZHANGAI_MMPROJ="$DIR/model/mmproj.gguf"
export ZHANGAI_CTX=8192
export ZHANGAI_NGL=99
# Extra engine args, e.g. parallel /think debates:
# export ZHANGAI_LLAMA_ARGS="-np 4 -c 32768"

# fall back to llama-server in PATH (e.g. installed via brew)
if [ ! -x "$ZHANGAI_LLAMA" ]; then
  if command -v llama-server >/dev/null 2>&1; then
    export ZHANGAI_LLAMA="$(command -v llama-server)"
  else
    echo " [ERROR] llama/llama-server not found (and not in PATH)."
    echo "         Run ./setup_llama.sh first - it downloads the right build."
    exit 1
  fi
fi

if [ ! -f "$ZHANGAI_MODEL" ]; then
  echo " [ERROR] model/main.gguf not found."
  echo "         Run ./download_model.sh or place your own GGUF there."
  exit 1
fi

PY=python3
command -v "$PY" >/dev/null 2>&1 || PY=python
if ! command -v "$PY" >/dev/null 2>&1; then
  echo " [ERROR] python3 not found. Install Python 3 first."
  exit 1
fi

# selenium is used by /search (headless Google); install once if missing
if ! "$PY" -c "import selenium" >/dev/null 2>&1; then
  echo " [setup] installing selenium for /search ..."
  "$PY" -m pip install selenium --quiet || true
fi

exec "$PY" "$DIR/server.py"
