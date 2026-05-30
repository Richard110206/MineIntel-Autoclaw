MineIntel AutoClaw Skill 提交包
==============================

Skill 入口：
  SKILL.md                         顶层总入口，负责把 MineIntel-AutoClaw-Skill / 矿小智 路由到主控流程
  mineintel-research/SKILL.md      主控闭环 Skill

Skill 组：
  mineintel-research                主控闭环 Skill
  mineintel-application-kg          矿井应用知识图谱 Skill
  mineintel-knowledge-rag           补充本地知识库与导师匹配 Skill
  mineintel-literature-baseline     论文线索与 GitHub baseline Skill，内置 MCP 检索工具
  mineintel-experience-insights     知乎/小红书科研经验参考 Skill
  mineintel-report-export           报告交付父级 Skill
  mineintel-html-poster             HTML 完整报告 Skill（沿用 poster 文件名）
  mineintel-deck-export             归藏风格横向翻页 HTML deck Skill
  mineintel-literature-review       文献综述 LaTeX/PDF Skill
  mineintel-email-draft             导师套磁邮件草稿 Skill（只写 Gmail Drafts，不发送）
  excalidraw-diagram-generator      项目内 Excalidraw skill，用于生成技术路线图源文件

演示 UI：
  demo-ui/index.html
  mineintel-research/scripts/start_progress_ui.py
  mineintel-research/scripts/progress_update.py

用途：
  面向矿井/矿业场景完成科研选题调研、矿井应用知识图谱检索、论文线索整理、GitHub baseline 推荐、导师方向匹配、知乎/小红书经验参考和报告交付。
  这是原 MineIntel 项目的 AutoClaw 原生 Skill 迁移版，重点保留多专家编排、知识图谱、MCP 检索和可演示交付闭环。

使用方式：
  将整个 MineIntel-AutoClaw-Skill 文件夹作为 Skill 组导入 AutoClaw。
  端到端演示优先调用 MineIntel-AutoClaw-Skill（矿小智）或 mineintel-research；局部能力可单独调用其他子 Skill。
  如果 AutoClaw 支持 MCP 注册，可把 mineintel-literature-baseline/mcp_servers/mcp_config.json 中的 server 加入配置；未启用 MCP 时，SKILL.md 会退回 Python 脚本兜底。

输出：
  每次生成报告都会保存到：
    output/<时间戳_报告标题>/

  默认正式输出：
    <标题>_poster.html  （HTML 完整报告，沿用 poster 文件名）
    <标题>_deck.html     （逐页展示版 HTML deck）
    assets/<标题>_technical_route.excalidraw（技术路线图源文件，已嵌入 HTML 技术路线章节）
    <标题>_literature_review.tex
    <标题>_literature_review.pdf（工作区内 xelatex 可用时）

  Markdown 只作为输入中间内容，不作为最终交付文件；Word/docx 不再生成。

依赖：
  不需要启动原项目后端，不需要本地外部模型 API Key，不需要本地向量模型。
  运行时主要依赖 AutoClaw/GLM、AutoGLM 搜索能力和 Python 3 标准库。
  提交包不内置 MiKTeX/TeX Live。演示机如需 PDF，可把编译器放在工作区根目录 local_tools/MiKTeX/，与 MineIntel-AutoClaw-Skill 平级；脚本只在工作区内查找 xelatex，不跳出工作区调用外部绝对路径。
  若工作区内 xelatex 不可用，仍会保留 HTML 完整报告、逐页展示 Deck 和文献综述 tex。
  Gmail 草稿功能只使用 Python 标准库 IMAP append 写入 Drafts；需要用户在本机环境变量中自行配置 GMAIL_USER 和 GMAIL_APP_PASSWORD，不在聊天或文件中保存凭证。

演示提示词：
  见 demo_prompts.txt。

说明：
  每个 Skill 的 scripts 目录只封装底层能力，任务拆解与编排逻辑写在对应 SKILL.md 中，符合 AutoClaw 原生 Skill 模式。
  详细迁移说明见 mineintel-research/references/original_feature_mapping.md。
