# -*- coding: utf-8 -*-
"""Shared helpers for ZHANGAI skills."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # project root
GEN_DIR = ROOT / "generated"
GEN_DIR.mkdir(exist_ok=True)

# Sandbox flag - set per-request by server.py from the user's settings.
# When False (default) skills may only touch files inside the project folder.
ALLOW_ABS = False


def resolve(p: str) -> Path:
    """Resolve a user/model-supplied path with sandbox enforcement."""
    path = Path(p or ".")
    if path.is_absolute():
        if ALLOW_ABS:
            return path
        raise PermissionError(
            "absolute paths are disabled - enable 'Allow skills outside "
            "project folder' in Settings to use them")
    full = (ROOT / path).resolve()
    if not str(full).startswith(str(ROOT.resolve())):
        raise PermissionError("path escapes the project folder")
    return full
