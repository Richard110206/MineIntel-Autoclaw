#!/usr/bin/env python3
"""Create a local email preview and open a prefilled Gmail compose page."""

from __future__ import annotations

import argparse
import json
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlencode


SKILL_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = SKILL_DIR.parent
STATE_PATH = PACKAGE_DIR / "demo-ui" / "progress_state.json"
EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


def read_text(path: Path | None) -> str:
    if path is None:
        return ""
    return path.read_text(encoding="utf-8")


def clean_name(value: str) -> str:
    value = re.sub(r"\s+", "", value or "")
    value = re.sub(r"(?:教授|副教授|讲师|老师)$", "", value)
    return value or "老师"


def build_body(topic: str, advisor_name: str, student_name: str, report: str) -> str:
    advisor = clean_name(advisor_name)
    student = student_name.strip() or "学生"
    evidence = ""
    for line in report.splitlines():
        line = re.sub(r"^[#>*\-\d.、\s]+", "", line).strip()
        if advisor != "老师" and advisor in line and 20 <= len(line) <= 180:
            evidence = line
            break
    direction_sentence = (
        f"我在项目调研中关注到您的相关研究方向：{evidence}。"
        if evidence
        else "我通过学校公开资料了解到您的研究方向与该选题具有较高契合度。"
    )
    return (
        f"尊敬的{advisor}老师：\n\n"
        f"您好！我是{student}，目前正在围绕“{topic}”开展前期调研与项目设计。"
        f"{direction_sentence}\n\n"
        "目前我已完成应用场景梳理、相关文献检索和基础技术路线设计，计划进一步推进数据整理、"
        "基线模型复现、实验评估与原型实现。我希望能在您的指导下继续完善研究问题和实施方案，"
        "也愿意从文献整理、实验复现和工程实现等基础工作做起。\n\n"
        "若您方便，恳请您对该方向是否适合作为本科生科研项目给予建议。感谢您在百忙之中阅读邮件，"
        "期待您的回复。\n\n"
        f"祝工作顺利、科研顺遂！\n\n{student}\n{datetime.now():%Y年%m月%d日}"
    )


def gmail_compose_url(recipient: str, subject: str, body: str) -> str:
    query = urlencode(
        {"view": "cm", "fs": "1", "to": recipient, "su": subject, "body": body},
        quote_via=quote,
    )
    return f"https://mail.google.com/mail/?{query}"


def update_ui(status: str, preview_path: Path, subject: str, message: str) -> None:
    if not STATE_PATH.exists():
        return
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        relative_path = str(preview_path.resolve().relative_to(PACKAGE_DIR.resolve()))
    except (OSError, json.JSONDecodeError, ValueError):
        return
    state.setdefault("results", {})["email"] = {
        "status": status,
        "path": relative_path,
        "subject": subject,
        "message": message,
    }
    artifacts = state.setdefault("artifacts", [])
    artifact = {"label": "邮件草稿预览", "path": relative_path, "kind": "email_draft"}
    if not any(item.get("path") == relative_path for item in artifacts if isinstance(item, dict)):
        artifacts.append(artifact)
    state["updated_at"] = datetime.now().isoformat(timespec="seconds")
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-file", type=Path)
    parser.add_argument("--body-file", type=Path)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--advisor-name", default="老师")
    parser.add_argument("--advisor-email", required=True)
    parser.add_argument("--student-name", default="学生")
    parser.add_argument("--subject")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--mode", choices=("browser", "preview", "auto", "imap"), default="browser")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    recipient = args.advisor_email.strip()
    if not EMAIL_RE.fullmatch(recipient):
        raise SystemExit("导师邮箱格式无效；请使用学校或学院官网核验邮箱。")

    report = read_text(args.report_file)
    body = read_text(args.body_file).strip() or build_body(
        args.topic.strip(), args.advisor_name, args.student_name, report
    )
    subject = args.subject or f"本科生科研咨询：{args.topic.strip()}"
    output_dir = (args.output_dir or (args.report_file.parent if args.report_file else Path.cwd())).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    preview_txt = output_dir / "email_draft_preview.txt"
    preview_json = output_dir / "email_draft_preview.json"
    payload = {"to": recipient, "subject": subject, "body": body}
    preview_txt.write_text(f"To: {recipient}\nSubject: {subject}\n\n{body}\n", encoding="utf-8")
    preview_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    mode = "browser" if args.mode in {"auto", "imap"} else args.mode
    if mode == "preview":
        message = "已生成本地邮件草稿预览，未打开浏览器、未发送。"
        update_ui("preview_created", preview_txt, subject, message)
        result = {"status": "preview_created", "preview": str(preview_txt), "sent": False}
    else:
        opened = webbrowser.open(gmail_compose_url(recipient, subject, body), new=2, autoraise=True)
        status = "browser_opened" if opened else "browser_open_failed"
        message = (
            "已在浏览器打开 Gmail 撰写页并预填邮件；请登录后复核，未自动发送。"
            if opened
            else "浏览器未确认打开，已保留本地邮件草稿预览，未发送。"
        )
        update_ui(status, preview_txt, subject, message)
        result = {"status": status, "preview": str(preview_txt), "sent": False}

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
