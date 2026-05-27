---
name: mineintel-html-poster
description: >
  MineIntel HTML 完整报告导出 Skill。用于把矿业科研调研报告完整渲染为 magazine-poster 风格的单页 HTML，
  适合比赛演示、结果展示、可打印网页和 MineIntel 品牌化报告页面。当用户要求 HTML、网页报告、
  海报风格、magazine poster、展示页或报告视觉优化时使用。
mode: generate
scenario: poster
surface: html
---

# MineIntel HTML Poster Skill

本 Skill 把已经生成的调研内容完整转换为 MineIntel 品牌化 HTML，不负责重新检索论文、导师或 GitHub。

## 使用方式

### 方式一：Skill 直接生成（推荐）

Agent 根据下方「设计规则」和「模板结构」，将报告 markdown 内容直接渲染为完整 HTML 文件，写入 `--output-dir` 指定目录。

这是比赛展示推荐的方式——由 AI agent 作为 Skill 执行者，根据规则即时生成高质量海报 HTML。

### 方式二：Python 脚本备选

当 agent 不具备直接生成能力时，可降级调用脚本：

```bash
python {baseDir}/scripts/render_html_poster.py --title "<报告标题>" --content-file report_content.md --output-dir "<本次 output 文件夹>"
```

也可以通过 `--content` 或 stdin 传入报告正文。脚本输出：

- `files.html`：`<标题>_poster.html`

## 设计规则

- 采用 **magazine-poster / Sunday-paper editorial** 风格。
- 必须保留原报告的**完整内容**，不得把报告压缩成摘要卡片。
- 保留章节、列表、表格、论文链接、导师、GitHub baseline、技术路线、科研经验和搜索溯源。
- 所有外部论文、导师、仓库信息只作为"已检索线索"展示，正式申报前仍需核验。
- 不生成 Word、Markdown 或 PDF。

## 模板结构

```
┌──────────────────────────────────────────────────┐
│  Dateline 顶栏                                    │
│  CUMT · 矿业纪事报  §  日期 · Vol.1 · AutoClaw    │
│  ══════════════════════════════════════════════    │
│  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬    │
│                                                    │
│  MineIntel Research                               │
│  <大标题>超大 serif 粗体                           │
│                                                    │
│  <deck 摘要段落，serif 正文字号>                    │
│                                                    │
│  ┌────────┬────────┬────────┬────────┐            │
│  │ N 章节 │ N 论文  │ N 链接  │ 生成时间 │           │
│  └────────┴────────┴────────┴────────┘            │
│  ══════════════════════════════════════════════    │
│                                                    │
│  ┌─── 双栏正文 ───────────────────────────┐       │
│  │ Section 1  │  Section 2               │       │
│  │ 小标题+正文 │  小标题+正文              │       │
│  │            │                          │       │
│  │ Section 3  │  Section 4               │       │
│  │ ...        │  ...                     │       │
│  └────────────────────────────────────────┘       │
│                                                    │
│  ══════════════════════════════════════════════    │
│  † MineIntel · 矿小智科研情报平台 · 中国矿业大学    │
│    Magazine-Poster Style · Full Report Retained    │
└──────────────────────────────────────────────────┘
```

## 视觉规范

### 配色

| 变量 | 值 | 用途 |
|------|----|------|
| `--paper` | `#f3eee2` | 主背景，暖灰奶油色 |
| `--paper-deep` | `#e8dfcb` | 表头、深色背景区域 |
| `--ink` | `#1a1710` | 主文字色 |
| `--muted` | `#6e685a` | 辅助文字、日期、标签 |
| `--rule` | `#c8bea4` | 分隔线、表格边框 |
| `--accent` | `#1a5c2e` | 主强调色（绿），链接、blockquote 左线 |
| `--accent-2` | `#a04a2a` | 副强调色（砖红），h3 标题 |
| `--tint` | `#e6ead8` | blockquote 背景 |

### 字体

| 角色 | 字体栈 |
|------|--------|
| 展示标题 | `"Playfair Display", "Noto Serif SC", "Songti SC", Georgia, serif` |
| 正文 | `"IBM Plex Serif", "Noto Serif SC", "Songti SC", Georgia, serif` |
| 中文 | `"Noto Serif SC", "Songti SC", "SimSun", "STSong", Georgia, serif` |
| 等宽 | `"JetBrains Mono", "IBM Plex Mono", Consolas, monospace` |

Google Fonts 引用：
```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,800;0,900;1,400;1,700;1,800&family=IBM+Plex+Serif:ital,wght@0,400;0,500;0,600;1,400;1,500&family=JetBrains+Mono:wght@400;500&family=Noto+Serif+SC:wght@400;500;600;700;900&display=swap" rel="stylesheet">
```

### 布局参数

- 页面容器：`max-width: 1100px; padding: 48px 56px 64px`
- 大标题：`font-weight: 900; font-size: clamp(48px, 7vw, 88px)`
- 双栏正文：`column-count: 2; column-gap: 3.2rem; column-rule: 1px solid var(--rule)`
- 纸感背景：`radial-gradient(circle, rgba(31,28,23,0.06) 1px, transparent 1.4px) 0 0 / 16px 16px` 叠加 `var(--paper)`
- Dateline 底线：`border-bottom: 3px double var(--ink)`
- 正文上方粗线：`height: 4px; background: var(--ink)`
- Section 标题上方：`border-top: 3px solid var(--ink)`
- 响应式断点：`860px` 以下切为单栏

### Blockquote 引用块

- 左线：`5px solid var(--accent)`
- 背景：`var(--tint)`
- 伪元素装饰性左引号，`font-size: 48px; opacity: .35; color: var(--accent)`

### 统计条 (Stats Strip)

- 4 列 grid：`grid-template-columns: repeat(4, minmax(0, 1fr))`
- 数字 `font: 800 32px/1.1 serif-display`
- 标签 `font: 11px/1.4 mono; letter-spacing: .06em; text-transform: uppercase`

## 生成输出要求

- 文件名：`<标题>_poster.html`
- `<html lang="zh-CN">`
- 所有 CSS 内联在 `<style>` 中，不依赖外部 CSS 文件
- 必须包含 Google Fonts 预连接和引用
- 响应式支持（860px 以下单栏）和打印样式
- 保留全部原始 markdown 内容的完整渲染（不压缩为摘要）

## 父级调用

`mineintel-report-export` 是父级交付 Skill。完整报告导出时由父级调用本 Skill，再调用 `mineintel-literature-review` 生成文献综述 LaTeX/PDF。
