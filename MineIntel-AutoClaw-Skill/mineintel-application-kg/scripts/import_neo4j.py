#!/usr/bin/env python3
"""Upsert the MineIntel graph exchange artifact into Neo4j."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from neo4j_store import (
    InfrastructureError,
    display_path,
    load_driver,
    neo4j_label,
    relationship_type,
    safe_identifier,
)


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = SKILL_DIR / "data" / "kg" / "kg_graph.json"


def batches(items: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


def validate_graph(graph: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise InfrastructureError("图谱交换文件必须包含 nodes 和 edges 数组。")
    node_ids = {node.get("id") for node in nodes}
    if None in node_ids or len(node_ids) != len(nodes):
        raise InfrastructureError("图谱节点 id 缺失或重复。")
    dangling = [edge.get("id") for edge in edges if edge.get("source") not in node_ids or edge.get("target") not in node_ids]
    if dangling:
        raise InfrastructureError(f"图谱包含悬空关系：{dangling[:5]}")
    return nodes, edges


def node_row(node: dict[str, Any]) -> dict[str, Any]:
    aliases = [str(value) for value in node.get("aliases", []) if value]
    return {
        "id": str(node["id"]),
        "type": str(node.get("type", "concept")),
        "name": str(node.get("name", "")),
        "aliases": aliases,
        "aliases_text": " ".join(aliases),
        "attributes_json": json.dumps(node.get("attributes", {}), ensure_ascii=False, sort_keys=True),
    }


def edge_row(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(edge["id"]),
        "source": str(edge["source"]),
        "target": str(edge["target"]),
        "confidence": float(edge.get("confidence") or 0.0),
        "evidence_json": json.dumps(edge.get("evidence", {}), ensure_ascii=False, sort_keys=True),
    }


def import_graph(graph_path: Path) -> dict[str, Any]:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes, edges = validate_graph(graph)
    driver, config = load_driver()
    database = config["database"]
    batch_size = int(config["batch_size"])
    index_name = safe_identifier(config["entity_search_index"])
    try:
        driver.execute_query(
            "CREATE CONSTRAINT mineintel_entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE",
            database_=database,
        )
        rows = [node_row(node) for node in nodes]
        for batch in batches(rows, batch_size):
            driver.execute_query(
                """
                UNWIND $rows AS row
                MERGE (n:Entity {id: row.id})
                SET n.type = row.type,
                    n.name = row.name,
                    n.aliases = row.aliases,
                    n.aliases_text = row.aliases_text,
                    n.attributes_json = row.attributes_json
                """,
                rows=batch,
                database_=database,
            )

        nodes_by_label: dict[str, list[str]] = defaultdict(list)
        for node in nodes:
            nodes_by_label[neo4j_label(str(node.get("type", "concept")))].append(str(node["id"]))
        for label, ids in nodes_by_label.items():
            for batch_ids in batches([{"id": value} for value in ids], batch_size):
                driver.execute_query(
                    f"UNWIND $rows AS row MATCH (n:Entity {{id: row.id}}) SET n:`{label}`",
                    rows=batch_ids,
                    database_=database,
                )

        edges_by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in edges:
            edges_by_type[relationship_type(str(edge.get("relation", "related_to")))].append(edge_row(edge))
        for relation, relation_rows in edges_by_type.items():
            for batch in batches(relation_rows, batch_size):
                driver.execute_query(
                    f"""
                    UNWIND $rows AS row
                    MATCH (source:Entity {{id: row.source}})
                    MATCH (target:Entity {{id: row.target}})
                    MERGE (source)-[rel:`{relation}` {{id: row.id}}]->(target)
                    SET rel.confidence = row.confidence,
                        rel.evidence_json = row.evidence_json
                    """,
                    rows=batch,
                    database_=database,
                )

        driver.execute_query(
            f"""
            CREATE FULLTEXT INDEX `{index_name}` IF NOT EXISTS
            FOR (n:Entity) ON EACH [n.name, n.aliases_text]
            OPTIONS {{indexConfig: {{`fulltext.analyzer`: 'cjk'}}}}
            """,
            database_=database,
        )
        records, _, _ = driver.execute_query(
            "MATCH (n:Entity) WITH count(n) AS nodes MATCH ()-[r]->() RETURN nodes, count(r) AS relationships",
            database_=database,
        )
        counts = records[0].data() if records else {"nodes": 0, "relationships": 0}
    finally:
        driver.close()
    return {
        "status": "success",
        "database": database,
        "source": display_path(graph_path),
        "imported_nodes": len(nodes),
        "imported_relationships": len(edges),
        "database_counts": counts,
        "search_index": index_name,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    args = parser.parse_args()
    try:
        result = import_graph(args.graph.resolve())
    except (InfrastructureError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
