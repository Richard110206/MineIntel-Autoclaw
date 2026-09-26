#!/usr/bin/env python3
"""Search Zhihu/Xiaohongshu style research-experience references.

The output is intentionally treated as experience clues, not authoritative
technical evidence. Final reports should use it for planning suggestions,
pitfall reminders, and presentation/competition preparation notes.
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
PACKAGE_DIR = SCRIPT_DIR.parents[1]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from mineintel_common import web_search  # noqa: E402


def safe_search(query: str, max_results: int, timeout: int) -> dict[str, Any]:
    try:
        return web_search.web_search(query, max_results=max_results, timeout=timeout)
    except Exception as exc:
        return {"status": "error", "query": query, "error": str(exc), "results": []}


def run(topic: str, scenario: str, max_results: int, timeout: int) -> dict[str, Any]:
    topic = topic.strip()
    scenario = scenario.strip()
    combined_parts = [topic]
    if scenario and scenario not in topic:
        combined_parts.append(scenario)
    combined = " ".join(part for part in combined_parts if part)
    queries = [
        {
            "platform": "知乎",
            "query": f"site:zhihu.com {combined} 大创 科研 选题 经验",
            "purpose": "检索科研选题、大创申报和答辩经验",
        },
        {
            "platform": "小红书",
            "query": f"site:xiaohongshu.com {combined} 大创 科研 经验",
            "purpose": "检索更口语化的项目推进、组队、材料准备经验",
        },
        {
            "platform": "知乎",
            "query": f"site:zhihu.com 大学生创新创业训练计划 科研项目 经验",
            "purpose": "补充通用大创执行和结题经验",
        },
    ]
    groups = []
    error_count = 0
    for item in queries:
        result = safe_search(item["query"], max_results=max_results, timeout=timeout)
        error_count += int(result.get("status") == "error")
        groups.append({**item, "result": result})
    return {
        "status": "success" if error_count == 0 else ("error" if error_count == len(queries) else "partial"),
        "source": "mineintel-experience-search",
        "topic": topic,
        "scenario": scenario,
        "query_count": len(queries),
        "results_by_query": groups,
        "usage_note": "知乎/小红书内容只作为科研经验参考，报告中应与论文、官网和白皮书证据分开写。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Search Zhihu/Xiaohongshu research experience clues.")
    parser.add_argument("topic")
    parser.add_argument("--scenario", default="")
    parser.add_argument("--max-results", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=15)
    args = parser.parse_args()
    result = run(args.topic, args.scenario, args.max_results, args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
