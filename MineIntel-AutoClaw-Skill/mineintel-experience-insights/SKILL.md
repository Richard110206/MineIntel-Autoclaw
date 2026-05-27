---
name: mineintel-experience-insights
description: >
  MineIntel 科研经验参考检索 Skill。用于检索知乎、小红书等公开平台上的大创选题经验、科研入门经验、
  项目推进经验、组队经验、答辩和结题准备经验。当用户需要“经验参考、避坑建议、科研规划建议、
  小红书/知乎经验”时使用。本 Skill 只输出经验线索和可采纳建议，不作为论文、导师、白皮书或技术事实依据。
compatibility:
  requires:
    - Python 3.x standard library
---

# MineIntel Experience Insights Skill

这是 MineIntel 技能组中的科研经验参考 Skill，边界是“公开平台经验检索与建议提炼”。它不负责论文核验、导师推荐、GitHub baseline 或知识图谱检索。

## 使用时机

当用户需要以下能力时使用：

- 检索知乎/小红书上的大创、科研入门、项目推进和答辩经验。
- 提炼适合报告“科研经验参考”章节的建议。
- 给出选题范围、数据准备、组队分工、答辩材料和结题风险方面的提醒。

## 调用方式

```bash
python {baseDir}/scripts/experience_search.py "<技术方向> <矿井场景>" --scenario "<矿井场景>" --max-results 4
```

示例：

```bash
python {baseDir}/scripts/experience_search.py "计算机视觉 矿井安全监测" --scenario "矿井安全监测" --max-results 4
python {baseDir}/scripts/experience_search.py "机器人 井下巡检" --scenario "井下巡检" --max-results 4
```

## 执行规则

1. 检索关键词必须同时包含技术方向和矿业场景。
2. 优先检索知乎和小红书公开网页；搜索不可用时允许返回本地兜底经验提示，保证演示流程不断裂。
3. 输出只作为经验参考，不能写成确定事实。
4. 报告中必须单独写“科研经验参考（知乎/小红书）”，不要混入论文线索、导师推荐或白皮书依据。
5. 对话区不要输出“搜索失败、超时、重试”等内部过程；只写“当前：正在补充科研经验参考。”或让 UI 显示进度。

## 输出

默认输出：

```text
科研经验参考：
1. 经验来源：
2. 可采纳建议：
3. 风险与核验提示：
```
