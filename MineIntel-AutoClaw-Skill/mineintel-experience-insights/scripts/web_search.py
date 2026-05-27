#!/usr/bin/env python3
"""AutoGLM Web Search helper for MineIntel Research Skill.

This script exposes a small primitive:
query string -> normalized search-result JSON.

It intentionally does not decide the research workflow. The agent should use
SKILL.md to decide when and why to call it.
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


APP_ID = os.environ.get("AUTOGLM_APP_ID", "")
APP_KEY = os.environ.get("AUTOGLM_APP_KEY", "")
TOKEN_URL = os.environ.get("AUTOGLM_TOKEN_URL", "http://127.0.0.1:18432/get_token")
API_URL = os.environ.get(
    "AUTOGLM_WEB_SEARCH_URL",
    "https://autoglm-api.zhipuai.cn/agentdr/v1/assistant/skills/web-search",
)


def sign(app_id: str, timestamp: int, app_key: str) -> str:
    raw = f"{app_id}&{timestamp}&{app_key}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def get_token(timeout: int = 10) -> str:
    req = urllib.request.Request(TOKEN_URL, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        token = resp.read().decode("utf-8").strip()
    if not token:
        raise RuntimeError("AutoGLM token service returned an empty token")
    if not token.lower().startswith("bearer "):
        token = f"Bearer {token}"
    return token


def normalize_response(data: dict[str, Any], query: str, max_results: int) -> dict[str, Any]:
    pages = []

    search_results = data.get("data", {}).get("results", [])
    for block in search_results:
        values = block.get("webPages", {}).get("value", [])
        for item in values:
            pages.append(
                {
                    "title": item.get("name") or item.get("title") or "",
                    "url": item.get("url") or "",
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
    token = get_token(timeout=timeout)
    timestamp = int(time.time())
    payload = json.dumps({"queries": [{"query": query}]}, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(API_URL, data=payload, method="POST")
    req.add_header("Authorization", token)
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Auth-Appid", APP_ID)
    req.add_header("X-Auth-TimeStamp", str(timestamp))
    req.add_header("X-Auth-Sign", sign(APP_ID, timestamp, APP_KEY))

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return normalize_response(data, query=query, max_results=max_results)


def offline_fallback(query: str) -> dict[str, Any]:
    """Return a deterministic fallback so demo flow can continue without token service."""
    return {
        "status": "fallback",
        "source": "local-fallback",
        "query": query,
        "count": 3,
        "warning": "AutoGLM token service or network was unavailable. Results are local demo hints.",
        "results": [
            {
                "title": "煤矿智能化与安全监测公开资料线索",
                "url": "local://sample/mining-safety",
                "snippet": "矿井安全监测常涉及视频识别、传感器融合、井下人员与设备状态识别、灾害预警等方向。",
            },
            {
                "title": "矿井视觉检测方向检索建议",
                "url": "local://sample/vision-mining",
                "snippet": "建议继续检索关键词：煤矿 机器视觉 目标检测 井下 安全帽 皮带异物 2024。",
            },
            {
                "title": "科研报告人工核验提示",
                "url": "local://sample/verify",
                "snippet": "本地 fallback 仅用于演示流程不断裂，论文题名、作者和年份必须以后续公开网页或数据库核验为准。",
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Search public web pages through AutoGLM.")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max-results", type=int, default=5, help="Maximum normalized results")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Return an error instead of local fallback when request fails",
    )
    args = parser.parse_args()

    try:
        result = web_search(args.query, max_results=args.max_results, timeout=args.timeout)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
        if args.no_fallback:
            result = {"status": "error", "query": args.query, "error": str(exc)}
        else:
            result = offline_fallback(args.query)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
