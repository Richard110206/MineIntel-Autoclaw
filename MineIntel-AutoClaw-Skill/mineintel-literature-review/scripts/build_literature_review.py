#!/usr/bin/env python3
"""Build a MineIntel literature-review LaTeX source and compile it with xelatex."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


BASE_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = BASE_DIR.parent
WORKSPACE_DIR = PACKAGE_DIR.parent
OUTPUT_ROOT = PACKAGE_DIR / "output"
XELATEX_CONFIG_PATHS = (
    BASE_DIR / "config" / "xelatex_path.txt",
    PACKAGE_DIR / "mineintel-report-export" / "config" / "xelatex_path.txt",
    PACKAGE_DIR / "mineintel-research" / "config" / "xelatex_path.txt",
)


def display_path(path: Path) -> str:
    """结果输出统一使用相对包根的路径，避免泄露本机目录结构。"""
    try:
        return path.resolve().relative_to(PACKAGE_DIR).as_posix()
    except ValueError:
        return path.as_posix()


@dataclass
class Paper:
    title: str
    source: str = ""
    summary: str = ""
    url: str = ""
    section: str = ""


def safe_filename(title: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", title).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:60] or "mineintel_report"


def read_content(args: argparse.Namespace) -> str:
    if args.content_file:
        return Path(args.content_file).read_text(encoding="utf-8")
    if args.content:
        return args.content
    data = sys.stdin.read()
    if data.strip():
        return data
    raise ValueError("No report content provided. Use --content, --content-file, or stdin.")


def strip_markdown(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", str(text), flags=re.S)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"[#>*_]+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -:：，,。")


def split_sections(markdown: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current_title = "报告摘要"
    lines: list[str] = []

    def flush() -> None:
        body = "\n".join(lines).strip()
        if body:
            sections.append({"title": strip_markdown(current_title), "content": body})

    for raw in markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", raw.strip())
        if heading:
            flush()
            current_title = heading.group(2)
            lines = []
        else:
            lines.append(raw)
    flush()
    return sections


def section_text(markdown: str, patterns: tuple[str, ...], limit: int = 1000) -> str:
    parts: list[str] = []
    for section in split_sections(markdown):
        title = section["title"].lower()
        if any(pattern.lower() in title for pattern in patterns):
            clean_lines = []
            for raw in section["content"].splitlines():
                line = raw.strip()
                if line and not line.startswith("|"):
                    clean_lines.append(line)
            parts.append(strip_markdown(" ".join(clean_lines)))
    text = re.sub(r"\s+", " ", " ".join(parts)).strip()
    text = re.sub(r"\s+-\s+", "；", text)
    if len(text) > limit:
        return text[: limit - 1].rstrip("，。；; ") + "…"
    return text


def extract_urls(text: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"https?://[^\s)）\]】>,，。；;]+", text):
        url = match.group(0).rstrip(").,，。；;")
        if url not in seen:
            urls.append(url)
            seen.add(url)
    return urls




def is_paper_section_title(title: str) -> bool:
    lowered = strip_markdown(title).lower()
    blocked = ("github", "baseline", "导师", "课题组", "技术路线", "研究建议", "科研经验", "搜索路径", "溯源")
    if any(token.lower() in lowered for token in blocked):
        return False
    allowed = ("论文", "文献", "前沿线索", "国际前沿", "经典代表性线索", "近年前沿线索")
    return any(token.lower() in lowered for token in allowed)


def is_paper_url(url: str) -> bool:
    if not url:
        return False
    blocked = (
        r"github\.com",
        r"zhihu\.com",
        r"xiaohongshu\.com",
        r"baidu\.com/s",
        r"faculty\.cumt\.edu\.cn",
        r"cs\.cumt\.edu\.cn/info/",
        r"safe\.cumt\.edu\.cn/info/",
        r"cese\.cumt\.edu\.cn/info/",
        r"cmee\.cumt\.edu\.cn/info/",
        r"siee\.cumt\.edu\.cn/info/",
        r"导师|教师|teacher|faculty",
    )
    return not re.search("|".join(blocked), url, re.I)


def reference_urls_from_paper_sections(markdown: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for section in split_sections(markdown):
        if not is_paper_section_title(section["title"]):
            continue
        for url in extract_urls(section["content"]):
            if is_paper_url(url) and url not in seen:
                urls.append(url)
                seen.add(url)
    return urls




def ensure_minimum_papers(papers: list[Paper], minimum: int = 5) -> list[Paper]:
    results: list[Paper] = []
    seen: set[str] = set()
    for paper in papers:
        if not valid_paper_title(paper.title, paper.section):
            continue
        if paper.url and not is_paper_url(paper.url):
            continue
        key = (paper.url or paper.title).lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(paper)
    return results


def markdown_table_cells(line: str) -> list[str]:
    value = line.strip()
    if not value.startswith("|") or "|" not in value[1:]:
        return []
    value = value.strip("|")
    return [strip_markdown(cell.strip()) for cell in value.split("|")]


def is_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", cell.replace(" ", "")) for cell in cells)


def header_index(headers: list[str], terms: tuple[str, ...], fallback: int | None = None) -> int | None:
    for index, header in enumerate(headers):
        if any(term in header for term in terms):
            return index
    return fallback if fallback is not None and fallback < len(headers) else None


def paper_from_table_row(headers: list[str], row: list[str], section: str, raw: str) -> Paper | None:
    if not row or is_table_separator(row):
        return None
    if len(row) == 1:
        return None
    title_index = header_index(headers, ("线索", "标题", "论文", "文献", "题名", "名称"), 1 if re.fullmatch(r"\d+", row[0]) else 0)
    if title_index is None or title_index >= len(row):
        return None
    title = strip_markdown(row[title_index])[:180]
    if not valid_paper_title(title, section):
        return None
    source_index = header_index(headers, ("来源", "期刊", "平台", "出处"), None)
    year_index = header_index(headers, ("年份", "时间", "发表"), None)
    summary_index = header_index(headers, ("价值", "内容", "摘要", "说明", "方向"), None)
    source_parts: list[str] = []
    if source_index is not None and source_index < len(row):
        source_parts.append(row[source_index])
    if year_index is not None and year_index < len(row):
        source_parts.append(row[year_index])
    summary = row[summary_index] if summary_index is not None and summary_index < len(row) else ""
    urls = extract_urls(raw)
    return Paper(title=title, source="，".join(part for part in source_parts if part), summary=summary[:420], url=urls[0] if urls else "", section=section)


def valid_paper_title(title: str, section: str) -> bool:
    value = strip_markdown(title)
    if len(value) < 6:
        return False
    bad = (
        "导师",
        "GitHub",
        "baseline",
        "科研经验",
        "搜索路径",
        "技术路线",
        "经验来源",
        "可采纳建议",
        "不确定性说明",
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
    )
    if any(token.lower() in value.lower() for token in bad):
        return False
    useful = (
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
        "视觉",
        "矿",
        "煤",
        "井",
        "YOLO",
        "SLAM",
        "PPE",
        "VLM",
        "Survey",
        "Review",
        "Detection",
        "Monitoring",
        "Mining",
        "Safety",
        "Dataset",
    )
    return any(term.lower() in value.lower() for term in useful) or any(term in section for term in ("论文", "前沿", "文献"))


def extract_papers(markdown: str) -> list[Paper]:
    papers: list[Paper] = []
    seen: set[str] = set()
    current: Paper | None = None
    current_heading = ""
    in_paper_parent = False
    active_paper_area = False
    table_headers: list[str] = []

    def push() -> None:
        nonlocal current
        if current and current.title and current.title not in seen and valid_paper_title(current.title, current.section):
            seen.add(current.title)
            papers.append(current)
        current = None

    for raw in markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            push()
            current_heading = strip_markdown(heading.group(2))
            table_headers = []
            level = len(heading.group(1))
            if level <= 2:
                in_paper_parent = is_paper_section_title(current_heading)
            active_paper_area = is_paper_section_title(current_heading) or (
                in_paper_parent
                and not any(token.lower() in current_heading.lower() for token in ("github", "baseline", "导师", "技术路线", "研究建议", "科研经验", "搜索路径", "溯源"))
            )
            continue

        cells = markdown_table_cells(line)
        if cells:
            push()
            if not active_paper_area:
                continue
            if is_table_separator(cells):
                continue
            header_terms = ("序号", "线索", "标题", "论文", "文献", "来源", "期刊", "年份", "链接", "价值", "内容")
            if not table_headers and sum(1 for cell in cells if any(term in cell for term in header_terms)) >= 2:
                table_headers = cells
                continue
            if not table_headers:
                table_headers = [f"列{index}" for index in range(len(cells))]
            paper = paper_from_table_row(table_headers, cells, current_heading, line)
            if paper and paper.title not in seen:
                seen.add(paper.title)
                papers.append(paper)
            continue

        item = re.match(r"^\d+[.)、]\s+\*\*(.+?)\*\*(?:\s*[-－]\s*(.+))?$", line)
        if item:
            push()
            if not active_paper_area:
                continue
            title = strip_markdown(item.group(1))[:160]
            source = strip_markdown(item.group(2) or "")
            current = Paper(title=title, source=source, section=current_heading)
            continue
        if current is None:
            continue
        clean = re.sub(r"^[-*+]\s+", "", line).strip()
        if clean.startswith(("核心内容", "综述价值", "主要内容", "价值")):
            current.summary = strip_markdown(clean.split("：", 1)[-1])[:420]
        elif clean.startswith(("链接", "地址", "来源链接")):
            urls = extract_urls(clean)
            if urls:
                current.url = urls[0]
        elif clean.startswith(("来源", "平台")) and not current.source:
            current.source = strip_markdown(clean.split("：", 1)[-1])[:80]
    push()

    if papers:
        return ensure_minimum_papers(papers)
    url_papers = [
        Paper(title=f"论文线索 {index}", url=url, section="链接线索")
        for index, url in enumerate(extract_urls(markdown), 1)
        if is_paper_url(url)
    ]
    return ensure_minimum_papers(url_papers)


def classify_papers(papers: list[Paper]) -> tuple[list[Paper], list[Paper]]:
    domestic: list[Paper] = []
    international: list[Paper] = []
    for paper in papers:
        joined = f"{paper.title} {paper.source} {paper.section}"
        if re.search(r"[\u4e00-\u9fff]", paper.title) or any(token in joined for token in ("煤炭", "工矿", "矿业科学", "知网", "维普", "学报")):
            domestic.append(paper)
        else:
            international.append(paper)
    return domestic, international


def method_family(paper: Paper) -> str:
    text = f"{paper.title} {paper.summary}".lower()
    if "yolo" in text:
        return "YOLO 系目标检测方法"
    if "safety helmet" in text or "安全帽" in text or "ppe" in text:
        return "人员防护装备/安全帽识别"
    if "smoke" in text or "火灾" in text or "烟雾" in text:
        return "火灾烟雾视觉监测"
    if "slam" in text or "robot" in text or "机器人" in text:
        return "巡检机器人感知与导航"
    if "dataset" in text or "数据集" in text:
        return "井下场景数据集与基准构建"
    if "review" in text or "survey" in text or "综述" in text:
        return "矿井视觉/安全监测综述"
    if "vision language" in text or "vlm" in text or "多模态" in text:
        return "多模态视觉语言模型"
    return "矿井视觉监测方法"


def summarize_paper(paper: Paper) -> str:
    summary = paper.summary or "该条目提供了可继续核验的研究线索。"
    source = f"来源为 {paper.source}。" if paper.source else "来源仍需二次核验。"
    return f"{source}从题名和公开摘要线索看，它主要支撑“{method_family(paper)}”这一类问题；可用于论证本选题的场景合理性、方法选择或实验对比。具体实验数据和结论应以原文为准。{summary}"


def group_review_paragraph(papers: list[Paper], group_name: str) -> list[str]:
    family_counter = Counter(method_family(paper) for paper in papers)
    family_summary = "；".join(f"{family} {count} 条" for family, count in family_counter.most_common(4))
    source_counter = Counter(paper.source for paper in papers if paper.source)
    source_summary = "、".join(source for source, _ in source_counter.most_common(4))
    if not family_summary:
        family_summary = "矿井视觉监测方法、工程系统线索和数据集构建"
    if not source_summary:
        source_summary = "公开论文数据库、期刊官网和检索线索"

    if "中文" in group_name:
        text = (
            f"{group_name}共抽取 {len(papers)} 条可核验线索，来源主要包括{source_summary}。"
            f"这些文献集中在{family_summary}，更适合支撑本课题的场景必要性、工程指标、矿井约束和系统落地论证。"
            "正文不再逐条重复论文题名，避免和文末参考文献重复；具体题名、链接和来源统一放在文末参考文献列表。"
        )
    else:
        text = (
            f"{group_name}共抽取 {len(papers)} 条可核验线索，来源主要包括{source_summary}。"
            f"这些研究集中在{family_summary}，更适合支撑模型改进、鲁棒性设计、数据集建设和对比实验。"
            "本课题应从其中提取方法路线，而不是把论文题名逐条堆在正文里；具体条目统一放在文末参考文献列表。"
        )
    return [text, ""]


def build_review_markdown(title: str, markdown: str) -> str:
    """Format this research only; synthesis must be supplied by the research agent."""
    papers = extract_papers(markdown)
    lines = [f"# {title}：文献调研", "", "## 资料状态", "",
             f"本次提取 {len(papers)} 条文献线索。提取不等于全文核验；正式引用前需核验原文。", ""]
    sections = (
        ("研究背景", ("研究主题", "主题概述", "背景")),
        ("学生能力与选题匹配", ("能力", "项目记忆", "选题", "候选")),
        ("场景难点与资源缺口", ("难点", "痛点", "资源", "约束")),
        ("文献分析", ("文献分析", "论文", "文献", "前沿")),
        ("推进路线", ("技术路线", "研究建议", "路线", "里程碑")),
    )
    for heading, patterns in sections:
        body = section_text(markdown, patterns, 4000)
        lines.extend([f"## {heading}", "", body or "本轮调研未提供该部分，尚需补充。", ""])
    return "\n".join(lines)



def collect_reference_items(papers: list[Paper], markdown: str) -> list[dict[str, str]]:
    """汇总参考文献条目：论文优先，其次报告正文链接，最后补充稳定公开链接。"""
    items: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for paper in papers:
        if paper.url and paper.url not in seen_urls:
            items.append(
                {"title": paper.title, "source": paper.source, "url": paper.url}
            )
            seen_urls.add(paper.url)
    for index, url in enumerate(reference_urls_from_paper_sections(markdown), 1):
        if url in seen_urls or not is_paper_url(url):
            continue
        items.append({"title": f"补充链接 {index}", "source": "", "url": url})
        seen_urls.add(url)
        if len(items) >= 12:
            break
    return items


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in str(text))


def latex_text(text: str) -> str:
    value = re.sub(r"https?://\S+", lambda m: r"\url{" + m.group(0).rstrip(").,，。；;") + "}", str(text))
    parts = re.split(r"(\\url\{[^}]+\})", value)
    return "".join(part if part.startswith(r"\url{") else latex_escape(part) for part in parts)


def split_inline_ordered_items(text: str) -> tuple[str, list[str]] | None:
    value = str(text).strip()
    arabic = list(re.finditer(r"(?<![\w/.-])(\d{1,2})[.、]\s+", value))
    if len(arabic) >= 2:
        intro = value[: arabic[0].start()].strip()
        items = []
        for index, match in enumerate(arabic):
            end = arabic[index + 1].start() if index + 1 < len(arabic) else len(value)
            item = value[match.end() : end].strip(" ；;")
            if item:
                items.append(item)
        if len(items) >= 2:
            return intro, items

    chinese = list(re.finditer(r"(第一|第二|第三|第四|第五|第六|第七|第八|第九|第十)[，、:：]\s*", value))
    if len(chinese) >= 2:
        intro = value[: chinese[0].start()].strip()
        items = []
        for index, match in enumerate(chinese):
            end = chinese[index + 1].start() if index + 1 < len(chinese) else len(value)
            item = value[match.end() : end].strip(" ；;")
            if item:
                items.append(item)
        if len(items) >= 2:
            return intro, items

    chinese_plain = list(re.finditer(r"(一是|二是|三是|四是|五是|六是|七是|八是|九是|十是)", value))
    if len(chinese_plain) >= 2:
        intro = value[: chinese_plain[0].start()].strip()
        items = []
        for index, match in enumerate(chinese_plain):
            end = chinese_plain[index + 1].start() if index + 1 < len(chinese_plain) else len(value)
            item = value[match.end() : end].strip(" ；;")
            if item:
                items.append(item)
        if len(items) >= 2:
            return intro, items

    return None


def markdown_to_latex_body(markdown: str) -> str:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    para: list[str] = []
    in_itemize = False
    first_heading = True

    def flush_para() -> None:
        if para:
            text = " ".join(para)
            ordered = split_inline_ordered_items(text)
            if ordered:
                intro, items = ordered
                if intro:
                    out.append(latex_text(intro))
                    out.append("")
                out.append("\\begin{enumerate}")
                for item in items:
                    out.append("\\item " + latex_text(item))
                out.append("\\end{enumerate}")
            else:
                out.append(latex_text(text))
            out.append("")
            para.clear()

    def close_itemize() -> None:
        nonlocal in_itemize
        if in_itemize:
            out.append("\\end{itemize}")
            out.append("")
            in_itemize = False

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_para()
            close_itemize()
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_para()
            close_itemize()
            level = len(heading.group(1))
            heading_text = strip_markdown(heading.group(2))
            if first_heading and level == 1:
                first_heading = False
                continue
            first_heading = False
            if heading_text == "摘要":
                out.append(r"\section*{摘要}")
                out.append(r"\addcontentsline{toc}{section}{摘要}")
                out.append("")
                continue
            command = "section" if level <= 2 else "subsection" if level == 3 else "subsubsection"
            out.append(f"\\{command}{{{latex_text(heading_text)}}}")
            continue
        first_heading = False
        if line.startswith(">"):
            flush_para()
            close_itemize()
            out.append("\\begin{quote}")
            out.append(latex_text(strip_markdown(line.lstrip("> "))))
            out.append("\\end{quote}")
            out.append("")
            continue
        bullet = re.match(r"^[-*+]\s+(.+)$", line)
        if bullet:
            flush_para()
            if not in_itemize:
                out.append("\\begin{itemize}")
                in_itemize = True
            out.append("\\item " + latex_text(strip_markdown(bullet.group(1))))
            continue
        bold_line = re.match(r"^\*\*(.+?)\*\*\s*$", line)
        if bold_line:
            flush_para()
            close_itemize()
            out.append("\\par\\noindent\\textbf{" + latex_text(strip_markdown(bold_line.group(1))) + "}\\par")
            out.append("")
            continue
        close_itemize()
        para.append(strip_markdown(line))
    flush_para()
    close_itemize()
    return "\n".join(out)


def format_reference_item(item: dict[str, str], index: int) -> str:
    parts = [latex_text(item.get("title", "")).rstrip(".")]
    if item.get("source", ""):
        parts.append(latex_text(item["source"]))
    if item.get("url"):
        parts.append(r"\url{" + item["url"] + "}")
    return r"\bibitem{mineintel-ref-" + str(index) + "} " + ". ".join(parts) + "."


def references_block(references: list[dict[str, str]]) -> str:
    if not references:
        return "\\section*{参考文献}\n当前报告未抽取到稳定链接，需回到论文检索阶段补充。"
    lines = [r"\begin{thebibliography}{99}", r"\addcontentsline{toc}{section}{参考文献}"]
    for index, item in enumerate(references, 1):
        lines.append(format_reference_item(item, index))
    lines.append(r"\end{thebibliography}")
    return "\n".join(lines)


def latex_document(title: str, review_markdown: str, references: list[dict[str, str]] | None = None) -> str:
    body = markdown_to_latex_body(review_markdown)
    pdf_title = latex_escape(f"{title}：文献综述")
    return rf"""\documentclass[UTF8,zihao=-4]{{ctexart}}
