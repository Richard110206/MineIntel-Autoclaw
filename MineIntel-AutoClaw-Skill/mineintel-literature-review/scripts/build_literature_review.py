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


DEFAULT_REFERENCE_LINKS = [
    ("机器视觉感知理论与技术在煤炭工业领域应用进展综述", "http://www.gkzdh.cn/cn/article/pdf/preview/10.13272/j.issn.1671-251x.2022100087.pdf"),
    ("矿井视觉计算体系架构与关键技术", "https://www.mtkxjs.com.cn/cn/article/pdf/preview/10.12438/cst.2023-0152.pdf"),
    ("煤矿井下工业视频图像增强技术研究与分析", "http://www.chinaminingmagazine.com/cn/article/pdf/preview/10.12075/j.issn.1004-4051.20240273.pdf"),
    ("矿井视频图像目标检测与隐患识别方法研究综述", "https://mtkxjs.com.cn/cn/article/pdf/preview/10.12438/cst.2025-1116.pdf"),
    ("Safety monitoring method of moving target in underground coal mine based on computer vision processing", "https://www.nature.com/articles/s41598-022-22564-8"),
    ("The Future of Mine Safety: Anti-Collision Systems Based on Computer Vision in Underground Mines", "https://www.mdpi.com/1424-8220/23/9/4294"),
    ("An open paradigm dataset for intelligent monitoring of underground drilling operations in coal mines", "https://www.nature.com/articles/s41597-025-05118-1"),
    ("全国煤矿智能化建设典型案例汇编", "http://www.nea.gov.cn/download/%E5%85%A8%E5%9B%BD%E7%85%A4%E7%9F%BF%E6%99%BA%E8%83%BD%E5%8C%96%E5%BB%BA%E8%AE%BE%E5%85%B8%E5%9E%8B%E6%A1%88%E4%BE%8B%E6%B1%87%E7%BC%96%EF%BC%882023%E5%B9%B4%EF%BC%89.pdf"),
]


def is_paper_url(url: str) -> bool:
    return bool(url) and not re.search(r"(github\.com|zhihu\.com|xiaohongshu\.com|baidu\.com/s)", url, re.I)


def default_reference_papers() -> list[Paper]:
    return [Paper(title=title, source="公开论文/资料链接", url=url, section="默认补充文献") for title, url in DEFAULT_REFERENCE_LINKS[:7]]


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
    if len([paper for paper in results if paper.url]) < minimum:
        for paper in default_reference_papers():
            key = paper.url.lower()
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

    def paper_heading(title: str) -> bool:
        lowered = title.lower()
        blocked = ("github", "baseline", "导师", "技术路线", "研究建议", "科研经验", "搜索路径", "溯源")
        if any(token.lower() in lowered for token in blocked):
            return False
        allowed = ("论文", "文献", "前沿线索", "国际前沿", "经典代表性线索", "近年前沿线索")
        return any(token.lower() in lowered for token in allowed)

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
                in_paper_parent = paper_heading(current_heading)
            active_paper_area = paper_heading(current_heading) or (
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
            "正文不再逐条重复论文题名，避免和文末参考文献重复；具体题名、链接和来源统一放在第七节。"
        )
    else:
        text = (
            f"{group_name}共抽取 {len(papers)} 条可核验线索，来源主要包括{source_summary}。"
            f"这些研究集中在{family_summary}，更适合支撑模型改进、鲁棒性设计、数据集建设和对比实验。"
            "本课题应从其中提取方法路线，而不是把论文题名逐条堆在正文里；具体条目统一放在第七节。"
        )
    return [text, ""]


def _cite(idx: int) -> str:
    """Produce a citation marker like [1]."""
    return f"[{idx}]"


