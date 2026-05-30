#!/usr/bin/env python3
"""Update MineIntel progress state for the demo UI."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


BASE_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = BASE_DIR.parent
STATE_PATH = PACKAGE_DIR / "demo-ui" / "progress_state.json"

DEFAULT_STEPS = [
    {"id": "confirm", "label": "确认专业和研究领域"},
    {"id": "knowledge", "label": "矿井应用知识图谱"},
    {"id": "paper", "label": "领域论文线索检索"},
    {"id": "baseline", "label": "前沿技术与 baseline"},
    {"id": "advisor", "label": "导师方向匹配"},
    {"id": "experience", "label": "科研经验参考检索"},
    {"id": "report", "label": "报告生成与导出"},
    {"id": "email", "label": "邮件草稿生成"},
]

STEP_ORDER = {step["id"]: index for index, step in enumerate(DEFAULT_STEPS)}


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def default_state() -> dict[str, Any]:
    return {
        "task": "等待任务",
        "status": "idle",
        "current_step": "confirm",
        "current_label": "等待 AutoClaw 开始执行",
        "message": "进度面板已就绪。",
        "percent": 0,
        "steps": DEFAULT_STEPS,
        "completed": [],
        "selection": {
            "major": "",
            "field": "",
            "scene": "",
            "formats": "HTML 完整报告 / 逐页展示 Deck / 文献综述 LaTeX / PDF",
        },
        "sections": {
            "papers": {"title": "论文线索", "content": "", "items": []},
            "baseline": {"title": "GitHub baseline", "content": "", "items": []},
            "advisors": {"title": "导师匹配", "content": "", "items": []},
            "route": {"title": "技术路线", "content": "", "items": []},
            "experience": {"title": "科研经验参考", "content": "", "items": []},
            "email": {"title": "邮件草稿", "content": "", "items": []},
        },
        "results": {
            "papers": [],
            "baseline": [],
            "advisors": [],
            "route": {"center": "技术路线", "branches": []},
            "experience": [],
            "email": {},
        },
        "artifacts": [],
        "output": {},
        "logs": [{"time": now(), "text": "进度面板已就绪。"}],
        "updated_at": now(),
    }


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return default_state()
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_state()


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def find_label(step_id: str) -> str:
    for step in DEFAULT_STEPS:
        if step["id"] == step_id:
            return step["label"]
    return step_id


def read_text_arg(value: str | None, file_path: str | None) -> str:
    if file_path:
        return Path(file_path).read_text(encoding="utf-8")
    return value or ""


def apply_selection(state: dict[str, Any], args: argparse.Namespace) -> None:
    selection = state.setdefault("selection", {})
    for key in ("major", "field", "scene", "formats"):
        value = getattr(args, key)
        if value:
            selection[key] = value


def apply_section(state: dict[str, Any], args: argparse.Namespace) -> None:
    if not args.section:
        return
    sections = state.setdefault("sections", {})
    section = sections.setdefault(args.section, {"title": args.section, "content": "", "items": []})
    if args.section_title:
        section["title"] = args.section_title
    content = read_text_arg(args.section_content, args.section_file).strip()
    if content:
        section["content"] = content


def parse_artifact(value: str) -> dict[str, str]:
    if "=" in value:
        label, path = value.split("=", 1)
        return {"label": label.strip() or Path(path).name, "path": path.strip()}
    return {"label": Path(value).name, "path": value.strip()}


def apply_artifacts(state: dict[str, Any], artifacts: list[str]) -> None:
    if not artifacts:
        return
    existing = state.setdefault("artifacts", [])
    seen = {(item.get("label"), item.get("path")) for item in existing if isinstance(item, dict)}
    for raw in artifacts:
        item = parse_artifact(raw)
        key = (item.get("label"), item.get("path"))
        if item["path"] and key not in seen:
            existing.append(item)
            seen.add(key)


def clear_finished_outputs_for_active_run(state: dict[str, Any]) -> None:
    """Avoid showing stale report/result data when a new run starts in the same UI."""
    current_step = state.get("current_step", "confirm")
    percent = int(state.get("percent") or 0)
    if state.get("status") != "running":
        return
    if STEP_ORDER.get(current_step, 0) >= STEP_ORDER["report"]:
        return
    if percent >= 90:
        return
    state["artifacts"] = []
    state["output"] = {}
    state["results"] = {
        "papers": [],
        "baseline": [],
        "advisors": [],
        "route": {"center": "技术路线", "branches": []},
        "experience": [],
        "email": {},
    }


def sanitize_completed(state: dict[str, Any], mark_current_done: bool) -> None:
    """Keep completed steps consistent when the same UI window is reused."""
    current_step = state.get("current_step", "confirm")
    percent = int(state.get("percent") or 0)
    if state.get("status") == "done" and percent >= 100:
        state["percent"] = 100
        state["completed"] = [step["id"] for step in DEFAULT_STEPS]
        return

    current_index = STEP_ORDER.get(current_step, 0)
    max_done_index = current_index if mark_current_done else current_index - 1
    completed = [step["id"] for index, step in enumerate(DEFAULT_STEPS) if index <= max_done_index]
    for step_id in state.get("completed", []):
        index = STEP_ORDER.get(step_id)
        if index is not None and index <= max_done_index and step_id not in completed:
            completed.append(step_id)
    state["completed"] = completed


def main() -> int:
    parser = argparse.ArgumentParser(description="Update MineIntel demo UI progress.")
    parser.add_argument("--task")
    parser.add_argument("--step", choices=[x["id"] for x in DEFAULT_STEPS])
    parser.add_argument("--status", choices=["idle", "running", "done", "error"])
    parser.add_argument("--message", default="")
    parser.add_argument("--percent", type=int)
    parser.add_argument("--done", action="store_true", help="Mark the current step as completed.")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--major", help="User-selected major or background.")
    parser.add_argument("--field", help="User-selected research field.")
    parser.add_argument("--scene", help="User-selected mining scenario.")
    parser.add_argument("--formats", help="Requested output formats.")
    parser.add_argument("--section", choices=["papers", "baseline", "advisors", "route", "experience", "email", "report"])
    parser.add_argument("--section-title")
    parser.add_argument("--section-content")
    parser.add_argument("--section-file")
    parser.add_argument("--artifact", action="append", default=[], help="Register a downloadable file as LABEL=PATH.")
    parser.add_argument("--verbose", action="store_true", help="Print the updated state for debugging.")
    args = parser.parse_args()

    state = default_state() if args.reset else load_state()
    if not args.reset and args.task and args.task != state.get("task") and state.get("task") != "等待任务":
        state = default_state()
    if args.task:
        state["task"] = args.task
    if args.step:
        state["current_step"] = args.step
        state["current_label"] = find_label(args.step)
    if args.status:
        state["status"] = args.status
    if args.percent is not None:
        state["percent"] = max(0, min(100, args.percent))
    if args.message:
        state["message"] = args.message
        logs = state.setdefault("logs", [])
        logs.append({"time": now(), "text": args.message})
        state["logs"] = logs[-12:]
    if args.done and args.step:
        completed = state.setdefault("completed", [])
        if args.step not in completed:
            completed.append(args.step)
    apply_selection(state, args)
    apply_section(state, args)
    apply_artifacts(state, args.artifact)
    sanitize_completed(state, mark_current_done=bool(args.done and args.step))
    clear_finished_outputs_for_active_run(state)
    state["updated_at"] = now()
    save_state(state)
    if args.verbose:
        print(json.dumps({"status": "success", "state_path": str(STATE_PATH), "state": state}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
