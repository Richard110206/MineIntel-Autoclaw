#!/usr/bin/env python3
"""AutoGLM Open Link helper for MineIntel Research Skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


APP_ID = os.environ.get("AUTOGLM_APP_ID", "")
APP_KEY = os.environ.get("AUTOGLM_APP_KEY", "")
TOKEN_URL = os.environ.get("AUTOGLM_TOKEN_URL", "http://127.0.0.1:18432/get_token")
API_URL = os.environ.get(
    "AUTOGLM_OPEN_LINK_URL",
    "https://autoglm-api.zhipuai.cn/agentdr/v1/assistant/skills/open-link",
)


def sign(app_id: str, timestamp: int, app_key: str) -> str:
    raw = f"{app_id}&{timestamp}&{app_key}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def get_token(timeout: int = 10) -> str:
    with urllib.request.urlopen(TOKEN_URL, timeout=timeout) as resp:
        token = resp.read().decode("utf-8").strip()
    if not token.lower().startswith("bearer "):
        token = f"Bearer {token}"
    return token


def open_link(url: str, timeout: int) -> dict[str, Any]:
    token = get_token(timeout=timeout)
    timestamp = int(time.time())
    payload = json.dumps({"url": url}, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(API_URL, data=payload, method="POST")
    req.add_header("Authorization", token)
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Auth-Appid", APP_ID)
    req.add_header("X-Auth-TimeStamp", str(timestamp))
    req.add_header("X-Auth-Sign", sign(APP_ID, timestamp, APP_KEY))

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    text = data.get("data", {}).get("text") or data.get("data", {}).get("content") or ""
    title = data.get("data", {}).get("title") or ""
    return {
        "status": "success",
        "source": "autoglm-open-link",
        "url": url,
        "title": title,
        "text": text[:12000],
        "text_length": len(text),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Open a public URL through AutoGLM.")
    parser.add_argument("url", help="Public URL to read")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    try:
        result = open_link(args.url, timeout=args.timeout)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        result = {"status": "error", "url": args.url, "error": str(exc)}

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