def _build_references(papers: list[Paper], extra_urls: list[str]) -> list[tuple[str, str]]:
    """Build a numbered reference list: [(key, formatted_entry), ...].

    Only includes actual paper references, filtering out advisor pages and non-academic URLs.
    """
    refs: list[tuple[str, str]] = []
    seen: set[str] = set()
    non_paper_domains = ("github.com", "zhihu.com", "xiaohongshu.com", "baidu.com/s",
                         "cs.cumt.edu.cn", "cese.cumt.edu.cn", "safe.cumt.edu.cn",
                         "mtxb.com.cn", "nea.gov.cn")
    for paper in papers:
        key = (paper.url or paper.title).lower()
        if key in seen:
            continue
        # Skip non-paper URLs (advisor pages, government PDFs, etc.)
        if paper.url and any(domain in paper.url for domain in non_paper_domains):
            continue
        seen.add(key)
        source_part = f"  {paper.source}" if paper.source else ""
        entry = f"{paper.title}.{source_part}"
        if paper.url:
            entry += f"  [{paper.url}]"
        refs.append((paper.title, entry))
    for url in extra_urls:
        if url.lower() in seen or not is_paper_url(url):
            continue
        if any(domain in url for domain in non_paper_domains):
            continue
        seen.add(url.lower())
        refs.append((url, f"[online] {url}"))
    return refs


