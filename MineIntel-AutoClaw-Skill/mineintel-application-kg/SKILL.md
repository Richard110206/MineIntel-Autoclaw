---
name: mineintel-application-kg
description: >
  MineIntel 矿井应用知识图谱 Skill。用于矿井应用专家场景分析、矿井场景-痛点-解决方案-技术设备结构化检索、
  白皮书/蓝皮书/政策标准证据溯源和知识图谱查询。当用户需要矿井应用场景、行业白皮书依据、知识图谱、
  场景痛点分析、解决方案拆解或矿井应用专家检索时使用。
---

# MineIntel Application KG Skill

这是 MineIntel 技能组中的“矿井应用专家”Skill。它不做泛泛 RAG，而是基于清洗后的白皮书、蓝皮书、政策标准和团队人工场景表，查询“矿井场景-痛点-解决方案-技术设备-来源依据”的轻量知识图谱。

## 使用时机

- 需要判断某个技术方向在矿井/矿山中的典型应用场景。
- 需要列出场景痛点、解决方案、所需技术设备和行业依据。
- 需要从煤矿智能化蓝皮书、智能矿山/无人驾驶白皮书、5G 智慧矿山白皮书、国家能源局标准指南等资料中做结构化溯源。
- 主控 Skill `mineintel-research` 执行 Step 2 场景分析时优先调用本 Skill。

## 关键数据

- `data/user_sources/矿井场景总览.csv`：团队人工整理的 20 个矿井应用场景，是高置信骨架。
- `data/clean/`：清洗后的白皮书、蓝皮书、政策标准和原 MineIntel 语料。
- `data/kg/kg_graph.json`：完整知识图谱。
- `data/kg/kg_nodes.json`：节点。
- `data/kg/kg_edges.json`：关系。
- `data/kg/kg_triples.csv`：便于人工检查的三元组表。

## 查询图谱

```bash
python {baseDir}/scripts/kg_search.py "井下主运输 皮带异物" --limit 8
python {baseDir}/scripts/kg_search.py "瓦斯监测 预警 传感器" --limit 8
python {baseDir}/scripts/kg_search.py "<技术方向> <矿井场景> 痛点 解决方案" --limit 8
```

输出重点字段：

- `matched_nodes[]`：匹配到的场景、技术、痛点或来源节点。
- `related_edges[]`：一跳关系，包含 `belongs_to`、`has_pain_point`、`needs_solution`、`requires_technology`、`evidenced_by` 等。
- `evidence`：来源编号、CSV 字段、清洗文本块或证据片段。

## 重建图谱

只有当 `data/user_sources/矿井场景总览.csv` 或 `data/clean/` 发生变化时，才重建图谱：

```bash
python {baseDir}/scripts/build_application_kg.py
```

重建后检查：

```bash
python {baseDir}/scripts/kg_search.py "矿井安全监测 计算机视觉" --limit 5
```

## 输出规则

返回内容应整理为：

```text
矿井应用知识图谱结果：
1. 相关场景：
2. 主要痛点：
3. 解决方案：
4. 技术/设备要求：
5. 来源依据：
```

不要把没有证据边的内容写成确定事实。来自 `related_concept` 或 `mentions` 的内容可作为辅助线索；来自人工 CSV 的 `has_pain_point`、`needs_solution`、`requires_technology` 和 `evidenced_by` 优先级更高。
