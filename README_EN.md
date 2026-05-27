<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/MineIntel-AutoClaw-0a0f12?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzNGI3YTAiIHN0cm9rZS13aWR0aD0iMiI+PHBhdGggZD0iTTIgMjJoMjBWMkgydjIweiIvPjxwYXRoIGQ9Ik0xMiAyVjIyIi8+PHBhdGggZD0iTTIgMTJoMjAiLz48L3N2Zz4=&logoColor=34b7a0&labelColor=0a0f12&color=34b7a0">
    <img src="https://img.shields.io/badge/MineIntel-AutoClaw-1a1a2e?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMzNGI3YTAiIHN0cm9rZS13aWR0aD0iMiI+PHBhdGggZD0iTTIgMjJoMjBWMkgydjIweiIvPjxwYXRoIGQ9Ik0xMiAyVjIyIi8+PHBhdGggZD0iTTIgMTJoMjAiLz48L3N2Zz4=&logoColor=34b7a0&labelColor=1a1a2e&color=34b7a0" alt="MineIntel-AutoClaw">
  </picture>
</p>

<h1 align="center">MineIntel-AutoClaw</h1>

<h3 align="center">Multi-Agent Based Sci-Tech Innovation Incubation Assistant</h3>

<p align="center">
  <strong>English</strong> | <a href="README.md">中文</a>
</p>

<p align="center">
  <a href="https://github.com/Richard110206/MineIntel-Autoclaw">
    <img src="https://img.shields.io/github/stars/Richard110206/MineIntel-Autoclaw?style=social" alt="GitHub stars">
  </a>
  <img src="https://img.shields.io/badge/Platform-AutoClaw%20%7C%20GLM-34b7a0?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/MCP-Compatible-4ac8e8?style=flat-square" alt="MCP">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Knowledge_Graph-7%20Skills-brightgreen?style=flat-square" alt="Skills">
  <img src="https://img.shields.io/badge/Multi_Agent-7%20Experts-orange?style=flat-square" alt="Agents">
  <img src="https://img.shields.io/badge/Progress_UI-Demo%20Ready-34b7a0?style=flat-square" alt="Demo">
  <img src="https://img.shields.io/badge/Report_Output-HTML%20%7C%20LaTeX%20%7C%20PDF-e74c3c?style=flat-square" alt="Output">
</p>

---

## Award

> **2026 Chinese Collegiate Computing Competition (CCDC) — Intelligent Agent Special Track, Jiangsu Province First Prize**
>
> 2026 (21st) Chinese Collegiate Computing Competition

---

## Overview

