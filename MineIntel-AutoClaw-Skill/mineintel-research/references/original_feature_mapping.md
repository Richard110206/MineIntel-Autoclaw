# 原 MineIntel 能力迁移说明

该文件用于在提交材料或答辩中解释：为什么 Skill 版和原项目不同，以及哪些能力被保留。

| 原项目能力 | 原实现方式 | Skill 版实现方式 | 取舍 |
| --- | --- | --- | --- |
| 多智能体调度 | Python Agent/LLM 编排 | `SKILL.md` + `multi_agent_workflow.md` 指导 AutoClaw/GLM 分角色执行 | 不再依赖本地 Agent 框架，更符合 AutoClaw 原生 Skill 模式 |
| 外部模型 API 调用 | 本地配置 API Key 后调用模型 | 交给 AutoClaw 内置 GLM 调度 | 用户导入 Skill 后不需要额外模型 Key |
| RAG/知识库检索 | `data/knowledge` 源文档 + `data/rag_index` 向量索引 + txtai/FastAPI 服务 | `mineintel-application-kg` 构建“场景-痛点-解决方案-技术设备-来源依据”知识图谱，`mineintel-knowledge-rag` 保留补充知识检索 | 不需要安装向量模型和服务，结构化依据更强，但向量语义召回弱于原版 |
| Web 检索 | MCP/后端工具 | `mineintel-literature-baseline` 内置 MCP server，暴露领域分析师和行业前沿技术专家两个检索工具 | 贴近比赛允许的 Skill + MCP 扩展方式，未启用 MCP 时仍可脚本兜底 |
| 论文调研 | Agent 生成检索词并整合 | MCP tool `mineintel_domain_analyst_search` 检索中文应用期刊，`mineintel_frontier_technology_search` 检索国际前沿 | 查询角色更清晰，但最终核验仍依赖公开网页 |
| GitHub baseline | MCP/搜索工具 | `mineintel_frontier_technology_search` 内部补充 1 个最相关 GitHub baseline，失败时 fallback | 不需要登录 GitHub，避免网页端重复展示多个地址 |
| 报告保存 | 后端生成文件 | `mineintel-report-export` 编排 `mineintel-html-poster`、`mineintel-deck-export` 和 `mineintel-literature-review`，生成 HTML 完整报告、逐页展示 Deck、文献综述 LaTeX 和 PDF | 保留比赛演示最需要的报告、演示和论文综述交付 |

## 结论

Skill 版不是把原项目所有后端搬进 AutoClaw，而是把核心业务闭环迁移成 AutoClaw 可直接调度的技能组：`mineintel-research` 负责主控编排，`mineintel-application-kg` 负责矿井应用知识图谱，`mineintel-literature-baseline` 通过 MCP/脚本负责论文和 baseline，`mineintel-experience-insights` 负责科研经验参考，`mineintel-report-export` 负责交付编排，并进一步拆成 `mineintel-html-poster`、`mineintel-deck-export` 与 `mineintel-literature-review` 三个原子输出 Skill。原知识库源文件可以随 Skill 一起提交；原 `rag_index` 属于模型生成缓存，不适合作为唯一提交物。这样牺牲了一部分向量语义召回能力，但换来更低依赖、更容易一键试运行，也更符合比赛对原生 Skill 的要求。
