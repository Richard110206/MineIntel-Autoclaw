#!/usr/bin/env python3
"""Compatibility wrapper: the canonical AutoGLM open-link client lives in mineintel_common."""

from __future__ import annotations

import sys
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parents[2]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from mineintel_common.open_link import main, open_link  # noqa: E402,F401

if __name__ == "__main__":
    sys.exit(main())
