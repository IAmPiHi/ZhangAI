#!/usr/bin/env bash
# ============================================================
#  ZHANGAI - default model downloader (macOS / Linux)
#  Model: HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive
#  License: apache-2.0 | supports vision via mmproj
# ============================================================
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="https://huggingface.co/HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive/resolve/main"
NAME="Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive"
mkdir -p "$DIR/model"

echo
echo "  Pick a quantization (smaller = less RAM/VRAM, lower quality):"
echo
echo "    1. IQ2_M   11.7 GB  (~12 GB, minimum)"
echo "    2. IQ3_M   15.4 GB  (~16 GB, recommended)"
echo "    3. IQ4_XS  18.7 GB  (~20 GB)"
echo "    4. Q4_K_M  21.2 GB  (~24 GB)"
echo "    5. Q5_K_P  28.0 GB  (~32 GB)"
echo
read -r -p "  Enter 1-5 [2]: " PICK
case "${PICK:-2}" in
  1) QUANT="IQ2_M" ;;
  2) QUANT="IQ3_M" ;;
  3) QUANT="IQ4_XS" ;;
  4) QUANT="Q4_K_M" ;;
  5) QUANT="Q5_K_P" ;;
  *) echo "  Invalid choice."; exit 1 ;;
esac

echo
echo "  Downloading $NAME-$QUANT.gguf -> model/main.gguf"
echo "  (resume supported - rerun this script if interrupted)"
curl -L -C - -o "$DIR/model/main.gguf" "$BASE/$NAME-$QUANT.gguf"

echo
echo "  Downloading vision projector (899 MB) -> model/mmproj.gguf"
curl -L -C - -o "$DIR/model/mmproj.gguf" "$BASE/mmproj-$NAME-f16.gguf"

echo
echo "  Done! Now run ./start.sh"
