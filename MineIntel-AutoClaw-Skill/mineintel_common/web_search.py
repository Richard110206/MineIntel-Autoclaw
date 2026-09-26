#!/usr/bin/env python3
"""MineIntel 共享的 AutoGLM 网页搜索客户端。

凭据必须通过环境变量显式提供（AUTOGLM_APP_ID / AUTOGLM_APP_KEY）；
token 与 API 地址默认读取 config/infrastructure.json，可用环境变量覆盖。
检索失败时显式报错，不返回任何兜底数据。

命令行入口：``python -m mineintel_common.web_search "<query>" --max-results 5``
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


def search_config() -> dict[str, str]:
    config = load_infrastructure()["web_search"]
    values = {
        "app_id": os.getenv("AUTOGLM_APP_ID", ""),
        "app_key": os.getenv("AUTOGLM_APP_KEY", ""),
        "token_url": os.getenv("AUTOGLM_TOKEN_URL", config["token_url"]),
        "api_url": os.getenv("AUTOGLM_WEB_SEARCH_URL", config["api_url"]),
    }
    missing = [name for name in ("app_id", "app_key") if not values[name]]
    if missing:
        env_names = ", ".join(f"AUTOGLM_{name.upper()}" for name in missing)
        raise RuntimeError(f"AutoGLM 搜索凭据未配置：{env_names}")
    return values


def sign(app_id: str, timestamp: int, app_key: str) -> str:
    raw = f"{app_id}&{timestamp}&{app_key}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def get_token(token_url: str, timeout: int) -> str:
    req = urllib.request.Request(token_url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        token = resp.read().decode("utf-8").strip()
    if not token:
        raise RuntimeError("AutoGLM token service returned an empty token")
    return token if token.lower().startswith("bearer ") else f"Bearer {token}"


def normalize_response(data: dict[str, Any], query: str, max_results: int) -> dict[str, Any]:
    pages: list[dict[str, str]] = []
    for block in data.get("data", {}).get("results", []):
        for item in block.get("webPages", {}).get("value", []):
            url = item.get("url") or ""
            title = item.get("name") or item.get("title") or ""
            if not url or not title:
                continue
            pages.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": item.get("snippet") or item.get("summary") or "",
                }
            )
    return {
        "status": "success",
        "source": "autoglm-web-search",
        "query": query,
        "count": min(len(pages), max_results),
        "results": pages[:max_results],
        "raw_status": data.get("status") or data.get("code"),
    }


def web_search(query: str, max_results: int, timeout: int) -> dict[str, Any]:
    if not query.strip():
        raise ValueError("Search query must not be empty")
    config = search_config()
    token = get_token(config["token_url"], timeout)
    timestamp = int(time.time())
    payload = json.dumps({"queries": [{"query": query}]}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(config["api_url"], data=payload, method="POST")
    req.add_header("Authorization", token)
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Auth-Appid", config["app_id"])
    req.add_header("X-Auth-TimeStamp", str(timestamp))
    req.add_header("X-Auth-Sign", sign(config["app_id"], timestamp, config["app_key"]))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return normalize_response(data, query=query, max_results=max_results)


def main() -> int:
    parser = argparse.ArgumentParser(description="Authenticated AutoGLM web-search primitive with explicit failure semantics.")
    parser.add_argument("query")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()
    try:
        result = web_search(args.query, args.max_results, args.timeout)
    except (OSError, ValueError, RuntimeError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "query": args.query, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
