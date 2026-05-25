# GitHub 每日热点监控_2026-05-06

## 今日 Trending Top 10

> 统计口径：过去24小时内新建仓库，按 Stars 数量排序

| # | 仓库 | Stars | 简介 |
|---|------|-------|------|
| 1 | NamKhoa-07/Voidstrap | 482 | Voidstrap is a simple yet advanced fork of Bloxstrap, advanced customization and improvements. |
| 2 | WeritoP/BetterNitroDiscord | 462 | BetterDiscord Plugin for Nitro features. Unlock screensharing modes, use cross-server and gif emotes and much more! |
| 3 | cv-cat/XHS_ALL_IN_ONE | 105 | XHS_ALL_IN_ONE 小红书全域运营 |
| 4 | 432539/plus_gopay_gptp-plus | 105 | plus+gopay开通GPTPLUS会员,已经比较稳定,部分技术支持QQ1114639355 |
| 5 | Predictional-Infra/polymarket-trading-bot | 29 | Polymarket 预测市场交易机器人 |
| 6 | Predictional-Infra/polymarket-copy-trading-bot | 29 | Polymarket 跟单交易机器人 |
| 7 | 2234839/ai-nvr | 19 | AI 网络视频录像机相关项目 |
| 8 | rihebty/flow-kit | 19 | 一套融合了bmad、spec-kit、OpenSpec、GSD、claude-task-master、superpowers、gstack、skills的 AI 编程规范化流程 |
| 9 | hexianWeb/tsl-scifi-earth | 16 | Three.js WebGPU / TSL 粒子地球与 Flyline 可视化，Tweakpane 即时调参 |
| 10 | 0xUnixIO/relay | 12 | Relay 相关项目 |

**今日观察：**
- 今日 Trending 整体热度偏低，排名第一的 Voidstrap 仅 482 stars，反映出周末期间社区活跃度下降
- 华人开发者项目表现亮眼：小红书运营工具（XHS_ALL_IN_ONE）和 AI 编程流程套件（flow-kit）进入前十，说明垂直场景工具仍有市场空间
- Discord 插件类项目（BetterNitroDiscord）热度较高，Nitro 功能解锁类需求持续旺盛
- 预测市场方向（Polymarket）出现两个相关仓库，可能代表近期 DeFi 预测市场热度回升

---

## 重点仓库动态

### 🦅 openclaw/openclaw

| 指标 | 内容 |
|------|------|
| 最新版本 | **v2026.5.5**（2026-05-06 09:00 UTC） |
| 最新 commit | d9ffc1a — fix cron run binding route (#78373) |
| 最近3条 commit | `d9ffc1a` fix cron run binding route<br>`0b88d62` chore: bump version to 2026.5.6<br>`5cf55ed` fix(openai): suppress stale Codex OAuth models |

**简评：** OpenClaw 当前处于高频迭代期（一天内多次版本更新），v2026.5.6 已在 v2026.5.5 发布后数分钟内跟进，版本节奏非常激进。主要修复集中在 cron 路由绑定和 OpenAI Codex OAuth 模型过时问题上，显示出对生产稳定性的快速响应能力。建议关注平台在大规模并发场景下的表现。

---

### 🔮 NousResearch/hermes-agent

| 指标 | 内容 |
|------|------|
| 最新版本 | **v2026.4.30**（2026-04-30 18:31 UTC） |
| 最新 commit | aa88dcc — fix: salvage batch — compaction guidance, memory authority, cache eviction after compression |
| 最近3条 commit | `aa88dcc` fix: salvage batch — compaction guidance, memory authority, cache eviction after compression<br>`f27fcb6` feat(models): add x-ai/grok-4.3 to OpenRouter + Nous Portal curated lists<br>`477e4a2` feat(models): add deepseek/deepseek-v4-pro to OpenRouter + Nous Portal curated lists |

**简评：** NousResearch 的 hermes-agent 近期主要在**模型列表扩展**方面发力，接入 x-ai/grok-4.3 和 deepseek/deepseek-v4-pro，显示出对多模型生态的积极整合策略。值得注意的是，最新 commit 涉及 salvage batch 机制的修复（压缩后缓存驱逐和内存权限），说明产品正在强化大规模批处理场景的稳定性。与 OpenClaw 相比，hermes-agent 的版本迭代节奏相对平稳（间隔一周），但 commit 内容更偏向上层功能扩展而非底层 bug 修复。

---

## 📊 总结

今日 GitHub 社区整体较为平静，没有出现单日数千 stars 的爆款项目。OpenClaw 保持极高迭代频率，平台能力快速演进中；竞品 NousResearch/h ermes-agent 则聚焦多模型整合，生态布局意图明显。建议持续关注下周一社区活跃度回升后的 Trending 变化。
