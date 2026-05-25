# 共享规范与最佳实践

> 所有 subagent 每次启动时必须读取此文件。发现新规范时立即写入，其他 agent 下次启动自动同步。

---

## 文档命名规范（2026-04-23 确立）

| 报告类型 | 格式 |
|---------|------|
| 系统优化 | `【系统优化】<主题>_YYYY-MM-DD.md` |
| 每日巡检 | `【每日巡检】每日巡检_YYYY-MM-DD.md` |
| 每日复盘 | `【每日复盘】<角色>每日复盘_YYYY-MM-DD.md` |
| 媒体热点 | `【媒体热点】<关键词>_YYYY-MM-DD.md` |
| 市场调研 | `【市场调研】<关键词>_YYYY-MM-DD.md` |

**通则**：
- 分隔符用 `】`，不是 `】报告`
- 日期格式：`YYYY-MM-DD`（如 2026-04-23）
- 标题内不含日期下划线（下划线是标题和日期的分隔符）
- 禁止使用中文括号（）、【】内不嵌套

**归档目录**：
- 系统优化报告 → `/mnt/data/km/knowledge/raw/Tech/系统优化报告/`
- 媒体热点报告 → `/mnt/data/km/knowledge/raw/Tech/媒体热点报告/`
- 市场调研报告 → `/mnt/data/km/knowledge/raw/Tech/市场调研报告/`

---

---

## 共享机制说明

- **读取**：每次 session 启动时读取此文件
- **写入**：发现新规范时立即追加，不要覆盖已有内容
- **格式**：追加时注明日期、来源 agent、内容描述
- **文件路径**：`/mnt/data/sub_agents/shared/norms.md`

---

## Agent ↔ 飞书 Bot ↔ 职责对应关系（2026-04-23 确立）

| OpenClaw Agent ID | 飞书 Bot | 实际 workspace | 主要职责 |
|---|---|---|---|
| main | OpenClaw | /mnt/data/openclaw/workspace/ | 系统管理、Cron 诊断、广播 |
| manager | Media-Bot | /mnt/data/sub_agents/manager/ | 媒体热点报告、GitHub 监控 |
| service | service-bot | /mnt/data/sub_agents/service/ | 客服 Q&A、Bitable 工单 |
| wiki-agent | Wiki-Bot | /mnt/data/sub_agents/librarian/ | vault scan、wiki ingest、去重 |
| publisher | doc-bot | /mnt/data/sub_agents/publisher/ | 飞书文档发布 |
| writer | — | /mnt/data/sub_agents/writer/ | 内容写作（subagent，非 Bot） |
| researcher | — | /mnt/data/sub_agents/researcher/ | 搜索研究（subagent，非 Bot） |

**重要说明**：
- `wiki-agent`（cron 配置中的 agentId）= `librarian`（workspace 目录名）= **Wiki-Bot**，两者是同一个 agent
- subagent 没有独立飞书 Bot，靠父 agent（main）统一对外通信
- 当需要协调跨 agent 任务时，通过 `/mnt/data/sub_agents/shared/norms.md` 同步信息


---

## Bot 群内协作规范（2026-04-23 确立）

**目标**：让群里 5 个 Bot（OpenClaw、Media-Bot、Wiki-Bot、service-bot、doc-bot）可以相互对话和协作。

### 协作原则

1. **主动请求协助**：如果任务需要另一个 Bot 的能力，在群里 @该 Bot 请求协助，不要静默等待
2. **响应 @mention**：每个 Bot 收到 @ 后必须响应（即使是"收到，我正在处理"）
3. **跨 Bot 协调**：当一个 Bot 需要另一个 Bot 的能力时，@对方说明需求和预期结果

### 权限确认

所有 5 个 Bot（OpenClaw、Media-Bot、Wiki-Bot、service-bot、doc-bot）均已测试确认可在本群（oc_3355491c025a6baff0d50c9845e2c5de）发送消息。

