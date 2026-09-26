"""Shared configuration loading and path-display helpers for MineIntel."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PACKAGE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = PACKAGE_DIR / "config" / "infrastructure.json"


def load_infrastructure() -> dict[str, Any]:
    """Load config/infrastructure.json; missing file is an explicit error."""
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"缺少基础设施配置：{display_path(CONFIG_PATH)}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    """对外输出统一使用相对包根的路径，避免泄露本机目录结构。"""
    try:
        return path.resolve().relative_to(PACKAGE_DIR).as_posix()
    except ValueError:
        return path.as_posix()
