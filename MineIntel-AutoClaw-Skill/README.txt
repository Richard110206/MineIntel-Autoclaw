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
  mineintel-email-draft             导师套磁邮件草稿 Skill（浏览器预填 Gmail，不自动发送）
  excalidraw-diagram-generator      项目内 Excalidraw skill，用于生成技术路线图源文件

演示 UI：
  demo-ui/index.html
  mineintel-research/scripts/start_progress_ui.py
  mineintel-research/scripts/progress_update.py

仓库结构（脚本分层）：
  pyproject.toml / uv.lock           UV 依赖管理（uv sync 一键创建虚拟环境）
  config/infrastructure.json         全局基础设施配置：嵌入模型、FAISS、Neo4j、AutoGLM 地址
  mineintel_common/                  共享基础设施层（各 Skill 通过 import 复用，只有这一份实现）
    config.py                          配置加载与相对路径显示
    web_search.py                      AutoGLM 网页搜索客户端（显式失败，无兜底数据）
    open_link.py                       AutoGLM 网页阅读客户端（凭据全部来自环境变量）
  mineintel-research/scripts/        主控编排与进度 UI；paper/github 检索已收编到
                                     literature-baseline，这里只留委托包装
  mineintel-literature-baseline/     论文/GitHub 检索规范实现（scripts/）+ MCP 服务（mcp_servers/）
  mineintel-experience-insights/     知乎/小红书经验检索（唯一实现）
  mineintel-knowledge-rag/           FAISS 语义 RAG（faiss_store 索引库 + local_search 检索）
  mineintel-application-kg/          Neo4j 知识图谱（clean/build/import/neo4j_store/kg_search）
  mineintel-report-export 等导出类    HTML 报告、Deck、LaTeX 综述的渲染与导出
  同一能力全仓库只有一份规范实现；跨 Skill 调用一律通过 mineintel_common 或委托包装完成。

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
  依赖管理使用 UV（推荐）：在仓库根目录执行 `uv sync`，自动创建 .venv 并按 uv.lock 安装
  faiss-cpu、neo4j、numpy、sentence-transformers；之后用 `uv run python <脚本>` 运行。
  没有 uv 时可用 `python -m pip install -r requirements-advanced.txt`（与 pyproject.toml 保持一致）。
  运行时依赖 AutoClaw/GLM 编排、AutoGLM 搜索能力和 Python 3.10+；不需要启动原项目后端。
  所有路径均为相对路径，仓库放在任意目录都能运行；嵌入模型与索引配置见 config/infrastructure.json。

  FAISS 语义知识库（mineintel-knowledge-rag）：
    python -m pip install -r requirements-advanced.txt
    python mineintel-knowledge-rag/scripts/build_faiss_index.py
    python mineintel-knowledge-rag/scripts/local_search.py "查询词" --limit 5
    首次构建需联网下载嵌入模型（BAAI/bge-m3）；国内网络建议设置 HF_ENDPOINT=https://hf-mirror.com，
    模型已缓存后可设置 HF_HUB_OFFLINE=1 离线运行。构建与检索必须使用同一嵌入模型。

  Neo4j 知识图谱（mineintel-application-kg）：
    设置环境变量 MINEINTEL_NEO4J_PASSWORD 后执行 docker compose -f docker-compose.neo4j.yml up -d
    环境变量 MINEINTEL_NEO4J_URI / MINEINTEL_NEO4J_USER / MINEINTEL_NEO4J_PASSWORD / MINEINTEL_NEO4J_DATABASE
    的说明见 .env.example。然后：
    python mineintel-application-kg/scripts/import_neo4j.py
    python mineintel-application-kg/scripts/kg_search.py "查询词" --limit 8
    Neo4j 未启动或未配置时，图谱阶段会显式报错，不会降级读取本地 JSON。

  AutoGLM 网页搜索凭据：设置 AUTOGLM_APP_ID / AUTOGLM_APP_KEY 环境变量（参见 .env.example）。

  提交包不内置 MiKTeX/TeX Live。演示机如需 PDF，可把编译器放在工作区根目录 local_tools/MiKTeX/，与 MineIntel-AutoClaw-Skill 平级；脚本只在工作区内查找 xelatex，不跳出工作区调用外部绝对路径。
  若工作区内 xelatex 不可用，仍会保留 HTML 完整报告、逐页展示 Deck 和文献综述 tex。
  Gmail 草稿功能只使用 Python 标准库生成本地预览并打开浏览器撰写页；不需要保存邮箱密码，不调用 SMTP/IMAP，也不会自动发送。

演示提示词：
  见 demo_prompts.txt。

说明：
  每个 Skill 的 scripts 目录只封装底层能力，任务拆解与编排逻辑写在对应 SKILL.md 中，符合 AutoClaw 原生 Skill 模式。
  详细迁移说明见 mineintel-research/references/original_feature_mapping.md。
