#!/usr/bin/env python3
"""Render a complete MineIntel report with a magazine-style visual system."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


BASE_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = BASE_DIR.parent
OUTPUT_ROOT = PACKAGE_DIR / "output"


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


def clean_markdown(markdown: str) -> str:
    text = re.sub(r"<!--.*?-->", "", markdown, flags=re.S)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{4,}", "\n\n\n", text).strip() + "\n"


def strip_markdown(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
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

    for raw in clean_markdown(markdown).split("\n"):
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", raw.strip())
        if heading:
            flush()
            current_title = heading.group(2).strip()
            lines = []
        else:
            lines.append(raw)
    flush()
    return sections


def compact(text: str, limit: int = 240) -> str:
    value = re.sub(r"\s+", " ", strip_markdown(text)).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip("，。；; ") + "…"


def section_text(markdown: str, patterns: tuple[str, ...], limit: int = 420) -> str:
    parts: list[str] = []
    for section in split_sections(markdown):
        title = section["title"].lower()
        if any(pattern.lower() in title for pattern in patterns):
            text = "\n".join(
                line.strip()
                for line in section["content"].splitlines()
                if line.strip() and not re.match(r"^\s*\|", line)
            )
            parts.append(strip_markdown(text))
    return compact(" ".join(parts), limit)


def heading_block(markdown: str, title_pattern: str) -> str:
    lines = clean_markdown(markdown).splitlines()
    capture = False
    capture_level = 0
    body: list[str] = []
    for raw in lines:
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", raw.strip())
        if heading:
            level = len(heading.group(1))
            title = strip_markdown(heading.group(2))
            if capture and level <= capture_level:
                break
            if re.search(title_pattern, title):
                capture = True
                capture_level = level
                continue
        if capture:
            body.append(raw)
    return "\n".join(body).strip()


def route_steps(markdown: str) -> list[str]:
    route_text = heading_block(markdown, r"技术路线|研究路线|实施路线|路线图")
    plain = strip_markdown(route_text)
    candidates = [
        ("数据集整理", ("数据集", "数据整理", "公开数据", "标注")),
        ("YOLO baseline 复现", ("YOLO", "baseline", "基线", "复现")),
        ("低照度与小目标优化", ("低照度", "小目标", "增强", "轻量化", "注意力")),
        ("边缘推理部署", ("边缘", "部署", "推理", "导出")),
        ("Web 看板", ("Web", "看板", "可视化", "系统")),
        ("报警闭环", ("报警", "预警", "闭环", "规则")),
    ]
    steps = [label for label, keywords in candidates if any(keyword in plain for keyword in keywords)]
    if "YOLO baseline 复现" not in steps and ("计算机视觉" in plain or "目标检测" in plain):
        steps.insert(1 if steps else 0, "YOLO baseline 复现")
    if len(steps) < 4:
        steps = ["数据集整理", "YOLO baseline 复现", "场景适配优化", "Web 看板与报警闭环"]
    return steps[:6]


def technical_route_diagram_html(markdown: str, diagram_href: str | None = None) -> str:
    steps = route_steps(markdown)
    nodes = []
    for index, step in enumerate(steps, start=1):
        nodes.append(
            f"""          <div class="route-node">
            <span class="route-index">{index:02d}</span>
            <strong>{html.escape(step)}</strong>
          </div>"""
        )
    download = (
        f'<a class="route-download" href="{html.escape(diagram_href, quote=True)}" download>下载 Excalidraw 源文件</a>'
        if diagram_href
        else ""
    )
    return f"""<figure class="technical-route-diagram">
        <figcaption>
          <span>Technical route map</span>
          <strong>从数据到可演示闭环</strong>
          {download}
        </figcaption>
        <div class="route-flow" aria-label="技术路线流程图">
{chr(10).join(nodes)}
        </div>
      </figure>"""


def excalidraw_text(text: str, x: int, y: int, width: int, font_size: int = 20) -> dict:
    return {
        "id": uuid4().hex[:16],
        "type": "text",
        "x": x,
        "y": y,
        "width": width,
        "height": 28,
        "angle": 0,
        "strokeColor": "#1f1c17",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "index": "a0",
        "roundness": None,
        "seed": 1000000000,
        "version": 1,
        "versionNonce": 2000000000,
        "isDeleted": False,
        "boundElements": [],
        "updated": 1738195200000,
        "link": None,
        "locked": False,
        "text": text,
        "fontSize": font_size,
        "fontFamily": 5,
        "textAlign": "center",
        "verticalAlign": "middle",
        "containerId": None,
        "originalText": text,
        "autoResize": True,
        "lineHeight": 1.25,
    }


def excalidraw_box(text: str, x: int, y: int, width: int = 180, height: int = 76) -> list[dict]:
    box = {
        "id": uuid4().hex[:16],
        "type": "rectangle",
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "angle": 0,
        "strokeColor": "#1f1c17",
        "backgroundColor": "#e6ead8",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "index": "a0",
        "roundness": {"type": 3},
        "seed": 1000000000,
        "version": 1,
        "versionNonce": 2000000000,
        "isDeleted": False,
        "boundElements": [],
        "updated": 1738195200000,
        "link": None,
        "locked": False,
    }
    label = excalidraw_text(text, x + 12, y + 22, width - 24, 18)
    return [box, label]


def excalidraw_arrow(from_x: int, from_y: int, to_x: int, to_y: int) -> dict:
    return {
        "id": uuid4().hex[:16],
        "type": "arrow",
        "x": from_x,
        "y": from_y,
        "width": to_x - from_x,
        "height": to_y - from_y,
        "angle": 0,
        "strokeColor": "#2f7d32",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "index": "a0",
        "roundness": {"type": 2},
        "seed": 1000000000,
        "version": 1,
        "versionNonce": 2000000000,
        "isDeleted": False,
        "boundElements": [],
        "updated": 1738195200000,
        "link": None,
        "locked": False,
        "points": [[0, 0], [to_x - from_x, to_y - from_y]],
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": "arrow",
        "lastCommittedPoint": None,
    }


def build_route_excalidraw(title: str, markdown: str) -> dict:
    steps = route_steps(markdown)
    elements: list[dict] = [excalidraw_text("MineIntel 技术路线图", 80, 40, 360, 28)]
    x0, y0 = 80, 130
    width, height, gap = 180, 76, 72
    centers: list[tuple[int, int]] = []
    for index, step in enumerate(steps):
        row = index // 3
        col = index % 3
        x = x0 + col * (width + gap)
        y = y0 + row * 150
        elements.extend(excalidraw_box(step, x, y, width, height))
        centers.append((x + width, y + height // 2))
    for index in range(len(steps) - 1):
        row = index // 3
        next_row = (index + 1) // 3
        if row == next_row:
            from_x, from_y = centers[index]
            to_x = centers[index + 1][0] - width
            to_y = centers[index + 1][1]
        else:
            from_x, from_y = centers[index][0] - width // 2, centers[index][1] + height // 2
            to_x, to_y = centers[index + 1][0] - width // 2, centers[index + 1][1] - height // 2
        elements.append(excalidraw_arrow(from_x + 8, from_y, to_x - 8, to_y))
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {
            "viewBackgroundColor": "#f3eee2",
            "gridSize": 20,
            "name": f"{strip_markdown(title)} 技术路线图",
        },
        "files": {},
    }


def count_links(markdown: str) -> int:
    urls = set(re.findall(r"https?://[^\s)）\]】>,，。；;]+", markdown))
    return len(urls)


def count_papers(markdown: str) -> int:
    count = 0
    active = False
    parent = False
    for raw in clean_markdown(markdown).splitlines():
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", raw.strip())
        if heading:
            title = strip_markdown(heading.group(2)).lower()
            blocked = ("github", "baseline", "导师", "技术路线", "研究建议", "科研经验", "搜索路径", "溯源")
            allowed = ("论文", "文献", "前沿线索", "国际前沿", "经典代表性线索", "近年前沿线索")
            is_allowed = any(token.lower() in title for token in allowed) and not any(token.lower() in title for token in blocked)
            if len(heading.group(1)) <= 2:
                parent = is_allowed
            active = is_allowed or (parent and not any(token.lower() in title for token in blocked))
            continue
        if active and re.match(r"^\d+[.)、]\s+\*\*.+?\*\*", raw.strip()):
            count += 1
    return count


def headline_html(title: str) -> str:
    clean = strip_markdown(title)
    if "计算机视觉" in clean and "矿井安全监测" in clean:
        return '计算机视觉<br><span class="strike">泛泛调研</span><br>到矿井安全的 <span class="accent">可交付选题</span>'
    words = clean[:32] or "MineIntel Research"
    return f'{html.escape(words)}<br><span class="accent">Research Dossier</span>'


def poster_cells(markdown: str) -> list[dict[str, str]]:
    specs = [
        (
            "01 · POSITION",
            "选题定位",
            ("研究主题", "主题概述", "研判结论"),
            "把矿业痛点、计算机视觉和软件工程原型收束到一个可申报题目。",
            "先定场景，再定模型。",
        ),
        (
            "02 · SCENE",
            "矿井场景",
            ("应用场景", "场景"),
            "人员 PPE、巷道巡检、输送带安全和多传感器联动构成主要落点。",
            "矿井不是普通摄像头场景。",
        ),
        (
            "03 · CONSTRAINT",
            "关键难点",
            ("难点", "挑战"),
            "低照度、粉尘水雾、小目标遮挡、数据合规和边缘部署是核心约束。",
            "难点在场景适配，不在模型名称。",
        ),
        (
            "04 · EVIDENCE",
            "论文线索",
            ("论文", "文献", "前沿"),
            "中文矿业论文和国际综述用于证明问题真实、路线可查、边界需核验。",
            "未核验线索不得写成确定事实。",
        ),
        (
            "05 · BASELINE",
            "工程基线",
            ("github", "baseline", "代码", "仓库"),
            "以成熟 YOLO 工具链复现、迁移、部署，再接入 Web 看板和报警闭环。",
            "先复现，再迁移，再系统化。",
        ),
        (
            "06 · DELIVERY",
            "交付闭环",
            ("导师", "技术路线", "科研经验", "最终建议", "大创"),
            "导师匹配、技术路线、项目建议和搜索溯源共同服务答辩展示。",
            "报告不是终点，是推进路线图。",
        ),
    ]
    cells: list[dict[str, str]] = []
    for num, title, patterns, fallback, quote in specs:
        text = section_text(markdown, patterns, 300) or fallback
        cells.append({"num": num, "title": title, "text": text, "quote": quote})
    return cells


def render_poster_grid(markdown: str) -> str:
    return "\n".join(
        f"""      <section class="cell">
        <div class="num"><span class="bar"></span>{html.escape(cell["num"])}</div>
        <h3>{html.escape(cell["title"])}</h3>
        <p>{inline_html(cell["text"])}</p>
        <div class="quote">{html.escape(cell["quote"])}</div>
      </section>"""
        for cell in poster_cells(markdown)
    )


def inline_html(text: str) -> str:
    raw = str(text)
    tokens: list[str] = []

    def stash(value: str) -> str:
        tokens.append(value)
        return f"§§TOKEN{len(tokens) - 1}§§"

    raw = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        lambda m: stash(
            f'<a href="{html.escape(m.group(2), quote=True)}" target="_blank" rel="noopener noreferrer">'
            f"{html.escape(strip_markdown(m.group(1)))}</a>"
        ),
        raw,
    )
    raw = re.sub(
        r"`([^`]+)`",
        lambda m: stash(f"<code>{html.escape(m.group(1))}</code>"),
        raw,
    )
    escaped = html.escape(raw)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(
        r"(?<![\"'=])(https?://[^\s<]+)",
        lambda m: f'<a href="{html.escape(m.group(1), quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(m.group(1))}</a>',
        escaped,
    )
    for index, value in enumerate(tokens):
        escaped = escaped.replace(f"§§TOKEN{index}§§", value)
    return escaped


def table_cells(line: str) -> list[str]:
    value = line.strip()
    if not value.startswith("|") or "|" not in value[1:]:
        return []
    value = value.strip("|")
    return [cell.strip() for cell in value.split("|")]


def is_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", cell.replace(" ", "")) for cell in cells)


def render_table(lines: list[str]) -> str:
    rows = [table_cells(line) for line in lines]
    rows = [row for row in rows if row]
    if len(rows) >= 2 and is_table_separator(rows[1]):
        header = rows[0]
        body = rows[2:]
    else:
        header = []
        body = rows
    out = ["<div class=\"table-wrap\"><table>"]
    if header:
        out.append("<thead><tr>" + "".join(f"<th>{inline_html(cell)}</th>" for cell in header) + "</tr></thead>")
    out.append("<tbody>")
    for row in body:
        out.append("<tr>" + "".join(f"<td>{inline_html(cell)}</td>" for cell in row) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def render_markdown(markdown: str, route_diagram_href: str | None = None) -> str:
    lines = clean_markdown(markdown).splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    table_buffer: list[str] = []
    in_code = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            out.append(f"<p>{inline_html(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    def flush_table() -> None:
        nonlocal table_buffer
        if table_buffer:
            out.append(render_table(table_buffer))
            table_buffer = []

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            flush_table()
            close_list()
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            flush_table()
            close_list()
            continue

        cells = table_cells(stripped)
        if cells:
            flush_paragraph()
            close_list()
            table_buffer.append(stripped)
            continue
        flush_table()

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", stripped)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            clean_title = strip_markdown(heading.group(2))
            title = inline_html(clean_title)
            tag = "h2" if level <= 2 else "h3" if level == 3 else "h4"
            css = "major-heading" if level <= 1 else ""
            out.append(f'<{tag} class="{css}">{title}</{tag}>')
            if level <= 2 and re.search(r"技术路线|研究路线|实施路线|路线图", clean_title):
                out.append(technical_route_diagram_html(markdown, route_diagram_href))
            continue

        quote = re.match(r"^>\s*(.+)$", stripped)
        if quote:
            flush_paragraph()
            close_list()
            out.append(f"<blockquote>{inline_html(strip_markdown(quote.group(1)))}</blockquote>")
            continue

        ordered = re.match(r"^\d+[.)、]\s+(.+)$", stripped)
        bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
        if ordered or bullet:
            flush_paragraph()
            next_type = "ol" if ordered else "ul"
            content = ordered.group(1) if ordered else bullet.group(1)
            if list_type != next_type:
                close_list()
                out.append(f"<{next_type}>")
                list_type = next_type
            out.append(f"<li>{inline_html(content)}</li>")
            continue

        close_list()
        paragraph.append(stripped)

    flush_paragraph()
    flush_table()
    close_list()
    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    return "\n".join(out)


def render_html(title: str, markdown: str, route_diagram_href: str | None = None) -> str:
    cleaned = clean_markdown(markdown)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    section_count = len(re.findall(r"^#{1,6}\s+", cleaned, flags=re.M))
    body = render_markdown(cleaned, route_diagram_href)
    css = """
