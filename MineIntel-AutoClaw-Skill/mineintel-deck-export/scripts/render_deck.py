#!/usr/bin/env python3
"""Render a MineIntel report as a Guizang-style horizontal HTML deck."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
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
OUTPUT_ROOT = PACKAGE_DIR / "output"
GUIZANG_DIR = Path(
    os.environ.get(
        "GUIZANG_PPT_SKILL_DIR",
        r"C:\Users\34833\.codex\skills\guizang-ppt-skill-main",
    )
)
GUIZANG_TEMPLATE = GUIZANG_DIR / "assets" / "template.html"
GUIZANG_MOTION = GUIZANG_DIR / "assets" / "motion.min.js"


INDIGO_THEME = {
    "--ink:#0a0a0b;": "--ink:#0a1f3d;",
    "--ink-rgb:10,10,11;": "--ink-rgb:10,31,61;",
    "--paper:#f1efea;": "--paper:#f1f3f5;",
    "--paper-rgb:241,239,234;": "--paper-rgb:241,243,245;",
    "--paper-tint:#e8e5de;": "--paper-tint:#e4e8ec;",
    "--ink-tint:#18181a;": "--ink-tint:#152a4a;",
}


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

    for raw in clean_markdown(markdown).splitlines():
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", raw.strip())
        if heading:
            flush()
            current_title = heading.group(2).strip()
            lines = []
        else:
            lines.append(raw)
    flush()
    return sections


def compact(text: str, limit: int = 180) -> str:
    value = re.sub(r"\s+", " ", strip_markdown(text)).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip("，。；; ") + "..."


def section_body(sections: list[dict[str, str]], patterns: tuple[str, ...]) -> str:
    bodies: list[str] = []
    for section in sections:
        title = section["title"].lower()
        if any(pattern.lower() in title for pattern in patterns):
            bodies.append(section["content"])
    return "\n".join(bodies).strip()


def lines_from_body(body: str, limit: int, fallback: list[str]) -> list[str]:
    lines: list[str] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^\s*[-*+]\s+", "", line)
        line = re.sub(r"^\s*\d+[.)、]\s+", "", line)
        if line.startswith("链接：") or line.startswith("地址："):
            continue
        clean = compact(line, 96)
        if clean and clean not in lines:
            lines.append(clean)
        if len(lines) >= limit:
            return lines
    if lines:
        return lines[:limit]
    return fallback[:limit]


def count_urls(markdown: str) -> int:
    return len(set(re.findall(r"https?://[^\s)）\]】>,，。；;]+", markdown)))


def count_paper_items(markdown: str) -> int:
    body = section_body(split_sections(markdown), ("论文", "文献", "前沿"))
    return len(re.findall(r"^\s*\d+[.)、]\s+\*\*", body, flags=re.M))


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def chrome(left: str, page: int, total: int) -> str:
    return f"""
  <div class="chrome">
    <div>{esc(left)}</div>
    <div>MineIntel · {page:02d} / {total:02d}</div>
  </div>"""


def foot(left: str) -> str:
    return f"""
  <div class="foot">
    <div>{esc(left)}</div>
    <div>AutoClaw Native Skill</div>
  </div>"""


def stat_card(label: str, value: str, note: str) -> str:
    return f"""
      <div class="stat-card" data-anim>
        <div class="stat-label">{esc(label)}</div>
        <div class="stat-nb">{esc(value)}</div>
        <div class="stat-note">{esc(note)}</div>
      </div>"""


def text_card(title: str, detail: str) -> str:
    return f"""
      <div class="stat-card" data-anim>
        <div class="stat-label">{esc(title)}</div>
        <div class="stat-note" style="font-family:var(--sans-zh);font-size:max(15px,1.05vw);line-height:1.68;opacity:.86">{esc(detail)}</div>
      </div>"""


def slide_cover(title: str, summary: str, total: int) -> str:
    return f"""
