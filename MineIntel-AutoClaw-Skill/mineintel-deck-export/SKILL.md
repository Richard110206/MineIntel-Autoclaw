---
name: mineintel-deck-export
description: >
  MineIntel 逐页展示版导出 Skill。用于把已经生成的矿业科研调研报告转换为归藏风格横向翻页 HTML deck，
  便于答辩、路演和课堂展示。输出内容与 HTML 完整报告同源，但按演示叙事重排为一页一页的 slides。
---

# MineIntel Deck Export Skill

本 Skill 只负责把已经生成的调研内容转换为逐页展示版 HTML，不负责重新检索论文、导师或 GitHub。

## 使用方式

```bash
python {baseDir}/scripts/render_deck.py --title "<报告标题>" --content-file report_content.md --output-dir "<本次 output 文件夹>"
```

脚本输出：

- `files.deck`：`<标题>_deck.html`

## 设计规则

- 使用 `guizang-ppt-skill-main` 的风格 A：电子杂志 × 电子墨水模板。
- 默认主题为“靛蓝瓷”，适合矿业科研、技术报告和答辩场景。
- 内容必须与正式 HTML 报告同源，不另写一套低密度摘要。
- 每页只承载一个展示意图：结论、场景、难点、论文、baseline、导师、路线、建议、核验。
- 生成单文件 HTML deck，同时复制 Motion One 本地兜底脚本到输出目录的 `assets/motion.min.js`。

## 父级调用

`mineintel-report-export` 是父级交付 Skill。完整报告导出时由父级调用本 Skill，并把 deck 加入结果区 artifacts。