\usepackage[a4paper,top=2.5cm,bottom=2.5cm,left=2.6cm,right=2.6cm]{{geometry}}
\usepackage{{xcolor}}
\usepackage{{fancyhdr}}
\usepackage{{setspace}}
\usepackage{{enumitem}}
\usepackage{{url}}
\usepackage{{hyperref}}
\definecolor{{minegreen}}{{HTML}}{{2F7D32}}
\definecolor{{mineblue}}{{HTML}}{{1F4E79}}
\hypersetup{{
  colorlinks=true, linkcolor=mineblue, urlcolor=mineblue, citecolor=mineblue,
  pdftitle={{{pdf_title}}}, pdfauthor={{MineIntel 矿小智}}, pdflang={{zh-CN}}
}}
\Urlmuskip=0mu plus 2mu
\sloppy
\setstretch{{1.22}}
\setlist{{itemsep=2pt,topsep=4pt,parsep=0pt}}
\setcounter{{secnumdepth}}{{2}}
\setcounter{{tocdepth}}{{2}}
\ctexset{{
  section={{format=\Large\bfseries\color{{minegreen}}}},
  subsection={{format=\large\bfseries}},
  subsubsection={{format=\normalsize\bfseries}}
}}
\pagestyle{{fancy}}
\fancyhf{{}}
\fancyhead[L]{{\small\color{{minegreen}}MineIntel 文献综述}}
\fancyhead[R]{{\small\nouppercase{{\leftmark}}}}
\fancyfoot[C]{{\small 第 \thepage\ 页}}
\renewcommand{{\headrulewidth}}{{0.4pt}}
\renewcommand{{\headrule}}{{\color{{minegreen}}\hrule width\headwidth height \headrulewidth}}
\title{{\textbf{{{latex_text(title + "：文献综述")}}}\\\large MineIntel 矿小智科研情报}}
\author{{CUMT MineIntel / AutoClaw Native Skill}}
\date{{{latex_text(datetime.now().strftime("%Y-%m-%d"))}}}
\begin{{document}}
\maketitle
\thispagestyle{{fancy}}
\tableofcontents
\vspace{{1em}}
{body}