<section class="slide hero dark">
{chrome("CUMT MineIntel · Research Deck", 1, total)}
  <div class="frame" style="display:grid;gap:4vh;align-content:center;min-height:80vh">
    <div class="kicker" data-anim>矿小智 · 科研选题情报</div>
    <h1 class="h-hero" style="font-size:min(8.6vw,14vh)" data-anim>矿小智</h1>
    <h2 class="h-sub" data-anim>{esc(title)}</h2>
    <p class="lead" style="max-width:64vw" data-anim>{esc(summary)}</p>
    <div class="meta-row" data-anim>
      <span>HTML 报告同源</span><span>·</span><span>逐页展示版</span><span>·</span><span>{datetime.now().strftime("%Y-%m-%d")}</span>
    </div>
  </div>
{foot("Deck version for presentation")}
</section>"""


def slide_verdict(total: int, sections: list[dict[str, str]], markdown: str) -> str:
    verdict = section_body(sections, ("研判", "结论", "摘要"))
    items = lines_from_body(
        verdict,
        4,
        [
            "选题可行性高，适合从矿井视觉安全监测切入。",
            "建议聚焦 PPE 合规检测、低照度增强和边缘预警闭环。",
            "核心难点是矿井场景适配，而不是堆模型名称。",
            "申报材料要突出安全价值、软件系统闭环和可复现实验。",
        ],
    )
    return f"""
<section class="slide light">
{chrome("Executive Snapshot", 2, total)}
  <div class="kicker" data-anim>先把判断说清楚</div>
  <h1 class="h-xl" data-anim>结论不是“能做”，而是怎么收敛。</h1>
  <div class="grid-4" style="padding-top:7vh">
    {stat_card("报告章节", str(len(sections)), "完整报告中的结构化章节")}
    {stat_card("论文线索", str(max(1, count_paper_items(markdown))), "中文与国际前沿线索")}
    {stat_card("链接证据", str(count_urls(markdown)), "论文、仓库、导师页面")}
    {stat_card("核心建议", "小闭环", "PPE + 低照度 + 边缘预警")}
  </div>
  <div class="callout" style="margin-top:4vh" data-anim>
    <div class="q-big">{esc(items[0])}</div>
    <span class="cite">{esc(items[1] if len(items) > 1 else "MineIntel synthesis")}</span>
  </div>
{foot("结论摘要")}
</section>"""


def slide_scenarios(total: int, sections: list[dict[str, str]]) -> str:
    items = lines_from_body(
        section_body(sections, ("应用场景", "场景")),
        4,
        ["人员 PPE 与不安全行为监测", "巷道巡检与固定摄像头异常识别", "输送带与机电设备安全监测", "瓦斯、顶板、矿压等传感器联动"],
    )
    return f"""
<section class="slide dark">
{chrome("Act I · Mining Scene", 3, total)}
  <div class="frame grid-2-7-5" style="padding-top:7vh">
    <div>
      <div class="kicker" data-anim>矿井不是普通摄像头场景</div>
      <h1 class="h-xl" data-anim>先落场景，再谈模型。</h1>
      <p class="lead" style="margin-top:3vh" data-anim>视觉识别的价值不在“看见目标”，而在把人员、设备、巷道和传感器报警串成安全闭环。</p>
    </div>
    <div class="col" style="gap:2vh">
      {''.join(text_card(f"场景 {idx:02d}", item) for idx, item in enumerate(items, 1))}
    </div>
  </div>
{foot("应用场景")}
</section>"""


def slide_challenges(total: int, sections: list[dict[str, str]]) -> str:
    items = lines_from_body(
        section_body(sections, ("难点", "挑战")),
        6,
        ["低照度与光照不均", "粉尘、水雾和镜头污染", "小目标与密集遮挡", "真实数据采集难", "边缘部署约束", "误报/漏报代价高"],
    )
    return f"""
<section class="slide light">
{chrome("Act II · Constraints", 4, total)}
  <div class="kicker" data-anim>真正的难点</div>
  <h1 class="h-xl" style="font-size:5.4vw" data-anim>矿井会把通用视觉模型的短板放大。</h1>
  <div class="grid-6" style="padding-top:6vh">
    {''.join(text_card(f"{idx:02d}", item) for idx, item in enumerate(items[:6], 1))}
  </div>
{foot("矿井特殊技术难点")}
</section>"""


def slide_papers(total: int, sections: list[dict[str, str]]) -> str:
    items = lines_from_body(
        section_body(sections, ("论文", "文献", "前沿")),
        5,
        ["矿井视频图像目标检测与隐患识别方法研究综述", "矿井复杂环境小目标检测算法", "地下矿山计算机视觉防碰撞系统综述"],
    )
    return f"""
