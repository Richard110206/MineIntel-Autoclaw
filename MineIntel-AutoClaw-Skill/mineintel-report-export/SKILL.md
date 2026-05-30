---
name: mineintel-report-export
description: >
  MineIntel 报告交付编排 Skill。用于把已经完成的矿业科研调研内容保存到 output/<时间戳_标题>/，
  并调用子 Skill 生成 MineIntel 杂志排版风格完整 HTML 报告、归藏风格逐页展示 Deck、
  文献综述 LaTeX 源码和可选 PDF。
  当用户需要正式交付、HTML 展示页、LaTeX 文献综述、PDF、报告保存或输出文件夹整理时使用。
compatibility:
  requires:
    - Python 3.x standard library
---

# MineIntel Report Export Skill

本 Skill 是交付层父级 Skill，只负责编排和落盘。内容生成、论文判断和导师匹配应在 `mineintel-research` 主控流程里完成。

## 子 Skill

- `mineintel-html-poster`：把报告正文完整渲染为杂志排版风格 HTML 报告，不生成摘要宫格，不删减章节内容。
- `mineintel-deck-export`：把同一份报告正文重排为归藏风格横向翻页 HTML deck，便于答辩展示。
- `mineintel-literature-review`：从报告正文中抽取论文、背景、痛点和路线，生成文献综述 `.tex`，并在工作区内 `xelatex` 可用时编译 PDF。

## 使用方式

优先调用：

```bash
python {baseDir}/scripts/save_report.py --title "<报告标题>" --content-file report_content.md
```

默认输出目录：

```text
MineIntel-AutoClaw-Skill/output/<时间戳_报告标题>/
```

默认交付文件：

- `<标题>_poster.html`
- `<标题>_deck.html`
- `<标题>_literature_review.tex`
- `<标题>_literature_review.pdf`（工作区内 xelatex 编译成功时）

不再把 Markdown 和 Word 作为正式输出。Markdown 只作为脚本输入，Word/docx 不生成。

## 实时进度

开始导出时同步：

```bash
python {baseDir}/../mineintel-research/scripts/progress_update.py --step report --status running --percent 94 --message "正在生成 HTML 完整报告、逐页展示 Deck 和文献综述 PDF。"
```

导出完成后同步：

```bash
python {baseDir}/../mineintel-research/scripts/progress_update.py --step report --status done --percent 100 --done --message "报告已生成并导出完成。"
```

对话区只输出当前阶段和最终路径，不输出编码问题、命令修复、重试或工具切换过程。

## 执行规则

1. 必须保存文件到 `output/<时间戳_标题>/`，不要只返回聊天文本。
2. 必须调用 `mineintel-html-poster` 生成 HTML 完整报告。
3. 必须调用 `mineintel-deck-export` 生成逐页展示版 HTML deck。
4. 必须调用 `mineintel-literature-review` 生成文献综述 `.tex`；如果工作区内 `xelatex` 可用，再编译 PDF。
5. 禁止跳出工作区调用外部 MiKTeX/TeX Live 绝对路径。演示机编译器应放在工作区根目录 `local_tools/MiKTeX/`，与提交包平级。
6. PDF 编译失败不能中断任务，保留 `.tex`、HTML 报告和 deck。
7. Windows/PowerShell 下不要使用 Bash heredoc；长中文报告先写入临时 Markdown 文件，再用 `--content-file` 调用脚本。

## 最终回复

只给出高信号路径：

```text
HTML 完整报告：<poster.html 路径>
逐页展示 Deck：<deck.html 路径>
文献综述 LaTeX：<literature_review.tex 路径>
文献综述 PDF：<literature_review.pdf 路径，如已编译成功>
输出目录：<output 目录>
```
