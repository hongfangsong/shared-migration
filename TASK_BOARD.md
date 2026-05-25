# TASK_BOARD.md
## 说明
1. 所有任务状态唯一记录处，Manager/Researcher/Writer/Publisher按阶段更新，**仅补全/修改自身负责字段，不改动他人填写内容**；
2. 任务状态仅可选：初始化/研究中/研究完成/写作中/写作完成/发布中/发布完成/失败，**执行者开始执行时先标记为「XX中」，完成后再改为「XX完成」**；
3. Publisher完成后，在「飞书发布信息」处补充完整链接+渠道；失败时由**当前阶段执行者**将任务从「进行中任务」移入对应「失败任务」区，并填写失败原因；
4. 状态更新时间统一格式：YYYY-MM-DD HH:MM:SS，每次修改状态必须同步更新。

## 进行中任务
### 任务条目（{TASK_ID}）【新建任务时替换{TASK_ID}，删除此注释】
- 任务ID：{TASK_ID}
- 任务描述：【如：撰写AI行业周报并发布至飞书部门群】
- 当前阶段：初始化
- 阶段执行者：无
- 状态更新时间：【YYYY-MM-DD HH:MM:SS】
- 失败原因：无
- 关联共享文件：
  - 研究报告：./shared/{TASK_ID}_research_report.md
  - 写作草稿：./shared/{TASK_ID}_article_draft.md
- 飞书发布信息：【Publisher完成后填写，格式：飞书文档链接：https://xxx | 发布渠道：xxx】

## 已完成任务
### 任务条目（20250402_160000）【示例，可保留作参考】
- 任务ID：20250402_160000
- 任务描述：撰写春季运营方案并发布至飞书运营群
- 当前阶段：发布完成
- 阶段执行者：publisher
- 状态更新时间：2025-04-02 18:30:00
- 失败原因：无
- 关联共享文件：
  - 研究报告：./shared/20250402_160000_research_report.md
  - 写作草稿：./shared/20250402_160000_article_draft.md
- 飞书发布信息：飞书文档链接：https://www.feishu.cn/docx/XXX | 发布渠道：飞书运营部全员群

## 失败任务
### 任务条目（{TASK_ID}）【由当前阶段执行者移入，删除此注释】
- 任务ID：{TASK_ID}
- 任务描述：【对应任务描述，与进行中任务一致】
- 当前阶段：失败
- 阶段执行者：【如：researcher/writer/publisher，填写任务失败时的执行者】
- 状态更新时间：【YYYY-MM-DD HH:MM:SS，填写移入失败区的时间】
- 失败原因：【具体填写，如：研究报告文件缺失/飞书接口调用失败/草稿文件读取失败】
- 关联共享文件：
  - 研究报告：./shared/{TASK_ID}_research_report.md
  - 写作草稿：./shared/{TASK_ID}_article_draft.md
- 飞书发布信息：无
### 任务条目（20260417_github_daily）
- 任务ID：20260417_github_daily
- 任务描述：GitHub 每日热点监控报告（2026-04-17）并发布至飞书
- 当前阶段：发布完成
- 阶段执行者：publisher
- 状态更新时间：2026-04-17 23:14:00
- 失败原因：无
- 关联共享文件：
  - 研究报告：无
  - 写作草稿：./shared/github_daily_2026-04-17_article_draft.md
- 飞书发布信息：飞书文档链接：https://wcnnzsg4e3ax.feishu.cn/docx/XzTddbPHSoEhHxxoGaGcx6Iqnur | 发布渠道：飞书文件夹 PvyrfDRLXlkQ2WdC10EcECfGnGg
