# mcp-push

**Agent 执行结果 → 实时推送到外部系统的标准化 MCP 桥接**

将 AI Agent 的执行过程和结果，通过事件流实时推送到 20+ 通知渠道（钉钉、飞书、Telegram、企业微信、邮件等）。可作为工作流编排、异步任务系统和通知平台的桥梁。

## 核心特性

- **MCP 标准化接口**：符合 Model Context Protocol 规范的工具集成
- **事件流架构**：支持 `start|update|end|error` 四种事件类型
- **多渠道并发**：20+ 通知渠道并行推送，最佳努力交付
- **双语言实现**：Python 和 JavaScript 完整支持
- **零侵入集成**：保留原有 API，向后完全兼容

---

## 安装与配置

### 1. 安装 mcp-push

```bash
# 使用 claude mcp 命令行工具安装
claude mcp add mcp-push -s user --transport stdio -- python /path/to/mcp-push/server.py
```
> 将 `/path/to/mcp-push` 替换为本仓库的实际路径

### 2. 配置通知渠道

复制配置模板并填入凭据：

```bash
cp config.sh.example config.sh
# 编辑 config.sh，填入通知渠道的 Token/Secret
```

### 3. 验证安装

```bash
claude mcp list
```
看到 `mcp-push: ... - ✓ Connected` 说明安装成功

---

## MCP Agent 集成指南 (Core Instruction)

本章节是 **mcp-push** 的核心使用指南，专为 Agent 和 MCP 客户端设计。在需要通知用户或推送任务状态时，请遵循以下规范。

### 调用时机与策略

1.  **简单消息**：当需要向用户推送简单消息时，使用 `notify.send` 工具。
2.  **任务追踪**：当需要追踪长时间任务的执行进度时，使用 `notify.event` 工具发送结构化事件流。
3.  **事件生命周期**：任务开始时发送 `start`，执行中发送 `update`，完成时发送 `end`，出错时发送 `error`。
4.  **自动分发**：mcp-push 会自动将消息并发推送到所有已配置的渠道，无需关心具体细节。

### 可用工具详解

#### 1. `notify.send` - 简单消息推送

**用途**：发送简单的 "标题 + 内容" 消息到所有已配置渠道。适用于即时通知、系统告警、无进度概念的一次性消息。

**参数**：
- `title` (string, 必选): 消息标题
- `content` (string, 必选): 消息内容（支持换行符 `\n`）

**调用示例**：
```python
# 简单通知
await mcp_client.call_tool("notify.send", {
  "title": "任务完成",
  "content": "数据分析已完成，共处理 10000 条记录"
})
```

#### 2. `notify.event` - 结构化事件推送

**用途**：发送带任务 ID、进度、状态的结构化事件，适合长时间运行的任务追踪（>30秒）、多步骤流程或可量化的任务。

**参数**：
- `run_id` (string, 必选): 任务唯一标识符（建议格式：`{任务类型}-{日期}-{序号}`）
- `event` (string, 必选): 事件类型 (`start`, `update`, `end`, `error`)
- `message` (string, 必选): 人类可读的状态描述
- `data` (object, 可选): 附加数据
  - `step` (string): 当前执行步骤
  - `progress` (float): 进度百分比（0.0 - 1.0）
  - `artifact_url` (string): 生成的产物地址
  - `error_code` (string): 错误代码（仅 error 事件）
- `timestamp` (string, 可选): ISO 8601 格式时间戳

**调用示例**：

**Step 1: 任务开始**
```python
await mcp_client.call_tool("notify.event", {
  "run_id": "data-analysis-20240101-001",
  "event": "start",
  "message": "开始分析 10GB 日志数据"
})
```

**Step 2: 进度更新**
```python
await mcp_client.call_tool("notify.event", {
  "run_id": "data-analysis-20240101-001",
  "event": "update",
  "message": "已处理 3.2GB (32%)",
  "data": {
    "step": "data_parsing",
    "progress": 0.32
  }
})
```

**Step 3: 任务完成**
```python
await mcp_client.call_tool("notify.event", {
  "run_id": "data-analysis-20240101-001",
  "event": "end",
  "message": "分析完成，共发现 127 个异常事件",
  "data": {
    "step": "generate_report",
    "progress": 1.0,
    "artifact_url": "https://example.com/reports/20240101-001.html"
  }
})
```

### 调用规范与注意事项

1.  **run_id 一致性**：同一任务的所有事件必须使用完全相同的 `run_id`。
2.  **状态转换**：
    - 正常：`start` → `update`... → `end`
    - 异常：`start` → `update`... → `error`
    - 禁止在 `end` 或 `error` 后继续发送 `update`。
3.  **Progress 范围**：必须在 `0.0` 到 `1.0` 之间。`end` 事件必须设为 `1.0`。
4.  **错误处理**：推送是异步的最佳努力交付，单个渠道失败不影响其他渠道。不要依赖 `notify` 工具的返回值来决定后续业务逻辑。

---

## 库模式调用 (非 MCP 场景)

除了通过 MCP 协议调用，你也作为普通 Python/JS 库直接使用。

**Python**
```python
from notify import send
send("任务完成", "已生成 PDF 报告，耗时 3.2s")
```

**JavaScript**
```javascript
const { sendNotify } = require('./sendNotify');
await sendNotify('任务完成', '已生成 PDF 报告，耗时 3.2s');
```

---

## 支持的通知渠道

只需配置相应渠道的环境变量即可自动启用。

