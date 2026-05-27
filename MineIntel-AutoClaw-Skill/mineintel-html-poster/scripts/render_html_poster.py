#!/usr/bin/env python3
"""Render a complete MineIntel report with a magazine-poster visual style."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path

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


def render_markdown(markdown: str) -> str:
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
            title = inline_html(strip_markdown(heading.group(2)))
            tag = "h2" if level <= 2 else "h3" if level == 3 else "h4"
            css = "major-heading" if level <= 1 else ""
            out.append(f'<{tag} class="{css}">{title}</{tag}>')
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


def render_html(title: str, markdown: str) -> str:
    cleaned = clean_markdown(markdown)
    deck = section_text(cleaned, ("研究主题", "主题概述", "研判结论"), 320)
    if not deck:
        deck = "面向矿业科研选题的完整调研报告，保留论文线索、baseline、导师方向、技术路线和溯源信息。"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    section_count = len(re.findall(r"^#{1,6}\s+", cleaned, flags=re.M))
    paper_count = count_papers(cleaned)
    link_count = count_links(cleaned)
    body = render_markdown(cleaned)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} - MineIntel</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,800;0,900;1,400;1,700;1,800&family=IBM+Plex+Serif:ital,wght@0,400;0,500;0,600;1,400;1,500&family=JetBrains+Mono:wght@400;500&family=Noto+Serif+SC:wght@400;500;600;700;900&display=swap" rel="stylesheet">
<style>
/* ── Magazine Poster / 矿业纪事报 ── Sunday-paper editorial ──────── */
:root {{
  --paper: #f3eee2;
  --paper-deep: #e8dfcb;
  --ink: #1a1710;
  --muted: #6e685a;
  --rule: #c8bea4;
  --accent: #1a5c2e;
  --accent-2: #a04a2a;
  --tint: #e6ead8;
  --serif-display: "Playfair Display", "Noto Serif SC", "Songti SC", Georgia, serif;
  --serif-body: "IBM Plex Serif", "Noto Serif SC", "Songti SC", Georgia, serif;
  --serif-cn: "Noto Serif SC", "Songti SC", "SimSun", "STSong", Georgia, serif;
  --mono: "JetBrains Mono", "IBM Plex Mono", Consolas, monospace;
  --column-gap: 3.2rem;
  --column-rule: 1px solid var(--rule);
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

html {{
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}}

body {{
  color: var(--ink);
  background:
    radial-gradient(circle, rgba(31,28,23,0.06) 1px, transparent 1.4px) 0 0 / 16px 16px,
    var(--paper);
  font: 16px/1.8 var(--serif-body);
  word-break: break-word;
}}

/* ── page container ─────────────────────────────────────────── */
.page {{
  max-width: 1100px;
  margin: 0 auto;
  padding: 48px 56px 64px;
}}

/* ── dateline top bar ───────────────────────────────────────── */
.dateline {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  font: 11px/1.4 var(--mono);
  color: var(--muted);
  letter-spacing: .18em;
  text-transform: uppercase;
  padding-bottom: 12px;
  border-bottom: 3px double var(--ink);
  margin-bottom: 4px;
}}
.dateline .ornament {{
  font-size: 18px;
  letter-spacing: 0;
  color: var(--accent);
}}

/* ── thick rule under dateline ──────────────────────────────── */
.top-thick-rule {{
  height: 4px;
  background: var(--ink);
  margin-bottom: 36px;
}}

/* ── oversized serif headline ───────────────────────────────── */
.headline {{
  font-family: var(--serif-display);
  font-weight: 900;
  font-size: clamp(48px, 7vw, 88px);
  line-height: 1.0;
  letter-spacing: -0.02em;
  margin: 0 0 20px;
  max-width: 14ch;
}}
.headline em {{
  font-style: italic;
  color: var(--accent);
}}
.headline s {{
  text-decoration: line-through;
  text-decoration-color: var(--accent-2);
  text-decoration-thickness: 3px;
  color: var(--muted);
  opacity: .6;
}}

/* ── deck / summary ─────────────────────────────────────────── */
.deck {{
  max-width: 68ch;
  font: 20px/1.7 var(--serif-body);
  margin: 0 0 28px;
  color: var(--ink);
}}

/* ── stats strip ────────────────────────────────────────────── */
.stats {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  border-top: 2px solid var(--ink);
  border-bottom: 1px solid var(--rule);
  padding: 16px 0;
  margin: 0 0 40px;
  font: 11px/1.4 var(--mono);
  color: var(--muted);
  letter-spacing: .06em;
  text-transform: uppercase;
}}
.stat strong {{
  display: block;
  font: 800 32px/1.1 var(--serif-display);
  color: var(--ink);
  margin-bottom: 4px;
  letter-spacing: -0.01em;
}}

/* ── two-column body ────────────────────────────────────────── */
.content {{
  column-count: 2;
  column-gap: var(--column-gap);
  column-rule: var(--column-rule);
  max-width: 980px;
  text-align: justify;
  hyphens: auto;
}}

/* ── numbered section headings ──────────────────────────────── */
h2 {{
  font-family: var(--serif-display);
  font-weight: 800;
  font-size: 26px;
  line-height: 1.2;
  margin: 38px 0 12px;
  padding-top: 14px;
  border-top: 3px solid var(--ink);
  color: var(--ink);
  break-after: avoid;
  column-span: none;
}}
h2.major-heading {{
  font-size: 32px;
  column-span: all;
  border-top-width: 4px;
  color: var(--accent);
  margin-top: 44px;
}}
h2 .sec-num {{
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 500;
  color: var(--muted);
  margin-right: 8px;
  vertical-align: super;
  letter-spacing: .04em;
}}

h3 {{
  font-family: var(--serif-display);
  font-weight: 700;
  font-size: 20px;
  margin: 24px 0 8px;
  color: var(--accent-2);
  break-after: avoid;
}}
h4 {{
  font-family: var(--serif-body);
  font-size: 17px;
  font-weight: 600;
  margin: 16px 0 6px;
  break-after: avoid;
}}

/* ── body text ──────────────────────────────────────────────── */
p {{ margin: 0 0 12px; }}
ul, ol {{ margin: 0 0 14px 1.4em; }}
li {{ margin: 4px 0; }}

/* ── pull-quote (blockquote) ────────────────────────────────── */
blockquote {{
  margin: 20px -12px;
  padding: 16px 20px;
  background: var(--tint);
  border-left: 5px solid var(--accent);
  border-right: 1px solid var(--rule);
  font: italic 18px/1.65 var(--serif-display);
  color: var(--ink);
  break-inside: avoid;
}}
blockquote::before {{
  content: "\\201C";
  font-size: 48px;
  line-height: 1;
  color: var(--accent);
  opacity: .35;
  display: block;
  margin-bottom: -8px;
  font-family: var(--serif-display);
}}

/* ── links ──────────────────────────────────────────────────── */
a {{
  color: var(--accent);
  text-decoration-thickness: 1px;
  text-underline-offset: 3px;
  overflow-wrap: anywhere;
}}

strong {{ font-weight: 800; }}

code {{
  font-family: var(--mono);
  background: rgba(47,125,50,.11);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 0.9em;
}}

pre {{
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: transparent;
  color: var(--ink);
  padding: 10px 0 10px 16px;
  border-left: 3px solid var(--rule);
  border-radius: 0;
  font-family: var(--mono);
  font-size: 13px;
  break-inside: avoid;
}}

/* ── tables ─────────────────────────────────────────────────── */
.table-wrap {{
  break-inside: avoid;
  overflow-x: auto;
  margin: 16px 0 20px;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  font: 13px/1.55 var(--serif-body);
  background: rgba(255,255,255,.28);
}}
th, td {{ border: 1px solid var(--rule); padding: 7px 8px; vertical-align: top; }}
th {{ background: var(--paper-deep); color: var(--ink); text-align: left; }}

/* ── footer with ornament ───────────────────────────────────── */
.footer {{
  column-span: all;
  margin-top: 48px;
  padding-top: 16px;
  border-top: 3px double var(--ink);
  font: 11px/1.5 var(--mono);
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .12em;
  text-align: center;
}}
.footer .ornament {{
  display: block;
  font-size: 20px;
  letter-spacing: 0;
  text-transform: none;
  color: var(--accent);
  margin-bottom: 6px;
}}

/* ── responsive ─────────────────────────────────────────────── */
@media (max-width: 860px) {{
  .page {{ padding: 24px 20px 44px; }}
  .content {{ column-count: 1; column-rule: none; }}
  .stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .headline {{ font-size: 42px; max-width: none; }}
}}

@media print {{
  body {{ background: white; }}
  .page {{ max-width: none; padding: 20mm 16mm; }}
  a {{ color: var(--ink); }}
}}
</style>
</head>
<body>
<main class="page">
  <!-- dateline -->
  <div class="dateline">
    <span>CUMT &middot; 矿业纪事报</span>
    <span class="ornament">&sect;</span>
    <span>{html.escape(generated_at)} &middot; Vol.1 &middot; AutoClaw Report</span>
  </div>
  <div class="top-thick-rule"></div>

  <!-- oversized serif headline -->
  <h1 class="headline">MineIntel <em>Research</em><br>{inline_html(title)}</h1>

  <!-- deck / summary -->
  <p class="deck">{inline_html(deck)}</p>

  <!-- stats strip -->
  <section class="stats" aria-label="报告统计">
    <div class="stat"><strong>{section_count}</strong>章节</div>
    <div class="stat"><strong>{paper_count}</strong>论文线索</div>
    <div class="stat"><strong>{link_count}</strong>链接</div>
    <div class="stat"><strong>{html.escape(generated_at)}</strong>生成时间</div>
  </section>

  <!-- two-column body -->
  <article class="content">
{body}
  </article>

  <!-- footer with ornament -->
  <footer class="footer">
    <span class="ornament">&dagger;</span>
    MineIntel &middot; 矿小智科研情报平台 &middot; 中国矿业大学<br>
    Magazine-Poster Style &middot; Full Report Content Retained
  </footer>
</main>
</body>
</html>
"""


def export(title: str, markdown: str, output_dir: Path, filename: str | None = None) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(filename or title)
    path = output_dir / f"{stem}_poster.html"
    path.write_text(render_html(title, markdown), encoding="utf-8")
    return {"status": "success", "title": title, "files": {"html": str(path.resolve())}}


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
