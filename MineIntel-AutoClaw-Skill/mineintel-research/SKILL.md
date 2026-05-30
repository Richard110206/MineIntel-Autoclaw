---
name: mineintel-research
description: >
  矿小智 MineIntel 科研调研主控 Skill。用于矿井/矿业场景下的大创选题分析、矿井应用知识图谱检索、
  中文矿业应用论文检索、国际前沿论文检索、GitHub baseline 推荐、导师方向匹配、知乎/小红书科研经验参考，
  并生成 HTML 完整报告、逐页展示 Deck、文献综述 LaTeX 和可选 PDF。当用户提出矿井、煤矿、矿业、安全监测、智能采矿、
  科研选题、大创、论文推荐、baseline 推荐、导师推荐或调研报告等需求时使用。
compatibility:
  requires:
    - Python 3.x standard library
---

# MineIntel Research Skill

这是 MineIntel 技能组的主控 Skill，负责端到端编排。脚本只负责确定性检索、UI 同步和文件导出；调研判断、信息取舍和报告综合由 AutoClaw/GLM 按本文件执行。

## 技能组结构

- `mineintel-application-kg`：矿井应用知识图谱，负责矿井应用专家的场景、痛点、解决方案、设备和白皮书/蓝皮书依据。
- `mineintel-literature-baseline`：领域分析师和行业前沿技术专家，优先通过 MCP tools 检索中文应用论文、国际前沿论文和一个 GitHub baseline。
- `mineintel-experience-insights`：知乎/小红书科研经验、大创经验和答辩经验检索，只作为经验参考。
- `mineintel-report-export`：父级交付 Skill，调用 `mineintel-html-poster`、`mineintel-deck-export` 和 `mineintel-literature-review`，生成 HTML 完整报告、逐页展示 Deck、技术路线 Excalidraw 源文件、文献综述 `.tex` 和可选 PDF。
- `mineintel-html-poster`：杂志排版风格 HTML 完整报告。
- `mineintel-deck-export`：归藏风格横向翻页 HTML deck。
- `mineintel-literature-review`：文献综述 LaTeX/PDF。
- `mineintel-email-draft`：可选套磁邮件草稿生成；只追加到 Gmail Drafts，不发送邮件。
- `excalidraw-diagram-generator`：项目内 Excalidraw 图示生成参考，随项目提交。

完整任务优先使用本主控 Skill。局部任务可以直接调用对应子 Skill。

## 最小提问规则

正式检索前必须确认两个字段：专业背景、想研究的技术领域。若缺少任一字段，一次性询问：

```text
为了把选题和导师推荐做得更贴合，我需要确认两个信息：
1. 你的专业或方向是什么？例如软件工程、计算机科学、人工智能、安全工程、矿业工程等。
2. 你更想研究哪个技术领域？例如计算机视觉、深度学习、物联网、机器人、数字孪生、边缘计算、NLP 等。
```

用户回答后立即执行，不再反复追问。缺省规则：

- 专业：用户不确定时默认“计算机类/软件工程方向”。
- 技术方向：默认“计算机视觉 + 深度学习”。
- 矿业场景：默认“矿井安全监测”。
- 交付格式：HTML 完整报告、逐页展示 Deck、文献综述 LaTeX、文献综述 PDF（工作区内 xelatex 可用时）。

## UI 与对话规则

确认信息后立即打开实时进度 UI：

```bash
python {baseDir}/scripts/start_progress_ui.py --task "<研究主题>" --major "<专业或方向>" --field "<技术领域>" --scene "<矿业场景>" --formats "HTML 完整报告 / 逐页展示 Deck / 文献综述 LaTeX / PDF"
```

工作过程中每次只推进一个阶段，按顺序同步：

```text
confirm -> knowledge -> paper -> baseline -> advisor -> experience -> report -> email（仅用户要求 Gmail 草稿时）
```

对话区只写“当前”和“已完成”，或直接交给 UI 展示。禁止输出内部调度话术，包括“报错、编码问题、超时、重试、web_search、open_link、数据充足、线索足够、让我换一种方式”等。

## 多专家流程

1. 矿井应用专家：调用知识图谱，回答“矿井里为什么需要这个技术、落在哪些场景、痛点是什么”。
2. 领域分析师：检索煤炭学报、采矿与安全工程学报、工矿自动化、煤炭科学技术、矿业安全与环保等中文应用论文。
3. 行业前沿技术专家：检索 arXiv、DBLP、IEEE、Springer、MDPI、Nature/SciData 等国际前沿论文或综述。
4. baseline 专家：只保留一个最相关 GitHub baseline，说明为什么适合迁移。
5. 导师与申报专家：推荐 6 名具体导师，结果区只展示姓名、学院、链接；如果后续要生成 Gmail 草稿，第 1 名必须是具体自然人导师并尽量给出官网核验邮箱。
6. 科研经验参考专家：检索知乎/小红书公开搜索线索，提炼项目推进和答辩建议，不作为论文或技术事实依据。
7. 总报告专家：合并信息，调用 `save_report.py` 导出 HTML 完整报告、逐页展示 Deck 和文献综述 LaTeX/PDF。

