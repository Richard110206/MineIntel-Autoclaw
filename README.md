<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/MineIntel-AutoClaw-0a0f12?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzNGI3YTAiIHN0cm9rZS13aWR0aD0iMiI+PHBhdGggZD0iTTIgMjJoMjBWMkgydjIweiIvPjxwYXRoIGQ9Ik0xMiAyVjIyIi8+PHBhdGggZD0iTTIgMTJoMjAiLz48L3N2Zz4=&logoColor=34b7a0&labelColor=0a0f12&color=34b7a0">
    <img src="https://img.shields.io/badge/MineIntel-AutoClaw-1a1a2e?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzNGI3YTAiIHN0cm9rZS13aWR0aD0iMiI+PHBhdGggZD0iTTIgMjJoMjBWMkgydjIweiIvPjxwYXRoIGQ9Ik0xMiAyVjIyIi8+PHBhdGggZD0iTTIgMTJoMjAiLz48L3N2Zz4=&logoColor=34b7a0&labelColor=1a1a2e&color=34b7a0" alt="MineIntel-AutoClaw">
  </picture>
</p>

<h1 align="center">MineIntel-AutoClaw</h1>

<h3 align="center">基于多智能体的科创孵化助手</h3>

<p align="center">
  <a href="README_EN.md">English</a> | <strong>中文</strong>
</p>

<p align="center">
  <a href="https://github.com/Richard110206/MineIntel-Autoclaw">
    <img src="https://img.shields.io/github/stars/Richard110206/MineIntel-Autoclaw?style=social" alt="GitHub stars">
  </a>
  <img src="https://img.shields.io/badge/%E8%B5%9B%E4%BA%8B-2026%20%E8%AE%A1%E7%AE%97%E6%9C%BA%E8%AE%BE%E8%AE%A1%E5%A4%A7%E8%B5%9B-ff6b6b?style=flat-square" alt="Competition">
  <img src="https://img.shields.io/badge/%E5%A5%96%E9%A1%B9-%E6%B1%9F%E8%8B%8F%E7%9C%81%E4%B8%80%E7%AD%89%E5%A5%96-gold?style=flat-square&labelColor=%23c9a227&color=%23ffd700" alt="Award">
  <img src="https://img.shields.io/badge/%E8%B5%9B%E9%81%93-%E6%99%BA%E8%83%BD%E4%BD%93%E4%B8%93%E9%A1%B9%E8%B5%9B-9b59b6?style=flat-square" alt="Track">
  <br>
  <img src="https://img.shields.io/badge/%E5%B9%B3%E5%8F%B0-AutoClaw%20%7C%20GLM-34b7a0?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/MCP-%E5%85%BC%E5%AE%B9-4ac8e8?style=flat-square" alt="MCP">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/%E7%9F%BF%E4%BA%95%E5%BA%94%E7%94%A8%E7%9F%A5%E8%AF%86%E5%9B%BE%E8%B0%B1-7%20Skills-brightgreen?style=flat-square" alt="Skills">
  <img src="https://img.shields.io/badge/%E5%A4%9A%E4%B8%93%E5%AE%B6%E7%BC%96%E6%8E%92-7%20Agents-orange?style=flat-square" alt="Agents">
  <img src="https://img.shields.io/badge/%E5%AE%9E%E6%97%B6%E8%BF%9B%E5%BA%A6UI-Demo%20Ready-34b7a0?style=flat-square" alt="Demo">
  <img src="https://img.shields.io/badge/%E6%8A%A5%E5%91%8A%E8%BE%93%E5%87%BA-HTML%20%7C%20LaTeX%20%7C%20PDF-e74c3c?style=flat-square" alt="Output">
</p>

---

## 获奖

> **2026 年（第 21 届）中国大学生计算机设计大赛 — 智能体专项赛 江苏省一等奖**

---

## 项目简介

