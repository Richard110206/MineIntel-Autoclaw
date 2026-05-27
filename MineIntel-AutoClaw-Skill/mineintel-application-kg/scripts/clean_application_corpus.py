#!/usr/bin/env python3
"""Clean MineIntel application-intelligence corpus for KG construction.

Inputs:
- data/application_raw_sources.md
- data/download_manifest.csv
- data/download_additional_manifest.csv
- data/raw_docs/*.html|*.pdf
- legacy MineIntel knowledge files from sibling skill folders or repo data/

Outputs:
- data/clean/clean_sources.json
- data/clean/clean_chunks.jsonl
- data/clean/entity_candidates.json
- data/clean/cleaning_report.md

This script prepares corpus data only. It does not build kg_nodes/kg_edges.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
RAW_DIR = DATA_DIR / "raw_docs"
USER_SOURCE_DIR = DATA_DIR / "user_sources"
CLEAN_DIR = DATA_DIR / "clean"


def add_optional_site_packages() -> None:
    repo = SKILL_DIR.parents[1] if len(SKILL_DIR.parents) >= 2 else SKILL_DIR
    candidates = [
        repo / ".venv" / "Lib" / "site-packages",
        repo / "dist" / "MineIntel" / "python_env" / "Lib" / "site-packages",
    ]
    for path in candidates:
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))


add_optional_site_packages()

try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    PdfReader = None  # type: ignore


@dataclass
class Source:
    source_id: str
    title: str
    publisher: str = ""
    year: str = ""
    credibility: str = ""
    url: str = ""
    summary_hint: str = ""
    source_type: str = "application_source"
    local_files: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip_depth = 0
        self.parts: list[str] = []
        self.block_tags = {
            "p",
            "div",
            "section",
            "article",
            "br",
            "li",
            "tr",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "title",
        }

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
            return
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
            return
        if tag in self.block_tags:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if data and data.strip():
            self.parts.append(data)

    def text(self) -> str:
        return "\n".join(self.parts)


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "gb18030", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def normalize_text(text: str) -> str:
    text = html.unescape(text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    cleaned_lines: list[str] = []
    seen_short: set[str] = set()
    noise_patterns = [
        r"^(登录|注册|退出登录|分享到|版权所有|联系我们|上一篇|下一篇|提交评论|验证码|记住我)$",
        r"^window\.",
        r"^var\s+",
        r"^function\s*",
        r"^https?://",
        r"^\s*[{}();,]+\s*$",
    ]
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue
        if any(re.search(pattern, line, re.I) for pattern in noise_patterns):
            continue
        if len(line) <= 6:
            if line in seen_short:
                continue
            seen_short.add(line)
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def html_to_text(path: Path) -> str:
    raw = read_text(path)
    raw = re.sub(r"<!--.*?-->", " ", raw, flags=re.S)
    parser = TextExtractor()
    try:
        parser.feed(raw)
        text = parser.text()
    except Exception:
        text = re.sub(r"<[^>]+>", " ", raw)
    return normalize_text(text)


def pdf_to_text(path: Path) -> tuple[str, str]:
    if PdfReader is None:
        return "", "pypdf unavailable"
    try:
        reader = PdfReader(str(path))
        pages: list[str] = []
        for i, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            page_text = normalize_text(page_text)
            if page_text:
                pages.append(f"[PAGE {i}]\n{page_text}")
        return normalize_text("\n\n".join(pages)), ""
    except Exception as exc:
        return "", str(exc)


def parse_raw_sources(path: Path) -> dict[str, Source]:
    sources: dict[str, Source] = {}
    if not path.exists():
        return sources
    for line in read_text(path).splitlines():
        if not re.match(r"^\| [A-Z]\d{2} \|", line):
            continue
        parts = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(parts) < 7:
            continue
        source_id, title, publisher, year, credibility, url, summary = parts[:7]
        sources[source_id] = Source(
            source_id=source_id,
            title=title,
            publisher=publisher,
            year=year,
            credibility=credibility,
            url=url,
            summary_hint=summary,
        )
    return sources


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def base_source_id(file_name: str) -> str:
    match = re.match(r"^([A-Z]\d{2})", file_name)
    if match:
        return match.group(1)
    match = re.match(r"^([A-Z]\d{2})[A-Z]", file_name)
    if match:
        return match.group(1)
    return ""


def attach_local_files(sources: dict[str, Source]) -> None:
    for file in sorted(RAW_DIR.glob("*")):
        if not file.is_file():
            continue
        sid = base_source_id(file.name)
        if not sid:
            continue
        if sid not in sources:
            sources[sid] = Source(source_id=sid, title=file.stem, source_type="download_only")
        sources[sid].local_files.append(str(file.relative_to(DATA_DIR)))


def add_legacy_sources(sources: dict[str, Source]) -> None:
    repo = SKILL_DIR.parents[1] if len(SKILL_DIR.parents) >= 2 else SKILL_DIR
    candidates = [
        (
            "L01",
            "原 MineIntel 矿业计算机应用知识库",
            repo / "data" / "knowledge" / "mining_cs_domain.md",
        ),
        (
            "L02",
            "竞赛版矿业科研选题补充知识库",
            SKILL_DIR.parent / "mineintel-research" / "data" / "knowledge" / "mining_research_guide.md",
        ),
        (
            "L03",
            "竞赛版结构化矿业场景样例",
            SKILL_DIR.parent / "mineintel-research" / "data" / "sample_knowledge.json",
        ),
    ]
    for sid, title, path in candidates:
        if path.exists():
            sources[sid] = Source(
                source_id=sid,
                title=title,
                publisher="MineIntel 项目内置数据",
                year="",
                credibility="B",
                url="local://legacy-mineintel-knowledge",
                summary_hint="项目已有矿业场景、技术路线和应用知识，用于与新采集白皮书/蓝皮书资料合并清洗。",
                source_type="legacy_mineintel_knowledge",
                local_files=[str(path)],
            )


def add_user_sources(sources: dict[str, Source]) -> None:
    if not USER_SOURCE_DIR.exists():
        return
    for index, path in enumerate(sorted(USER_SOURCE_DIR.glob("*.csv")), start=1):
        sid = f"U{index:02d}"
        sources[sid] = Source(
            source_id=sid,
            title=path.stem,
            publisher="团队人工整理数据",
            year="2026",
            credibility="A-",
            url="local://user-curated-scenario-csv",
            summary_hint="团队人工整理的矿井场景、痛点、解决方案、技术设备和参考来源总览，用作知识图谱高置信场景骨架。",
            source_type="user_curated_scenario",
            local_files=[str(path.relative_to(DATA_DIR))],
        )


def csv_to_text(path: Path) -> str:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({(k or "").strip(): (v or "").strip() for k, v in row.items()})
    parts: list[str] = []
    for row in rows:
        scene = row.get("矿井场景") or row.get("场景") or ""
        category = row.get("场景大类") or ""
        pain = row.get("有什么问题（痛点）") or row.get("痛点") or ""
        solution = row.get("需要什么解决方案") or row.get("解决方案") or ""
        tech = row.get("要求什么技术/设备") or row.get("技术/设备") or ""
        refs = row.get("参考白皮书来源") or row.get("来源") or ""
        block = [
            f"矿井场景：{scene}",
            f"场景大类：{category}",
            f"痛点问题：{pain}",
            f"解决方案：{solution}",
            f"技术设备：{tech}",
            f"参考来源：{refs}",
        ]
        parts.append("\n".join(block))
    return normalize_text("\n\n".join(parts))


def text_from_file(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm"}:
        text = html_to_text(path)
        if "请先登录" in text and len(text) < 500:
            return "", "login_or_access_prompt"
        return text, ""
    if suffix == ".pdf":
        return pdf_to_text(path)
    if suffix in {".md", ".txt"}:
        return normalize_text(read_text(path)), ""
    if suffix == ".json":
        try:
            data = json.loads(read_text(path))
            return normalize_text(json.dumps(data, ensure_ascii=False, indent=2)), ""
        except Exception as exc:
            return "", str(exc)
    if suffix == ".csv":
        try:
            return csv_to_text(path), ""
        except Exception as exc:
            return "", str(exc)
    return "", "unsupported file type"


def chunk_text(text: str, max_chars: int = 1100, overlap: int = 120) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            start = 0
            while start < len(paragraph):
                chunk = paragraph[start : start + max_chars].strip()
                if len(chunk) >= 80:
                    chunks.append(chunk)
                start += max_chars - overlap
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) > max_chars and current:
            chunks.append(current.strip())
            current = paragraph
        else:
            current = candidate
    if current.strip():
        chunks.append(current.strip())
    return [c for c in chunks if len(c) >= 80]


APPLICATION_TERMS = [
    "智能采煤",
    "智能综采",
    "智能掘进",
    "掘进机远程控制",
    "远程控制",
    "主运皮带",
    "皮带巡检",
    "皮带异物",
    "煤流调速",
    "矿山态势可视化",
    "三维GIS",
    "地质保障",
    "安全管控",
    "智能反三违",
    "瓦斯管理",
    "瓦斯预警",
    "探放水",
    "巡检机器人",
    "无人驾驶",
    "露天矿卡",
    "矿卡无人驾驶",
    "有轨电机车",
    "铲运车",
    "边坡监测",
    "智能洗选",
    "预测性维护",
    "远程运营中心",
    "集中控制",
]

TECH_TERMS = [
    "5G",
    "F5G",
    "5G LAN",
    "超级上行",
    "高精度定位",
    "网络授时",
    "工业互联网",
    "云边端",
    "边缘计算",
    "人工智能",
    "AI",
    "机器视觉",
    "计算机视觉",
    "视频识别",
    "传感器融合",
    "数字孪生",
    "物联网",
    "机器人",
    "大数据",
    "矿山大模型",
    "大模型",
    "无人化",
    "自动驾驶",
    "设备云化",
    "软硬解耦",
    "工业环网",
    "V2X",
]

PAIN_TERMS = [
    "光照",
    "粉尘",
    "遮挡",
    "网络不稳定",
    "低时延",
    "高可靠",
    "数据孤岛",
    "烟囱",
    "互联互通",
    "设备异构",
    "本安",
    "防爆",
    "安全风险",
    "灾害",
    "运维",
    "故障",
    "标准体系",
    "成本",
    "人才",
    "常态化运行",
    "信息安全",
]

SOLUTION_TERMS = [
    "一张网",
    "一朵云",
    "一平台",
    "一套安全体系",
    "云边协同",
    "智能调度",
    "智能监测",
    "预测预警",
    "远程驾驶",
    "远程监控",
    "集中管控",
    "数据平台",
    "统一平台",
    "智能终端",
    "智能网关",
    "工业融合网关",
    "矿用摄像仪",
    "智能矿灯",
    "健康监测",
]

METRIC_TERMS = [
    "准确率",
    "实时性",
    "响应时延",
    "可靠性",
    "可用性",
    "稳定性",
    "减人",
    "增安",
    "提效",
    "节能",
    "能耗",
    "成本",
    "覆盖率",
    "常态化",
    "安全合规",
]


def term_categories() -> dict[str, list[str]]:
    return {
        "application_scenario": APPLICATION_TERMS,
        "technology": TECH_TERMS,
        "pain_point": PAIN_TERMS,
        "solution": SOLUTION_TERMS,
        "metric": METRIC_TERMS,
    }


def collect_entity_candidates(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bucket: dict[tuple[str, str], dict[str, Any]] = {}
    for chunk in chunks:
        text = chunk["text"]
        compact = re.sub(r"\s+", " ", text)
        for category, terms in term_categories().items():
            for term in terms:
                if term.lower() not in compact.lower():
                    continue
                key = (category, term)
                item = bucket.setdefault(
                    key,
                    {
                        "category": category,
                        "term": term,
                        "count": 0,
                        "source_ids": set(),
                        "evidence": [],
                    },
                )
                item["count"] += 1
                item["source_ids"].add(chunk["source_id"])
                if len(item["evidence"]) < 3:
                    idx = compact.lower().find(term.lower())
                    start = max(0, idx - 80)
                    end = min(len(compact), idx + len(term) + 120)
                    item["evidence"].append(
                        {
                            "chunk_id": chunk["chunk_id"],
                            "source_id": chunk["source_id"],
                            "text": compact[start:end],
                        }
                    )
    results: list[dict[str, Any]] = []
    for item in bucket.values():
        item["source_ids"] = sorted(item["source_ids"])
        results.append(item)
    results.sort(key=lambda x: (x["category"], -x["count"], x["term"]))
    return results


def source_to_dict(source: Source) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "title": source.title,
        "publisher": source.publisher,
        "year": source.year,
        "credibility": source.credibility,
        "url": source.url,
        "summary_hint": source.summary_hint,
        "source_type": source.source_type,
        "local_files": source.local_files,
        "notes": source.notes,
    }


def clean_corpus() -> dict[str, Any]:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    sources = parse_raw_sources(DATA_DIR / "application_raw_sources.md")
    attach_local_files(sources)
    add_legacy_sources(sources)
    add_user_sources(sources)

    chunks: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    seen_hashes: set[str] = set()
    source_stats: dict[str, dict[str, int]] = {}

    for source in sorted(sources.values(), key=lambda s: s.source_id):
        source_stats[source.source_id] = {"files": len(source.local_files), "chunks": 0, "chars": 0}
        for local in source.local_files:
            path = Path(local)
            if not path.is_absolute():
                path = DATA_DIR / local
            if not path.exists():
                skipped.append({"source_id": source.source_id, "file": local, "reason": "missing"})
                continue
            text, error = text_from_file(path)
            if error:
                skipped.append({"source_id": source.source_id, "file": str(path), "reason": error})
            if len(text) < 160:
                if not error:
                    skipped.append({"source_id": source.source_id, "file": str(path), "reason": "too_little_text"})
                continue
            source_stats[source.source_id]["chars"] += len(text)
            for index, chunk in enumerate(chunk_text(text), start=1):
                digest = hashlib.sha256(chunk.encode("utf-8")).hexdigest()[:16]
                if digest in seen_hashes:
                    continue
                seen_hashes.add(digest)
                chunk_id = f"{source.source_id}-{digest}"
                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "source_id": source.source_id,
                        "title": source.title,
                        "publisher": source.publisher,
                        "year": source.year,
                        "credibility": source.credibility,
                        "source_type": source.source_type,
                        "local_file": str(path),
                        "chunk_index": index,
                        "char_count": len(chunk),
                        "text": chunk,
                    }
                )
                source_stats[source.source_id]["chunks"] += 1

    candidates = collect_entity_candidates(chunks)

    (CLEAN_DIR / "clean_sources.json").write_text(
        json.dumps([source_to_dict(s) for s in sorted(sources.values(), key=lambda s: s.source_id)], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (CLEAN_DIR / "clean_chunks.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    (CLEAN_DIR / "entity_candidates.json").write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = build_report(sources, chunks, candidates, skipped, source_stats)
    (CLEAN_DIR / "cleaning_report.md").write_text(report, encoding="utf-8")

    return {
        "sources": len(sources),
        "chunks": len(chunks),
        "entity_candidates": len(candidates),
        "skipped": len(skipped),
        "clean_dir": str(CLEAN_DIR),
    }


def build_report(
    sources: dict[str, Source],
    chunks: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    skipped: list[dict[str, str]],
    source_stats: dict[str, dict[str, int]],
) -> str:
    by_category: dict[str, list[dict[str, Any]]] = {}
    for item in candidates:
        by_category.setdefault(item["category"], []).append(item)

    lines: list[str] = [
        "# MineIntel 矿井应用知识图谱数据清洗报告",
        "",
        "本报告记录本轮数据整合与清洗结果。当前产物仍是图谱构建前的清洗语料，不是最终知识图谱。",
        "",
        "## 汇总",
        "",
        f"- 统一来源数：{len(sources)}",
        f"- 清洗文本块数：{len(chunks)}",
        f"- 候选实体数：{len(candidates)}",
        f"- 跳过或异常文件数：{len(skipped)}",
        "",
        "## 数据来源构成",
        "",
        "| 类型 | 数量 |",
        "| --- | ---: |",
    ]
    type_counts: dict[str, int] = {}
    for source in sources.values():
        type_counts[source.source_type] = type_counts.get(source.source_type, 0) + 1
    for source_type, count in sorted(type_counts.items()):
        lines.append(f"| {source_type} | {count} |")

    lines.extend(["", "## Top 来源清洗量", "", "| 来源 | 文本块 | 字符数 |", "| --- | ---: | ---: |"])
    top_sources = sorted(source_stats.items(), key=lambda x: x[1]["chunks"], reverse=True)[:20]
    for sid, stat in top_sources:
        title = sources.get(sid, Source(sid, sid)).title
        lines.append(f"| {sid} {title} | {stat['chunks']} | {stat['chars']} |")

    lines.extend(["", "## 候选实体 Top 结果", ""])
    category_names = {
        "application_scenario": "应用场景",
        "technology": "技术方向",
        "pain_point": "痛点问题",
        "solution": "解决方案",
        "metric": "评价指标",
    }
    for category, name in category_names.items():
        lines.extend([f"### {name}", "", "| 候选词 | 次数 | 来源数 |", "| --- | ---: | ---: |"])
        for item in by_category.get(category, [])[:20]:
            lines.append(f"| {item['term']} | {item['count']} | {len(item['source_ids'])} |")
        lines.append("")

    lines.extend(["## 跳过或异常文件", "", "| 来源 | 文件 | 原因 |", "| --- | --- | --- |"])
    for item in skipped[:80]:
        file_name = Path(item["file"]).name
        reason = item["reason"].replace("|", "/")
        lines.append(f"| {item['source_id']} | `{file_name}` | {reason} |")
    if len(skipped) > 80:
        lines.append(f"| ... | ... | 其余 {len(skipped) - 80} 条略 |")

    lines.extend(
        [
            "",
            "## 已生成文件",
            "",
            "- `clean_sources.json`：统一来源元数据。",
            "- `clean_chunks.jsonl`：清洗后的文本块，可直接作为知识图谱抽取输入。",
            "- `entity_candidates.json`：基于词表和证据片段生成的候选实体。",
            "- `cleaning_report.md`：本报告。",
            "",
            "## 下一步",
            "",
            "1. 人工确认候选实体同义词，例如“矿卡无人驾驶/露天矿卡/无人驾驶运输”。",
            "2. 依据候选实体和证据块抽取 `kg_nodes.json`。",
            "3. 从证据句中抽取 `kg_edges.json`，优先关系为：提到、适用于、解决、依赖、评估、属于。",
            "4. 为每条边保留 `source_id` 和 `chunk_id`，便于报告溯源。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean MineIntel application corpus.")
    parser.parse_args()
    result = clean_corpus()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
