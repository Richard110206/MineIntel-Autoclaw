#!/usr/bin/env python3
"""Save MineIntel report deliverables.

The final competition outputs are the complete MineIntel HTML report, the
presentation deck, and the literature-review LaTeX/PDF bundle. Markdown is
accepted as input only; it is not saved as a formal output artifact.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


BASE_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = BASE_DIR.parent
STATE_PATH = PACKAGE_DIR / "demo-ui" / "progress_state.json"
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = PACKAGE_DIR / "output"
BRAND_MARKER = "<!-- MINEINTEL_BRANDED_REPORT -->"

ASCII_LOGO = r"""
 __  __ ___ _   _ _____ ___ _   _ _____ _____ _
|  \/  |_ _| \ | | ____|_ _| \ | |_   _| ____| |
| |\/| || ||  \| |  _|  | ||  \| | | | |  _| | |
| |  | || || |\  | |___ | || |\  | | | | |___| |___
|_|  |_|___|_| \_|_____|___|_| \_| |_| |_____|_____|
""".strip("\n")


def safe_filename(title: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", title).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:60] or "mineintel_report"


def make_run_dir(output_root: Path, title: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_root / f"{timestamp}_{safe_filename(title)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def read_content(args: argparse.Namespace) -> str:
    if args.content_file:
        return Path(args.content_file).read_text(encoding="utf-8")
    if args.content:
        return args.content
    stdin_data = sys.stdin.read()
    if stdin_data.strip():
        return stdin_data
    raise ValueError("No report content provided. Use --content, --content-file, or stdin.")


def load_script_module(module_name: str, script_path: Path):
    if not script_path.exists():
        raise FileNotFoundError(f"{script_path} not found")
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def export_formats(title: str, markdown: str, output_dir: Path, formats: str) -> dict:
    requested = [x.strip().lower() for x in formats.split(",") if x.strip()]
    if not requested:
        return {}

    files: dict[str, str] = {}
    exports: dict[str, dict] = {}

    if "html" in requested or "poster" in requested:
        html_module = load_script_module(
            "mineintel_html_poster",
            PACKAGE_DIR / "mineintel-html-poster" / "scripts" / "render_html_poster.py",
        )
        html_result = html_module.export(title, markdown, output_dir)
        exports["html_poster"] = html_result
        files.update(html_result.get("files", {}))

    if any(fmt in requested for fmt in ("deck", "ppt", "slides")):
        deck_module = load_script_module(
            "mineintel_deck_export",
            PACKAGE_DIR / "mineintel-deck-export" / "scripts" / "render_deck.py",
        )
        deck_result = deck_module.export(title, markdown, output_dir)
        exports["deck"] = deck_result
        files.update(deck_result.get("files", {}))

    if any(fmt in requested for fmt in ("tex", "latex", "pdf")):
        review_module = load_script_module(
            "mineintel_literature_review",
            PACKAGE_DIR / "mineintel-literature-review" / "scripts" / "build_literature_review.py",
        )
        review_result = review_module.export(
            title,
            markdown,
            output_dir,
            compile_pdf=any(fmt in requested for fmt in ("pdf",)),
        )
        exports["literature_review"] = review_result
        files.update(review_result.get("files", {}))

    return {
        "status": "success",
        "title": title,
        "formats_requested": requested,
        "files": files,
        "children": exports,
    }


def load_progress_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_progress_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def strip_existing_brand_header(content: str) -> str:
    text = content.strip()
    if BRAND_MARKER in text:
        marker_pos = text.find(BRAND_MARKER)
        tail = text[marker_pos:]
        divider = re.search(r"\n---\s*\n", tail)
        if divider:
            return tail[divider.end() :].strip() + "\n"
    if text.startswith("# MineIntel 矿小智科研情报简报"):
        divider = re.search(r"\n---\s*\n", text)
        if divider:
            return text[divider.end() :].strip() + "\n"
    return content


def experience_link_block(state: dict) -> str:
    selection = state.get("selection", {}) if isinstance(state, dict) else {}
    query = " ".join(
        part
        for part in (
            str(selection.get("field", "")).strip(),
            str(selection.get("scene", "")).strip(),
            "大创 科研 选题 经验",
        )
        if part
    )
    zhihu = f"https://www.zhihu.com/search?type=content&q={quote_plus(query)}"
    xhs = f"https://www.xiaohongshu.com/search_result?keyword={quote_plus(query)}"
    return (
        "   - 平台/链接：知乎、小红书公开搜索入口；用于演示和人工核验，不作为论文或技术事实依据。\n"
        f"   - 知乎：[公开搜索入口]({zhihu})\n"
        f"   - 小红书：[公开搜索入口]({xhs})"
    )


def sanitize_report_content(content: str, state: dict | None = None) -> str:
    """Remove generated text that should not enter final report artifacts."""
    state = state or {}
    lines = strip_existing_brand_header(content).splitlines()
    cleaned: list[str] = []
    skip_advisor_block = False
    for line in lines:
        line = line.replace("文献综述 LaTeX, PDF", "文献综述 PDF").replace("文献综述 LaTeX / PDF", "文献综述 PDF")
        stripped = strip_markdown(line).strip()
        starts_numbered_item = bool(re.match(r"^\s*\d+[.)、]\s+", line))
        is_heading = bool(re.match(r"^\s*#{1,6}\s+", line))
        if any(token in stripped for token in ("导师群体", "教师群体", "课题组群体", "导师队伍", "师资队伍")):
            skip_advisor_block = True
            continue
        if skip_advisor_block:
            if starts_numbered_item or is_heading:
                skip_advisor_block = False
            else:
                continue
        if re.match(r"^\s*-\s*(知乎|小红书)：\[公开搜索入口\]", line):
            continue
        if "知乎/小红书经验检索在本地脚本中未返回可核验网页" in line:
            line = "以下为科研经验参考建议，主要用于大创执行、材料组织和答辩准备，不作为论文或技术事实依据："
        if (
            "本地经验提示作为兜底" in line
            or "未返回可稳定核验的具体帖子链接" in line
            or "平台/链接：知乎、小红书公开搜索入口" in line
        ):
            line = experience_link_block(state)
        cleaned.append(line)
    result = "\n".join(cleaned).strip() + "\n"
    if (
        ("知乎" in result or "小红书" in result)
        and "zhihu.com/search" not in result
        and "xiaohongshu.com/search_result" not in result
    ):
        result = result.rstrip() + "\n\n## 科研经验公开搜索入口\n" + experience_link_block(state).strip() + "\n"
    return result


def decorate_markdown(title: str, content: str, state: dict) -> str:
    content = strip_existing_brand_header(content)
    selection = state.get("selection", {}) if isinstance(state, dict) else {}
    major = selection.get("major") or "待确认"
    field = selection.get("field") or "待确认"
    scene = selection.get("scene") or "矿井/矿业场景"
    formats = selection.get("formats") or "HTML 完整报告, 文献综述 LaTeX, 文献综述 PDF(工作区内编译器可用时)"
    formats = formats.replace("文献综述 LaTeX, PDF", "文献综述 PDF").replace("文献综述 LaTeX / PDF", "文献综述 PDF")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    header = f"""# MineIntel 矿小智科研情报简报

