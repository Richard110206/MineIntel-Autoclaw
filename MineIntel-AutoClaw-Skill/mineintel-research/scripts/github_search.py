#!/usr/bin/env python3
"""Compatibility wrapper for the literature-baseline Skill (canonical GitHub search)."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


TARGET = Path(__file__).resolve().parents[2] / "mineintel-literature-baseline" / "scripts" / "github_search.py"


if __name__ == "__main__":
    sys.argv[0] = str(TARGET)
    runpy.run_path(str(TARGET), run_name="__main__")
