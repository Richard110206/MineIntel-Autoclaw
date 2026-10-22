# 原生记忆接口核验

核验日期：2026-09-26。此文件记录接口事实与待接入项，不代表集成已经完成。

## 本机证据

检测到 OpenClaw 2026.3.2，安装包为当前 Windows 用户的全局 npm 包。未检测到可核验的 AutoClaw 桌面实例、Hermes CLI 或 Hermes 原生记忆工具。工作区 AGENTS.md 中的 Hermes-Evolution 是演化指令，不能证明原生用户记忆可调用。

`openclaw memory status --json` 返回：agentId=main，backend=builtin，provider=none，searchMode=fts-only，files=0，chunks=0；记忆源目录缺失。当前没有可供学生项目召回的记录，也没有可用的语义嵌入配置。此状态仅描述本机 OpenClaw，不代表其他电脑上的 AutoClaw。

## OpenClaw 2026.3.2 已核验接口

从安装包 memory-core 插件及工具实现核验：

| 工具 | 参数 | 用途 |
|---|---|---|
| memory_search | query 必填；maxResults、minScore 可选 | 返回来源路径、行范围及片段 |
| memory_get | path 必填；from、lines 可选 | 读取检索命中的原始记忆片段 |

工具由宿主注册，Skill 本身不是 HTTP 服务，不应凭空创建 /memory/search 等端点。无可用工具时明确报告未接入，不用本地 JSON 冒充原生记忆。

记忆来源是工作区 MEMORY.md 和 memory/**/*.md；memory_get 不支持任意路径。memory-core 只注册上述两个召回工具，记录通过宿主文件写入/编辑工具维护 Markdown。写入成功与向量索引成功需要分别核验。

索引按 agent 区分，不能自动视为按学生隔离。多人应用需要明确学生身份和独立 agent/workspace 或平台提供的可靠隔离机制。不能用统一 main 档案承载所有学生。

CLI 可核验命令：

```text
openclaw memory status --json
openclaw memory search --query "用户明确提供的项目关键词" --agent <实际agentId> --json
```

## 与 Hermes Agent 的区别

NousResearch Hermes Agent 官方接口为 memory(action=add/replace/remove, target=memory/user, ...)，长期摘要在会话开始时注入；session_search 用于历史对话召回。它不是本机 OpenClaw 的 memory_search/memory_get 接口。AutoClaw 内置 Hermes 版本是否暴露这些接口尚未核验，不能照搬。

参考：
- https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
- https://docs.openclaw.ai/concepts/memory
- 本机 OpenClaw 安装包 extensions/memory-core/index.ts、dist 中 src/agents/tools/memory-tool.ts 的打包实现，以及 docs/concepts/memory.md。

## 接入后的调研契约

1. 确定实际平台版本、学生身份、可用工具及隔离范围。
2. 调研开始先召回当前学生项目及本人贡献，读取来源；缺失时补问，检索失败不得宣称没有经历。
3. 模型形成有来源的能力判断，区分用户陈述、成果核验与推断。
4. 同一矿井大选题分别给出基础交付、可选拓展、当前不建议承担部分；分别说明方法复杂度、数据、周期、资源和验收要求的适配依据。
5. 仅将真实新增经历及用户纠正写回宿主原生记忆，不把推荐写成已完成。无需自动实验迭代。
6. 在隔离测试身份下核验保存、新会话召回、更新、删除，以及两个学生的记忆互不串用。

接入前必须先确认实际 AutoClaw/Hermes 安装位置与版本，再配置嵌入及原生工具。现有 project_memory.py 是独立本地方案；原生接入后不能未经声明同时写两套主记忆。