:root {
  --paper: #f3eee2;
  --ink: #1f1c17;
  --muted: #6e6a5d;
  --rule: #d3cdbe;
  --accent: #2f7d32;
  --accent-2: #b85a3a;
  --tint: #e6ead8;
  --paper-deep: #e8dfcb;
  --serif-display: 'Playfair Display', 'Noto Serif SC', 'Iowan Old Style', Georgia, serif;
  --serif-body: 'IBM Plex Serif', 'Noto Serif SC', 'Iowan Old Style', 'Charter', Georgia, serif;
  --sans: 'Noto Sans SC', 'Microsoft YaHei', Arial, sans-serif;
  --mono: 'IBM Plex Mono', ui-monospace, 'JetBrains Mono', Consolas, monospace;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  color: var(--ink);
  background:
    radial-gradient(circle, rgba(31,28,23,0.05) 1px, transparent 1.4px) 0 0 / 16px 16px,
    var(--paper);
  font: 15px/1.65 var(--serif-body);
}
a { color: var(--accent); text-decoration-thickness: 1px; text-underline-offset: 3px; overflow-wrap: anywhere; }
.page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 36px 56px 56px;
}
.top-rule {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  font: 10.5px/1.4 var(--mono);
  color: var(--muted);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--ink);
}
.eyebrow-row {
  padding: 14px 0 28px;
  font: 10.5px/1.4 var(--mono);
  color: var(--muted);
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
h1.headline {
  font-family: var(--serif-display);
  font-weight: 900;
  font-size: clamp(54px, 7vw, 96px);
  line-height: 0.98;
  letter-spacing: 0;
  margin: 0 0 16px;
  max-width: 18ch;
}
.report-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 22px;
  align-items: center;
  margin: 24px 0 30px;
  padding: 12px 0;
  border-top: 1px solid var(--ink);
  border-bottom: 1px solid var(--rule);
  font: 10.5px/1.4 var(--mono);
  color: var(--muted);
  letter-spacing: 0.14em;
  text-transform: uppercase;
}
.report-meta span:first-child {
  color: var(--accent);
  font-weight: 700;
}
.full-report {
  margin-top: 0;
  padding-top: 28px;
  border-top: 3px double var(--ink);
}
.full-report-title {
  font: 900 clamp(34px, 4.6vw, 58px)/1.05 var(--serif-display);
  margin: 0 0 18px;
}
.report-body {
  max-width: 980px;
}
.report-body h2, .report-body h3, .report-body h4 { break-after: avoid; page-break-after: avoid; }
.report-body h2 {
  font-family: var(--serif-display);
  font-size: 30px;
  line-height: 1.25;
  margin: 34px 0 14px;
  padding-top: 12px;
  border-top: 3px solid var(--ink);
}
.report-body h2.major-heading { font-size: 36px; color: var(--accent); }
.report-body h3 {
  font-family: var(--serif-display);
  font-size: 22px;
  margin: 26px 0 10px;
  color: var(--accent-2);
}
.report-body h4 { font-family: var(--sans); font-size: 17px; margin: 18px 0 8px; }
.report-body p { margin: 0 0 13px; text-align: justify; }
.report-body ul, .report-body ol { margin: 0 0 15px 1.2em; padding: 0; }
.report-body li { margin: 5px 0; }
.report-body blockquote {
  margin: 18px 0;
  padding: 14px 18px;
  background: var(--tint);
  border-left: 5px solid var(--accent);
  font-style: italic;
}
.report-body code { font-family: var(--mono); background: rgba(47,125,50,.11); padding: 1px 4px; border-radius: 4px; }
.report-body pre {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: transparent;
  padding: 10px 0 10px 16px;
  border-left: 3px solid var(--rule);
  font-family: var(--sans);
}
.technical-route-diagram {
  margin: 18px 0 22px;
  padding: 18px 18px 16px;
  border: 2px solid var(--ink);
  background: rgba(230,234,216,.62);
  break-inside: avoid;
}
.technical-route-diagram figcaption {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px 14px;
  margin: 0 0 16px;
  font-family: var(--sans);
}
.technical-route-diagram figcaption span {
  font: 10px/1.3 var(--mono);
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--muted);
}
.technical-route-diagram figcaption strong {
  font-size: 18px;
}
.route-download {
  margin-left: auto;
  font: 11px/1.2 var(--mono);
  color: var(--accent-2);
}
.route-flow {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(138px, 1fr));
  gap: 12px 28px;
  counter-reset: route;
}
.route-node {
  position: relative;
  min-height: 72px;
  padding: 12px 14px 12px;
  border: 2px solid var(--ink);
  background: var(--paper);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}