| 渠道类型 | 环境变量 | 文档 |
|---------|---------|------|
| 🔔 Bark | `BARK_PUSH` | [配置指南](docs/CHANNEL_CONFIG.md#bark) |
| 💬 钉钉机器人 | `DD_BOT_TOKEN`, `DD_BOT_SECRET` | [配置指南](docs/CHANNEL_CONFIG.md#钉钉机器人-dingtalk) |
| 🕊️ 飞书机器人 | `FSKEY` | [配置指南](docs/CHANNEL_CONFIG.md#飞书机器人-feishulark) |
| ✈️ Telegram | `TG_BOT_TOKEN`, `TG_USER_ID` | [配置指南](docs/CHANNEL_CONFIG.md#telegram-bot) |
| 🏢 企业微信机器人 | `QYWX_KEY` | [配置指南](docs/CHANNEL_CONFIG.md#企业微信机器人-wecom-bot) |
| 🏢 企业微信应用 | `QYWX_AM` | [配置指南](docs/CHANNEL_CONFIG.md#企业微信应用-wecom-app) |
| 📧 SMTP 邮件 | `SMTP_SERVER`, `SMTP_SSL`, `SMTP_EMAIL`, `SMTP_PASSWORD`, `SMTP_NAME` | [配置指南](docs/CHANNEL_CONFIG.md#smtp-邮件) |
| 📮 Server 酱 | `PUSH_KEY` | [配置指南](docs/CHANNEL_CONFIG.md#server酱-serverchan) |
| ➕ PushPlus | `PUSH_PLUS_TOKEN` | [配置指南](docs/CHANNEL_CONFIG.md#pushplus) |
| 🦌 PushDeer | `DEER_KEY` | [配置指南](docs/CHANNEL_CONFIG.md#pushdeer) |
| 📡 Gotify | `GOTIFY_URL`, `GOTIFY_TOKEN` | [配置指南](docs/CHANNEL_CONFIG.md#gotify) |
| 📨 Ntfy | `NTFY_TOPIC` | [配置指南](docs/CHANNEL_CONFIG.md#ntfy) |
| 🤖 Go-cqhttp | `GOBOT_URL`, `GOBOT_QQ` | [配置指南](docs/CHANNEL_CONFIG.md#go-cqhttp) |
| 🐱 Chronocat | `CHRONOCAT_URL`, `CHRONOCAT_QQ`, `CHRONOCAT_TOKEN` | [配置指南](docs/CHANNEL_CONFIG.md#chronocat) |
| 💬 Qmsg | `QMSG_KEY`, `QMSG_TYPE` | [配置指南](docs/CHANNEL_CONFIG.md#qmsg-酱) |
| 🤖 智能微秘书 | `AIBOTK_KEY`, `AIBOTK_TYPE` | [配置指南](docs/CHANNEL_CONFIG.md#智能微秘书-aibotk) |
| 🔗 自定义 Webhook | `WEBHOOK_URL`, `WEBHOOK_METHOD` | [配置指南](docs/CHANNEL_CONFIG.md#自定义-webhook) |
| 🎯 iGot | `IGOT_PUSH_KEY` | [配置指南](docs/CHANNEL_CONFIG.md#igot) |
| 📬 PushMe | `PUSHME_KEY` | [配置指南](docs/CHANNEL_CONFIG.md#pushme) |
| 💬 Synology Chat | `CHAT_URL`, `CHAT_TOKEN` | [配置指南](docs/CHANNEL_CONFIG.md#synology-chat) |
| 🤖 微加机器人 | `WE_PLUS_BOT_TOKEN` | [配置指南](docs/CHANNEL_CONFIG.md#微加机器人-webot) |
| 🌐 WxPusher | `WXPUSHER_APP_TOKEN` | [配置指南](docs/CHANNEL_CONFIG.md#wxpusher) |

## 配置示例

**最小配置（仅钉钉）**
```bash
export DD_BOT_TOKEN="your-token"
export DD_BOT_SECRET="your-secret"
```

**多渠道配置**
```bash
# 钉钉
export DD_BOT_TOKEN="token"
export DD_BOT_SECRET="secret"

# Telegram
export TG_BOT_TOKEN="123456:ABC-DEF"
export TG_USER_ID="987654321"

# 邮件
export SMTP_SERVER="smtp.example.com:465"
export SMTP_SSL="true"
export SMTP_EMAIL="notify@example.com"
export SMTP_PASSWORD="password"
```

**通用配置**
- `HITOKOTO`: 是否附加一言随机句子（默认 `true`，设为 `false` 关闭）
- `SKIP_PUSH_TITLE`: 跳过推送的标题列表（换行分隔）

## 文档索引

- [MCP 集成架构](docs/MCP_INTEGRATION.md) - 技术实现细节
- [使用示例](docs/USAGE_EXAMPLES.md) - 更多实战案例
- [渠道配置指南](docs/CHANNEL_CONFIG.md) - 完整环境变量说明
- [迁移指南](docs/MIGRATION.md) - 从库模式迁移到 MCP 工具

## 许可证

MIT License

---

**工作原理**

```
┌─────────────┐      ┌──────────────┐      ┌────────────────┐
│  AI Agent   │─────▶│  MCP Server  │─────▶│  Notification  │
│  (任务执行)  │      │  (事件路由)  │      │  Channels (20+)│
└─────────────┘      └──────────────┘      └────────────────┘
                             │
                             ├─────▶ 钉钉机器人
                             ├─────▶ Telegram Bot
                             ├─────▶ SMTP 邮件
                             └─────▶ ... (并发推送)
```