<section class="slide dark">
{chrome("Act III · Evidence", 5, total)}
  <div class="frame grid-2-6-6" style="padding-top:7vh">
    <div>
      <div class="kicker" data-anim>论文不是堆列表</div>
      <h1 class="h-xl" data-anim>用文献证明场景真实、问题具体。</h1>
      <div class="callout" style="margin-top:5vh" data-anim>
        <div class="q-big">所有外部论文线索在正式申报前仍需核验题名、作者、期刊、年份和 DOI。</div>
        <span class="cite">Verification first</span>
      </div>
    </div>
    <div class="col" style="gap:2vh">
      {''.join(text_card(f"线索 {idx:02d}", item) for idx, item in enumerate(items, 1))}
    </div>
  </div>
{foot("论文与前沿线索")}
</section>"""


def slide_baseline(total: int, sections: list[dict[str, str]]) -> str:
    baseline = section_body(sections, ("github", "baseline", "代码", "仓库"))
    items = lines_from_body(
        baseline,
        4,
        ["ultralytics/ultralytics：生态成熟，适合快速构建检测闭环", "先复现公开 PPE/安全帽数据集", "再迁移到矿井低照度样例", "导出 ONNX/TensorRT 并接入 Web 看板"],
    )
    return f"""
<section class="slide light">
{chrome("Baseline · Engineering Path", 6, total)}
  <div class="frame grid-2-8-4" style="padding-top:6vh">
    <div>
      <div class="kicker" data-anim>一个 baseline 就够</div>
      <h1 class="h-xl" data-anim>先复现，再迁移，再做系统闭环。</h1>
      <p class="lead" style="margin-top:3vh" data-anim>{esc(compact(baseline, 210) or "推荐以 YOLO 系列目标检测作为 baseline，并把训练、推理、报警和看板做成可演示系统。")}</p>
    </div>
    <div class="col" style="gap:2vh">
      {''.join(text_card(f"Step {idx}", item) for idx, item in enumerate(items, 1))}
    </div>
  </div>
{foot("GitHub baseline")}
</section>"""


def slide_advisors(total: int, sections: list[dict[str, str]]) -> str:
    items = lines_from_body(
        section_body(sections, ("导师", "研究方向")),
        6,
        ["计算机视觉与模式识别方向导师", "图像处理与视频分析方向导师", "智慧矿山与边缘部署方向导师"],
    )
    return f"""
<section class="slide dark">
{chrome("Advisor Match", 7, total)}
  <div class="kicker" data-anim>导师匹配不是泛泛推荐</div>
  <h1 class="h-xl" style="font-size:5.2vw" data-anim>候选导师要能接住“视觉 + 矿井 + 系统”。</h1>
  <div class="grid-3" style="padding-top:7vh">
    {''.join(text_card(f"候选 {idx:02d}", item) for idx, item in enumerate(items[:3], 1))}
  </div>
  <div class="callout" style="margin-top:4vh" data-anim>
    正式联系前，以学院官网最新页面和导师本人确认信息为准。
    <span class="callout-src">Official pages required</span>
  </div>
{foot("导师方向匹配")}
</section>"""


def slide_route(total: int, sections: list[dict[str, str]]) -> str:
    route = lines_from_body(
        section_body(sections, ("技术路线", "研究目标", "创新点", "评价指标")),
        6,
        ["明确矿井目标对象和安全边界", "整理公开数据与可合规采集样例", "复现 YOLO baseline", "加入低照度增强和轻量化策略", "部署边缘端推理与报警看板", "沉淀申报材料和实验记录"],
    )
    steps = "".join(
        f"""
        <div class="step" data-anim="step">
          <div class="step-nb">{idx:02d}</div>
          <div class="step-title">{esc(item.split('，')[0].split('：')[0][:18])}</div>
          <div class="step-desc">{esc(item)}</div>
        </div>"""
        for idx, item in enumerate(route[:6], 1)
    )
    return f"""