.route-node:not(:last-child)::after {
  content: "→";
  position: absolute;
  right: -23px;
  top: 50%;
  transform: translateY(-50%);
  font: 22px/1 var(--sans);
  color: var(--accent);
}
.route-index {
  font: 10px/1 var(--mono);
  color: var(--accent-2);
  letter-spacing: .1em;
}
.route-node strong {
  font: 700 15px/1.35 var(--sans);
}
.table-wrap { break-inside: avoid; overflow-x: auto; margin: 16px 0 20px; }
table { width: 100%; border-collapse: collapse; font: 14px/1.55 var(--sans); background: rgba(255,255,255,.28); }
th, td { border: 1px solid var(--rule); padding: 8px 9px; vertical-align: top; }
th { background: var(--paper-deep); color: var(--ink); text-align: left; }
@media (max-width: 900px) {
  .page { padding: 24px 24px 36px; }
  h1.headline { font-size: clamp(40px, 13vw, 68px); }
  .report-meta { gap: 8px 14px; }
  .route-node:not(:last-child)::after { display: none; }
  .route-download { margin-left: 0; }
}
@media print {
  body { background: white; }
  .page { max-width: none; padding: 20mm 16mm; }
  a { color: var(--ink); }
}
"""

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} - MineIntel</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,800;0,900;1,400;1,700;1,800&family=IBM+Plex+Serif:ital,wght@0,400;0,500;0,600;1,400;1,500&family=IBM+Plex+Mono:wght@400;500;600&family=Noto+Serif+SC:wght@400;500;600;700;900&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
  <div class="page">
    <div class="top-rule">
      <span>01 · CUMT MINEINTEL</span>
      <span>{html.escape(generated_at)} · AUTOCLAW REPORT</span>
    </div>
    <div class="eyebrow-row">— POSTED AS RESEARCH DOSSIER</div>

    <h1 class="headline">{html.escape(strip_markdown(title))}</h1>

    <section class="report-meta" aria-label="Report metadata">
      <span>Complete report</span>
      <span>{section_count} sections</span>
      <span>{html.escape(generated_at)}</span>
    </section>

    <section class="full-report">
      <h2 class="full-report-title">完整报告</h2>
      <article class="report-body">
{body}
      </article>
    </section>
  </div>
</body>
</html>
"""


def export(title: str, markdown: str, output_dir: Path, filename: str | None = None) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(filename or title)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    diagram_path = assets_dir / f"{stem}_technical_route.excalidraw"
    diagram_path.write_text(
        json.dumps(build_route_excalidraw(title, markdown), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    path = output_dir / f"{stem}_poster.html"
    path.write_text(
        render_html(title, markdown, f"assets/{diagram_path.name}"),
        encoding="utf-8",
    )
    return {
        "status": "success",
        "title": title,
        "files": {
            "html": str(path.resolve()),
            "route_diagram": str(diagram_path.resolve()),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a complete MineIntel report as styled HTML.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--content")
    parser.add_argument("--content-file")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT))
    parser.add_argument("--filename")
    args = parser.parse_args()

    try:
        result = export(args.title, read_content(args), Path(args.output_dir), args.filename)
    except Exception as exc:  # pragma: no cover
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