def build_review_markdown(title: str, markdown: str) -> tuple[str, str]:
    """Build an academic-style literature review with inline citations [1][2]...

    Returns (clean_title, review_markdown).
    """
    papers = extract_papers(markdown)
    domestic, international = classify_papers(papers)
    background = section_text(markdown, ("研究主题", "主题概述"), 900)

    # Collect all URLs for the reference list
    all_extra_urls = [url for url in extract_urls(markdown) if is_paper_url(url)]
    refs = _build_references(papers, all_extra_urls)
    # Pad with defaults if needed
    if len(refs) < 5:
        for ref_title, ref_url in DEFAULT_REFERENCE_LINKS:
            if len(refs) >= 12:
                break
            if ref_url.lower() not in {r[0].lower() for r in refs}:
                refs.append((ref_title, f"{ref_title}.  [{ref_url}]"))

    # Build title->citation-index mapping
    cite_map: dict[str, int] = {}
    for idx, (key, _entry) in enumerate(refs, 1):
        cite_map[key] = idx

    def cite_paper(paper: Paper) -> str:
        key = (paper.url or paper.title).lower()
        for ref_key, idx in cite_map.items():
            if ref_key.lower() == key:
                return _cite(idx)
        return ""

    def cite_papers_inline(paper_list: list[Paper]) -> str:
        markers = sorted({cite_paper(p) for p in paper_list if cite_paper(p)}, key=lambda s: int(s.strip("[]")))
        return "".join(markers)

    # Always use a clean academic background — never inject 大创/报告/选题 content
    background = (
        "矿井安全监测是保障煤矿安全生产的重要环节，也是煤矿智能化建设的核心内容之一。"
        "2020年，国家发改委等八部委联合印发《关于加快煤矿智能化发展的指导意见》，明确提出加快煤矿智能化技术研发与应用；"
        "2023年国家能源局发布《煤矿智能化标准体系建设指南》，系统规划了智能视频监控、算法平台等方向的标准体系；"
        "《十四五矿山安全生产规划》进一步强调推进少人化、无人化智能化矿山建设。"
        "在政策驱动下，基于计算机视觉和深度学习的矿井安全监测技术已成为学术界和工业界的研究热点。"
        "然而，井下环境存在弱光、粉尘、水雾、遮挡等特殊约束条件，对目标检测算法的鲁棒性和实时性提出了更高要求。"
        "近年来，基于卷积神经网络（CNN）和 Transformer 架构的目标检测算法在通用场景中取得了显著进展，"
        "但在矿井复杂环境中的适配性和工程落地仍是亟待解决的关键问题。"
    )

    # Derive a clean academic title
    clean_title = re.sub(r"(大创|选题|调研|报告|科研).*$", "研究", title).strip()
    if not clean_title.endswith(("研究", "综述", "分析", "方法")):
        clean_title = title.rstrip("调研报告") + "研究"

    # --- Section 1: 研究背景 ---
    lines: list[str] = [
        f"# {clean_title}文献综述",
        "",
        "## 研究背景",
        "",
        background,
        "",
        "煤炭工业作为我国基础能源产业，其安全生产直接关系到国家能源安全和社会稳定"
        + (cite_papers_inline([p for p in papers if "综述" in p.title or "survey" in p.title.lower() or "Review" in p.title]) or "")
        + "。在国家大力推进煤矿智能化建设的背景下，井下视频监控系统已基本普及，但传统人工巡检方式存在效率低、实时性差、易疲劳疏漏等不足。计算机视觉与深度学习技术为矿井安全监测提供了新的解决思路，能够在复杂环境下实现人员行为识别、设备状态监测、隐患自动预警等功能，具有重要的理论意义和工程应用价值。",
        "",
    ]

    # --- Section 2: 国内外研究现状 ---
    lines.append("## 国内外研究现状")
    lines.append("")

    # 2.1 国内研究现状
    lines.append("### 国内研究现状")
    lines.append("")

    if domestic:
        # Group by method family
        from collections import defaultdict
        families: dict[str, list[Paper]] = defaultdict(list)
        for p in domestic:
            families[method_family(p)].append(p)

        para = "国内学者在矿井安全监测领域开展了大量研究工作。"
        for family_name, family_papers in families.items():
            cites = cite_papers_inline(family_papers)
            first_paper = family_papers[0]
            summary_text = first_paper.summary[:120] if first_paper.summary else ""
            if "检测" in family_name or "识别" in family_name:
                para += f"在目标检测与识别方面，{first_paper.title}{cites}针对矿井环境特点提出了改进方法，{summary_text}。"
            elif "综述" in family_name:
                para += f"在综述性研究方面，{first_paper.title}{cites}系统梳理了矿井视觉领域的技术演进路线。"
            elif "数据" in family_name:
                para += f"在数据集构建方面，{first_paper.title}{cites}提供了可支撑模型训练的公开数据资源。"
            elif "监测" in family_name:
                para += f"在监测方法方面，{first_paper.title}{cites}从工程应用角度提出了可落地的技术方案。{summary_text}。"
            elif "火灾" in family_name or "烟雾" in family_name:
                para += f"在火灾烟雾检测方面，{first_paper.title}{cites}针对井下特殊光照和粉尘条件设计了视觉识别方案。"
            elif "机器人" in family_name or "slam" in family_name.lower():
                para += f"在巡检机器人方面，{first_paper.title}{cites}探索了井下自主导航与环境感知技术。"
            else:
                para += f"{first_paper.title}{cites}。{summary_text}。"

        para += f"总体来看，国内研究主要聚焦于YOLO系列目标检测算法在矿井场景中的适配改进{cite_papers_inline([p for p in domestic if 'yolo' in p.title.lower()])}、人员防护装备识别以及井下异常状态监测等方向。"
        lines.extend([para, ""])
    else:
        lines.extend(["目前暂无充分的国内论文条目，建议继续以煤炭学报、采矿与安全工程学报、工矿自动化、煤炭科学技术等来源进行补充检索。", ""])

    # 2.2 国外研究现状
    lines.append("### 国外研究现状")
    lines.append("")

    if international:
        intl_families: dict[str, list[Paper]] = defaultdict(list)
        for p in international:
            families[method_family(p)].append(p)
            intl_families[method_family(p)].append(p)

        para = "国际上，矿井安全监测领域的研究同样取得了显著进展。"
        for family_name, family_papers in intl_families.items():
            cites = cite_papers_inline(family_papers)
            first_paper = family_papers[0]
            summary_text = first_paper.summary[:120] if first_paper.summary else ""
            if "Safety" in family_name or "safety" in family_name:
                para += f"{first_paper.title}{cites}提出了一种基于计算机视觉的井下安全监测方法，{summary_text}。"
            elif "Detection" in family_name or "detection" in family_name:
                para += f"{first_paper.title}{cites}在目标检测方向取得了重要突破，{summary_text}。"
            elif "Monitoring" in family_name or "monitoring" in family_name:
                para += f"{first_paper.title}{cites}在监测系统构建方面提出了新方案。{summary_text}。"
            elif "Dataset" in family_name or "dataset" in family_name:
                para += f"{first_paper.title}{cites}公开了面向井下场景的基准数据集，为后续研究提供了数据基础。"
            elif "Survey" in family_name or "Review" in family_name:
                para += f"{first_paper.title}{cites}从国际视角综述了矿井安全监测技术的发展趋势。"
            elif "Collision" in family_name or "collision" in family_name:
                para += f"{first_paper.title}{cites}在井下防碰撞系统方面做出了重要贡献。{summary_text}。"
            else:
                para += f"{first_paper.title}{cites}。{summary_text}。"

        para += "国际研究在深度模型架构创新、多模态感知融合、以及基准数据集建设等方面具有较强引领性。"
        lines.extend([para, ""])
    else:
        lines.extend(["目前暂无充分的国际前沿论文条目，建议继续以 IEEE、Springer、Elsevier、MDPI 等来源进行补充检索。", ""])

    # --- Section 3: 研究趋势与展望 ---
    family_counter = Counter(method_family(paper) for paper in papers)
    family_summary = "、".join(f"{family}" for family, _ in family_counter.most_common(4))
    if not family_summary:
        family_summary = "矿井视觉监测方法、数据集与工程系统"

    lines.extend([
        "## 研究趋势与展望",
        "",
        f"综合上述国内外研究现状，当前矿井安全监测领域的研究主要集中在以下几个方面：{family_summary}。"
        "尽管已有大量研究成果，但以下问题仍待进一步解决：（1）井下真实场景数据获取困难，公开数据集与实际工况存在分布偏差；"
        "（2）弱光、粉尘、水雾和遮挡等多重退化因素同时出现时，现有算法的鲁棒性不足；"
        "（3）大多数研究侧重于算法精度提升，缺乏面向边缘端部署的轻量化设计；"
        "（4）从监测到预警再到处置的安全闭环尚未完全打通。",
        "",
        "未来研究方向应聚焦于：（1）构建更大规模、更多样化的矿井场景数据集；（2）设计面向复杂环境鲁棒性的自适应检测算法；"
        "（3）推进模型轻量化与边缘端实时部署；（4）建立从感知到决策的智能安全闭环系统。",
        "",
    ])

    # --- Section 4: 参考文献 ---
    lines.extend(["## 参考文献", ""])
    for idx, (_key, entry) in enumerate(refs[:30], 1):
        lines.append(f"[{idx}] {entry}")
    lines.append("")

    return clean_title, "\n".join(lines)


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
    bib_mode = False
    bib_idx = -1

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

    for line_idx, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            flush_para()
            close_itemize()
            continue
        if bib_mode:
            # After "参考文献" heading, collect numbered entries
            if re.match(r"^\[\d+\]", line):
                out.append("\\hangindent=2em \\hangafter=1 \\noindent " + latex_text(line))
                out.append("")
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
            # Handle "参考文献" section with hanging-indent items
            if "参考文献" in heading_text:
                out.append("\\section*{" + latex_text(heading_text) + "}")
                out.append("\\addcontentsline{toc}{section}{" + latex_text(heading_text) + "}")
                out.append("")
                bib_mode = True
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


