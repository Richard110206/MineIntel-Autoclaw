#!/usr/bin/env python3
"""Open the MineIntel demo UI in the system browser."""

from __future__ import annotations

import json
import sys
import webbrowser
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


BASE_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = BASE_DIR.parent
UI_PATH = PACKAGE_DIR / "demo-ui" / "index.html"


def main() -> int:
    if not UI_PATH.exists():
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": "demo-ui/index.html not found",
                    "expected_path": str(UI_PATH),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    url = UI_PATH.resolve().as_uri()
    opened = webbrowser.open(url, new=1, autoraise=True)
    print(
        json.dumps(
            {
                "status": "success" if opened else "warning",
                "ui_path": str(UI_PATH.resolve()),
                "url": url,
                "message": "已请求系统浏览器打开 MineIntel 演示控制台。" if opened else "浏览器未确认打开，请手动打开 ui_path。",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
