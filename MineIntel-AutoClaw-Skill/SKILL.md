---
name: MineIntel-AutoClaw-Skill
description: >
  矿小智 MineIntel 技能组总入口。用于矿井/矿业场景下的大创选题科研调研、矿井应用知识图谱检索、
  中文应用论文与国际前沿论文检索、GitHub baseline 推荐、导师方向匹配、知乎/小红书科研经验参考、
  MineIntel 实时进度网页展示，以及 HTML 完整报告、逐页展示 Deck、文献综述 LaTeX/PDF 和导师套磁邮件草稿生成。用户提到
  MineIntel-AutoClaw-Skill、MineIntel、矿小智、mineintel-research、矿井安全监测调研、大创选题报告、
  导师推荐、论文线索或 baseline 推荐时，应优先使用本技能组。
compatibility:
  requires:
    - Python 3.x standard library
---

# MineIntel-AutoClaw-Skill 总入口

这是矿小智 MineIntel 技能组的顶层入口。收到科研调研、大创选题、矿井安全监测、矿业智能化、论文线索、GitHub baseline、导师匹配或报告导出类任务时，不要改用通用 deepresearch；应进入本文件夹下的 `mineintel-research/SKILL.md` 作为主控流程。

## 触发别名

用户可能会用以下说法调用本技能组：

- MineIntel-AutoClaw-Skill
- MineIntel
- 矿小智
- mineintel-research
- 矿井安全监测科研调研
- 矿业大创选题报告
- 论文线索 + baseline + 导师推荐

这些都应路由到 `mineintel-research` 主控 Skill。

## 主控流程

主控入口：

```text
mineintel-research/SKILL.md
```

主控 Skill 会继续编排以下子 Skill：

- `mineintel-application-kg`：矿井应用知识图谱，负责场景、痛点、解决方案、设备和来源依据。
- `mineintel-literature-baseline`：论文线索与 GitHub baseline 检索，优先使用 MCP tools，失败时脚本兜底。
- `mineintel-knowledge-rag`：本地知识库与导师候选库补充。
- `mineintel-experience-insights`：知乎/小红书科研经验参考。
- `mineintel-report-export`：报告交付编排。
- `mineintel-html-poster`：MineIntel 杂志排版风格 HTML 完整报告，只保留完整正文，不再生成摘要宫格。
- `mineintel-deck-export`：归藏风格横向翻页 HTML deck。
- `mineintel-literature-review`：文献综述 LaTeX/PDF。
- `mineintel-email-draft`：根据第一个导师推荐生成套磁邮件草稿；只写 Gmail Drafts，不发送邮件。
- `excalidraw-diagram-generator`：项目内 Excalidraw 图示生成参考，用于技术路线流程图源文件。

## 执行要求

1. 如果用户没有说明专业和技术领域，最多问一次：
   - 专业背景是什么？
   - 想研究的技术方向是什么？
2. 一旦专业、技术方向和矿业场景明确，直接按 `mineintel-research/SKILL.md` 执行。
3. 不要在聊天区输出工具报错、编码问题、搜索超时、命令重试等内部过程；只输出“当前正在做什么、已经完成什么”。
4. 运行开始时打开并同步 `demo-ui` 实时进度页面。
5. 最终输出保存到 `output/<时间戳_报告标题>/`，至少包含 HTML 完整报告、逐页展示 Deck、技术路线 Excalidraw 源文件、文献综述 `.tex`，如果工作区内存在 `local_tools/MiKTeX/.../xelatex.exe` 则编译 PDF。

## 推荐调用句

```text
请使用 MineIntel-AutoClaw-Skill（矿小智）技能组，按 mineintel-research 主控流程，围绕“计算机视觉在矿井安全监测中的大创选题”生成科研调研报告。
我的专业是软件工程。
我想研究的技术领域是计算机视觉。
矿业场景是矿井安全监测。
```
