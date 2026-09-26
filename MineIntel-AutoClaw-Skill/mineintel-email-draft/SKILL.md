---
name: mineintel-email-draft
description: 为 MineIntel 导师推荐结果生成个性化套磁邮件草稿，并通过浏览器打开 Gmail 撰写页预填收件人、主题和正文。仅创建可审阅草稿，不自动发送邮件。
---

# MineIntel Browser Email Draft

根据报告中的第一位具体导师和研究主题撰写简洁、具体的联系邮件。先生成本地预览，再通过浏览器打开 Gmail 撰写页；不得自动点击发送。

## 工作流

1. 确认收件人是具体自然人导师，邮箱来自学校或学院官网。
2. 根据研究主题、学生背景和导师方向生成邮件正文。避免套话堆砌，不虚构论文、项目经历或附件。
3. 调用脚本生成 `.txt`、`.json` 预览，并打开 Gmail 网页撰写窗口：

```bash
python {baseDir}/scripts/create_gmail_draft.py \
  --report-file "<完整报告 Markdown>" \
  --topic "<研究主题>" \
  --advisor-name "<导师姓名>" \
  --advisor-email "<官网核验邮箱>" \
  --student-name "<学生姓名或学生>" \
  --mode browser
```

如已单独写好正文，使用 `--body-file <正文文件>`。只生成预览、不打开浏览器时使用 `--mode preview`。

## 约束

- 不保存 Gmail 密码、Cookie 或令牌。
- 不调用 SMTP、IMAP 或邮件发送接口。
- 不自动点击发送；浏览器打开后由用户复核。
- 缺少官网核验邮箱时仅生成预览，不打开收件人不明的撰写页。
- 输出预览文件不得包含密码、Cookie 或其他身份凭证。
