#!/usr/bin/env python3
"""Compatibility wrapper for the report-export formatter."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


TARGET = Path(__file__).resolve().parents[2] / "mineintel-report-export" / "scripts" / "format_report.py"


if __name__ == "__main__":
    sys.argv[0] = str(TARGET)
    runpy.run_path(str(TARGET), run_name="__main__")