{references_block(references or [])}
\end{{document}}
"""


def configured_xelatex_paths() -> list[Path]:
    paths: list[Path] = []
    for config_path in XELATEX_CONFIG_PATHS:
        if not config_path.exists():
            continue
        for raw in config_path.read_text(encoding="utf-8").splitlines():
            value = raw.strip()
            if not value or value.startswith("#"):
                continue
            path = Path(value.strip('"'))
            if not path.is_absolute():
                path = (config_path.parent / path).resolve()
            paths.append(path)
    return paths


def inside_workspace(path: Path) -> bool:
    try:
        path.resolve().relative_to(WORKSPACE_DIR.resolve())
        return True
    except ValueError:
        return False


def find_xelatex() -> str | None:
    candidate = shutil.which("xelatex")
    if candidate and inside_workspace(Path(candidate)):
        return candidate
    candidates = configured_xelatex_paths() + [
        WORKSPACE_DIR / "local_tools" / "MiKTeX" / "miktex" / "bin" / "x64" / "xelatex.exe",
        WORKSPACE_DIR / "local_tools" / "miktex" / "miktex" / "bin" / "x64" / "xelatex.exe",
        WORKSPACE_DIR / "local_tools" / "tex" / "xelatex.exe",
    ]
    for path in candidates:
        if path.exists() and inside_workspace(path):
            return str(path)
    return None


def build_latex_env(xelatex: str) -> dict[str, str]:
    env = os.environ.copy()
    compiler_path = Path(xelatex).resolve()
    env["PATH"] = str(compiler_path.parent) + os.pathsep + env.get("PATH", "")
    runtime_dir = WORKSPACE_DIR / "local_tools" / ".miktex-runtime"
    for sub in ("config", "data", "fontconfig-cache"):
        (runtime_dir / sub).mkdir(parents=True, exist_ok=True)
    compiler_root = compiler_path.parents[3]
    fontconfig_dir = runtime_dir / "config" / "fontconfig"
    fontconfig_dir.mkdir(parents=True, exist_ok=True)
    fonts_conf = fontconfig_dir / "fonts.conf"
    default_fontconfig_dir = compiler_root / "fontconfig" / "config"
    default_fonts_conf = default_fontconfig_dir / "fonts.conf"

    def write_fonts_conf(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        cache_dir = (runtime_dir / "fontconfig-cache").as_posix()
        windows_fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        path.write_text(
            f"""<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>{windows_fonts.as_posix()}</dir>
  <dir>{(compiler_root / "fonts").as_posix()}</dir>
  <cachedir>{cache_dir}</cachedir>
  <config><rescan><int>30</int></rescan></config>
