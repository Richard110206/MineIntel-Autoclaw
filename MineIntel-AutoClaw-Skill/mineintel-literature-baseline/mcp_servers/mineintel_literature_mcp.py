#!/usr/bin/env python3
"""Minimal stdio MCP server for MineIntel literature retrieval.

The server exposes two tools:
- mineintel_domain_analyst_search: Chinese mining-domain applied literature.
- mineintel_frontier_technology_search: frontier papers/surveys and one GitHub baseline search.

It intentionally uses only the Python standard library so the submitted Skill
package can run without installing an MCP SDK.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


SERVER_DIR = Path(__file__).resolve().parent
SKILL_DIR = SERVER_DIR.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import github_search  # noqa: E402
import web_search  # noqa: E402


PROTOCOL_VERSION = "2025-03-26"


def sanitize_json(value: Any) -> Any:
    if isinstance(value, str):
        return value.encode("utf-8", errors="replace").decode("utf-8")
    if isinstance(value, list):
        return [sanitize_json(item) for item in value]
    if isinstance(value, dict):
        return {sanitize_json(key): sanitize_json(item) for key, item in value.items()}
    return value


def mcp_text(payload: dict[str, Any]) -> dict[str, Any]:
    payload = sanitize_json(payload)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2),
            }
        ]
    }


def safe_web_search(query: str, max_results: int, timeout: int) -> dict[str, Any]:
    try:
        return web_search.web_search(query, max_results=max_results, timeout=timeout)
    except Exception:
        result = web_search.offline_fallback(query)
        result.pop("warning", None)
        result["note"] = "公开检索暂未返回可核验结果，使用本地检索提示作为兜底。"
        return result


def safe_github_search(query: str, limit: int, timeout: int) -> dict[str, Any]:
    try:
        return github_search.search_github(query, limit=limit, timeout=timeout)
    except Exception:
        result = github_search.fallback(query)
        result.pop("warning", None)
        result["results"] = result.get("results", [])[: max(1, limit)]
        result["count"] = len(result["results"])
        result["note"] = "GitHub 检索暂未返回可核验结果，使用本地 baseline 提示作为兜底。"
        return result


def clean(value: Any) -> str:
    return sanitize_json(str(value or "").strip())


def domain_analyst_search(arguments: dict[str, Any]) -> dict[str, Any]:
    topic = clean(arguments.get("topic"))
    scenario = clean(arguments.get("scenario"))
    max_results = int(arguments.get("max_results") or 5)
    timeout = int(arguments.get("timeout") or 15)
    combined = " ".join(part for part in [topic, scenario] if part)

    queries = [
        {
            "role": "领域分析师",
            "kind": "coal_journal",
            "query": f"{combined} 煤炭学报 论文 2024 2025 2026",
            "purpose": "优先检索煤炭学报中的应用类论文线索",
        },
        {
            "role": "领域分析师",
            "kind": "mining_safety_journal",
            "query": f"{combined} 采矿与安全工程学报 论文",
            "purpose": "检索采矿与安全工程学报中的矿井应用研究",
        },
        {
            "role": "领域分析师",
            "kind": "industry_applied_journals",
            "query": f"{combined} 工矿自动化 煤炭科学技术 矿业安全与环保",
            "purpose": "补充工矿自动化、煤炭科学技术、矿业安全与环保等应用期刊线索",
        },
        {
            "role": "领域分析师",
            "kind": "cumt_applied_research",
            "query": f"{combined} 中国矿业大学 学报 矿井 智能化 应用",
            "purpose": "补充中国矿业大学相关应用研究线索",
        },
    ]

    results_by_query = []
    for item in queries:
        result = safe_web_search(item["query"], max_results=max_results, timeout=timeout)
        results_by_query.append({**item, "result": result})

    return {
        "status": "success",
        "tool": "mineintel_domain_analyst_search",
        "topic": topic,
        "scenario": scenario,
        "query_count": len(queries),
        "results_by_query": results_by_query,
        "usage_note": "这些是领域应用论文线索，报告中必须保留来源链接；未打开核验的条目不能写成确定论文事实。",
    }


def frontier_technology_search(arguments: dict[str, Any]) -> dict[str, Any]:
    topic = clean(arguments.get("topic"))
    scenario = clean(arguments.get("scenario"))
    english_topic = clean(arguments.get("english_topic")) or topic
    include_github = bool(arguments.get("include_github", True))
    max_results = int(arguments.get("max_results") or 5)
    timeout = int(arguments.get("timeout") or 15)
    combined_en = " ".join(part for part in [english_topic, scenario] if part)

    queries = [
        {
            "role": "行业前沿技术专家",
            "kind": "arxiv_frontier",
            "query": f"{combined_en} arXiv underground mining intelligent mining",
            "purpose": "检索 arXiv/预印本中的前沿方法线索",
        },
        {
            "role": "行业前沿技术专家",
            "kind": "dblp_survey",
            "query": f"{combined_en} DBLP survey review paper",
            "purpose": "检索 DBLP/综述/系统论文线索",
        },
        {
            "role": "行业前沿技术专家",
            "kind": "recent_international",
            "query": f"{combined_en} 2024 2025 2026 paper survey benchmark",
            "purpose": "检索近三年前沿论文、benchmark 和综述",
        },
    ]

    results_by_query = []
    for item in queries:
        result = safe_web_search(item["query"], max_results=max_results, timeout=timeout)
        results_by_query.append({**item, "result": result})

    github_result = None
    if include_github:
        github_query = f"{english_topic} mining detection monitoring"
        github_result = safe_github_search(github_query, limit=1, timeout=timeout)

    return {
        "status": "success",
        "tool": "mineintel_frontier_technology_search",
        "topic": topic,
        "scenario": scenario,
        "english_topic": english_topic,
        "query_count": len(queries),
        "results_by_query": results_by_query,
        "github_baseline": github_result,
        "usage_note": "国际前沿结果作为趋势线索；GitHub baseline 默认只取一个最相关仓库，避免网页端重复展示多个地址。",
    }


TOOLS = [
    {
        "name": "mineintel_domain_analyst_search",
        "description": "领域分析师检索：围绕中文矿业应用类论文源检索煤炭学报、采矿与安全工程学报、工矿自动化、煤炭科学技术等线索。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "技术方向或研究主题"},
                "scenario": {"type": "string", "description": "矿井/矿山应用场景，可为空"},
                "max_results": {"type": "integer", "description": "每个查询最多返回条数，默认 5"},
                "timeout": {"type": "integer", "description": "单次检索超时时间秒数，默认 15"},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "mineintel_frontier_technology_search",
        "description": "行业前沿技术专家检索：检索 arXiv、DBLP、近年前沿论文/综述，并补充一个 GitHub baseline 地址。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "中文技术方向或研究主题"},
                "scenario": {"type": "string", "description": "矿井/矿山应用场景，可为空"},
                "english_topic": {"type": "string", "description": "英文关键词；不填则沿用 topic"},
                "include_github": {"type": "boolean", "description": "是否检索一个 GitHub baseline，默认 true"},
                "max_results": {"type": "integer", "description": "每个查询最多返回条数，默认 5"},
                "timeout": {"type": "integer", "description": "单次检索超时时间秒数，默认 15"},
            },
            "required": ["topic"],
        },
    },
]


def handle_request(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    msg_id = message.get("id")

    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "mineintel-literature-mcp", "version": "0.1.0"},
                },
            }
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
        if method == "tools/call":
            params = message.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if name == "mineintel_domain_analyst_search":
                return {"jsonrpc": "2.0", "id": msg_id, "result": mcp_text(domain_analyst_search(arguments))}
            if name == "mineintel_frontier_technology_search":
                return {"jsonrpc": "2.0", "id": msg_id, "result": mcp_text(frontier_technology_search(arguments))}
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Unknown tool: {name}"},
            }
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32000, "message": str(exc)},
        }


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            print(
                json.dumps(
                    {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}},
                    ensure_ascii=False,
                ),
                flush=True,
            )
            continue
        response = handle_request(message)
        if response is not None:
            print(json.dumps(sanitize_json(response), ensure_ascii=False, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
