#!/usr/bin/env python3
"""Shared Neo4j configuration and result helpers for MineIntel."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = SKILL_DIR.parent

if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from mineintel_common.config import display_path, load_infrastructure  # noqa: E402


class InfrastructureError(RuntimeError):
    """Raised when Neo4j configuration or connectivity is unavailable."""


def load_config() -> dict[str, Any]:
    try:
        config = load_infrastructure()["neo4j"]
    except RuntimeError as exc:
        raise InfrastructureError(str(exc)) from exc
    required = {
        "uri": os.getenv("MINEINTEL_NEO4J_URI"),
        "user": os.getenv("MINEINTEL_NEO4J_USER"),
        "password": os.getenv("MINEINTEL_NEO4J_PASSWORD"),
    }
    missing = [f"MINEINTEL_NEO4J_{key.upper()}" for key, value in required.items() if not value]
    if missing:
        raise InfrastructureError(
            "Neo4j 未配置；请设置环境变量：" + ", ".join(missing) + "。不会退回本地 JSON 查询。"
        )
    config.update(required)
    config["database"] = os.getenv("MINEINTEL_NEO4J_DATABASE", config["database"])
    return config


def load_driver() -> tuple[Any, dict[str, Any]]:
    try:
        from neo4j import GraphDatabase  # type: ignore
    except ImportError as exc:
        raise InfrastructureError(
            "缺少 Neo4j Python 驱动；请安装 requirements-advanced.txt。不会退回本地 JSON 查询。"
        ) from exc
    config = load_config()
    driver = GraphDatabase.driver(config["uri"], auth=(config["user"], config["password"]))
    try:
        driver.verify_connectivity()
    except Exception as exc:
        driver.close()
        raise InfrastructureError(f"无法连接 Neo4j：{exc}") from exc
    return driver, config


def safe_identifier(value: str) -> str:
    identifier = re.sub(r"[^A-Za-z0-9_]", "_", value).strip("_")
    if not identifier or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
        raise InfrastructureError(f"非法 Neo4j 标识符：{value!r}")
    return identifier


def neo4j_label(node_type: str) -> str:
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", node_type) if part]
    return safe_identifier("".join(part[:1].upper() + part[1:] for part in parts) or "Concept")


def relationship_type(relation: str) -> str:
    return safe_identifier(relation.upper())


def parse_json_object(value: Any) -> dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {"raw": str(value)}
    return parsed if isinstance(parsed, dict) else {"value": parsed}
