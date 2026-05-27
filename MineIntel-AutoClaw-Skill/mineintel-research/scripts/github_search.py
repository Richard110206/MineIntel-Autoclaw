#!/usr/bin/env python3
"""GitHub repository search helper for MineIntel Research Skill."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


GITHUB_API = "https://api.github.com/search/repositories"


def search_github(query: str, limit: int, timeout: int) -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": max(1, min(limit, 10)),
        }
    )
    req = urllib.request.Request(f"{GITHUB_API}?{params}", method="GET")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "mineintel-research-skill")

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    repos = []
    for item in data.get("items", [])[:limit]:
        repos.append(
            {
                "name": item.get("full_name"),
                "url": item.get("html_url"),
                "description": item.get("description") or "",
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language") or "",
                "updated_at": item.get("updated_at") or "",
                "topics": item.get("topics", []),
            }
        )

    return {
        "status": "success",
        "source": "github-api",
        "query": query,
        "count": len(repos),
        "results": repos,
    }


def fallback(query: str) -> dict[str, Any]:
    return {
        "status": "fallback",
        "source": "local-fallback",
        "query": query,
        "warning": "GitHub API unavailable. Use these as search-query hints, not verified repositories.",
        "results": [
            {
                "name": "ultralytics/ultralytics",
                "url": "https://github.com/ultralytics/ultralytics",
                "description": "YOLO vision models that can be adapted for mine-object detection baselines.",
                "stars": None,
                "language": "Python",
                "updated_at": "",
                "topics": ["object-detection", "yolo", "computer-vision"],
            },
            {
                "name": "open-mmlab/mmdetection",
                "url": "https://github.com/open-mmlab/mmdetection",
                "description": "General object detection toolbox, suitable for custom underground mining datasets.",
                "stars": None,
                "language": "Python",
                "updated_at": "",
                "topics": ["detection", "pytorch", "baseline"],
            },
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Search GitHub repositories.")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--no-fallback", action="store_true")
    args = parser.parse_args()

    try:
        result = search_github(args.query, limit=args.limit, timeout=args.timeout)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        result = {"status": "error", "query": args.query, "error": str(exc)} if args.no_fallback else fallback(args.query)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
