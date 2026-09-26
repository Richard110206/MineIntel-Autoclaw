#!/usr/bin/env python3
"""FAISS-backed semantic knowledge store for MineIntel."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SKILL_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = SKILL_DIR.parent
KNOWLEDGE_DIR = SKILL_DIR / "data" / "knowledge"
STRUCTURED_PATH = SKILL_DIR / "data" / "sample_knowledge.json"
INDEX_SCHEMA_VERSION = 1

if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from mineintel_common.config import display_path, load_infrastructure  # noqa: E402


class InfrastructureError(RuntimeError):
    """Raised when the configured semantic infrastructure is unavailable."""


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    source_file: str
    title: str
    text: str
    record: dict[str, Any]

    def metadata(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source_file": self.source_file,
            "title": self.title,
            "text": self.text,
            "record": self.record,
        }


def load_config() -> dict[str, Any]:
    try:
        config = load_infrastructure()
    except RuntimeError as exc:
        raise InfrastructureError(str(exc)) from exc
    config["embedding"]["model"] = os.getenv(
        "MINEINTEL_EMBEDDING_MODEL", config["embedding"]["model"]
    )
    config["embedding"]["device"] = os.getenv(
        "MINEINTEL_EMBEDDING_DEVICE", config["embedding"]["device"]
    )
    return config


def index_dir(config: dict[str, Any]) -> Path:
    path = Path(config["faiss"]["index_dir"])
    return path if path.is_absolute() else PACKAGE_DIR / path


def source_paths() -> list[Path]:
    paths = [STRUCTURED_PATH]
    if KNOWLEDGE_DIR.exists():
        paths.extend(
            path
            for path in sorted(KNOWLEDGE_DIR.rglob("*"))
            if path.is_file() and path.suffix.lower() in {".md", ".txt"}
        )
    missing = [str(display_path(path)) for path in paths if not path.exists()]
    if missing:
        raise InfrastructureError(f"知识库源文件缺失：{', '.join(missing)}")
    return paths


def corpus_fingerprint(config: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    embedding = config["embedding"]
    digest.update(str(embedding["chunk_chars"]).encode())
    digest.update(str(embedding["chunk_overlap_chars"]).encode())
    for path in source_paths():
        digest.update(str(path.relative_to(PACKAGE_DIR)).replace("\\", "/").encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def chunk_text(text: str, max_chars: int, overlap_chars: int) -> Iterable[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > max_chars:
            yield current
            tail = current[-overlap_chars:] if overlap_chars else ""
            current = f"{tail}\n\n{paragraph}".strip()
        else:
            current = candidate
    if current:
        yield current


def markdown_sections(text: str, fallback_title: str) -> Iterable[tuple[str, str]]:
    title = fallback_title
    buffer: list[str] = []
    for line in text.splitlines():
        heading = re.match(r"^#{1,6}\s+(.+?)\s*$", line.strip())
        if heading:
            body = "\n".join(buffer).strip()
            if body:
                yield title, body
            title = heading.group(1).strip()
            buffer = []
        else:
            buffer.append(line)
    body = "\n".join(buffer).strip()
    if body:
        yield title, body


def collect_chunks(config: dict[str, Any]) -> list[DocumentChunk]:
    max_chars = int(config["embedding"]["chunk_chars"])
    overlap = int(config["embedding"]["chunk_overlap_chars"])
    chunks: list[DocumentChunk] = []

    structured = json.loads(STRUCTURED_PATH.read_text(encoding="utf-8"))
    for item in structured:
        title = str(item.get("title") or item.get("name") or "结构化知识")
        text = json.dumps(item, ensure_ascii=False, sort_keys=True)
        cid = hashlib.sha256(f"sample_knowledge.json\0{title}\0{text}".encode("utf-8")).hexdigest()
        chunks.append(DocumentChunk(cid, STRUCTURED_PATH.name, title, text, dict(item)))

    for path in source_paths()[1:]:
        source = str(path.relative_to(SKILL_DIR)).replace("\\", "/")
        text = path.read_text(encoding="utf-8")
        for section_title, section_body in markdown_sections(text, path.stem):
            for part_index, part in enumerate(chunk_text(section_body, max_chars, overlap), start=1):
                title = section_title if part_index == 1 else f"{section_title} · {part_index}"
                cid = hashlib.sha256(f"{source}\0{title}\0{part}".encode("utf-8")).hexdigest()
                record = {"type": "knowledge_text", "title": title, "description": part}
                chunks.append(DocumentChunk(cid, source, title, part, record))

    if not chunks:
        raise InfrastructureError("知识库没有可索引内容。")
    return chunks


def load_dependencies() -> tuple[Any, Any, Any]:
    try:
        import faiss  # type: ignore
        import numpy as np  # type: ignore
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError as exc:
        raise InfrastructureError(
            "缺少 FAISS 语义检索依赖；请安装 requirements-advanced.txt，不能退回关键词匹配。"
        ) from exc
    return faiss, np, SentenceTransformer


def encode_documents(model: Any, texts: list[str], batch_size: int, np: Any) -> Any:
    embeddings = model.encode_document(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    return np.ascontiguousarray(embeddings, dtype="float32")


def build_index() -> dict[str, Any]:
    config = load_config()
    faiss, np, sentence_transformer = load_dependencies()
    chunks = collect_chunks(config)
    model_name = config["embedding"]["model"]
    model = sentence_transformer(model_name, device=config["embedding"]["device"])
    embeddings = encode_documents(
        model,
        [chunk.text for chunk in chunks],
        int(config["embedding"]["batch_size"]),
        np,
    )
    if embeddings.ndim != 2 or embeddings.shape[0] != len(chunks):
        raise InfrastructureError("嵌入模型返回的矩阵形状与知识块数量不一致。")

    index = faiss.IndexFlatIP(int(embeddings.shape[1]))
    index.add(embeddings)
    target = index_dir(config)
    target.mkdir(parents=True, exist_ok=True)
    index_tmp = target / "index.faiss.tmp"
    metadata_tmp = target / "metadata.jsonl.tmp"
    manifest_tmp = target / "manifest.json.tmp"
    # faiss 的 C 层 fopen 在 Windows 下无法可靠打开非 ASCII 路径，
    # 因此索引文件一律经内存序列化后由 Python 以字节流写读。
    index_tmp.write_bytes(faiss.serialize_index(index).tobytes())
    metadata_tmp.write_text(
        "".join(json.dumps(chunk.metadata(), ensure_ascii=False) + "\n" for chunk in chunks),
        encoding="utf-8",
    )
    manifest = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "model": model_name,
        "metric": "cosine",
        "embedding_dimension": int(embeddings.shape[1]),
        "count": len(chunks),
        "corpus_fingerprint": corpus_fingerprint(config),
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    index_tmp.replace(target / "index.faiss")
    metadata_tmp.replace(target / "metadata.jsonl")
    manifest_tmp.replace(target / "manifest.json")
    return manifest


def load_index_bundle() -> tuple[Any, list[dict[str, Any]], dict[str, Any], dict[str, Any], Any, Any]:
    config = load_config()
    target = index_dir(config)
    required = [target / "index.faiss", target / "metadata.jsonl", target / "manifest.json"]
    missing = [display_path(path) for path in required if not path.exists()]
    if missing:
        raise InfrastructureError(
            "FAISS 索引尚未初始化；请先运行 build_faiss_index.py。缺少：" + ", ".join(missing)
        )
    manifest = json.loads(required[2].read_text(encoding="utf-8"))
    if manifest.get("schema_version") != INDEX_SCHEMA_VERSION:
        raise InfrastructureError("FAISS 索引结构版本不兼容，请重建索引。")
    if manifest.get("corpus_fingerprint") != corpus_fingerprint(config):
        raise InfrastructureError("知识库源文件已变化，FAISS 索引已过期，请重建索引。")
    records = [
        json.loads(line)
        for line in required[1].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    faiss, np, sentence_transformer = load_dependencies()
    index = faiss.deserialize_index(np.frombuffer(required[0].read_bytes(), dtype=np.uint8))
    if index.ntotal != len(records) or index.ntotal != int(manifest["count"]):
        raise InfrastructureError("FAISS 索引与元数据数量不一致，请重建索引。")
    return index, records, manifest, config, np, sentence_transformer
