#!/usr/bin/env python3
"""MineIntel 共享的 AutoGLM 网页阅读客户端。

凭据必须通过环境变量显式提供（AUTOGLM_APP_ID / AUTOGLM_APP_KEY），
不内置任何默认凭据；token 与 API 地址默认读取 config/infrastructure.json。
打开失败时显式报错，不返回兜底数据。

命令行入口：``python -m mineintel_common.open_link "<url>" --timeout 30``
"""

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

from .config import load_infrastructure


def open_link_config() -> dict[str, str]:
    config = load_infrastructure()["open_link"]
    values = {
        "app_id": os.getenv("AUTOGLM_APP_ID", ""),
        "app_key": os.getenv("AUTOGLM_APP_KEY", ""),
        "token_url": os.getenv("AUTOGLM_TOKEN_URL", config["token_url"]),
        "api_url": os.getenv("AUTOGLM_OPEN_LINK_URL", config["api_url"]),
    }
    missing = [name for name in ("app_id", "app_key") if not values[name]]
    if missing:
        env_names = ", ".join(f"AUTOGLM_{name.upper()}" for name in missing)
        raise RuntimeError(f"AutoGLM 打开网页凭据未配置：{env_names}")
    return values


def sign(app_id: str, timestamp: int, app_key: str) -> str:
    raw = f"{app_id}&{timestamp}&{app_key}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def get_token(token_url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(token_url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        token = resp.read().decode("utf-8").strip()
    if not token:
        raise RuntimeError("AutoGLM token service returned an empty token")
    return token if token.lower().startswith("bearer ") else f"Bearer {token}"


def open_link(url: str, timeout: int) -> dict[str, Any]:
    config = open_link_config()
    token = get_token(config["token_url"], timeout=timeout)
    timestamp = int(time.time())
    payload = json.dumps({"url": url}, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(config["api_url"], data=payload, method="POST")
    req.add_header("Authorization", token)
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Auth-Appid", config["app_id"])
    req.add_header("X-Auth-TimeStamp", str(timestamp))
    req.add_header("X-Auth-Sign", sign(config["app_id"], timestamp, config["app_key"]))

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