**MineIntel-AutoClaw** is a multi-agent based sci-tech innovation incubation assistant designed for mining-related research scenarios. Built on [AutoClaw](https://github.com/zhipu-ai/autoclaw)'s native Skill architecture, it orchestrates 7 collaborative expert roles through a multi-step pipeline to automate the full research workflow — from scene analysis, knowledge graph retrieval, and literature search to baseline recommendation and advisor matching — ultimately delivering polished HTML reports and LaTeX/PDF literature reviews.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MineIntel-AutoClaw-Skill                      │
│                       (Master Entry Point)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────── mineintel-research ───────────────────┐   │
│  │                 (Main Orchestrator Skill)                  │   │
│  │                                                          │   │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │   │
│  │   │ Step 1   │→ │ Step 2   │→ │ Step 3               │  │   │
│  │   │ Task     │  │ Knowledge│  │ Chinese Literature   │  │   │
│  │   │ Analysis │  │ Graph    │  │ Search               │  │   │
│  │   └──────────┘  └──────────┘  └──────────┬───────────┘  │   │
│  │                                              │            │   │
│  │   ┌──────────────────────┐  ┌──────────┐    │            │   │
│  │   │ Step 6   Experience  │  │ Step 5   │    │            │   │
│  │   │ Insights (Zhihu etc) │← │ Advisor  │←   │            │   │
│  │   └──────────┬───────────┘  │ Matching │    │            │   │
│  │              ↓               └──────────┘    │            │   │
│  │   ┌──────────────────────┐  ┌──────────┐    │            │   │
│  │   │ Step 7   Report      │← │ Step 4   │←───┘            │   │
│  │   │ HTML / LaTeX / PDF   │  │ Frontier  │                 │   │
│  │   └──────────────────────┘  │ + Baseline│                 │   │
│  │                              └──────────┘                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────┐  ┌────────────┐  ┌─────────────────────────┐  │
│  │ Knowledge   │  │ Literature │  │ HTML Poster & LaTeX      │  │
│  │ Graph       │  │ MCP Server │  │ Report Engine            │  │
│  └─────────────┘  └────────────┘  └─────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               Real-time Progress UI (demo-ui)              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature Highlights

<table>
<tr>
<td width="50%">

### Mining Knowledge Graph
Built from white papers, blue books, policy standards, and manually curated scenario tables. Supports structured retrieval and traceability along the chain: **Scenario → Pain Point → Solution → Equipment → Evidence**.

</td>
<td width="50%">

### Multi-Agent Orchestration
7 collaborative expert roles orchestrated sequentially: Mining Application Expert → Domain Analyst → Frontier Technology Expert → Baseline Expert → Advisor Matching Expert → Experience Insights Expert → Report Synthesis Expert.

</td>
</tr>
<tr>
<td width="50%">

### Literature Search
Built-in MCP Server for searching Chinese mining journals (Journal of China Coal Society, Industry and Mine Automation, etc.) and international venues (arXiv, IEEE, MDPI). Falls back to Python scripts when MCP is unavailable.

</td>
<td width="50%">

### Advisor Matching
Automatically crawls faculty pages from colleges at China University of Mining and Technology, matching research-direction-relevant advisors with name, department, and official website links.

</td>
</tr>
<tr>
<td width="50%">

### Report Generation
Automatically produces **HTML full reports** (magazine-poster style) and **LaTeX/PDF literature reviews**, covering research topics, scene analysis, literature leads, technical roadmaps, and more.

</td>
<td width="50%">

### Real-time Progress UI
Synchronizes research progress to a web page in real time, displaying the current stage, agent thinking process, tool call status, and completion percentage.

</td>
</tr>
</table>

---

## Skill Structure

| Skill | Description | Key Capability |
|:------|:------------|:---------------|
| `mineintel-research` | Main Orchestrator Skill | End-to-end task orchestration, 7-step pipeline |
| `mineintel-application-kg` | Mining Application KG | Structured scenario-pain-solution retrieval |
| `mineintel-knowledge-rag` | Local Knowledge & Advisor | RAG retrieval + official advisor matching |
| `mineintel-literature-baseline` | Literature & Baseline | MCP tools + bilingual paper search |
| `mineintel-experience-insights` | Experience Insights | Zhihu/Xiaohongshu experience distillation |
| `mineintel-report-export` | Report Export | HTML + LaTeX/PDF export |
| `mineintel-html-poster` | HTML Poster | Magazine-poster style rendering |
| `mineintel-literature-review` | Literature Review | Structured LaTeX review + PDF compilation |

---

## Quick Start

### Prerequisites

- [AutoClaw](https://github.com/zhipu-ai/autoclaw) Desktop App
- Python 3.x
- (Optional) XeLaTeX — for PDF compilation

### Installation

```bash
# 1. Clone the repository
git clone git@github.com:Richard110206/MineIntel-Autoclaw.git

# 2. Import the entire MineIntel-AutoClaw-Skill folder into AutoClaw as a Skill group
#    Drag it into the AutoClaw Skills directory for automatic recognition

# 3. (Optional) If AutoClaw supports MCP registration, configure the literature MCP Server:
#    See MineIntel-AutoClaw-Skill/mineintel-literature-baseline/mcp_servers/mcp_config.json
```

### Usage

Send the following prompt in AutoClaw to trigger the full research pipeline:

```
Please use the MineIntel-AutoClaw-Skill to generate a research report on "Computer Vision for Safety Monitoring in Underground Mines."
My major is Software Engineering.
My research field is Computer Vision.
The mining scenario is underground mine safety monitoring.
```

Output is saved to `output/<timestamp_report-title>/`:

| File | Description |
|:-----|:------------|
| `<title>_poster.html` | Full HTML report (magazine-poster style) |
| `<title>_literature_review.tex` | Literature review LaTeX source |
| `<title>_literature_review.pdf` | Literature review PDF (requires XeLaTeX) |

---

## Tech Stack

<p>
  <img src="https://img.shields.io/badge/AutoClaw-Agent%20Platform-34b7a0?style=for-the-badge" alt="AutoClaw">
  <img src="https://img.shields.io/badge/GLM-LLM%20Engine-4285f4?style=for-the-badge" alt="GLM">
  <img src="https://img.shields.io/badge/MCP-Tool%20Protocol-4ac8e8?style=for-the-badge" alt="MCP">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/XeLaTeX-PDF%20Engine-008080?style=for-the-badge" alt="XeLaTeX">
</p>

---

## Data Sources

| Source | Type | Usage |
|:-------|:-----|:------|
| Coal Mine Intelligent Blue Book (2025) | Blue Book | Knowledge graph construction |
| Coal Mine Intelligent Construction Guide (2021) | Policy Standard | Scenario evidence |
| National Mine Safety Administration Policies | Policy Documents | Industry background |
| 5G Smart Mine White Papers | Industry White Paper | Technical reference |
| Huawei/ZTE/China Telecom Mining Solutions | Enterprise Solutions | Technology roadmap |
| ABB/Siemens/Schneider Mining | International Solutions | Frontier comparison |
| Mining Scenario Overview (20 scenarios) | Manual Annotation | High-confidence skeleton |

---

## Project Structure

```
MineIntel-AutoClaw-Skill/
├── SKILL.md                          # Master entry Skill
├── README.txt                        # Submission notes
├── demo_prompts.txt                  # Demo prompts
│
├── mineintel-research/               # Main orchestrator Skill
│   ├── SKILL.md
│   ├── scripts/                      # Core scripts
│   │   ├── progress_update.py
│   │   ├── start_progress_ui.py
│   │   ├── advisor_search.py
│   │   ├── paper_search.py
│   │   ├── github_search.py
│   │   └── ...
│   └── references/                   # Reference documents
│
├── mineintel-application-kg/         # Knowledge graph Skill
│   ├── SKILL.md
│   ├── scripts/
│   └── data/
│       ├── user_sources/             # Manual scenario tables
│       ├── raw_docs/                 # Raw documents (30+)
│       ├── clean/                    # Cleaned corpus
│       └── kg/                       # Knowledge graph data
│
├── mineintel-knowledge-rag/          # Local knowledge Skill
├── mineintel-literature-baseline/    # Literature search Skill (with MCP)
│   ├── mcp_servers/                  # MCP Server
│   └── scripts/
├── mineintel-experience-insights/    # Experience insights Skill
├── mineintel-report-export/          # Report export Skill
├── mineintel-html-poster/            # HTML poster Skill
├── mineintel-literature-review/      # Literature review Skill
│
├── demo-ui/                          # Real-time progress UI
│   ├── index.html
│   └── assets/
│
├── output/                           # Report output directory
└── tools/                            # Utility tools
```

---

## Competition Info

| Item | Detail |
|:-----|:-------|
| **Competition** | 2026 Chinese Collegiate Computing Competition (CCDC) |
| **Track** | Intelligent Agent Special |
| **Award** | Jiangsu Province First Prize |
| **Project** | MineIntel-AutoClaw |
| **Institution** | China University of Mining and Technology |

---

## Team

<p align="center">
  <a href="https://github.com/Richard110206">
    <img src="https://img.shields.io/badge/Author-Richard110206-34b7a0?style=for-the-badge&logo=github&logoColor=white" alt="Author">
  </a>
</p>

---

## License

This project is licensed under the MIT License.

---

<p align="center">
  <sub>Built with</sub>
  <img src="https://img.shields.io/badge/AutoClaw-34b7a0?style=flat-square" alt="AutoClaw">
  <img src="https://img.shields.io/badge/MineIntel-4fd4bb?style=flat-square" alt="MineIntel">
  <br>
  <sub>MineIntel-AutoClaw &copy; 2026</sub>
</p>
