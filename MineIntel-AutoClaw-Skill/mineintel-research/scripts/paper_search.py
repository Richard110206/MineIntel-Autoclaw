#!/usr/bin/env python3
"""Paper-search orchestrator for MineIntel Research Skill.

The script expands one research topic into several paper-oriented queries and
reuses web_search.py. It keeps the workflow deterministic while leaving final
judgment and synthesis to AutoClaw/GLM.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import web_search  # noqa: E402


def build_queries(topic: str, scope: str) -> list[dict[str, str]]:
    topic = topic.strip()
    chinese_queries = [
        {
            "kind": "chinese_recent",
            "query": f"{topic} 煤矿 矿井 论文 2024 2025 2026",
            "purpose": "检索近年中文矿业论文线索",
        },
        {
            "kind": "chinese_classic",
            "query": f"{topic} 煤矿 矿井 论文 2020 2021 2022",
            "purpose": "补充经典或早期代表性研究线索",
        },
        {
            "kind": "chinese_journals",
            "query": f"{topic} 煤炭学报 工矿自动化 煤炭科学技术",
            "purpose": "优先触达中文矿业核心期刊与行业期刊线索",
        },
    ]
    international_queries = [
        {
            "kind": "international_paper",
            "query": f"{topic} underground mining safety monitoring paper",
            "purpose": "检索国际矿井安全监测论文线索",
        },
        {
            "kind": "international_survey",
            "query": f"{topic} intelligent mining review survey",
            "purpose": "检索综述、系统框架和前沿趋势线索",
        },
    ]

    if scope == "chinese":
        return chinese_queries
    if scope == "international":
        return international_queries
    return chinese_queries + international_queries


def run_search(topic: str, scope: str, max_results: int, timeout: int) -> dict[str, Any]:
    queries = build_queries(topic, scope)
    groups = []
    fallback_count = 0

    for item in queries:
        try:
            result = web_search.web_search(item["query"], max_results=max_results, timeout=timeout)
        except Exception as exc:  # The fallback is intentional for contest demos.
            result = web_search.offline_fallback(item["query"])
            result["error"] = str(exc)
        if result.get("status") == "fallback":
            fallback_count += 1
        groups.append(
            {
                "kind": item["kind"],
                "purpose": item["purpose"],
                "query": item["query"],
                "result": result,
            }
        )

    return {
        "status": "success" if fallback_count == 0 else "partial_fallback",
        "source": "paper-query-expander",
        "topic": topic,
        "scope": scope,
        "query_count": len(queries),
        "fallback_count": fallback_count,
        "results_by_query": groups,
        "note": "输出是论文检索线索，最终报告中不得把未核验线索写成确定论文事实。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Expand a MineIntel topic into paper-oriented searches.")
    parser.add_argument("topic", help="Research topic")
    parser.add_argument("--scope", choices=["chinese", "international", "all"], default="all")
    parser.add_argument("--max-results", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()

    print(json.dumps(run_search(args.topic, args.scope, args.max_results, args.timeout), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