**MineIntel-AutoClaw（矿小智）** 是一个基于多智能体协作的科创孵化助手，面向矿井/矿业场景提供端到端科研调研服务。项目基于 [AutoClaw](https://github.com/zhipu-ai/autoclaw) 原生 Skill 架构构建，通过 7 个协作专家角色的多步编排，自动完成从场景分析、知识图谱检索、论文线索整理、Baseline 推荐到导师匹配的全链路科研调研，最终交付 HTML 完整报告与 LaTeX/PDF 文献综述。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    MineIntel-AutoClaw-Skill                      │
│                         （矿小智 总入口）                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────── mineintel-research ───────────────────┐   │
│  │                   （主控闭环 Skill）                        │   │
│  │                                                          │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │   │
│  │   │ Step 1   │→ │ Step 2   │→ │ Step 3               │  │   │
│  │   │ 任务理解  │  │ 知识图谱  │  │ 中文应用论文检索      │  │   │
│  │   └──────────┘  └──────────┘  └──────────┬───────────┘  │   │
│  │                                              │            │   │
│  │   ┌──────────────────────┐  ┌──────────┐    │            │   │
│  │   │ Step 6   经验参考     │  │ Step 5   │    │            │   │
│  │   │ 知乎/小红书           │← │ 导师匹配  │←   │            │   │
│  │   └──────────┬───────────┘  └──────────┘    │            │   │
│  │              ↓                               │            │   │
│  │   ┌──────────────────────┐  ┌──────────┐    │            │   │
│  │   │ Step 7   报告交付     │← │ Step 4   │←───┘            │   │
│  │   │ HTML / LaTeX / PDF   │  │ 国际前沿   │                 │   │
│  │   └──────────────────────┘  │ + Baseline │                 │   │
│  │                              └──────────┘                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────┐  ┌────────────┐  ┌─────────────────────────┐  │
│  │  知识图谱    │  │  MCP 检索   │  │  报告生成引擎            │  │
│  │  Knowledge   │  │  Literature │  │  HTML Poster & LaTeX    │  │
│  │  Graph       │  │  MCP Server │  │  Report Engine          │  │
│  └─────────────┘  └────────────┘  └─────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                 实时进度展示 UI (demo-ui)                    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心功能

<table>
<tr>
<td width="50%">

### 矿井应用知识图谱
基于白皮书、蓝皮书、政策标准和人工场景表构建，支持 **场景 → 痛点 → 解决方案 → 技术设备 → 来源依据** 的结构化检索与溯源。

</td>
<td width="50%">

### 多智能体协作编排
7 个协作专家角色按序编排：矿井应用专家 → 领域分析师 → 行业前沿专家 → Baseline 专家 → 导师申报专家 → 经验参考专家 → 总报告专家。

</td>
</tr>
<tr>
<td width="50%">

### 论文线索检索
内置 MCP Server，支持中文矿业期刊（煤炭学报、工矿自动化等）和国际前沿（arXiv、IEEE、MDPI）论文线索检索，MCP 不可用时自动脚本兜底。

</td>
<td width="50%">

### 导师方向匹配
自动检索中国矿业大学各学院官网师资页面，匹配研究方向相关的导师，给出姓名、学院和官网链接。

</td>
</tr>
<tr>
<td width="50%">

### 报告自动生成
自动生成 **HTML 完整报告**（magazine-poster 风格）和 **LaTeX/PDF 文献综述**，包含研究主题、场景分析、论文线索、技术路线等完整内容。

</td>
<td width="50%">

### 实时进度 UI
调研过程中实时同步进度到 Web 页面，展示当前阶段、思考过程、工具调用状态和完成百分比。

</td>
</tr>
</table>

---

## 技能组结构

| 技能 | 说明 | 核心能力 |
|:-----|:-----|:---------|
| `mineintel-research` | 主控闭环 Skill | 端到端任务编排，7 步流水线调度 |
| `mineintel-application-kg` | 矿井应用知识图谱 | 场景-痛点-解决方案结构化检索 |
| `mineintel-knowledge-rag` | 本地知识库与导师匹配 | RAG 检索 + 官网导师推荐 |
| `mineintel-literature-baseline` | 论文线索与 Baseline | MCP 工具 + 中英文论文检索 |
| `mineintel-experience-insights` | 科研经验参考 | 知乎/小红书经验提炼 |
| `mineintel-report-export` | 报告交付编排 | HTML + LaTeX/PDF 导出 |
| `mineintel-html-poster` | HTML 海报报告 | Magazine-poster 风格渲染 |
| `mineintel-literature-review` | 文献综述生成 | LaTeX 结构化综述 + PDF 编译 |

---

## 快速开始

### 环境要求

- [AutoClaw](https://github.com/zhipu-ai/autoclaw) Desktop App
- Python 3.x
- （可选）XeLaTeX — 用于 PDF 编译

### 安装

```bash
# 1. 克隆仓库
git clone git@github.com:Richard110206/MineIntel-Autoclaw.git

# 2. 将整个 MineIntel-AutoClaw-Skill 文件夹导入 AutoClaw 作为 Skill 组
#    拖入 AutoClaw Skills 目录即可自动识别

# 3. （可选）如果 AutoClaw 支持 MCP 注册，配置文献检索 MCP Server：
#    参见 MineIntel-AutoClaw-Skill/mineintel-literature-baseline/mcp_servers/mcp_config.json
```

### 使用方法

在 AutoClaw 中发送以下提示词即可触发完整的科研调研流程：

```
请使用 MineIntel-AutoClaw-Skill（矿小智）技能组，围绕"计算机视觉在矿井安全监测中的大创选题"生成科研调研报告。
我的专业是软件工程。
我想研究的技术领域是计算机视觉。
矿业场景是矿井安全监测。
```

输出将保存到 `output/<时间戳_报告标题>/` 目录：

| 文件 | 说明 |
|:-----|:-----|
| `<标题>_poster.html` | HTML 完整报告（magazine-poster 风格） |
| `<标题>_literature_review.tex` | 文献综述 LaTeX 源码 |
| `<标题>_literature_review.pdf` | 文献综述 PDF（需 XeLaTeX） |

---

## 技术栈

<p>
  <img src="https://img.shields.io/badge/AutoClaw-Agent%20Platform-34b7a0?style=for-the-badge" alt="AutoClaw">
  <img src="https://img.shields.io/badge/GLM-LLM%20Engine-4285f4?style=for-the-badge" alt="GLM">
  <img src="https://img.shields.io/badge/MCP-Tool%20Protocol-4ac8e8?style=for-the-badge" alt="MCP">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/XeLaTeX-PDF%20Engine-008080?style=for-the-badge" alt="XeLaTeX">
</p>

---

## 数据来源

| 来源 | 类型 | 用途 |
|:-----|:-----|:-----|
| 煤矿智能化蓝皮书（2025） | 白皮书 | 知识图谱构建 |
| 煤矿智能化建设指南（2021） | 政策标准 | 场景依据 |
| 国家矿山安全监察局政策 | 政策文件 | 行业背景 |
| 5G 智慧矿山白皮书 | 行业白皮书 | 技术参考 |
| 华为/中兴/中国电信矿山方案 | 企业方案 | 技术路线 |
| ABB/Siemens/Schneider Mining | 国际方案 | 前沿对比 |
| 矿井场景总览（20 场景） | 人工标注 | 高置信骨架 |

---

## 项目结构

```
MineIntel-AutoClaw-Skill/
├── SKILL.md                          # 总入口 Skill
├── README.txt                        # 提交说明
├── demo_prompts.txt                  # 演示提示词
│
├── mineintel-research/               # 主控闭环 Skill
│   ├── SKILL.md
│   ├── scripts/                      # 主控脚本
│   │   ├── progress_update.py
│   │   ├── start_progress_ui.py
│   │   ├── advisor_search.py
│   │   ├── paper_search.py
│   │   ├── github_search.py
│   │   └── ...
│   └── references/                   # 参考文档
│
├── mineintel-application-kg/         # 知识图谱 Skill
│   ├── SKILL.md
│   ├── scripts/
│   └── data/
│       ├── user_sources/             # 人工场景表
│       ├── raw_docs/                 # 原始文档（30+）
│       ├── clean/                    # 清洗后语料
│       └── kg/                       # 知识图谱数据
│
├── mineintel-knowledge-rag/          # 知识库 Skill
├── mineintel-literature-baseline/    # 论文检索 Skill（含 MCP）
│   ├── mcp_servers/                  # MCP Server
│   └── scripts/
├── mineintel-experience-insights/    # 经验参考 Skill
├── mineintel-report-export/          # 报告导出 Skill
├── mineintel-html-poster/            # HTML 海报 Skill
├── mineintel-literature-review/      # 文献综述 Skill
│
├── demo-ui/                          # 实时进度 UI
│   ├── index.html
│   └── assets/
│
├── output/                           # 报告输出目录
└── tools/                            # 辅助工具
```

---

## 参赛信息

| 项目 | 详情 |
|:-----|:-----|
| **赛事** | 2026 年中国大学生计算机设计大赛（CCDC） |
| **赛道** | 智能体专项赛 |
| **奖项** | 江苏省一等奖 |
| **作品** | MineIntel-AutoClaw（矿小智） |
| **院校** | 中国矿业大学 |

---

## 团队

<p align="center">
  <a href="https://github.com/Richard110206">
    <img src="https://img.shields.io/badge/Author-Richard110206-34b7a0?style=for-the-badge&logo=github&logoColor=white" alt="Author">
  </a>
</p>

---

## 许可证

本项目基于 MIT 许可证开源。

---

<p align="center">
  <sub>Built with</sub>
  <img src="https://img.shields.io/badge/AutoClaw-34b7a0?style=flat-square" alt="AutoClaw">
  <img src="https://img.shields.io/badge/%E7%9F%BF%E5%B0%8F%E6%99%BA-4fd4bb?style=flat-square" alt="矿小智">
  <br>
  <sub>MineIntel-AutoClaw &copy; 2026 — 2026 CCDC 智能体专项赛 江苏省一等奖</sub>
</p>