### Bot open_id（飞书内部 ID，用于 @mention）

| Bot | open_id |
|-----|---------|
| OpenClaw | ou_e88ce742d3665936bd9d14ff1aeb69d6 |
| Wiki-Bot | ou_486b92a6aca2dd381aa27ab12499a2e9 |
| Service-Bot | ou_2b1ae7181303c1a59010db2771fb1b20 |
| Media-Bot | ou_befff50063e5c1b48f90993c5ff4f7d9 |
| doc-bot | ou_30d1ccbafcb27c868350b48ce98d01a4 |

### 常用 @ 对应

| Bot | 用途 | 何时 @ |
|-----|------|--------|
| @OpenClaw | 系统管理、权限、配置变更 | 需要我协调时 |
| @Wiki-Bot | 知识库操作、Wiki 读写 | Librarian 需要时 |
| @Service-Bot | 客服 Q&A、Bitable 工单 | 需要创建工单时 |
| @Media-Bot | 媒体热点、Manager 相关 | 报告相关时 |
| @doc-bot | 文档发布 | Publisher 需要时 |

**@mention 格式**：在消息中使用 `<at user_id="BOT_OPEN_ID">BOT_NAME</at>` 格式

### 禁止行为

- ❌ 单方面等待另一个 Bot 的响应而不 @对方
- ❌ 假设另一个 Bot 知道你在做什么（主动说清楚）
- ❌ 在群里发消息但不 @需要响应的人


---

## 会话上下文大小管理（2026-04-23 确立）

**目标**：防止会话超出 200K token 上限导致 LLM API 报错。

### 规则

| 场景 | 阈值 | 处理 |
|------|------|------|
| 启动时检查 | > 150K（75%） | 主动触发 compaction |
| 运行时监控 | > 180K（90%） | 立即压缩最旧的 50% 内容 |
| 超 200K | API 报错 | 降级为简单文本处理（无 LLM） |

### Wiki-Bot 执行方式

每次 session 开始时检查会话文件大小：

```bash
SESSION_FILE="/mnt/data/openclaw/agents/wiki-agent/sessions/{session_id}.jsonl"
SIZE=$(wc -c < "$SESSION_FILE")
if [ $SIZE -gt 150000 ]; then
    # 通知 OpenClaw compaction（发消息或调用 session compaction API）
fi
```

### 降级策略

当 context 超 200K 无法压缩时：
- 切换为纯文本模式（不做 LLM 摘要，只做文件复制）
- 标记为 `[DEGRADED]` 并通知阿拉丁

---

## 长任务主动汇报规范（2026-04-23 确立）

**触发条件**：任务预计耗时超过 3 分钟

### 汇报规则

**1. 任务开始时**（立即发送）
```
📋 收到任务：[任务名]
⏱️ 预计耗时：X 分钟
🔄 状态：处理中
```

**2. 每 3 分钟进度汇报**（自动发送）
```
🔄 [任务名] 处理中
📊 进度：已完成 X/Y 个文件
⏱️ 已用时：X 分钟
💡 状态：正在处理 [当前文件/步骤]
```

**3. 任务完成时**
```
✅ [任务名] 完成
📊 结果：成功 X 个，失败 Y 个
⏱️ 总耗时：X 分钟
```

### 禁止行为

- ❌ 长任务开始后静默等待，不发任何消息
- ❌ 不在开始时预估时间，用户无法判断是否需要等待
- ❌ 完成后不汇报结果，用户不知道任务是否成功

### 实现方式

在 SOUL.md 中加入主动汇报规范，并在执行 exec 调用长时间任务时，实时发送消息到群。


---

## 系统备份规范（2026-04-23 确立）

### 标准备份目录

**路径**：`/mnt/data/backup/YYYYMMDD/`

每日 01:00 自动备份，生成的归档：

