# mcp-push

> 一个强大的 MCP (Model Context Protocol) 通知推送服务器，支持多渠道消息推送

[English](#english-version) | 中文

## 项目介绍

mcp-push 是一个基于 MCP 协议的通知推送服务器，可以将消息推送到多个通知渠道。它为 AI 助手（如 Claude、Codex、Gemini）提供了标准化的通知接口，让 AI 能够在任务完成或需要用户确认时主动发送通知。

### 核心特性

- **多渠道支持**：集成 20+ 主流通知服务（钉钉、飞书、Telegram、企业微信等）
- **标准化接口**：基于 MCP 协议，提供统一的工具调用方式
- **双模式推送**：
  - `notify_send`：简单消息推送，适合一次性通知
  - `notify_event`：结构化事件流，支持任务状态追踪
- **并发推送**：自动向所有已配置渠道并发发送消息
- **灵活配置**：通过环境变量配置，支持动态启用/禁用渠道

## 环境要求

- Python >= 3.8
- 支持的操作系统：Linux、macOS、Windows (需要 WSL 或 Git Bash)

## 安装

### 方法 1：从源码安装

```bash
git clone https://github.com/d4renk/mcp-push.git
cd mcp-push
pip install -r requirements.txt
```

### 方法 2：通过 uvx 安装

```bash
uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push --transport stdio
```

## 配置

### 基础配置

所有通知渠道通过环境变量配置。你可以：

1. **直接设置环境变量**：
```bash
export DD_BOT_TOKEN="your-token"
export DD_BOT_SECRET="your-secret"
```

2. **使用配置文件**（推荐）：
```bash
# 复制示例配置文件
cp config.sh.example config.sh

# 编辑 config.sh，填入你的配置
vim config.sh

# 加载配置
source config.sh
```

### 支持的通知渠道

#### 主要渠道

| 渠道名称 | 必需环境变量 | 说明 |
|---------|------------|------|
| **Bark** | `BARK_PUSH` | iOS 通知推送服务 |
| **钉钉机器人** | `DD_BOT_TOKEN`, `DD_BOT_SECRET` | 钉钉群机器人（加签方式） |
| **飞书机器人** | `FSKEY` | 飞书群机器人 Webhook Key |
| **Telegram** | `TG_BOT_TOKEN`, `TG_USER_ID` | Telegram Bot 推送 |
| **企业微信机器人** | `QYWX_KEY` | 企业微信群机器人 Webhook Key |
| **企业微信应用** | `QYWX_AM` | 企业微信应用消息 |
| **Gotify** | `GOTIFY_URL`, `GOTIFY_TOKEN` | 自托管通知服务 |
| **Ntfy** | `NTFY_URL`, `NTFY_TOPIC` | 自托管/云端通知服务 |
| **PushDeer** | `DEER_KEY` | PushDeer 推送服务 |
| **PushPlus** | `PUSH_PLUS_TOKEN` | PushPlus 微信推送 |
| **Server酱 (ServerJ/ServerChan)** | `PUSH_KEY` | Server酱推送服务 |

#### 其他支持的渠道

- **Go-cqhttp** (`GOBOT_URL`, `GOBOT_QQ`, `GOBOT_TOKEN` 可选) - QQ 消息推送
- **Chronocat** (`CHRONOCAT_URL`, `CHRONOCAT_QQ`, `CHRONOCAT_TOKEN`) - QQ 消息推送
- **WxPusher** (`WXPUSHER_APP_TOKEN`, `WXPUSHER_TOPIC_IDS`/`WXPUSHER_UIDS`) - 微信推送
- **Qmsg酱** (`QMSG_KEY`, `QMSG_TYPE`) - QQ 消息推送
- **iGot** (`IGOT_PUSH_KEY`) - 聚合推送
- **PushMe** (`PUSHME_KEY`, `PUSHME_URL` 可选) - 自建推送
- **微加机器人** (`WE_PLUS_BOT_TOKEN`, `WE_PLUS_BOT_RECEIVER`, `WE_PLUS_BOT_VERSION`) - 微信机器人
- **Aibotk** (`AIBOTK_KEY`, `AIBOTK_TYPE`, `AIBOTK_NAME`) - 智能微秘书
- **Synology Chat** (`CHAT_URL`, `CHAT_TOKEN`) - 群晖 Chat
- **SMTP** (`SMTP_SERVER`, `SMTP_EMAIL`, `SMTP_PASSWORD`, `SMTP_SSL`, `SMTP_NAME`) - 邮件推送
- **自定义 Webhook** (`WEBHOOK_URL`, `WEBHOOK_METHOD`, `WEBHOOK_BODY`) - 自定义推送

完整配置说明请参考 [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md)

## 注册 MCP 服务器

### 本地安装方式

**Codex:**
```bash
codex mcp add mcp-push -- python3 $(pwd)/src/server.py
```

**Claude:**
```bash
claude mcp add mcp-push -- python3 $(pwd)/src/server.py
```

**Gemini:**
```bash
gemini mcp add mcp-push -- python3 $(pwd)/src/server.py
```

> 注意：如果你的 CLI 版本需要显式传输参数，请把 `--transport stdio` 放在 `--` 之后，作为 MCP 服务器的参数传入。

### 通过 uvx 安装方式

**Codex:**
```bash
codex mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push --transport stdio
```

**Claude:**
```bash
claude mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push --transport stdio
```

**Gemini:**
```bash
gemini mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push --transport stdio
```

## 使用示例

### 示例 1：简单消息推送 (notify_send)

```python
# 在 AI 助手中调用
await mcp_client.call_tool("notify_send", {
    "title": "任务完成",
    "content": "数据分析已完成，共处理 10000 条记录"
})
```

**适用场景**：
- 长时间任务完成通知（>60秒）
- 需要用户确认的操作
- 一次性通知消息

### 示例 2：结构化事件推送 (notify_event)

```python
# 任务开始
await mcp_client.call_tool("notify_event", {
    "run_id": "data-analysis-20240101-001",
    "event": "start",
    "message": "开始分析数据..."
})

# 任务更新
await mcp_client.call_tool("notify_event", {
    "run_id": "data-analysis-20240101-001",
    "event": "update",
    "message": "已处理 50%",
    "data": {"progress": 0.5}
})

# 任务完成
await mcp_client.call_tool("notify_event", {
    "run_id": "data-analysis-20240101-001",
    "event": "end",
    "message": "分析完成，共发现 127 个异常事件",
    "data": {
        "progress": 1.0,
        "artifact_url": "https://example.com/reports/20240101-001.html"
    }
})

# 任务失败
await mcp_client.call_tool("notify_event", {
    "run_id": "data-analysis-20240101-001",
    "event": "error",
    "message": "任务失败：连接数据库超时",
    "data": {"error_code": "DB_TIMEOUT"}
})
```

**适用场景**：
- 长时间运行的任务状态追踪
- 需要进度更新的操作
- 复杂工作流的状态通知

## 使用建议

### 何时推送通知？

**务必推送**：
1. ✅ **任务完成**：长耗时任务（>60秒）执行结束（无论成功或失败）
2. ✅ **需要用户确认**：流程暂停，等待用户决策或授权

**避免推送**：
- ❌ 任务启动时的通知
- ❌ 频繁的中间过程更新（除非用户明确要求追踪进度）
- ❌ 简单操作的完成通知

### 推送频率控制

- 默认情况下，仅在任务的 `end` 或 `error` 状态时推送
- 如需实时监控，可在 `start` 和 `update` 事件时推送，但需注意避免打扰用户

## 常见问题

### 1. 如何测试配置是否正确？

```bash
python test_mcp_push.py
```

### 2. 支持同时推送到多个渠道吗？

是的，mcp-push 会自动向所有已配置的渠道并发推送消息。

### 3. 如何查看推送失败的原因？

推送结果会返回详细的错误信息：

```json
{
  "status": "partial_success",
  "message": "消息推送未完全成功",
  "channels_count": 3,
  "errors": {
    "dingding_bot": "签名验证失败"
  }
}
```

### 4. 如何获取各个渠道的配置信息？

请参考 [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md) 中的详细说明。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

---

<a name="english-version"></a>

# mcp-push

> A powerful MCP (Model Context Protocol) notification push server supporting multi-channel message delivery

[中文](#mcp-push) | English

## Overview

mcp-push is an MCP protocol-based notification push server that delivers messages to multiple notification channels. It provides a standardized notification interface for AI assistants (such as Claude, Codex, Gemini), enabling AI to proactively send notifications when tasks are completed or user confirmation is needed.

### Key Features

- **Multi-Channel Support**: Integrates 20+ mainstream notification services (DingTalk, Feishu, Telegram, WeCom, etc.)
- **Standardized Interface**: Based on MCP protocol, providing unified tool invocation
- **Dual Push Modes**:
  - `notify_send`: Simple message push for one-time notifications
  - `notify_event`: Structured event stream supporting task status tracking
- **Concurrent Push**: Automatically sends messages concurrently to all configured channels
- **Flexible Configuration**: Configure via environment variables, supports dynamic enabling/disabling of channels

## Requirements

- Python >= 3.8
- Supported OS: Linux, macOS, Windows (with WSL or Git Bash)

## Installation

### Method 1: Install from Source

```bash
git clone https://github.com/d4renk/mcp-push.git
cd mcp-push
pip install -r requirements.txt
```

### Method 2: Install via uvx

```bash
uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push --transport stdio
```

## Configuration

### Basic Configuration

All notification channels are configured through environment variables. You can:

1. **Set environment variables directly**:
```bash
export DD_BOT_TOKEN="your-token"
export DD_BOT_SECRET="your-secret"
```

2. **Use configuration file** (Recommended):
```bash
# Copy example configuration file
cp config.sh.example config.sh

# Edit config.sh and fill in your configuration
vim config.sh

# Load configuration
source config.sh
```

### Supported Notification Channels

#### Main Channels

| Channel | Required Environment Variables | Description |
|---------|-------------------------------|-------------|
| **Bark** | `BARK_PUSH` | iOS notification push service |
| **DingTalk Bot** | `DD_BOT_TOKEN`, `DD_BOT_SECRET` | DingTalk group bot (with signature) |
| **Feishu Bot** | `FSKEY` | Feishu group bot Webhook Key |
| **Telegram** | `TG_BOT_TOKEN`, `TG_USER_ID` | Telegram Bot push |
| **WeCom Bot** | `QYWX_KEY` | WeCom group bot Webhook Key |
| **WeCom App** | `QYWX_AM` | WeCom application message |
| **Gotify** | `GOTIFY_URL`, `GOTIFY_TOKEN` | Self-hosted notification service |
| **Ntfy** | `NTFY_URL`, `NTFY_TOPIC` | Self-hosted/cloud notification service |
| **PushDeer** | `DEER_KEY` | PushDeer push service |
| **PushPlus** | `PUSH_PLUS_TOKEN` | PushPlus WeChat push |
| **ServerChan (ServerJ)** | `PUSH_KEY` | ServerChan push service |

#### Other Supported Channels

- **Go-cqhttp** (`GOBOT_URL`, `GOBOT_QQ`, `GOBOT_TOKEN` optional) - QQ message push
- **Chronocat** (`CHRONOCAT_URL`, `CHRONOCAT_QQ`, `CHRONOCAT_TOKEN`) - QQ message push
- **WxPusher** (`WXPUSHER_APP_TOKEN`, `WXPUSHER_TOPIC_IDS`/`WXPUSHER_UIDS`) - WeChat push
- **Qmsg** (`QMSG_KEY`, `QMSG_TYPE`) - QQ message push
- **iGot** (`IGOT_PUSH_KEY`) - Aggregated push
- **PushMe** (`PUSHME_KEY`, `PUSHME_URL` optional) - Self-hosted push
- **WeBot** (`WE_PLUS_BOT_TOKEN`, `WE_PLUS_BOT_RECEIVER`, `WE_PLUS_BOT_VERSION`) - WeChat bot
- **Aibotk** (`AIBOTK_KEY`, `AIBOTK_TYPE`, `AIBOTK_NAME`) - Smart WeChat secretary
- **Synology Chat** (`CHAT_URL`, `CHAT_TOKEN`) - Synology Chat
- **SMTP** (`SMTP_SERVER`, `SMTP_EMAIL`, `SMTP_PASSWORD`, `SMTP_SSL`, `SMTP_NAME`) - Email push
- **Custom Webhook** (`WEBHOOK_URL`, `WEBHOOK_METHOD`, `WEBHOOK_BODY`) - Custom push

For complete configuration instructions (Chinese only), please refer to [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md)

## Register MCP Server

### Local Installation

**Codex:**
```bash
codex mcp add mcp-push -- python3 $(pwd)/src/server.py
```

**Claude:**
```bash
claude mcp add mcp-push -- python3 $(pwd)/src/server.py
```

**Gemini:**
```bash
gemini mcp add mcp-push -- python3 $(pwd)/src/server.py
```

> Note: If your CLI version requires explicit transport parameters, place `--transport stdio` after `--` as a parameter for the MCP server.

### Installation via uvx

**Codex:**
```bash
codex mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push --transport stdio
```

**Claude:**
```bash
claude mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push --transport stdio
```

**Gemini:**
```bash
gemini mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push --transport stdio
```

## Usage Examples

### Example 1: Simple Message Push (notify_send)

```python
# Call in AI assistant
await mcp_client.call_tool("notify_send", {
    "title": "Task Completed",
    "content": "Data analysis completed, processed 10000 records"
})
```

**Use Cases**:
- Long-running task completion notifications (>60 seconds)
- Operations requiring user confirmation
- One-time notification messages

### Example 2: Structured Event Push (notify_event)

```python
# Task start
await mcp_client.call_tool("notify_event", {
    "run_id": "data-analysis-20240101-001",
    "event": "start",
    "message": "Starting data analysis..."
})

# Task update
await mcp_client.call_tool("notify_event", {
    "run_id": "data-analysis-20240101-001",
    "event": "update",
    "message": "50% processed",
    "data": {"progress": 0.5}
})

# Task completion
await mcp_client.call_tool("notify_event", {
    "run_id": "data-analysis-20240101-001",
    "event": "end",
    "message": "Analysis completed, found 127 anomalous events",
    "data": {
        "progress": 1.0,
        "artifact_url": "https://example.com/reports/20240101-001.html"
    }
})

# Task failure
await mcp_client.call_tool("notify_event", {
    "run_id": "data-analysis-20240101-001",
    "event": "error",
    "message": "Task failed: database connection timeout",
    "data": {"error_code": "DB_TIMEOUT"}
})
```

**Use Cases**:
- Long-running task status tracking
- Operations requiring progress updates
- Complex workflow status notifications

## Usage Guidelines

### When to Send Notifications?

**Must Send**:
1. ✅ **Task Completion**: Long-running tasks (>60 seconds) finished (success or failure)
2. ✅ **User Confirmation Needed**: Process paused, waiting for user decision or authorization

**Avoid Sending**:
- ❌ Task start notifications
- ❌ Frequent intermediate progress updates (unless user explicitly requests progress tracking)
- ❌ Simple operation completion notifications

### Push Frequency Control

- By default, only push on `end` or `error` task states
- For real-time monitoring, you can push on `start` and `update` events, but be careful to avoid disturbing users

## FAQ

### 1. How to test if configuration is correct?

```bash
python test_mcp_push.py
```

### 2. Can I push to multiple channels simultaneously?

Yes, mcp-push automatically pushes messages concurrently to all configured channels.

### 3. How to view reasons for push failures?

Push results return detailed error information:

```json
{
  "status": "partial_success",
  "message": "Message push not fully successful",
  "channels_count": 3,
  "errors": {
    "dingding_bot": "Signature verification failed"
  }
}
```

### 4. How to get configuration information for each channel?

Please refer to the detailed instructions in [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md).

## Contributing

Issues and Pull Requests are welcome!

## License

MIT License
