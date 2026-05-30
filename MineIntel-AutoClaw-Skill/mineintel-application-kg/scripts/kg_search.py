#!/usr/bin/env python3
"""Search the MineIntel application knowledge graph."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
KG_DIR = SCRIPT_DIR.parent / "data" / "kg"


def tokenize(text: str) -> list[str]:
    text = text.lower()
    zh = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    en = re.findall(r"[a-z0-9_+-]{2,}", text)
    tokens: list[str] = []
    for chunk in zh:
        tokens.append(chunk)
        for size in (2, 3, 4):
            tokens.extend(chunk[i : i + size] for i in range(max(0, len(chunk) - size + 1)))
    tokens.extend(en)
    return [t for t in tokens if t.strip()]


def load_graph() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = json.loads((KG_DIR / "kg_nodes.json").read_text(encoding="utf-8"))
    edges = json.loads((KG_DIR / "kg_edges.json").read_text(encoding="utf-8"))
    return nodes, edges


def node_text(node: dict[str, Any]) -> str:
    return json.dumps(node, ensure_ascii=False)


def score_node(node: dict[str, Any], tokens: list[str]) -> int:
    text = node_text(node).lower()
    score = 0
    for token in tokens:
        if token in text:
            score += 1 if len(token) <= 3 else 2
    if node.get("type") == "application_scenario":
        score += 2
    if node.get("attributes", {}).get("curated"):
        score += 2
    return score


def search(query: str, limit: int) -> dict[str, Any]:
    nodes, edges = load_graph()
    tokens = tokenize(query)
    node_by_id = {node["id"]: node for node in nodes}

    scored = []
    for node in nodes:
        score = score_node(node, tokens)
        if score > 0:
            scored.append((score, node))
    scored.sort(key=lambda item: item[0], reverse=True)
    selected = scored[:limit]
    selected_ids = {node["id"] for _, node in selected}

    related_edges = []
    for edge in edges:
        if edge["source"] in selected_ids or edge["target"] in selected_ids:
            source = node_by_id.get(edge["source"], {})
            target = node_by_id.get(edge["target"], {})
            related_edges.append(
                {
                    "source": source.get("name", edge["source"]),
                    "source_type": source.get("type", ""),
                    "relation": edge["relation"],
                    "target": target.get("name", edge["target"]),
                    "target_type": target.get("type", ""),
                    "confidence": edge.get("confidence"),
                    "evidence": edge.get("evidence", {}),
                }
            )
        if len(related_edges) >= limit * 6:
            break

    return {
        "status": "success",
        "query": query,
        "matched_nodes": [
            {
                "score": score,
                "id": node["id"],
                "type": node["type"],
                "name": node["name"],
                "attributes": node.get("attributes", {}),
            }
            for score, node in selected
        ],
        "related_edges": related_edges,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Search MineIntel application knowledge graph.")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    result = json.dumps(search(args.query, args.limit), ensure_ascii=False, indent=2)
    with open("kg_output.json", "w", encoding="utf-8") as f:
        f.write(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