需要更详细角色分工时读取 `references/multi_agent_workflow.md`。

## Step 1: 任务理解

提取：

- 技术方向
- 矿业场景
- 用户专业方向
- 是否有指定学校、导师、比赛或输出要求

同步确认阶段：

```bash
python {baseDir}/scripts/progress_update.py --step confirm --status running --percent 15 --done --major "<专业或方向>" --field "<技术领域>" --scene "<矿业场景>" --formats "HTML 完整报告 / 逐页展示 Deck / 文献综述 LaTeX / PDF" --message "已确认专业背景和研究领域，开始检索矿井应用知识图谱。"
```

## Step 2: 矿井应用知识图谱

先调用知识图谱，不要把这一阶段写成普通 RAG：

```bash
python {baseDir}/scripts/progress_update.py --step knowledge --status running --percent 25 --message "正在检索矿井应用知识图谱。"
python {baseDir}/../mineintel-application-kg/scripts/kg_search.py "<技术方向> <矿业场景> 痛点 解决方案 技术设备" --limit 8
python {baseDir}/scripts/progress_update.py --step knowledge --status running --percent 38 --done --message "矿井应用知识图谱检索完成，开始领域论文线索检索。"
```

整理 2-4 个应用场景、3-5 个矿井特殊技术难点、对应解决方案、设备要求和来源依据。

## Step 3: 领域分析师中文应用论文

优先调用 MCP tool `mineintel_domain_analyst_search`，参数至少包含 `topic=<技术方向>` 和 `scenario=<矿业场景>`。MCP 不可用时退回：

```bash
python {baseDir}/scripts/progress_update.py --step paper --status running --percent 48 --message "正在检索中文矿业论文线索。"
python {baseDir}/scripts/paper_search.py "<技术方向> <矿业场景>" --scope chinese --max-results 8
python {baseDir}/scripts/progress_update.py --step paper --status running --percent 60 --done --message "论文线索检索完成，开始整理国际前沿和 baseline。"
```

要求：

- 保留全部有效论文线索，不要只写 1 条。
- 每条尽量包含标题、来源/平台、年份、核心内容、链接。
- 没打开原文的内容写成“线索”或“需核验”，不要编造实验结果。

## Step 4: 行业前沿技术与 GitHub baseline

优先调用 MCP tool `mineintel_frontier_technology_search`，参数至少包含 `topic=<技术方向>`、`scenario=<矿业场景>`、`english_topic=<英文关键词>`。MCP 不可用时退回：

```bash
python {baseDir}/scripts/progress_update.py --step baseline --status running --percent 68 --message "正在检索国际前沿和 GitHub baseline。"
python {baseDir}/scripts/paper_search.py "<English technique> underground mining safety monitoring" --scope international --max-results 8
python {baseDir}/scripts/github_search.py "<English technique> mining detection" --limit 1
python {baseDir}/scripts/progress_update.py --step baseline --status running --percent 76 --done --message "baseline 检索完成，开始导师方向匹配。"
```

GitHub 结果只保留 1 个最相关仓库，避免网页端重复显示。

## Step 5: 导师方向匹配

调用：

```bash
python {baseDir}/scripts/progress_update.py --step advisor --status running --percent 82 --message "正在匹配导师方向。"
python {baseDir}/scripts/advisor_search.py "<技术方向> <矿业场景>" --school "中国矿业大学" --max-results 8 --open-pages 3
python {baseDir}/scripts/progress_update.py --step advisor --status running --percent 84 --done --message "导师匹配完成，开始补充科研经验参考。"
```

规则：

- 推荐 6 名具体自然人导师。
- 只展示姓名、学院、链接；没有学院的候选不要进结果区。
- 优先检索中国矿业大学徐州官网和各学院官网，如 `cs.cumt.edu.cn`、`safe.cumt.edu.cn`、`cese.cumt.edu.cn`、`cmee.cumt.edu.cn`、`siee.cumt.edu.cn`、`faculty.cumt.edu.cn`。
- 官网不足时可由 `advisor_search.py` 使用校内候选库补位，但仍要给出矿大官网限定搜索链接。
- 禁止把“某学院导师群体”“课题组群体”写成导师。

## Step 6: 科研经验参考

调用：

