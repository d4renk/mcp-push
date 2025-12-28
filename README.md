# mcp-push

**Agent 执行结果 → 实时推送到外部系统的标准化 MCP 桥接**

将 AI Agent 的执行过程和结果，通过事件流实时推送到 20+ 通知渠道（钉钉、飞书、Telegram、企业微信、邮件等）。可作为工作流编排、异步任务系统和通知平台的桥梁。

## 核心特性

- **MCP 标准化接口**：符合 Model Context Protocol 规范的工具集成
- **事件流架构**：支持 `start|update|end|error` 四种事件类型
- **多渠道并发**：20+ 通知渠道并行推送，最佳努力交付
- **双语言实现**：Python 和 JavaScript 完整支持
- **零侵入集成**：保留原有 API，向后完全兼容

## 快速开始

### 作为 MCP 工具使用

```python
# Agent 端调用（通过 MCP 协议）
await mcp_client.call_tool("notify.event", {
  "run_id": "task-20240101-001",
  "event": "end",
  "message": "数据分析完成",
  "data": {
    "step": "generate_report",
    "progress": 1.0,
    "artifact_url": "https://example.com/report.pdf"
  }
})
```

### 作为库直接调用

```python
# Python
from notify import send
send("任务完成", "已生成 PDF 报告，耗时 3.2s")
```

```javascript
// JavaScript
const { sendNotify } = require('./sendNotify');
await sendNotify('任务完成', '已生成 PDF 报告，耗时 3.2s');
```

## 支持的通知渠道

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

## 架构设计

### MCP 工具集

1. **`notify.send`** - 广播消息到所有已配置渠道
2. **`notify.event`** - 发送结构化事件流（带 run_id、进度、状态等）
3. **`notify.channel.<name>`** - 单渠道推送（可选）

### Event Envelope 结构

```json
{
  "run_id": "task-20240101-001",
  "event": "start|update|end|error",
  "message": "人类可读的状态描述",
  "data": {
    "step": "当前执行步骤",
    "progress": 0.75,
    "artifact_url": "生成的产物地址（可选）"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 并发处理机制

- **Python**：使用 `threading.Thread` 并发执行所有渠道推送
- **JavaScript**：使用 `Promise.all` 并发执行所有渠道推送
- **错误隔离**：单个渠道失败不影响其他渠道
- **状态聚合**：返回每个渠道的推送结果汇总

## 使用场景

### 场景 1: Agent 任务进度通知

```python
# Agent 启动
await mcp.call_tool("notify.event", {
  "run_id": "data-analysis-001",
  "event": "start",
  "message": "开始分析 10GB 日志数据"
})

# 执行中更新进度
await mcp.call_tool("notify.event", {
  "run_id": "data-analysis-001",
  "event": "update",
  "message": "已处理 3.2GB",
  "data": {"progress": 0.32}
})

# 完成
await mcp.call_tool("notify.event", {
  "run_id": "data-analysis-001",
  "event": "end",
  "message": "分析完成",
  "data": {
    "progress": 1.0,
    "artifact_url": "https://example.com/report.html"
  }
})
```

### 场景 2: 异常告警

```python
# 错误事件
await mcp.call_tool("notify.event", {
  "run_id": "deployment-002",
  "event": "error",
  "message": "部署失败：数据库连接超时",
  "data": {
    "step": "db_migration",
    "error_code": "ECONNREFUSED"
  }
})
```

### 场景 3: 简单消息推送

```python
# 直接发送文本消息
await mcp.call_tool("notify.send", {
  "title": "系统告警",
  "content": "CPU 使用率超过 80%"
})
```

## 配置示例

### 最小配置（仅钉钉）

```bash
export DD_BOT_TOKEN="your-token"
export DD_BOT_SECRET="your-secret"
```

### 多渠道配置

```bash
# 钉钉
export DD_BOT_TOKEN="token"
export DD_BOT_SECRET="secret"

# Telegram
export TG_BOT_TOKEN="123456:ABC-DEF"
export TG_USER_ID="987654321"

# 企业微信
export QYWX_KEY="webhook-key"

# 邮件
export SMTP_SERVER="smtp.example.com:465"
export SMTP_SSL="true"
export SMTP_EMAIL="notify@example.com"
export SMTP_PASSWORD="password"
export SMTP_NAME="AI Agent"
```

## 文档索引

- [MCP 集成架构](docs/MCP_INTEGRATION.md) - 技术实现细节
- [使用示例](docs/USAGE_EXAMPLES.md) - 更多实战案例
- [渠道配置指南](docs/CHANNEL_CONFIG.md) - 完整环境变量说明
- [迁移指南](docs/MIGRATION.md) - 从库模式迁移到 MCP 工具

## 环境变量参考

### 通用配置

- `HITOKOTO`: 是否附加一言随机句子（默认 `true`）
- `SKIP_PUSH_TITLE`: 跳过推送的标题列表（换行分隔）

### 渠道开关

只需配置相应渠道的环境变量即可自动启用该渠道。未配置的渠道会被自动跳过。

## 工作原理

```
┌─────────────┐      ┌──────────────┐      ┌────────────────┐
│  AI Agent   │─────▶│  MCP Server  │─────▶│  Notification  │
│  (任务执行)  │      │  (事件路由)  │      │  Channels (20+)│
└─────────────┘      └──────────────┘      └────────────────┘
                             │
                             ├─────▶ 钉钉机器人
                             ├─────▶ Telegram Bot
                             ├─────▶ 企业微信
                             ├─────▶ SMTP 邮件
                             └─────▶ ... (并发推送)

✅ 模型做完事 → 用户立刻收到消息
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request。新增通知渠道请参考现有实现模式。
