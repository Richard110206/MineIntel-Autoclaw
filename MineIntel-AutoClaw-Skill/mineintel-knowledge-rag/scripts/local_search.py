#!/usr/bin/env python3
"""Semantic retrieval over the MineIntel FAISS vector index."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from faiss_store import InfrastructureError, load_index_bundle


def search(query: str, limit: int, min_score: float) -> dict[str, Any]:
    if not query.strip():
        raise InfrastructureError("查询不能为空。")
    if limit < 1:
        raise InfrastructureError("limit 必须大于 0。")

    index, records, manifest, config, np, sentence_transformer = load_index_bundle()
    model_name = manifest["model"]
    configured_model = config["embedding"]["model"]
    if model_name != configured_model:
        raise InfrastructureError(
            f"索引模型为 {model_name}，当前配置为 {configured_model}；请使用一致模型重建索引。"
        )
    model = sentence_transformer(model_name, device=config["embedding"]["device"])
    vector = model.encode_query(
        query,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    vector = np.ascontiguousarray(vector.reshape(1, -1), dtype="float32")
    if vector.shape[1] != int(manifest["embedding_dimension"]):
        raise InfrastructureError("查询向量维度与 FAISS 索引不一致，请重建索引。")

    scores, positions = index.search(vector, min(limit, index.ntotal))
    results = []
    for score, position in zip(scores[0].tolist(), positions[0].tolist()):
        if position < 0 or score < min_score:
            continue
        item = records[position]
        results.append(
            {
                "score": round(float(score), 6),
                "source_file": item["source_file"],
                "record": item["record"],
                "preview": item["text"][:500],
                "chunk_id": item["chunk_id"],
            }
        )
    return {
        "status": "success",
        "source": "faiss-semantic-search",
        "model": model_name,
        "metric": manifest["metric"],
        "query": query,
        "count": len(results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=0.25)
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
