#!/usr/bin/env python3
"""Build a lightweight MineIntel application knowledge graph.

The graph is deterministic and file-based. It uses the team curated scenario
CSV as the high-confidence backbone, then links cleaned corpus candidates as
evidence concepts. This is intentionally not a heavy Neo4j deployment.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
CLEAN_DIR = DATA_DIR / "clean"
USER_DIR = DATA_DIR / "user_sources"
KG_DIR = DATA_DIR / "kg"


def slug(value: str, max_len: int = 18) -> str:
    value = re.sub(r"\s+", "", value.strip().lower())
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    prefix = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value)[:max_len]
    return f"{prefix}-{digest}" if prefix else digest


def node_id(node_type: str, name: str) -> str:
    return f"{node_type}:{slug(name)}"


def edge_id(source: str, relation: str, target: str, evidence: str = "") -> str:
    raw = f"{source}|{relation}|{target}|{evidence}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def clean_item(text: str) -> str:
    text = re.sub(r"^\s*\d+[\.、]\s*", "", text.strip())
    text = text.strip("；;，,。 ")
    text = re.sub(r"\s+", " ", text)
    return text


def split_list(text: str) -> list[str]:
    if not text:
        return []
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    candidates: list[str] = []
    for line in text.splitlines():
        line = clean_item(line)
        if not line:
            continue
        parts = re.split(r"[；;]", line)
        for part in parts:
            item = clean_item(part)
            if item:
                candidates.append(item)
    seen: set[str] = set()
    result: list[str] = []
    for item in candidates:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def split_refs(text: str) -> list[str]:
    if not text:
        return []
    text = text.replace("；", ";").replace("，", ";").replace(",", ";")
    parts = [clean_item(p) for p in text.split(";")]
    return [p for p in parts if p]


def add_node(nodes: dict[str, dict[str, Any]], node_type: str, name: str, **attrs: Any) -> str:
    name = clean_item(name)
    nid = node_id(node_type, name)
    if nid not in nodes:
        nodes[nid] = {
            "id": nid,
            "type": node_type,
            "name": name,
            "aliases": [],
            "attributes": {},
        }
    node = nodes[nid]
    for key, value in attrs.items():
        if value in (None, "", [], {}):
            continue
        if key == "aliases":
            for alias in value:
                if alias and alias not in node["aliases"]:
                    node["aliases"].append(alias)
        else:
            node["attributes"][key] = value
    return nid


def add_edge(
    edges: dict[str, dict[str, Any]],
    source: str,
    relation: str,
    target: str,
    *,
    evidence: dict[str, Any] | None = None,
    confidence: float = 0.75,
) -> None:
    eid = edge_id(source, relation, target, json.dumps(evidence or {}, ensure_ascii=False, sort_keys=True))
    if eid in edges:
        return
    edges[eid] = {
        "id": eid,
        "source": source,
        "relation": relation,
        "target": target,
        "confidence": confidence,
        "evidence": evidence or {},
    }


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_clean_chunks() -> dict[str, dict[str, Any]]:
    chunks: dict[str, dict[str, Any]] = {}
    path = CLEAN_DIR / "clean_chunks.jsonl"
    if not path.exists():
        return chunks
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            chunks[item["chunk_id"]] = item
    return chunks


def load_curated_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(USER_DIR.glob("*.csv")):
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
                row["_source_file"] = str(path.relative_to(DATA_DIR))
                rows.append(row)
    return rows


def build_graph() -> dict[str, Any]:
    KG_DIR.mkdir(parents=True, exist_ok=True)
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}

    clean_sources = load_json(CLEAN_DIR / "clean_sources.json", [])
    entity_candidates = load_json(CLEAN_DIR / "entity_candidates.json", [])
    chunks = load_clean_chunks()
    curated_rows = load_curated_rows()

    # Source nodes from cleaned corpus.
    for source in clean_sources:
        sid = source.get("source_id", "")
        title = source.get("title", sid)
        source_node = add_node(
            nodes,
            "source_document",
            title,
            source_id=sid,
            publisher=source.get("publisher", ""),
            year=source.get("year", ""),
            credibility=source.get("credibility", ""),
            url=source.get("url", ""),
            source_type=source.get("source_type", ""),
        )
        nodes[source_node]["attributes"]["source_id"] = sid

    # High-confidence curated scenario backbone.
    for row in curated_rows:
        scene = row.get("矿井场景", "")
        category = row.get("场景大类", "")
        if not scene:
            continue
        scene_node = add_node(
            nodes,
            "application_scenario",
            scene,
            curated=True,
            source_file=row.get("_source_file", ""),
        )
        if category:
            category_node = add_node(nodes, "scenario_category", category, curated=True)
            add_edge(
                edges,
                scene_node,
                "belongs_to",
                category_node,
                evidence={"source_id": "U01", "field": "场景大类"},
                confidence=0.96,
            )

        for pain in split_list(row.get("有什么问题（痛点）", "")):
            target = add_node(nodes, "pain_point", pain, curated=True)
            add_edge(
                edges,
                scene_node,
                "has_pain_point",
                target,
                evidence={"source_id": "U01", "field": "有什么问题（痛点）", "scene": scene},
                confidence=0.94,
            )

        for solution in split_list(row.get("需要什么解决方案", "")):
            target = add_node(nodes, "solution", solution, curated=True)
            add_edge(
                edges,
                scene_node,
                "needs_solution",
                target,
                evidence={"source_id": "U01", "field": "需要什么解决方案", "scene": scene},
                confidence=0.94,
            )

        for tech in split_list(row.get("要求什么技术/设备", "")):
            target = add_node(nodes, "technology_equipment", tech, curated=True)
            add_edge(
                edges,
                scene_node,
                "requires_technology",
                target,
                evidence={"source_id": "U01", "field": "要求什么技术/设备", "scene": scene},
                confidence=0.94,
            )

        row_text = "\n".join(str(v) for k, v in row.items() if not k.startswith("_"))
        for ref in split_refs(row.get("参考白皮书来源", "")):
            ref_node = add_node(nodes, "source_document", ref, curated_reference=True)
            add_edge(
                edges,
                scene_node,
                "evidenced_by",
                ref_node,
                evidence={"source_id": "U01", "field": "参考白皮书来源", "scene": scene},
                confidence=0.9,
            )
            # Link matching official/local source nodes when title appears in the reference string.
            for source in clean_sources:
                title = source.get("title", "")
                sid = source.get("source_id", "")
                if not title or not sid:
                    continue
                if title[:8] in ref or ref[:8] in title or any(token and token in title for token in re.findall(r"《([^》]+)》", ref)):
                    official = add_node(nodes, "source_document", title, source_id=sid)
                    add_edge(
                        edges,
                        ref_node,
                        "same_or_related_source",
                        official,
                        evidence={"source_id": "U01", "reference": ref, "matched_source_id": sid},
                        confidence=0.7,
                    )

        # Link curated scenes to candidate concept nodes if terms appear in the row.
        for candidate in entity_candidates:
            term = candidate.get("term", "")
            category_name = candidate.get("category", "")
            if term and term.lower() in row_text.lower():
                concept_type = {
                    "application_scenario": "application_concept",
                    "technology": "technology",
                    "pain_point": "pain_concept",
                    "solution": "solution_concept",
                    "metric": "metric",
                }.get(category_name, "concept")
                concept = add_node(
                    nodes,
                    concept_type,
                    term,
                    candidate_category=category_name,
                    candidate_count=candidate.get("count", 0),
                )
                add_edge(
                    edges,
                    scene_node,
                    "related_concept",
                    concept,
                    evidence={"source_id": "U01", "scene": scene, "matched_term": term},
                    confidence=0.72,
                )

    # Evidence concept layer from cleaned corpus candidates.
    for candidate in entity_candidates:
        term = candidate.get("term", "")
        category_name = candidate.get("category", "")
        if not term:
            continue
        concept_type = {
            "application_scenario": "application_concept",
            "technology": "technology",
            "pain_point": "pain_concept",
            "solution": "solution_concept",
            "metric": "metric",
        }.get(category_name, "concept")
        concept = add_node(
            nodes,
            concept_type,
            term,
            candidate_category=category_name,
            candidate_count=candidate.get("count", 0),
            candidate_source_count=len(candidate.get("source_ids", [])),
        )
        for source_id in candidate.get("source_ids", []):
            source_title = source_id
            for source in clean_sources:
                if source.get("source_id") == source_id:
                    source_title = source.get("title") or source_id
                    break
            source_node = add_node(nodes, "source_document", source_title, source_id=source_id)
            evidence_items = [
                e for e in candidate.get("evidence", []) if e.get("source_id") == source_id
            ][:3]
            add_edge(
                edges,
                source_node,
                "mentions",
                concept,
                evidence={
                    "source_id": source_id,
                    "chunk_ids": [e.get("chunk_id") for e in evidence_items if e.get("chunk_id")],
                    "snippets": [e.get("text") for e in evidence_items if e.get("text")],
                },
                confidence=0.68,
            )

    connected_node_ids = set()
    for edge in edges.values():
        connected_node_ids.add(edge["source"])
        connected_node_ids.add(edge["target"])
    nodes = {
        nid: node
        for nid, node in nodes.items()
        if node["type"] != "source_document" or nid in connected_node_ids
    }

    graph = {
        "metadata": {
            "name": "MineIntel Application Knowledge Graph",
            "version": "0.1",
            "description": "矿井应用专家轻量知识图谱。以团队人工场景表为主骨架，融合白皮书、蓝皮书、政策标准和原 MineIntel 知识库证据。",
            "source_count": len(clean_sources),
            "curated_scene_count": len(curated_rows),
            "chunk_count": len(chunks),
        },
        "nodes": sorted(nodes.values(), key=lambda x: (x["type"], x["name"])),
        "edges": sorted(edges.values(), key=lambda x: (x["relation"], x["source"], x["target"])),
    }
    return graph


def write_outputs(graph: dict[str, Any]) -> None:
    nodes = graph["nodes"]
    edges = graph["edges"]
    (KG_DIR / "kg_nodes.json").write_text(json.dumps(nodes, ensure_ascii=False, indent=2), encoding="utf-8")
    (KG_DIR / "kg_edges.json").write_text(json.dumps(edges, ensure_ascii=False, indent=2), encoding="utf-8")
    (KG_DIR / "kg_graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")

    with (KG_DIR / "kg_triples.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "relation", "target", "confidence", "evidence"])
        writer.writeheader()
        node_names = {node["id"]: node["name"] for node in nodes}
        for edge in edges:
            writer.writerow(
                {
                    "source": node_names.get(edge["source"], edge["source"]),
                    "relation": edge["relation"],
                    "target": node_names.get(edge["target"], edge["target"]),
                    "confidence": edge["confidence"],
                    "evidence": json.dumps(edge.get("evidence", {}), ensure_ascii=False),
                }
            )

    node_counter = Counter(node["type"] for node in nodes)
    edge_counter = Counter(edge["relation"] for edge in edges)
    report = [
        "# MineIntel 矿井应用知识图谱构建报告",
        "",
        "本轮图谱以团队人工整理的 `矿井场景总览.csv` 为主骨架，融合清洗后的白皮书、蓝皮书、政策标准和原 MineIntel 知识库候选实体。",
        "",
        "## 汇总",
        "",
        f"- 节点数：{len(nodes)}",
        f"- 关系数：{len(edges)}",
        f"- 人工场景数：{graph['metadata']['curated_scene_count']}",
        f"- 清洗文本块数：{graph['metadata']['chunk_count']}",
        "",
        "## 节点类型",
        "",
        "| 类型 | 数量 |",
        "| --- | ---: |",
    ]
    for key, count in sorted(node_counter.items()):
        report.append(f"| {key} | {count} |")
    report.extend(["", "## 关系类型", "", "| 关系 | 数量 |", "| --- | ---: |"])
    for key, count in sorted(edge_counter.items()):
        report.append(f"| {key} | {count} |")
    report.extend(
        [
            "",
            "## 主要文件",
            "",
            "- `kg_nodes.json`：知识图谱节点。",
            "- `kg_edges.json`：知识图谱关系，含 source_id/chunk_id 证据。",
            "- `kg_graph.json`：节点、关系和元数据全集。",
            "- `kg_triples.csv`：便于人工查看的三元组表。",
            "",
            "## 说明",
            "",
            "- `application_scenario` 主要来自人工 CSV，是高置信场景骨架。",
            "- `pain_point`、`solution`、`technology_equipment` 主要来自人工 CSV 的结构化字段。",
            "- `technology`、`application_concept`、`metric` 等候选概念来自清洗语料统计，用于补充图谱覆盖面。",
            "- `mentions` 关系保留清洗语料中的 source_id、chunk_id 和证据片段，便于后续报告溯源。",
        ]
    )
    (KG_DIR / "kg_build_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> int:
    graph = build_graph()
    write_outputs(graph)
    print(
        json.dumps(
            {
                "nodes": len(graph["nodes"]),
                "edges": len(graph["edges"]),
                "kg_dir": str(KG_DIR),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