</fontconfig>
""",
            encoding="utf-8",
        )

    write_fonts_conf(fonts_conf)
    if default_fontconfig_dir.exists():
        write_fonts_conf(default_fonts_conf)
    env["MIKTEX_USERCONFIG"] = str(runtime_dir / "config")
    env["MIKTEX_USERDATA"] = str(runtime_dir / "data")
    env["MIKTEX_USERINSTALL"] = str(compiler_root)
    env["MIKTEX_AUTO_INSTALL"] = "0"
    env["FONTCONFIG_FILE"] = str(fonts_conf)
    env["FONTCONFIG_PATH"] = str(fontconfig_dir)
    return env


def initialize_miktex_runtime(xelatex: str, env: dict[str, str]) -> None:
    """Prepare workspace-local MiKTeX runtime without network access.

    Portable MiKTeX may refuse to run before a first update check. For the
    demo workspace we only need deterministic local compilation, so the script
    records local setup timestamps and disables package auto-install. Missing
    packages still fail normally instead of downloading anything.
    """
    initexmf = Path(xelatex).with_name("initexmf.exe")
    if not initexmf.exists() or not inside_workspace(initexmf):
        return
    now = str(int(time.time()))
    values = (
        f"[Setup]LastUserUpdateCheck={now}",
        f"[Setup]LastUserUpdate={now}",
        f"[Setup]LastUserUpdateDb={now}",
        f"[Setup]LastUserDiagnose={now}",
        f"[Setup]LastAdminUpdateCheck={now}",
        f"[Setup]LastAdminUpdate={now}",
        f"[Setup]LastAdminUpdateDb={now}",
        f"[Setup]LastAdminDiagnose={now}",
        "[MPM]AutoInstall=0",
    )
    for value in values:
        try:
            subprocess.run(
                [str(initexmf), f"--set-config-value={value}"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return
    try:
        subprocess.run(
            [str(initexmf), "--update-fndb"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return


def cleanup_latex_temp(tex_path: Path) -> None:
    for suffix in (".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk"):
        path = tex_path.with_suffix(suffix)
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
    synctex = Path(str(tex_path.with_suffix("")) + ".synctex.gz")
    try:
        if synctex.exists():
            synctex.unlink()
    except OSError:
        pass


def compile_latex(tex_path: Path) -> dict[str, Any]:
    xelatex = find_xelatex()
    if not xelatex:
        return {
            "status": "skipped",
            "warning": "工作区内未找到 xelatex，已保留文献综述 tex 源码。",
        }
    env = build_latex_env(xelatex)
    initialize_miktex_runtime(xelatex, env)
    runs = []
    last: subprocess.CompletedProcess[str] | None = None
    for _ in range(2):
        try:
            last = subprocess.run(
                [xelatex, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
                cwd=str(tex_path.parent),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
            )
        except subprocess.TimeoutExpired as exc:
            runs.append({"returncode": "timeout", "tail": str(exc)[-1200:]})
            return {"status": "error", "compiler": xelatex, "runs": runs}
        except OSError as exc:
            runs.append({"returncode": "oserror", "tail": str(exc)[-1200:]})
            return {"status": "error", "compiler": xelatex, "runs": runs}
        runs.append({"returncode": last.returncode, "tail": (last.stdout or "")[-1200:]})
        if last.returncode != 0:
            break
    pdf_path = tex_path.with_suffix(".pdf")
    if last and last.returncode == 0 and pdf_path.exists():
        cleanup_latex_temp(tex_path)
        return {"status": "success", "compiler": xelatex, "pdf": display_path(pdf_path), "runs": len(runs)}
    cleanup_latex_temp(tex_path)
    return {"status": "error", "compiler": xelatex, "runs": runs}


def export(title: str, markdown: str, output_dir: Path, filename: str | None = None, compile_pdf: bool = True) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(filename or title)
    papers = extract_papers(markdown)
    review_md = build_review_markdown(title, markdown)
    references = collect_reference_items(papers, markdown)
    tex_path = output_dir / f"{stem}_literature_review.tex"
    tex_path.write_text(latex_document(title, review_md, references), encoding="utf-8")
    files: dict[str, str] = {"tex": display_path(tex_path)}
    compile_result: dict[str, Any] | None = None
    if compile_pdf:
        compile_result = compile_latex(tex_path)
        pdf_path = tex_path.with_suffix(".pdf")
        if compile_result.get("status") == "success" and pdf_path.exists():
            files["pdf"] = display_path(pdf_path)
    result: dict[str, Any] = {
        "status": "success",
        "title": title,
        "files": files,
        "paper_count": len(papers),
        "reference_count": len(references),
    }
    if compile_result:
        result["latex_compile"] = compile_result
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build MineIntel literature-review LaTeX and PDF.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--content")
    parser.add_argument("--content-file")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    parser.add_argument("--no-pdf", action="store_true", help="Only generate .tex.")
    args = parser.parse_args()
    try:
        result = export(args.title, read_content(args), Path(args.output_dir), compile_pdf=not args.no_pdf)
    except Exception as exc:
        result = {"status": "error", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
