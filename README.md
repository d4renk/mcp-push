# mcp-push
> **Multi-channel Notification Server for MCP / MCP 多渠道通知推送服务**

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.8+-green.svg) ![MCP](https://img.shields.io/badge/MCP-Standard-orange.svg)

**mcp-push** is a standard Model Context Protocol (MCP) server that enables AI assistants (Claude, Codex, Gemini) to send notifications via 20+ channels including DingTalk, Lark, Telegram, and WeCom.

**mcp-push** 是一个标准的 MCP (Model Context Protocol) 服务器，支持 AI 助手（Claude、Codex、Gemini）通过钉钉、飞书、Telegram、企业微信等 20+ 个渠道发送标准化的通知。

---

## ✨ Features / 核心特性

- **🔌 Standardized Interface / 标准化接口**
  Native MCP support for seamless integration with AI agents.
  原生支持 MCP 协议，与 AI 助手无缝集成，开箱即用。

- **📢 Multi-Channel / 多渠道支持**
  Support for 20+ mainstream notification services (DingTalk, Lark, WeCom, Telegram, Gotify, etc.).
  支持 20+ 主流通知服务（钉钉、飞书、企业微信、Telegram、Server酱等）。

- **📨 Dual Push Modes / 双模式推送**
  - `notify_send`: Simple alerts for one-time notifications. (简单消息推送)
  - `notify_event`: Structured event streams for task lifecycle tracking. (结构化事件流)

- **⚡ Concurrent Delivery / 并发推送**
  Automatically broadcast messages to all configured channels simultaneously.
  自动向所有已配置渠道并发发送消息，确保通知必达。

---

## 🚀 Installation / 安装

We recommend using **`uvx`** to run the server directly. This handles dependencies automatically and isolates the environment.
推荐使用 **`uvx`** 直接运行，该方式会自动处理依赖并隔离环境，无需手动安装。

### Quick Start / 快速开始

Run the command corresponding to your MCP client:
根据您的客户端运行以下命令：

```bash
# For Codex
codex mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push

# For Claude Desktop
claude mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push

# For Gemini
gemini mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push
```

### Manual Installation / 手动安装

<details>
<summary>Click to expand manual steps / 点击展开手动安装步骤</summary>

If you prefer to manage dependencies yourself:
如果您通过源码安装：

```bash
git clone https://github.com/d4renk/mcp-push.git
cd mcp-push
pip install -r requirements.txt

# Register command (example for Claude)
claude mcp add mcp-push -- python3 $(pwd)/src/server.py
```
</details>

---

## ⚙️ Configuration / 配置

Configure channels via **Environment Variables**. You can create a `config.sh` or `.env` file to manage them.
通过 **环境变量** 配置通知渠道。建议创建一个 `config.sh` 文件来统一管理。

```bash
# Example config / 配置示例
export DD_BOT_TOKEN="your-dingtalk-token"    # DingTalk
export TG_BOT_TOKEN="your-telegram-token"    # Telegram
export TG_USER_ID="your-telegram-user-id"
```

### Supported Channels / 支持渠道概览

> 📚 **Full Guide / 详细配置文档**: [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md)

| Channel / 渠道 | Env Var / 环境变量 | Type / 类型 |
|:---|:---|:---|
| **DingTalk / 钉钉** | `DD_BOT_TOKEN` | Robot |
| **Lark / 飞书** | `FSKEY` | Webhook |
| **WeCom / 企业微信** | `QYWX_KEY` | Robot |
| **Telegram** | `TG_BOT_TOKEN` | Bot |
| **Bark** | `BARK_PUSH` | iOS App |
| **ServerChan / Server酱** | `PUSH_KEY` | Webhook |
| **Email / 邮件** | `SMTP_SERVER` | SMTP |
| **Gotify** | `GOTIFY_URL` | Self-hosted |

*And many more: PushDeer, PushPlus, Ntfy, Synology Chat, etc.*

---

## 🛠️ Usage / 使用

### 1. Simple Notification / 简单消息 (`notify_send`)

Best for one-time alerts, completion notices, or user confirmations.
适用于一次性通知、任务完成提醒或需要用户确认的场景。

```javascript
// Call from your AI Assistant
await use_mcp_tool("notify_send", {
    "title": "Build Success / 构建成功",
    "content": "The deployment to production has finished. / 生产环境部署已完成。"
});
```

### 2. Event Stream / 事件流 (`notify_event`)

Best for tracking long-running tasks with states (`start`, `update`, `end`, `error`).
适用于追踪长时间运行任务的状态，支持开始、更新、结束和错误状态。

```javascript
// Task Start
await use_mcp_tool("notify_event", {
    "run_id": "job-2024-001",
    "event": "start",
    "message": "Starting data analysis..."
});

// Task Complete
await use_mcp_tool("notify_event", {
    "run_id": "job-2024-001",
    "event": "end",
    "message": "Analysis complete. 500 records processed.",
    "data": { "count": 500, "status": "ok" }
});
```

---

## 📋 When to Notify / 推送时机

### ✅ Do Send / 务必推送

1. **Task Completion / 任务完成**: Long-running tasks (>60s) that succeed or fail
   长耗时任务（>60秒）执行结束（无论成功或失败）

2. **User Action Needed / 需要用户确认**: Paused workflows waiting for decisions or authorization
   流程暂停，等待用户决策或授权

### ❌ Don't Send / 避免推送

- Task start notifications (unless explicitly requested)
  任务启动通知（除非用户明确要求）

- Frequent intermediate updates (unless real-time monitoring is needed)
  频繁的中间过程更新（除非需要实时监控）

- Simple operation completions
  简单操作的完成通知

---

## 🔧 Testing / 测试

To verify your configuration:
验证配置是否正确：

```bash
python test_mcp_push.py
```

Response will show successful channels and any errors:
响应会显示成功的渠道和错误信息：

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

---

## 🤝 Contributing / 贡献

Issues and Pull Requests are welcome!
欢迎提交 Issue 和 Pull Request！

---

## 📜 License / 许可证

MIT License
