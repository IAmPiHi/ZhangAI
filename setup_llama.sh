#!/usr/bin/env bash
# ============================================================
#  ZHANGAI - llama.cpp auto-installer (macOS / Linux)
#  Downloads the right build from GitHub releases into llama/
# ============================================================
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$DIR/llama"

OS="$(uname -s)"; ARCH="$(uname -m)"

# macOS with Homebrew: easiest path
if [ "$OS" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
  echo "  Homebrew detected -> brew install llama.cpp (Metal accelerated)"
  brew install llama.cpp
  echo "  Done! start.sh will find llama-server in PATH."
  exit 0
fi

case "$OS-$ARCH" in
  Darwin-arm64)  KEY="macos-arm64" ;;
  Darwin-x86_64) KEY="macos-x64" ;;
  Linux-x86_64)  KEY="ubuntu-x64" ;;
  *) echo "  [ERROR] Unsupported platform $OS-$ARCH. Download manually:"
     echo "          https://github.com/ggml-org/llama.cpp/releases/latest"
     exit 1 ;;
esac

PY=python3; command -v "$PY" >/dev/null 2>&1 || PY=python
echo "  Fetching latest release info ($KEY)..."
URL=$(curl -s -H 'User-Agent: ZHANGAI-setup' \
  https://api.github.com/repos/ggml-org/llama.cpp/releases/latest | "$PY" -c "
import sys, json
assets = json.load(sys.stdin)['assets']
m = [a['browser_download_url'] for a in assets if '$KEY' in a['name'] and a['name'].endswith('.zip')]
print(m[0] if m else '')")

if [ -z "$URL" ]; then
  echo "  [ERROR] No matching asset. Download manually into llama/:"
  echo "          https://github.com/ggml-org/llama.cpp/releases/latest"
  exit 1
fi

echo "  Downloading $URL ..."
curl -L -o /tmp/zhangai_llama.zip "$URL"
unzip -o -q /tmp/zhangai_llama.zip -d "$DIR/llama"
rm /tmp/zhangai_llama.zip

# flatten if the zip nested files in a subfolder
if [ ! -x "$DIR/llama/llama-server" ]; then
  FOUND=$(find "$DIR/llama" -name llama-server -type f | head -1)
  [ -n "$FOUND" ] && mv "$(dirname "$FOUND")"/* "$DIR/llama/" 2>/dev/null || true
fi
chmod +x "$DIR/llama/llama-server" 2>/dev/null || true

if [ -x "$DIR/llama/llama-server" ]; then
  echo "  Done! -> llama/llama-server  Now run ./start.sh"
else
  echo "  [ERROR] llama-server still missing - check the llama/ folder."
  exit 1
fi
