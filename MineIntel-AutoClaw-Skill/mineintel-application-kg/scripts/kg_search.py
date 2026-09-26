#!/usr/bin/env python3
"""Query the MineIntel application knowledge graph in Neo4j."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

from neo4j_store import InfrastructureError, load_driver, parse_json_object, safe_identifier


def fulltext_query(text: str) -> str:
    cleaned = re.sub(r"[+\-!(){}\[\]^\"~*?:\\/]", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        raise InfrastructureError("查询不包含可检索内容。")
    return cleaned


def node_result(properties: dict[str, Any], score: float) -> dict[str, Any]:
    return {
        "score": round(float(score), 6),
        "id": properties.get("id"),
        "type": properties.get("type"),
        "name": properties.get("name"),
        "attributes": parse_json_object(properties.get("attributes_json")),
    }


def search(query: str, limit: int, min_score: float) -> dict[str, Any]:
    if limit < 1:
        raise InfrastructureError("limit 必须大于 0。")
    driver, config = load_driver()
    database = config["database"]
    index_name = safe_identifier(config["entity_search_index"])
    try:
        seed_records, _, _ = driver.execute_query(
            """
            CALL db.index.fulltext.queryNodes($index_name, $query, {limit: $limit})
            YIELD node, score
            WHERE node:Entity AND score >= $min_score
            RETURN properties(node) AS node, score
            ORDER BY score DESC
            """,
            index_name=index_name,
            query=fulltext_query(query),
            limit=limit,
            min_score=min_score,
            database_=database,
        )
        matched_nodes = [node_result(record["node"], record["score"]) for record in seed_records]
        seed_ids = [node["id"] for node in matched_nodes if node.get("id")]
        related_edges: list[dict[str, Any]] = []
        if seed_ids:
            edge_records, _, _ = driver.execute_query(
                """
                MATCH (seed:Entity)-[rel]-(neighbor:Entity)
                WHERE seed.id IN $seed_ids
                RETURN seed.id AS seed_id,
                       properties(startNode(rel)) AS source,
                       type(rel) AS relation,
                       properties(endNode(rel)) AS target,
                       rel.confidence AS confidence,
                       rel.evidence_json AS evidence_json
                ORDER BY coalesce(rel.confidence, 0.0) DESC
                LIMIT $edge_limit
                """,
                seed_ids=seed_ids,
                edge_limit=int(config["max_related_edges"]),
                database_=database,
            )
            for record in edge_records:
                source = record["source"]
                target = record["target"]
                related_edges.append(
                    {
                        "seed_id": record["seed_id"],
                        "source": source.get("name", source.get("id")),
                        "source_type": source.get("type", ""),
                        "relation": record["relation"].lower(),
                        "target": target.get("name", target.get("id")),
                        "target_type": target.get("type", ""),
                        "confidence": record["confidence"],
                        "evidence": parse_json_object(record["evidence_json"]),
                    }
                )
    except Exception as exc:
        raise InfrastructureError(f"Neo4j 图查询失败：{exc}") from exc
    finally:
        driver.close()
    return {
        "status": "success",
        "source": "neo4j",
        "database": database,
        "query": query,
        "matched_nodes": matched_nodes,
        "related_edges": related_edges,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--min-score", type=float, default=0.1)
    args = parser.parse_args()
    try:
        result = search(args.query, args.limit, args.min_score)
    except InfrastructureError as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
