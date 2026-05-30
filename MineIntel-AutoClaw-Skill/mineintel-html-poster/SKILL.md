---
name: mineintel-html-poster
description: >
  MineIntel HTML 完整报告导出 Skill。用于把矿业科研调研报告完整渲染为杂志排版风格的单页 HTML，
  适合比赛演示、结果展示、可打印网页和 MineIntel 品牌化报告页面。当用户要求 HTML、网页报告、
  magazine poster、展示页或报告视觉优化时使用。
---

# MineIntel HTML Report Skill

本 Skill 只负责把已经生成的调研内容完整转换为 MineIntel 品牌化 HTML，不负责重新检索论文、导师或 GitHub。

## 使用方式

优先调用脚本：

```bash
python {baseDir}/scripts/render_html_poster.py --title "<报告标题>" --content-file report_content.md --output-dir "<本次 output 文件夹>"
```

也可以通过 `--content` 或 stdin 传入报告正文。脚本输出：

- `files.html`：`<标题>_poster.html`

## 设计规则

- 采用杂志排版风格：顶部期刊栏、大标题、报告元信息、纸张纹理和正文排版。
- HTML 报告只输出完整报告正文，不生成摘要宫格、演示卡片或压缩版内容。
- 保留章节、列表、表格、论文链接、导师、GitHub baseline、技术路线、科研经验和搜索溯源。
- 所有外部论文、导师、仓库信息只作为“已检索线索”展示，正式申报前仍需核验。
- 不生成 Word、Markdown 或 PDF。

## 父级调用

`mineintel-report-export` 是父级交付 Skill。完整报告导出时由父级调用本 Skill，再调用 `mineintel-literature-review` 生成文献综述 LaTeX/PDF。