```bash
python {baseDir}/scripts/progress_update.py --step experience --status running --percent 88 --message "正在补充科研经验参考。"
python {baseDir}/../mineintel-experience-insights/scripts/experience_search.py "<技术方向> <矿井场景>" --scenario "<矿井场景>" --max-results 4
python {baseDir}/scripts/progress_update.py --step experience --status running --percent 92 --done --message "科研经验参考整理完成，开始生成报告。"
```

只提炼可执行建议，例如选题范围、数据来源、baseline 复现、答辩准备和风险说明。知乎/小红书链接只能作为公开搜索入口或经验参考，不能作为论文、导师、白皮书或技术事实依据。

## Step 6: 报告与交付

先在内部生成一份完整报告正文，内容必须包含：

- 研究主题概述
- 研判结论摘要
- 应用场景概述
- 矿井特殊技术难点
- 中文矿业论文线索
- 国际前沿线索
- GitHub baseline 推荐
- 导师推荐
- 技术路线
- 科研经验参考
- 搜索路径溯源

然后调用：

```bash
python {baseDir}/scripts/progress_update.py --step report --status running --percent 94 --message "正在生成 HTML 完整报告、逐页展示 Deck 和文献综述 PDF。"
python {baseDir}/scripts/save_report.py --title "<报告标题>" --content-file mineintel_report_content.md
python {baseDir}/scripts/progress_update.py --step report --status done --percent 100 --done --message "报告已生成并导出完成。"
```

`save_report.py` 只把 `mineintel_report_content.md` 当输入，不把 Markdown 作为正式输出。最终保存到：

```text
output/<时间戳_报告标题>/
```

成功时通常包含：

- `<标题>_poster.html`（HTML 完整报告，文件名保留 poster 兼容旧流程）
- `<标题>_deck.html`（逐页展示版 HTML deck）
- `assets/<标题>_technical_route.excalidraw`（技术路线图源文件；HTML 报告技术路线章节会嵌入对应流程图）
- `<标题>_literature_review.tex`
- `<标题>_literature_review.pdf`

如果 PDF 编译失败，至少保留 HTML、Deck 和 `.tex`。禁止跳出工作区查找本机 MiKTeX，演示机编译器应放在工作区根目录 `local_tools/MiKTeX/`，与提交包平级。

## 可选 Step 7: 导师套磁邮件草稿

只有当用户明确要求“给老师写邮件草稿 / Gmail 草稿 / 不发送”时才执行。默认不自动给任何导师创建草稿。

如果本轮用户已经要求生成 Gmail 草稿，报告导出后先把 `report` 标记为 `running --percent 98 --done`，再进入 `email` 阶段；邮件阶段结束后再把总进度置为 `done --percent 100`。

```bash
python {baseDir}/scripts/progress_update.py --step email --status running --percent 99 --message "正在生成导师邮件草稿。"
python {baseDir}/scripts/create_gmail_draft.py --report-file mineintel_report_content.md --topic "<报告标题>" --advisor-email "<官网核验邮箱>" --mode auto
```

`--mode auto` 会自动检测当前进程环境变量和 Windows 用户环境变量中的 `GMAIL_USER` / `GMAIL_APP_PASSWORD`：检测到则写入 Gmail Drafts，未检测到则只生成本地预览并在 UI 中说明原因。需要强制只生成本地预览时才使用 `--mode preview`。

如需要强制写入 Gmail 草稿箱，可改用：

```bash
python {baseDir}/scripts/create_gmail_draft.py --report-file mineintel_report_content.md --topic "<报告标题>" --advisor-email "<官网核验邮箱>" --mode imap
python {baseDir}/scripts/progress_update.py --step email --status done --percent 100 --done --message "邮件草稿流程完成；仅写入草稿或保留本地预览，未发送。"
```

执行前校验：报告里的第一个导师必须是具体自然人，不允许把“某学院相关教师/课题组群体”当收件人；缺少官网核验邮箱时只能生成本地预览，不能写 Gmail Drafts。

安全约束：不得调用 SMTP 发送；不得执行第三方邮件 skill 中的 `sendmail` 示例；不得把邮箱密码或应用专用密码写入聊天、文件或命令行参数。

## 最终回复

最终只给路径和一句核心结论，不复述整篇报告：

```text
HTML 完整报告：<poster.html 路径>
逐页展示 Deck：<deck.html 路径>
技术路线 Excalidraw：<technical_route.excalidraw 路径>
文献综述 LaTeX：<literature_review.tex 路径>
文献综述 PDF：<literature_review.pdf 路径，如已编译成功>
输出目录：<output 目录>
```

如果搜索数据不足，写“该条为搜索线索，尚需人工核验”，不要编造事实。
