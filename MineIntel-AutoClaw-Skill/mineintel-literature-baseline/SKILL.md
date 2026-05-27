---
name: mineintel-literature-baseline
description: >
  MineIntel 论文线索与 GitHub baseline 检索 Skill。用于矿井/矿业科研调研中的中文论文线索、国际前沿线索、
  综述线索、公开网页资料和 GitHub baseline 仓库检索。当用户需要论文推荐、开源项目、baseline、
  前沿技术调研、搜索路径溯源时使用。
compatibility:
  requires:
    - Python 3.x standard library
---

# MineIntel Literature And Baseline Skill

这是 MineIntel 技能组中的资料检索 Skill，边界是“公开资料、论文线索和 GitHub baseline 的检索与初筛”。

## 使用时机

当用户需要以下能力时使用本 Skill：

- 检索中文矿业论文线索。
- 检索国际前沿论文、综述或项目主页。
- 查找可迁移到矿井场景的 GitHub baseline。
- 对报告中的论文和仓库来源做路径溯源。

## 实时进度

开始执行本 Skill 时，先打开主控包提供的进度 UI，并同步本阶段状态：

```bash
python {baseDir}/../mineintel-research/scripts/start_progress_ui.py --task "论文线索与 baseline 检索"
python {baseDir}/../mineintel-research/scripts/progress_update.py --step paper --status running --percent 35 --message "正在检索论文线索。"
```

完成论文检索后同步：

```bash
python {baseDir}/../mineintel-research/scripts/progress_update.py --step paper --status running --percent 60 --done --message "论文线索检索完成，开始 baseline 检索。"
python {baseDir}/../mineintel-research/scripts/progress_update.py --step baseline --status done --percent 100 --done --message "论文线索与 baseline 检索完成。"
```

对话中只简短输出当前正在做什么和已经完成什么。不要输出编码问题、命令修复、GitHub 搜索重试、搜索超时、工具切换等过程性文字；这些细节内部处理或同步到网页进度。禁止在聊天区出现“超时”“web_search”“GitHub 搜索报错”“并行启动”“数据充足”“线索已足够”“让我换一种方式”等内部调度话术。

## MCP 工具优先

本 Skill 优先通过内置 MCP server 暴露两个检索工具，把“领域分析师”和“行业前沿技术专家”从普通脚本调用升级为可被 AutoClaw/GLM 路由的工具能力。

MCP server 文件：

```bash
python {baseDir}/mcp_servers/mineintel_literature_mcp.py
```

配置参考：

```text
{baseDir}/mcp_servers/mcp_config.json
```

可用 MCP tools：

- `mineintel_domain_analyst_search`：领域分析师检索，面向煤炭学报、采矿与安全工程学报、工矿自动化、煤炭科学技术、矿业安全与环保等中文矿业应用类来源。
- `mineintel_frontier_technology_search`：行业前沿技术专家检索，面向 arXiv、DBLP、近年前沿论文/综述，并补充一个最相关 GitHub baseline 地址。

如果 AutoClaw 当前环境没有启用 MCP 注册，再退回下面的 Python 脚本调用。不要在聊天区解释 MCP 注册失败、搜索超时或工具切换过程。

## 脚本兜底

### 论文检索扩展

```bash
python {baseDir}/scripts/paper_search.py "计算机视觉 矿井安全监测" --scope all --max-results 8
python {baseDir}/scripts/paper_search.py "煤矿皮带异物检测" --scope chinese --max-results 8
```

### 公开网页检索

```bash
python {baseDir}/scripts/web_search.py "计算机视觉 矿井 安全监测 应用" --max-results 5
python {baseDir}/scripts/open_link.py "https://example.com/page"
```

### GitHub baseline

```bash
python {baseDir}/scripts/github_search.py "YOLO coal mine detection" --limit 5
python {baseDir}/scripts/github_search.py "robot underground mining perception" --limit 5
```

## 执行规则

1. 先把用户的中文研究方向转为中英文关键词。
2. 中文应用论文优先调用 MCP tool `mineintel_domain_analyst_search`。如果 MCP 不可用，再用脚本检索：
   - `<技术方向> 煤矿 矿井 论文 2024 2025 2026`
   - `<技术方向> 煤炭学报 工矿自动化 煤炭科学技术`
   - `<技术方向> 采矿与安全工程学报 煤矿 智能化`
3. 国际前沿优先调用 MCP tool `mineintel_frontier_technology_search`。如果 MCP 不可用，再用脚本检索：
   - `<English technique> underground mining safety monitoring paper`
   - `<English technique> intelligent mining review survey`
4. GitHub baseline 由 `mineintel_frontier_technology_search` 只返回一个最相关地址；不要在网页端重复展示同一仓库、作者主页或拆开的地址片段。
5. GitHub baseline 重点看相关性、star、更新时间、训练脚本和自定义数据集支持。
6. 搜索结果只是线索，不能把未核验的搜索结果写成确定论文事实。
7. 输出论文线索时保留本次检索到的全部有效条目；每条必须包含标题、来源/平台、年份和链接，缺链接时保留空的“链接：”字段。
8. 科研经验参考由 `mineintel-experience-insights` 处理，不在本 Skill 内混入知乎/小红书经验。

## 输出

默认输出：

```text
论文与 baseline 检索结果：
1. 中文论文线索：
2. 国际前沿线索：
3. GitHub baseline：
4. 搜索关键词与来源：
5. 需人工核验事项：
```
