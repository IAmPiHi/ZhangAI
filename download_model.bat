@echo off
setlocal
REM ============================================================
REM  ZHANGAI - default model downloader (Windows)
REM  Model: HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive
REM  License: apache-2.0 | supports vision via mmproj
REM  Uses curl (built into Windows 10+), resume supported (-C -)
REM ============================================================
set "BASE=https://huggingface.co/HauhauCS/Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive/resolve/main"
set "NAME=Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive"
if not exist "%~dp0model" mkdir "%~dp0model"

echo.
echo  Pick a quantization (smaller = less VRAM, lower quality):
echo.
echo    1. IQ2_M   11.7 GB  (~12 GB VRAM, minimum)
echo    2. IQ3_M   15.4 GB  (~16 GB VRAM, recommended)
echo    3. IQ4_XS  18.7 GB  (~20 GB VRAM)
echo    4. Q4_K_M  21.2 GB  (~24 GB VRAM)
echo    5. Q5_K_P  28.0 GB  (~32 GB VRAM)
echo.
set /p PICK="  Enter 1-5 [2]: "
if "%PICK%"=="" set PICK=2
if "%PICK%"=="1" set "QUANT=IQ2_M"
if "%PICK%"=="2" set "QUANT=IQ3_M"
if "%PICK%"=="3" set "QUANT=IQ4_XS"
if "%PICK%"=="4" set "QUANT=Q4_K_M"
if "%PICK%"=="5" set "QUANT=Q5_K_P"
if not defined QUANT (
  echo  Invalid choice.
  pause
  exit /b 1
)

echo.
echo  Downloading %NAME%-%QUANT%.gguf  -^>  model\main.gguf
echo  (resume supported - rerun this script if interrupted)
echo.
curl -L -C - -o "%~dp0model\main.gguf" "%BASE%/%NAME%-%QUANT%.gguf"
if errorlevel 1 (
  echo  [ERROR] download failed. Rerun to resume.
  pause
  exit /b 1
)

echo.
echo  Downloading vision projector (899 MB)  -^>  model\mmproj.gguf
curl -L -C - -o "%~dp0model\mmproj.gguf" "%BASE%/mmproj-%NAME%-f16.gguf"

echo.
echo  Done! Now run start.bat
pause
