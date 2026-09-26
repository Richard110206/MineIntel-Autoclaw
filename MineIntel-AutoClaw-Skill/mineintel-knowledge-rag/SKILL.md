---
name: mineintel-knowledge-rag
description: >
  MineIntel 知识库与导师匹配 Skill。用于矿井/矿业科研调研中的 FAISS 语义 RAG 检索、矿业场景知识补全、
  学校/学院官网导师检索、技术难点和评估指标检索。当用户需要本地知识库、导师推荐、矿业场景分析、
  RAG 检索、专业方向匹配时使用。
compatibility:
  requires:
    - Python 3.x standard library
---

# MineIntel Knowledge RAG Skill

这是 MineIntel 技能组中的知识库与导师检索 Skill。边界是“通过语义向量检索补全矿业场景知识、检索技术难点与评估指标，并从中国矿业大学徐州官网匹配导师方向”。检索失败必须显式报告，禁止退回词匹配或静态导师候选。

## 使用时机

当用户需要以下能力时使用本 Skill：

- 根据专业和技术方向匹配导师，并优先检索学校/学院官网师资页面。
- 检索矿井/矿业领域的应用场景、特殊难点和评估指标。
- 用 FAISS 向量库检索本地知识文档，作为可复现的语义 RAG 依据。
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
- `data/sample_knowledge.json`：参与向量化的结构化场景知识。
- `data/vector_index/`：由 `build_faiss_index.py` 生成的 FAISS 索引、元数据和版本清单。
- `../config/infrastructure.json`：嵌入模型、分块和索引配置；可用环境变量覆盖模型与设备。

## 脚本

### 官网导师检索

导师推荐优先调用主控 Skill 的官网检索脚本：

```bash
python {baseDir}/../mineintel-research/scripts/advisor_search.py "<技术方向> <矿业场景>" --school "中国矿业大学" --max-results 8 --open-pages 3
python {baseDir}/../mineintel-research/scripts/advisor_search.py "<技术方向> <矿业场景>" --school "中国矿业大学" --college "安全工程学院" --max-results 8 --open-pages 3
python {baseDir}/../mineintel-research/scripts/advisor_search.py "<技术方向> <矿业场景>" --school "中国矿业大学" --college "矿业工程学院" --max-results 8 --open-pages 3
```

结果中优先使用 `results[].url` 为矿大徐州官网或学院官网域名的条目。写入网页结果区时只保留姓名、学院和链接；没有学院的候选不要展示。

### FAISS 语义知识库

首次运行或知识源变化前，在仓库根目录安装依赖（推荐 uv，详见 README.txt）：

```bash
uv sync
python {baseDir}/scripts/build_faiss_index.py
```

网络要求：首次构建需从 HuggingFace 下载嵌入模型。国内网络设置 `HF_ENDPOINT=https://hf-mirror.com`；模型已缓存后可设置 `HF_HUB_OFFLINE=1` 实现离线加载。构建和检索必须使用同一嵌入模型（`config/infrastructure.json` 或 `MINEINTEL_EMBEDDING_MODEL`）。

语义检索：

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
- `results[].score`（归一化向量的余弦相似度）
- `results[].chunk_id`

## 执行规则

1. 先从用户输入中提取专业背景、技术领域和矿业场景。
2. 如果专业或技术领域缺失，最多问一次；不要反复追问。
3. 场景知识和技术难点调用 `local_search.py` 检索 2-3 组关键词：
   - `<技术领域> 矿井 应用 难点`
   - `<技术领域> 评估指标 baseline 矿井`
   - `<专业> <技术领域> 申报建议`
4. 导师推荐必须调用 `advisor_search.py` 检索学校/学院官网；官网数据不足时明确返回不足，不允许静态候选补位。
5. 不要在聊天区输出“超时、web_search、open_link、编码问题、重试、英文搜索效果不佳、数据杂乱、让我换一种方式”等过程性文字。
6. 不编造官网之外的导师姓名、职称或研究方向。
7. 导师输出应尽量给出 3-6 名候选；网页结果区只显示姓名、学院和链接。
8. FAISS 索引缺失、过期或依赖不可用时停止该阶段并输出初始化命令，禁止降级为关键词包含判断。

## 输出

默认输出一段结构化结果：

```text
知识库与导师检索结果：
1. 场景和难点：
2. 官网导师候选：
3. 本地场景知识线索：
4. 需核验事项：
```