| 文件 | 内容 |
|------|------|
| `openclaw_YYYYMMDD.tar.gz` | OpenClaw 主配置（排除 logs/sessions/media） |
| `sub_agents_YYYYMMDD.tar.gz` | 所有 subagent workspace |
| `km_YYYYMMDD.tar.gz` | 知识库 /mnt/data/km |
| `openclaw-gateway.service.bak` | systemd 服务配置 |

### 手动备份命名格式

```
/mnt/data/backup/YYYYMMDD/<description>.bak.YYYYMMDDHHMMSS
```

示例：
- `/mnt/data/backup/20260423/openclaw.json.bak.154800`
- `/mnt/data/backup/20260423/ingest2.0.py.bak.211110`

### 重要操作前备份

进行重大配置修改前，必须先手动备份：

```bash
# 备份主配置
cp /mnt/data/openclaw/openclaw.json /mnt/data/backup/$(date +%Y%m%d)/openclaw.json.bak.$(date +%H%M%S)

# 备份工具脚本
cp /mnt/data/km/llm-wiki/tools/ingest2.0.py /mnt/data/backup/$(date +%Y%m%d)/ingest2.0.py.bak.$(date +%H%M%S)
```

### 恢复操作

1. 找到最近的备份目录（按日期）
2. 解压对应归档或复制单个文件
3. 重启 Gateway：`openclaw gateway restart`


---

### 飞书 Bot open_id 对应表（2026-04-24）

所有 Agent 之间互相 @mention 时使用此表：

| Agent ID | 飞书 Bot | open_id |
|----------|---------|---------|
| main | OpenClaw | `ou_e88ce742d3665936bd9d14ff1aeb69d6` |
| service | Service-Bot（伊里斯） | `ou_2b1ae7181303c1a59010db2771fb1b20` |
| wiki-agent | Wiki-Bot（雅典娜） | `ou_486b92a6aca2dd381aa27ab12499a2e9` |
| manager | Media-Bot（赫尔墨斯） | `ou_befff50063e5c1b48f90993c5ff4f7d9` |
| publisher | doc-bot | `ou_30d1ccbafcb27c868350b48ce98d01a4` |

**使用场景**：当一个 Agent 需要直接发消息给另一个 Agent 时，在群组中用 `<at user_id="OPEN_ID">Bot名称</at>` mention。

---

## Bot Group 多轮通讯协议（2026-05-06 确立）

**协调者**：荷鲁斯（main，open_id: `ou_e88ce742d3665936bd9d14ff1aeb69d6`）

### 协作规则

1. **阿拉丁 @ 我（荷鲁斯）发起任务**
2. **我决定由哪个 Bot 开始，按顺序传递**
3. **每 Bot 完成后 @ 我汇报，不要自己跳到下一个**
4. **我判断下一步，@ 下一个 Bot 或汇总结果**
5. **每话题每 Bot 最多 5 轮，超过我主动停止**

### @mention 格式（必须用飞书原生格式，纯文本 @ 无法触发 Bot）

```xml
<at user_id="ou_486b92a6aca2dd381aa27ab12499a2e9">Wiki-Bot</at>
<at user_id="ou_befff50063e5c1b48f90993c5ff4f7d9">Media-Bot</at>
<at user_id="ou_2b1ae7181303c1a59010db2771fb1b20">Service-Bot</at>
<at user_id="ou_30d1ccbafcb27c868350b48ce98d01a4">Doc-Bot</at>
<at user_id="ou_e88ce742d3665936bd9d14ff1aeb69d6">荷鲁斯</at>
```

### 轮次控制原则

| 规则 | 说明 |
|------|------|
| 发言权归属 | 话题由协调者（荷鲁斯）分配，完成后交回 |
| 禁止抢答 | 非目标 Bot 不主动响应（除非协调者要求） |
| 5 轮上限 | 单 Bot 处理同一话题超过 5 轮时，协调者主动介入 |
| 结束信号 | 协调者 @ 阿拉丁汇总结果，标志话题结束 |
