#!/usr/bin/env python3
"""Lightweight local knowledge search for MineIntel Research Skill.

This script uses simple token scoring over JSON files and Markdown/TXT
knowledge files in data/. It is designed for stable competition demos and
mining-domain knowledge retrieval, not as a full vector RAG system.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_FILES = [BASE_DIR / "data" / "sample_knowledge.json"]
KNOWLEDGE_DIR = BASE_DIR / "data" / "knowledge"
TEXT_EXTENSIONS = {".md", ".txt"}


def tokenize(text: str) -> list[str]:
    text = text.lower()
    zh_chunks = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    en_words = re.findall(r"[a-zA-Z0-9_+-]{2,}", text)
    tokens: list[str] = []
    for chunk in zh_chunks:
        tokens.append(chunk)
        for size in (2, 3, 4):
            tokens.extend(chunk[i : i + size] for i in range(max(0, len(chunk) - size + 1)))
    tokens.extend(en_words)
    return [t for t in tokens if t.strip()]


def load_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in DATA_FILES:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            item = dict(item)
            item["_source_file"] = path.name
            records.append(item)
    records.extend(load_text_records())
    return records


def split_text_sections(text: str, fallback_title: str, max_chars: int = 1400) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    title = fallback_title
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        body = "\n".join(buffer).strip()
        if body:
            sections.append((title, body))
        buffer = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            flush()
            title = stripped.lstrip("#").strip() or fallback_title
            continue
        buffer.append(line)
    flush()

    if not sections and text.strip():
        sections.append((fallback_title, text.strip()))

    chunked: list[tuple[str, str]] = []
    for section_title, body in sections:
        if len(body) <= max_chars:
            chunked.append((section_title, body))
            continue
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
        chunk = ""
        chunk_index = 1
        for paragraph in paragraphs:
            candidate = f"{chunk}\n\n{paragraph}".strip()
            if len(candidate) > max_chars and chunk:
                chunked.append((f"{section_title} {chunk_index}", chunk))
                chunk_index += 1
                chunk = paragraph
            else:
                chunk = candidate
        if chunk:
            suffix = f" {chunk_index}" if chunk_index > 1 else ""
            chunked.append((f"{section_title}{suffix}", chunk))
    return chunked


def load_text_records() -> list[dict[str, Any]]:
    if not KNOWLEDGE_DIR.exists():
        return []

    records: list[dict[str, Any]] = []
    for path in sorted(KNOWLEDGE_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")
        for index, (title, body) in enumerate(split_text_sections(text, fallback_title=path.stem), start=1):
            summary = re.sub(r"\s+", " ", body)[:220]
            records.append(
                {
                    "type": "knowledge_text",
                    "title": title,
                    "description": body,
                    "summary": summary,
                    "keywords": tokenize(title)[:12],
                    "_source_file": str(path.relative_to(BASE_DIR)),
                    "_chunk": index,
                }
            )
    return records


def record_text(record: dict[str, Any]) -> str:
    parts = []
    for value in record.values():
        if isinstance(value, list):
            parts.extend(str(x) for x in value)
        elif isinstance(value, dict):
            parts.append(json.dumps(value, ensure_ascii=False))
        else:
            parts.append(str(value))
    return " ".join(parts)


def search(query: str, limit: int) -> dict[str, Any]:
    q_tokens = tokenize(query)
    records = load_records()
    scored = []

    for record in records:
        text = record_text(record).lower()
        score = 0
        matched = []
        for token in q_tokens:
            if token and token.lower() in text:
                score += 1 if len(token) <= 3 else 2
                matched.append(token)
        if score > 0:
            preview = record.get("summary") or record.get("description") or record.get("research_direction") or ""
            scored.append(
                {
                    "score": score,
                    "matched_terms": sorted(set(matched), key=matched.index)[:10],
                    "source_file": record.get("_source_file"),
                    "record": {k: v for k, v in record.items() if not k.startswith("_")},
                    "preview": preview,
                }
            )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return {
        "status": "success",
        "source": "local-knowledge-search",
        "query": query,
        "count": min(len(scored), limit),
        "results": scored[:limit],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Search local MineIntel knowledge JSON files.")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    print(json.dumps(search(args.query, limit=args.limit), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
