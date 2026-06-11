# -*- coding: utf-8 -*-
"""Shared helpers for ZHANGAI skills."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # E:\MODEL
GEN_DIR = ROOT / "generated"
GEN_DIR.mkdir(exist_ok=True)


def resolve(p: str) -> Path:
    """Relative paths are based at ROOT; absolute paths allowed."""
    path = Path(p or ".")
    return path if path.is_absolute() else (ROOT / path)
