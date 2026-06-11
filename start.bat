@echo off
setlocal
REM ============================================================
REM  ZHANGAI - Local AI Console launcher (single terminal)
REM  server.py serves the UI on :8080 and spawns llama-server
REM  on :8090 with its native web UI disabled. All logs here.
REM
REM  Folder layout:
REM    llama\llama-server.exe   inference engine
REM    model\main.gguf          language model  (swap freely)
REM    model\mmproj.gguf        vision projector (optional)
REM    front\index.html         web UI
REM    server.py                backend
REM ============================================================
set "ZHANGAI_LLAMA=%~dp0llama\llama-server.exe"
set "ZHANGAI_MODEL=%~dp0model\main.gguf"
set "ZHANGAI_MMPROJ=%~dp0model\mmproj.gguf"
set "ZHANGAI_CTX=8192"
set "ZHANGAI_NGL=99"
REM Extra engine args, e.g. parallel /think debates:
REM set "ZHANGAI_LLAMA_ARGS=-np 4 -c 32768"

if not exist "%ZHANGAI_LLAMA%" (
  echo  [ERROR] llama\llama-server.exe not found.
  echo  Run setup_llama.bat first - it auto-detects your GPU and
  echo  downloads the matching llama.cpp build.
  pause
  exit /b 1
)
if not exist "%ZHANGAI_MODEL%" (
  echo  [ERROR] model\main.gguf not found.
  echo  Run download_model.bat or place your own GGUF there.
  pause
  exit /b 1
)
where python >nul 2>nul
if errorlevel 1 (
  echo  [ERROR] python not found in PATH. Install Python 3 first.
  pause
  exit /b 1
)

REM selenium is used by /search (headless Google); install once if missing
python -c "import selenium" >nul 2>nul
if errorlevel 1 (
  echo  [setup] installing selenium for /search ...
  python -m pip install selenium --quiet
)

python "%~dp0server.py"

pause
