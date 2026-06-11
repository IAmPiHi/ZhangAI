@echo off
REM One-time setup: downloads the llama.cpp build matching your GPU.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_llama.ps1"
pause