<section class="slide light" data-animate="pipeline">
{chrome("Route · MVP to Research", 8, total)}
  <div class="kicker" data-anim>把科研题目拆成工程路径</div>
  <h1 class="h-xl" style="font-size:5.2vw" data-anim>从 baseline 到可答辩系统。</h1>
  <div class="pipeline-section" style="margin-top:6vh">
    <div class="pipeline-label">Execution Pipeline</div>
    <div class="pipeline" data-cols="6">
      {steps}
    </div>
  </div>
{foot("技术路线")}
</section>"""


def slide_project(total: int, sections: list[dict[str, str]]) -> str:
    items = lines_from_body(
        section_body(sections, ("大创", "建议书", "科研经验", "最终建议")),
        4,
        ["题目里明确对象、场景、方法和系统", "先复现 baseline，再做小改进", "数据来源必须合规", "答辩重点解释矿井场景差异"],
    )
    return f"""
<section class="slide dark">
{chrome("Competition Ready", 9, total)}
  <div class="frame grid-2-6-6" style="padding-top:7vh">
    <div>
      <div class="kicker" data-anim>不是只交模型</div>
      <h1 class="h-xl" data-anim>大创要交一条可信的项目线。</h1>
      <p class="lead" style="margin-top:3vh" data-anim>答辩老师要看到问题、证据、路线、实验、系统和风险边界，而不只是一个算法名字。</p>
    </div>
    <div class="grid-4" style="gap:2vh 2vw">
      {''.join(text_card(f"建议 {idx:02d}", item) for idx, item in enumerate(items, 1))}
    </div>
  </div>
{foot("申报与答辩建议")}
</section>"""


def slide_close(total: int) -> str:
    return f"""
<section class="slide hero light">
{chrome("Closing", 10, total)}
  <div class="frame" style="display:grid;gap:5vh;align-content:center;min-height:80vh">
    <div class="kicker" data-anim>Takeaway</div>
    <h1 class="h-hero" style="font-size:min(7.2vw,12vh)" data-anim>从泛泛调研，到可执行选题。</h1>
    <p class="lead" style="max-width:62vw" data-anim>矿小智的价值不是替学生写结论，而是把矿业场景、论文线索、baseline、导师方向和交付物组织成一条能演示、能核验、能继续推进的路线。</p>
    <div class="meta-row" data-anim>
      <span>HTML 完整报告</span><span>·</span><span>文献综述</span><span>·</span><span>逐页展示 deck</span>
    </div>
  </div>
{foot("End")}
</section>"""


def build_slides(title: str, markdown: str) -> str:
    sections = split_sections(markdown)
    summary = compact(section_body(sections, ("研究主题", "主题概述", "研判结论")), 180)
    if not summary:
        summary = "面向矿井安全监测的大创选题调研，聚焦场景、论文、baseline、导师和可交付路线。"
    total = 10
    slides = [
        slide_cover(title, summary, total),
        slide_verdict(total, sections, markdown),
        slide_scenarios(total, sections),
        slide_challenges(total, sections),
        slide_papers(total, sections),
        slide_baseline(total, sections),
        slide_advisors(total, sections),
        slide_route(total, sections),
        slide_project(total, sections),
        slide_close(total),
    ]
    return "\n".join(slides)


def load_template() -> str:
    if not GUIZANG_TEMPLATE.exists():
        raise FileNotFoundError(f"Guizang template not found: {GUIZANG_TEMPLATE}")
    template = GUIZANG_TEMPLATE.read_text(encoding="utf-8")
    for old, new in INDIGO_THEME.items():
        template = template.replace(old, new)
    return template


def render_deck(title: str, markdown: str) -> str:
    template = load_template()
    html_doc = template.replace("[必填] 替换为 PPT 标题 · Deck Title", f"{title} · MineIntel Deck")
    html_doc = html_doc.replace("<!-- SLIDES_HERE -->", build_slides(title, markdown))
    return html_doc


def copy_motion_asset(output_dir: Path) -> None:
    if not GUIZANG_MOTION.exists():
        return
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(GUIZANG_MOTION, assets_dir / "motion.min.js")


def export(title: str, markdown: str, output_dir: Path, filename: str | None = None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    copy_motion_asset(output_dir)
    stem = safe_filename(filename or title)
    path = output_dir / f"{stem}_deck.html"
    path.write_text(render_deck(title, markdown), encoding="utf-8")
    return {"status": "success", "title": title, "files": {"deck": str(path.resolve())}}


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a MineIntel report as a Guizang-style HTML deck.")
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
