#!/usr/bin/env python3
"""Local, provenance-aware project memory for personalized research."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import uuid

STATUSES = {"planned", "ongoing", "completed", "abandoned"}
SOURCES = {"user_statement", "verified_artifact"}
CONSTRAINTS = {"major", "year", "interests", "team", "deadline", "hours_per_week", "data", "equipment", "compute", "preferences"}


def read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("JSON 必须为对象")
    return value


def validate_project(item: dict) -> None:
    for field in ("id", "title", "contribution"):
        if not isinstance(item.get(field), str) or not item[field].strip():
            raise ValueError(f"项目缺少 {field}")
    if item.get("status") not in STATUSES or item.get("source") not in SOURCES:
        raise ValueError("项目 status 或 source 无效")
    for field in ("skills", "artifacts"):
        if not isinstance(item.get(field, []), list) or any(not isinstance(v, str) for v in item.get(field, [])):
            raise ValueError(f"{field} 必须为字符串数组")
    if item["source"] == "verified_artifact" and not item.get("artifacts"):
        raise ValueError("已核验项目必须提供 artifacts")


def load_profile(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": 1, "projects": [], "constraints": {}}
    value = read_object(path)
    if value.get("schema_version") != 1 or not isinstance(value.get("projects"), list) or not isinstance(value.get("constraints"), dict):
        raise ValueError("记忆档案结构无效，拒绝覆盖")
    seen = set()
    for item in value["projects"]:
        if not isinstance(item, dict):
            raise ValueError("项目记录必须为对象")
        validate_project(item)
        if item["id"] in seen:
            raise ValueError("项目 id 重复")
        seen.add(item["id"])
    return value


@contextmanager
def lock_profile(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(path.name + ".lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode())
        yield
    finally:
        os.close(fd)
        lock.unlink()


def save_profile(path: Path, profile: dict) -> None:
    profile["updated_at"] = datetime.now(timezone.utc).isoformat()
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("x", encoding="utf-8") as stream:
            json.dump(profile, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("context")
    commands.add_parser("add").add_argument("--project", type=Path, required=True)
    commands.add_parser("forget").add_argument("--id", required=True)
    commands.add_parser("constraints").add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == "context":
            exists = args.profile.exists()
            profile = load_profile(args.profile)
            result = {"status": "success" if exists else "needs_profile", "profile": profile}
        else:
            with lock_profile(args.profile):
                profile = load_profile(args.profile)
                if args.action == "add":
                    item = read_object(args.project)
                    validate_project(item)
                    item["recorded_at"] = datetime.now(timezone.utc).isoformat()
                    items = profile["projects"]
                    position = next((i for i, p in enumerate(items) if p["id"] == item["id"]), None)
                    if position is None:
                        items.append(item)
                    else:
                        items[position] = item
                elif args.action == "forget":
                    if not any(p["id"] == args.id for p in profile["projects"]):
                        raise ValueError("项目 id 不存在")
                    profile["projects"] = [p for p in profile["projects"] if p["id"] != args.id]
                else:
                    constraints = read_object(args.input)
                    if set(constraints) - CONSTRAINTS:
                        raise ValueError("包含不支持的约束字段")
                    profile["constraints"].update(constraints)
                save_profile(args.profile, profile)
                result = {"status": "success", "project_count": len(profile["projects"])}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
