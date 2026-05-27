这个目录只保留提交包内部的小工具和说明文件，不放 MiKTeX/TeX Live。

比赛提交包不应内置 1GB 级别的 LaTeX 编译器。演示机如果需要由 AutoClaw 在工作区内编译文献综述 PDF，请把编译器放在工作区根目录：

  local_tools/MiKTeX/

该目录应与提交 Skill 文件夹平级，例如：

  kuangxiaozhi/
    MineIntel-AutoClaw-Skill/
    local_tools/MiKTeX/

脚本会优先查找 ../local_tools/MiKTeX/miktex/bin/x64/xelatex.exe。提交给比赛时只提交 MineIntel-AutoClaw-Skill，不提交 local_tools。

如果没有工作区内 xelatex，系统仍会稳定生成 HTML 完整报告，并保留文献综述 .tex 作为手动编译兜底；PDF 成功时只清理 aux/log/toc 等临时文件，保留 tex 源码。
