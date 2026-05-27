---
name: mineintel-knowledge-rag
description: >
  MineIntel 知识库与导师匹配 Skill。用于矿井/矿业科研调研中的本地 RAG 检索、矿业场景知识补全、
  学校/学院官网导师检索、技术难点和评估指标检索。当用户需要本地知识库、导师推荐、矿业场景分析、
  RAG 检索、专业方向匹配时使用。
compatibility:
  requires:
    - Python 3.x standard library
---

# MineIntel Knowledge RAG Skill

这是 MineIntel 技能组中的知识库与导师检索 Skill。边界是“补全矿业场景知识、检索技术难点与评估指标，并优先从中国矿业大学徐州官网匹配导师方向”。官网结果不足时，允许由校内导师候选库少量补位。

## 使用时机

当用户需要以下能力时使用本 Skill：

- 根据专业和技术方向匹配导师，并优先检索学校/学院官网师资页面。
- 检索矿井/矿业领域的应用场景、特殊难点和评估指标。
- 用本地知识库补全报告背景，作为轻量 RAG 依据。
- 对主控 Skill `mineintel-research` 的报告内容做本地交叉验证。

## 实时进度

开始执行本 Skill 时，先打开主控包提供的进度 UI，并同步本阶段状态：

```bash
python {baseDir}/../mineintel-research/scripts/start_progress_ui.py --task "本地知识库与导师匹配"
python {baseDir}/../mineintel-research/scripts/progress_update.py --step knowledge --status running --percent 25 --message "正在检索本地知识库和官网导师方向。"
```

完成后调用：

```bash
python {baseDir}/../mineintel-research/scripts/progress_update.py --step knowledge --status done --percent 100 --done --message "本地知识库与导师匹配完成。"
```

对话中只简短输出当前正在做什么和已经完成什么。不要输出编码问题、命令修复、重试搜索、搜索超时、工具切换等过程性文字；这些细节内部处理或同步到网页进度。禁止在聊天区出现“超时”“web_search”“open_link”“并行启动”“数据充足”“线索已足够”“让我换一种方式”等内部调度话术。

## 关键资源

- `data/knowledge/mining_cs_domain.md`：原 MineIntel 矿业计算机应用知识库。
- `data/knowledge/mining_research_guide.md`：竞赛版补充知识库。
- `data/sample_knowledge.json`：稳定演示用结构化场景样例。
- `data/advisor_fallback.md`：导师参考库，只由 `advisor_search.py` 在官网结果不足时补位。

## 脚本

### 官网导师检索

导师推荐优先调用主控 Skill 的官网检索脚本：

```bash
python {baseDir}/../mineintel-research/scripts/advisor_search.py "<技术方向> <矿业场景>" --school "中国矿业大学" --max-results 8 --open-pages 3
python {baseDir}/../mineintel-research/scripts/advisor_search.py "<技术方向> <矿业场景>" --school "中国矿业大学" --college "安全工程学院" --max-results 8 --open-pages 3
python {baseDir}/../mineintel-research/scripts/advisor_search.py "<技术方向> <矿业场景>" --school "中国矿业大学" --college "矿业工程学院" --max-results 8 --open-pages 3
```

结果中优先使用 `results[].url` 为矿大徐州官网或学院官网域名的条目。写入网页结果区时只保留姓名、学院和链接；没有学院的候选不要展示。

### 本地知识库检索

```bash
python {baseDir}/scripts/local_search.py "计算机视觉 矿井 安全监测" --limit 5
python {baseDir}/scripts/local_search.py "软件工程 机器人 矿井 巡检" --limit 5
python {baseDir}/scripts/local_search.py "联邦学习 边缘计算 矿井 数据异构" --limit 3
```

输出为 JSON，重点字段：

- `results[].source_file`
- `results[].record.title`
- `results[].record.description`
- `results[].preview`
- `results[].matched_terms`

## 执行规则

1. 先从用户输入中提取专业背景、技术领域和矿业场景。
2. 如果专业或技术领域缺失，最多问一次；不要反复追问。
3. 场景知识和技术难点调用 `local_search.py` 检索 2-3 组关键词：
   - `<技术领域> 矿井 应用 难点`
   - `<技术领域> 评估指标 baseline 矿井`
   - `<专业> <技术领域> 申报建议`
4. 导师推荐必须调用 `advisor_search.py`，先检索学校/学院官网，再由脚本决定是否使用校内导师候选库补位。
5. 不要在聊天区输出“超时、web_search、open_link、编码问题、重试、英文搜索效果不佳、数据杂乱、让我换一种方式”等过程性文字。
6. 不编造官网和校内导师候选库之外的导师姓名、职称或研究方向。
7. 导师输出应尽量给出 3-6 名候选；网页结果区只显示姓名、学院和链接。

## 输出

默认输出一段结构化结果：

```text
知识库与导师检索结果：
1. 场景和难点：
2. 官网导师候选：
3. 本地场景知识线索：
4. 需核验事项：
```
