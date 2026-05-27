---
name: mineintel-literature-review
description: >
  MineIntel 文献综述 LaTeX/PDF Skill。用于从矿业科研调研报告中抽取论文线索、研究背景、
  技术痛点和研究路线，重组为独立文献综述 LaTeX 源码，并在工作区内 xelatex 可用时编译 PDF。
  当用户要求文献综述、LaTeX、tex、PDF、论文背景分析或综述质量提升时使用。
---

# MineIntel Literature Review Skill

本 Skill 只负责文献综述交付，不负责重新搜索。输入应是已经由 MineIntel 主控流程整理好的报告正文。

## 使用方式

```bash
python {baseDir}/scripts/build_literature_review.py --title "<报告标题>" --content-file report_content.md --output-dir "<本次 output 文件夹>"
```

脚本输出：

- `files.tex`：文献综述 LaTeX 源码，始终保留。
- `files.pdf`：工作区内 `xelatex` 编译成功时生成。

如果工作区内没有 `xelatex` 或 MiKTeX 未完成初始化，不能中断任务，只保留 `.tex` 并在结果 JSON 的 `latex_compile` 中记录状态。

## 文献综述结构

生成内容必须包含：

1. 研究背景
2. 研究问题与技术痛点
3. 已有论文方法综述
4. 我们的研究路线与论文契合关系
5. 论文解决了什么，以及仍未解决什么
6. 面向大创的选题建议
7. 参考文献与链接

## 写作边界

- 只能根据已检索到的题名、摘要/网页片段、公开链接和已解析资料做归纳。
- 未获取全文的论文不能编造实验数据、指标或结论。
- 综述要把论文内容延伸到“背景、问题、方法类别、对我们路线的支撑”，但必须标注正式引用前需要二次核验。
- 不生成 Word、Markdown 或完整报告 PDF；这里只生成文献综述的 `.tex` 和可选 `.pdf`。