> CUMT MineIntel / AutoClaw Native Skill Report

| 项目 | 内容 |
| --- | --- |
| 报告标题 | {title} |
| 专业或方向 | {major} |
| 研究领域 | {field} |
| 矿业场景 | {scene} |
| 交付格式 | {formats} |
| 生成时间 | {generated_at} |

## Executive Snapshot

- **定位**：面向矿井/矿业场景的科研选题、论文线索、baseline、导师方向与技术路线综合分析。
- **方法**：AutoClaw 主控 Skill 编排，本地知识库补充，公开检索与 GitHub baseline 作为外部线索。
- **核验**：论文、导师、仓库等外部信息均应在正式申报前二次核验；本报告不替代学校官网、论文数据库或导师确认。

---

"""
    return header + content.strip() + "\n"


def markdown_sections(markdown: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current_title = "报告摘要"
    current_lines: list[str] = []

    def flush() -> None:
        body = "\n".join(current_lines).strip()
        if body:
            sections.append({"title": current_title, "content": body})

    for line in markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            flush()
            current_title = re.sub(r"[*_`]+", "", heading.group(2)).strip()
            current_lines = []
            continue
        current_lines.append(line)
    flush()
    return sections


def compact_text(text: str, max_chars: int = 1200) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n……完整内容请下载报告查看。"


def strip_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"[#>*_`]+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -:：，,。")


def section_body(markdown: str, patterns: tuple[str, ...]) -> str:
    bodies: list[str] = []
    for section in markdown_sections(markdown):
        title = section["title"].lower()
        if any(pattern.lower() in title for pattern in patterns):
            bodies.append(section["content"])
    return "\n".join(bodies)


def candidate_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"^\d+[.)、]\s+", "", line)
        line = line.strip()
        if len(line) >= 6:
            lines.append(line)
    return lines


def markdown_table_cells(line: str) -> list[str]:
    value = line.strip()
    if "|" not in value:
        return []
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    cells = [strip_markdown(cell.strip()) for cell in value.split("|")]
    return [cell for cell in cells if cell]


def is_table_separator(line: str) -> bool:
    cells = markdown_table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", cell.replace(" ", "")) for cell in cells)


def is_table_header(cells: list[str]) -> bool:
    header_terms = {"序号", "线索", "方向", "可用价值", "标题", "论文", "来源", "年份", "链接", "说明", "内容"}
    return bool(cells) and sum(1 for cell in cells if cell in header_terms) >= 2


def valid_paper_title(title: str) -> bool:
    value = strip_markdown(title)
    if not value or len(value) < 6:
        return False
    bad_exact = {"线索", "方向", "可用价值", "链接", "来源", "年份", "---", "----"}
    if value in bad_exact:
        return False
    bad_fragments = (
        "|",
        "---",
        "以下为",
        "请以",
        "最终确认",
        "人工核验",
        "搜索线索",
        "中文核心期刊",
        "国际期刊",
        "GitHub开源项目",
        "GitHub 开源项目",
        "论文检索来源",
        "检索来源",
        "网络服务限制",
        "公开资料",
        "基于知识图谱",
        "需进一步核验",
        "可进一步核验",
        "需人工",
        "该条为",
    )
    if any(fragment in value for fragment in bad_fragments):
        return False
    useful_terms = (
        "论文",
        "文献",
        "研究",
        "方法",
        "系统",
        "模型",
        "检测",
        "识别",
        "监测",
        "预警",
        "智能",
        "矿",
        "煤",
        "井",
        "YOLO",
        "CNN",
        "Transformer",
        "review",
        "survey",
        "detection",
        "monitoring",
        "mining",
    )
    return any(term.lower() in value.lower() for term in useful_terms)


def extract_unique_urls(text: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"https?://[^\s)）\]】>,，。；;]+", text):
        url = match.group(0).rstrip(").,，。；;")
        if url and url not in seen:
            urls.append(url)
            seen.add(url)
    return urls





def paper_results_with_fallback(papers: list[dict[str, str]], minimum: int = 5) -> list[dict[str, str]]:
    """Compatibility name; validate actual links without adding defaults."""
    results = []
    seen = set()
    for item in papers:
        url = item.get("url", "").strip()
        if not item.get("title", "").strip() or not re.match(r"^https?://", url):
            continue
        if re.search(r"(github\.com|zhihu\.com|xiaohongshu\.com|baidu\.com/s)", url, re.I):
            continue
        if url.lower() not in seen:
            seen.add(url.lower())
            results.append(item)
    return results


def relevant_repo_context(name: str, line: str) -> bool:
    value = f"{name} {line}".lower()
    positive = (
        "mine",
        "mining",
        "coal",
        "ppe",
        "helmet",
        "safety",
        "monitoring",
        "detection",
        "vision",
        "yolo",
        "ultralytics",
        "mmdetection",
        "detectron",
        "openmmlab",
        "underground",
        "矿",
        "煤",
        "井",
        "安全",
        "检测",
        "识别",
        "监测",
        "视觉",
    )
    generic_bad = ("neurons", "awesome", "tutorial", "demo", "examples")
    return any(token in value for token in positive) and not any(token in name.lower() for token in generic_bad)


def valid_repo_name(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name.strip()))


def paper_from_table_row(line: str, sources: tuple[str, ...]) -> dict[str, str] | None:
    if is_table_separator(line):
        return None
    cells = markdown_table_cells(line)
    if not cells or is_table_header(cells):
        return None
    url_match = re.search(r"https?://\S+", line)
    year_match = re.search(r"\b(20\d{2})\b", line)
    title = ""
    for cell in cells:
        if re.search(r"https?://", cell):
            continue
        if re.fullmatch(r"20\d{2}", cell):
            continue
        if valid_paper_title(cell):
            title = cell
            break
    if not title:
        return None
    source = first_match(line, sources)
    if not source:
        for cell in cells:
            if cell != title and not re.fullmatch(r"20\d{2}", cell) and not re.search(r"https?://", cell):
                source = cell[:24]
                break
    return {
        "title": title[:80],
        "source": source or "论文线索",
        "year": year_match.group(0) if year_match else "",
        "url": url_match.group(0).rstrip(").,，。") if url_match else "",
    }


def first_match(text: str, patterns: tuple[str, ...]) -> str:
    for pattern in patterns:
        if pattern.lower() in text.lower():
            return pattern
    return ""


def parse_papers(markdown: str) -> list[dict[str, str]]:
    body = section_body(markdown, ("论文", "文献", "前沿", "paper", "survey"))
    direct_urls = extract_unique_urls(body)
    direct_urls = [url for url in direct_urls if not re.search(r"(github\.com|zhihu\.com|xiaohongshu\.com|baidu\.com/s)", url, re.I)]
    if direct_urls:
        return paper_results_with_fallback([
            {"title": f"论文链接 {index}", "source": "论文线索", "year": "", "url": url}
            for index, url in enumerate(direct_urls, start=1)
        ])

    sources = ("煤炭学报", "工矿自动化", "煤炭科学技术", "ResearchGate", "IEEE", "arXiv", "Springer", "Elsevier", "CNKI", "MDPI")
    papers: list[dict[str, str]] = []
    seen: set[str] = set()

    def push_item(item: dict[str, str] | None) -> None:
        if not item:
            return
        title = item.get("title", "").strip()
        if not valid_paper_title(title) or title in seen:
            return
        seen.add(title)
        papers.append(item)

    current: dict[str, str] | None = None
    for line in candidate_lines(body):
        if "github" in line.lower() or "baseline" in line.lower():
            continue
        if "|" in line:
            push_item(current)
            current = None
            push_item(paper_from_table_row(line, sources))
            continue
        if any(token in line for token in ("以下为", "请以", "最终确认", "未经", "人工核验", "搜索线索", "中文核心期刊", "国际期刊", "GitHub开源项目", "GitHub 开源项目", "论文检索来源", "检索来源", "网络服务限制", "公开资料", "基于知识图谱", "需进一步核验")):
            continue
        url_match = re.search(r"https?://\S+", line)
        is_meta_line = any(token in line for token in ("链接", "地址", "URL", "核心内容", "核验状态", "来源链接"))
        if is_meta_line:
            if current and url_match:
                current["url"] = url_match.group(0).rstrip(").,，。")
            continue

        push_item(current)
        year_match = re.search(r"\b(20\d{2})\b", line)
        line_without_url = re.sub(r"https?://\S+", "", line)
        line_without_url = re.split(r"\s+-\s+", line_without_url, maxsplit=1)[0]
        title = strip_markdown(line_without_url)
        title = re.split(r"[。；;]", title)[0]
        title = title[:80]
        if not valid_paper_title(title):
            current = None
            continue
        current = {
            "title": title,
            "source": first_match(line, sources) or "论文线索",
            "year": year_match.group(1) if year_match else "",
            "url": url_match.group(0).rstrip(").,，。") if url_match else "",
        }
    push_item(current)
    return paper_results_with_fallback(papers)


def parse_baseline(markdown: str) -> list[dict[str, str]]:
    """Preserve actual repository links without renderer-side method ranking."""
    body = section_body(markdown, ("github", "baseline", "代码", "仓库", "开源"))
    results = []
    seen = set()
    for url in re.findall(r"https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", body):
        url = url.rstrip(".")
        name = "/".join(url.split("/")[-2:])
        if name.lower() not in seen:
            seen.add(name.lower())
            results.append({"name": name, "url": url, "use": "本轮报告提供的工程参考；适配性见调研正文。"})
    return results



def parse_advisors(markdown: str, state: dict) -> list[dict[str, str]]:
    body = section_body(markdown, ("导师", "课题组", "研究方向"))
    return diversify_advisors([item for item in parse_report_advisors(body) if is_valid_advisor(item)], 6)


BAD_ADVISOR_NAMES = {
    "学院",
    "部门",
    "职称",
    "方向",
    "匹配方向",
    "推荐理由",
    "导师推荐",
    "主导师优",
    "研究方向",
    "官网来源",
    "智能系统",
    "智能控制",
    "控制系统",
    "先进控制",
    "信息控制",
    "研究团队",
    "科研团队",
    "部门智能",
    "模式识别",
    "机械工程",
    "机械电气",
    "计算机科",
    "相关教师",
    "教师",
    "学院相关",
    "导师群体",
    "教师群体",
    "主导师",
    "导师优先",
    "安全",
    "煤矿",
}
BAD_ADVISOR_NAME_FRAGMENTS = (
    "学院",
    "导师",
    "优先",
    "建议",
    "联系",
    "项目",
    "方向",
    "部门",
    "职称",
    "系统",
    "控制",
    "工程",
    "团队",
    "研究",
    "信息",
    "智能",
    "机械",
    "电气",
    "模式",
    "识别",
    "计算机",
    "相关",
    "教师",
    "群体",
    "队伍",
)
ALLOWED_DEPARTMENT_KEYWORDS = (
    "计算机科学与技术学院",
    "人工智能学院",
    "安全工程学院",
    "矿业工程学院",
    "力学与土木工程学院",
    "机电工程学院",
    "信息与控制工程学院",
    "资源与地球科学学院",
    "化工学院",
    "环境与测绘学院",
    "电气工程学院",
    "低碳能源与动力工程学院",
    "材料与物理学院",
    "数学学院",
    "经济管理学院",
    "公共管理学院",
    "应急管理学院",
    "马克思主义学院",
    "外国语言文化学院",
    "建筑与设计学院",
    "人文与艺术学院",
    "体育学院",
    "孙越崎学院",
    "未来技术学院",
    "能源学院",
    "国家卓越工程师学院",
    "国际学院",
    "继续教育学院",
)
BLOCKED_DEPARTMENT_KEYWORDS = (
    "中国矿业大学北京",
    "北京",
    "机械与电气工程学院",
)


def is_valid_name(name: str) -> bool:
    name = name.strip()
    if not re.fullmatch(r"[\u4e00-\u9fff]{2,4}", name):
        return False
    return name not in BAD_ADVISOR_NAMES and not any(token in name for token in BAD_ADVISOR_NAME_FRAGMENTS)


def clean_department(value: str) -> str:
    value = re.sub(r"\s+", "", value or "")
    value = value.strip(" ：:，,。；;|｜-—–")
    for keyword in ALLOWED_DEPARTMENT_KEYWORDS:
        if keyword in value:
            return keyword
    if value in {"学院", "部门", "导师队伍", "师资队伍", "教师简介"}:
        return ""
    return value


def is_valid_department(value: str) -> bool:
    value = clean_department(value)
    if not value or any(token in value for token in BLOCKED_DEPARTMENT_KEYWORDS):
        return False
    return any(token in value for token in ALLOWED_DEPARTMENT_KEYWORDS)


def is_valid_advisor(item: dict[str, str]) -> bool:
    return is_valid_name(item.get("name", "")) and is_valid_department(item.get("department", ""))


def diversify_advisors(items: list[dict[str, str]], limit: int, max_per_department: int = 6) -> list[dict[str, str]]:
    picked: list[dict[str, str]] = []
    counts: dict[str, int] = {}
    overflow: list[dict[str, str]] = []
    for item in items:
        department = item.get("department", "").strip()
        if counts.get(department, 0) < max_per_department:
            picked.append(item)
            counts[department] = counts.get(department, 0) + 1
        else:
            overflow.append(item)
        if len(picked) >= limit:
            return picked
    for item in overflow:
        if len(picked) >= limit:
            break
        picked.append(item)
    return picked[:limit]


def is_online_advisor(item: dict[str, str]) -> bool:
    url = item.get("url", "").strip().lower()
    name = item.get("name", "").strip()
    if not name:
        return False
    return url.startswith(("http://", "https://"))










def parse_report_advisors(body: str) -> list[dict[str, str]]:
    advisors: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    seen: set[str] = set()

    def push(item: dict[str, str] | None) -> None:
        if not item:
            return
        name = item.get("name", "").strip()
        if not is_valid_advisor(item):
            return
        key = name or item.get("url", "") or item.get("direction", "")
        if not key or key in seen:
            return
        seen.add(key)
        advisors.append(item)

    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"^\d+[.)、]\s+", "", line)
        url_match = re.search(r"https?://\S+", line)
        if any(token in line for token in ("链接", "官网", "主页", "来源", "URL")):
            if current and url_match:
                current["url"] = url_match.group(0).rstrip(").,，。")
                current["source"] = "official-website"
            continue

        clean = strip_markdown(re.sub(r"https?://\S+", "", line))
        if not clean:
            continue
        if any(token in clean for token in ("导师群体", "教师群体", "课题组群体", "导师队伍", "师资队伍")):
            continue
        if re.match(r"^(学院|部门|职称|方向|匹配方向|推荐理由)[:：]", clean):
            continue
        name_match = re.match(r"([\u4e00-\u9fff]{2,4})", clean)
        if not name_match:
            continue
        push(current)
        parts = [part.strip(" ，,。()（）") for part in re.split(r"[，,、/|｜（）()]", clean) if part.strip()]
        name = name_match.group(1)
        if not is_valid_name(name):
            continue
        title = next((part for part in parts if any(word in part for word in ("教授", "副教授", "讲师", "研究员", "博导", "硕导"))), "")
        department = clean_department(next((part for part in parts if any(word in part for word in ("学院", "系", "中心", "实验室"))), ""))
        direction_parts = [part for part in parts if part not in {name, title, department}]
        current = {
            "name": name,
            "department": department,
            "title": title,
            "direction": "、".join(direction_parts[:4]) or clean[:120],
            "reason": "",
            "source": "official-website" if url_match else "report",
            "url": url_match.group(0).rstrip(").,，。") if url_match else "",
        }
    push(current)
    return advisors


def parse_route(markdown: str, state: dict) -> dict:
    selection = state.get("selection", {}) if isinstance(state, dict) else {}
    center = " / ".join(
        item
        for item in (
            str(selection.get("field", "")).strip(),
            str(selection.get("scene", "")).strip(),
        )
        if item
    ) or "技术路线"
    body = section_body(markdown, ("技术路线", "研究建议", "方案", "路线"))
    branches: list[dict[str, str]] = []
    for line in candidate_lines(body):
        clean = strip_markdown(line)
        if not clean:
            continue
        title = re.split(r"[:：，,。；;]", clean, maxsplit=1)[0][:18]
        detail = clean[:80]
        branches.append({"title": title, "detail": detail})
        if len(branches) >= 6:
            break
    return {"center": center, "branches": branches}


def build_structured_results(markdown: str, state: dict) -> dict:
    return {
        "papers": parse_papers(markdown),
        "baseline": parse_baseline(markdown),
        "advisors": parse_advisors(markdown, state),
        "route": parse_route(markdown, state),
        "experience": [],
    }


def paper_urls_in_text(markdown: str) -> list[str]:
    return [
        url
        for url in extract_unique_urls(markdown)
        if not re.search(r"(github\.com|zhihu\.com|xiaohongshu\.com|baidu\.com/s)", url, re.I)
    ]


def ensure_minimum_report_content(title: str, content: str, state: dict) -> str:
    """Preserve supplied research without inventing missing facts."""
    return content.strip() + "\n"


def pick_sections(markdown: str) -> dict:
    buckets = {
        "papers": {"title": "论文线索", "patterns": ("论文", "文献", "前沿", "paper", "survey"), "content": []},
        "baseline": {"title": "GitHub baseline", "patterns": ("github", "baseline", "代码", "仓库", "开源"), "content": []},
        "advisors": {"title": "导师匹配", "patterns": ("导师", "课题组", "研究方向"), "content": []},
        "route": {"title": "技术路线", "patterns": ("技术路线", "研究建议", "可行性", "方案", "路线"), "content": []},
        "experience": {"title": "科研经验参考", "patterns": ("科研经验", "知乎", "小红书", "经验参考", "答辩", "结题"), "content": []},
    }
    for section in markdown_sections(markdown):
        title_lower = section["title"].lower()
        combined = f"### {section['title']}\n{section['content']}"
        for key, bucket in buckets.items():
            if any(pattern.lower() in title_lower for pattern in bucket["patterns"]):
                bucket["content"].append(combined)

    result = {}
    for key, bucket in buckets.items():
        content = "\n\n".join(bucket["content"]).strip()
        result[key] = {
            "title": bucket["title"],
            "content": compact_text(content) if content else "报告已生成，完整内容请点击下方文件下载查看。",
            "items": [],
        }
    return result


def collect_artifacts(result: dict) -> list[dict[str, str]]:
    artifacts: list[dict[str, str]] = []
    exports = result.get("exports")
    if isinstance(exports, dict):
        files = exports.get("files")
        if isinstance(files, dict):
            labels = {
                "html": "MineIntel HTML 完整报告",
                "deck": "MineIntel 逐页展示 Deck",
                "route_diagram": "技术路线 Excalidraw 源文件",
                "tex": "文献综述 LaTeX 源码",
                "pdf": "文献综述 PDF",
            }
            for key in ("html", "deck", "route_diagram", "tex", "pdf"):
                file_path = files.get(key)
                if not file_path:
                    continue
                artifacts.append({"label": labels.get(key, key), "path": file_path, "kind": key})
    return artifacts


def update_progress_from_report(title: str, content: str, output_dir: Path, result: dict) -> None:
    state = load_progress_state()
    state.setdefault("task", title)
    state["status"] = "done"
    state["current_step"] = "report"
    state["current_label"] = "报告生成与导出"
    state["message"] = "报告已生成并导出完成，可在结果区查看和下载。"
    state["percent"] = 100
    state["completed"] = ["confirm", "knowledge", "paper", "baseline", "advisor", "experience", "report"]
    state.setdefault("selection", {})["formats"] = "HTML 完整报告 / 逐页展示 Deck / 文献综述 LaTeX / PDF"
    state["sections"] = pick_sections(content)
    state["results"] = build_structured_results(content, state)
    state["artifacts"] = collect_artifacts(result)
    output_dir = output_dir.resolve()
    try:
        relative_dir = str(output_dir.relative_to(PACKAGE_DIR.resolve()))
    except ValueError:
        relative_dir = str(output_dir)
    state["output"] = {
        "run_id": output_dir.name,
        "dir": str(output_dir),
        "relative_dir": relative_dir,
    }
    logs = [
        log for log in state.setdefault("logs", [])
        if "PowerPoint" not in str(log.get("text", ""))
    ]
    logs.append({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "text": state["message"]})
    state["logs"] = logs[-12:]
    state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_progress_state(state)


def main() -> int:
    parser = argparse.ArgumentParser(description="Save MineIntel HTML report, deck, and literature-review deliverables.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--content")
    parser.add_argument("--content-file")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    parser.add_argument(
        "--formats",
        default="html,deck,tex,pdf",
        help="Comma-separated formats: html, deck, tex, pdf. Default: html,deck,tex,pdf.",
    )
    parser.add_argument("--no-format", action="store_true", help="Create the run directory but skip deliverable export.")
    args = parser.parse_args()

    try:
        state = load_progress_state()
        content = sanitize_report_content(read_content(args), state)
        complete_content = ensure_minimum_report_content(args.title, content, state)
        decorated_content = decorate_markdown(args.title, complete_content, state)
        out_dir = make_run_dir(Path(args.output_dir), args.title)
        result = {
            "status": "success",
            "dir": str(out_dir.resolve()),
            "title": args.title,
        }
        if not args.no_format:
            try:
                result["exports"] = export_formats(args.title, decorated_content, out_dir, args.formats)
            except Exception as export_exc:
                result["export_warning"] = str(export_exc)
        update_progress_from_report(args.title, complete_content, out_dir, result)
    except Exception as exc:
        result = {"status": "error", "error": str(exc)}

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