def latex_document(title: str, review_markdown: str) -> str:
    """Generate a LaTeX document following Chinese university thesis formatting conventions.

    - No forced page break after title (content starts immediately)
    - ctex auto-numbering (no manual 一、二、三、)
    - Hanging-indent bibliography at the end
    """
    body = markdown_to_latex_body(review_markdown)
    return rf"""\documentclass[UTF8,zihao=-4,fontset=fandol]{{ctexart}}
\usepackage[a4paper,left=3cm,right=2.5cm,top=2.5cm,bottom=2.5cm]{{geometry}}
\usepackage{{xcolor}}
\usepackage{{hyperref}}
\usepackage{{url}}
\usepackage{{setspace}}
\usepackage{{tabularx}}
\usepackage{{booktabs}}

% ---- Fonts: Fandol (bundled, works with tectonic/xelatex/lualatex) ----

% ---- Academic formatting ----
\setstretch{{1.5}}
\setlength{{\parindent}}{{2em}}
\setlength{{\parskip}}{{0pt}}
\setcounter{{secnumdepth}}{{3}}
\setcounter{{tocdepth}}{{2}}

\hypersetup{{
  colorlinks=true,
  linkcolor=black,
  urlcolor=blue!70!black,
  citecolor=black,
  bookmarks=true,
  bookmarksopen=true
}}
\Urlmuskip=0mu plus 2mu
\sloppy

% ---- Section formatting: GB/T academic style ----
\ctexset{{
  section = {{
    format = \centering\bfseries\fontsize{{15bp}}{{20bp}}\selectfont,
    beforeskip = 1.5ex plus .2ex minus .2ex,
    afterskip = 1.5ex plus .2ex minus .2ex,
  }},
  subsection = {{
    format = \bfseries\fontsize{{14bp}}{{18bp}}\selectfont,
    beforeskip = 1ex plus .2ex minus .2ex,
    afterskip = 1ex plus .2ex minus .2ex,
  }},
  subsubsection = {{
    format = \bfseries\fontsize{{12bp}}{{16bp}}\selectfont,
    beforeskip = 0.8ex plus .2ex minus .2ex,
    afterskip = 0.8ex plus .2ex minus .2ex,
  }}
}}

% ---- Title formatting ----
\renewcommand{{\maketitle}}{{
  \begin{{center}}
    \vspace*{{0.8cm}}
    {{\bfseries\fontsize{{22bp}}{{26bp}}\selectfont {latex_text(title)}}}\\[0.6cm]
    {{\fontsize{{14bp}}{{18bp}}\selectfont 文献综述}}
  \end{{center}}
  \vspace{{0.8cm}}
}}

\begin{{document}}
\maketitle
\pagestyle{{plain}}

{body}
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


def find_tectonic() -> str | None:
    """Find tectonic binary on the system PATH."""
    return shutil.which("tectonic")


def compile_latex(tex_path: Path) -> dict[str, Any]:
    # Try tectonic first (modern, self-contained, no MiKTeX needed)
    tectonic = find_tectonic()
    if tectonic:
        runs = []
        last: subprocess.CompletedProcess[str] | None = None
        try:
            last = subprocess.run(
                [tectonic, "-X", "compile", str(tex_path)],
                cwd=str(tex_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
            )
        except subprocess.TimeoutExpired as exc:
            runs.append({"returncode": "timeout", "tail": str(exc)[-1200:]})
            return {"status": "error", "compiler": tectonic, "runs": runs}
        except OSError as exc:
            runs.append({"returncode": "oserror", "tail": str(exc)[-1200:]})
            return {"status": "error", "compiler": tectonic, "runs": runs}
        runs.append({"returncode": last.returncode, "tail": (last.stdout or "")[-1200:]})
        pdf_path = tex_path.with_suffix(".pdf")
        if last and last.returncode == 0 and pdf_path.exists():
            cleanup_latex_temp(tex_path)
            return {"status": "success", "compiler": tectonic, "pdf": str(pdf_path.resolve()), "runs": len(runs)}
        cleanup_latex_temp(tex_path)
        return {"status": "error", "compiler": tectonic, "runs": runs}

    # Fallback to xelatex (MiKTeX or system install)
    xelatex = find_xelatex()
    if not xelatex:
        return {
            "status": "skipped",
            "warning": "未找到 tectonic 或 xelatex，已保留文献综述 tex 源码。可手动运行: tectonic <file>.tex",
        }
    env = build_latex_env(xelatex)
    initialize_miktex_runtime(xelatex, env)
    runs = []
    last = None
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
        return {"status": "success", "compiler": xelatex, "pdf": str(pdf_path.resolve()), "runs": len(runs)}
    cleanup_latex_temp(tex_path)
    return {"status": "error", "compiler": xelatex, "runs": runs}


def export(title: str, markdown: str, output_dir: Path, filename: str | None = None, compile_pdf: bool = True) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(filename or title)
    clean_title, review_md = build_review_markdown(title, markdown)
    tex_path = output_dir / f"{stem}_literature_review.tex"
    tex_path.write_text(latex_document(clean_title, review_md), encoding="utf-8")
    files: dict[str, str] = {"tex": str(tex_path.resolve())}
    compile_result: dict[str, Any] | None = None
    if compile_pdf:
        compile_result = compile_latex(tex_path)
        pdf_path = tex_path.with_suffix(".pdf")
        if compile_result.get("status") == "success" and pdf_path.exists():
            files["pdf"] = str(pdf_path.resolve())
    result: dict[str, Any] = {
        "status": "success",
        "title": title,
        "files": files,
        "paper_count": len(extract_papers(markdown)),
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
