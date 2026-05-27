# MineIntel 矿井应用知识图谱构建报告

本轮图谱以团队人工整理的 `矿井场景总览.csv` 为主骨架，融合清洗后的白皮书、蓝皮书、政策标准和原 MineIntel 知识库候选实体。

## 汇总

- 节点数：489
- 关系数：928
- 人工场景数：20
- 清洗文本块数：436

## 节点类型

| 类型 | 数量 |
| --- | ---: |
| application_concept | 23 |
| application_scenario | 20 |
| metric | 13 |
| pain_concept | 20 |
| pain_point | 98 |
| scenario_category | 11 |
| solution | 98 |
| solution_concept | 17 |
| source_document | 45 |
| technology | 27 |
| technology_equipment | 117 |

## 关系类型

| 关系 | 数量 |
| --- | ---: |
| belongs_to | 20 |
| evidenced_by | 57 |
| has_pain_point | 98 |
| mentions | 452 |
| needs_solution | 98 |
| related_concept | 79 |
| requires_technology | 118 |
| same_or_related_source | 6 |

## 主要文件

- `kg_nodes.json`：知识图谱节点。
- `kg_edges.json`：知识图谱关系，含 source_id/chunk_id 证据。
- `kg_graph.json`：节点、关系和元数据全集。
- `kg_triples.csv`：便于人工查看的三元组表。

## 说明

- `application_scenario` 主要来自人工 CSV，是高置信场景骨架。
- `pain_point`、`solution`、`technology_equipment` 主要来自人工 CSV 的结构化字段。
- `technology`、`application_concept`、`metric` 等候选概念来自清洗语料统计，用于补充图谱覆盖面。
- `mentions` 关系保留清洗语料中的 source_id、chunk_id 和证据片段，便于后续报告溯源。
