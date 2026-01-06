# mcp-push

**Unified Notification Gateway for AI Agents**

[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Server-blue)](https://modelcontextprotocol.io)

> [中文文档](README_CN.md) | English

**mcp-push** is a standard MCP server and hook utility designed to bridge AI Agents (like Claude Code, Cursor) with your daily communication tools. It supports sending notifications to **20+ channels** including DingTalk, Lark, Telegram, WeCom, and Email.

---

## ✨ Key Features

- **🔌 20+ Channels**: DingTalk, Lark, WeCom, Telegram, Email, Bark, ServerChan, and more.
- **🤖 Zero-Config Hook**: Automatically detects long-running tasks (>60s) in Claude Code and notifies you upon completion or failure.
- **📊 Structured Events**: Supports structured JSON logging (`notify_event`) for detailed task tracking.
- **🚀 Easy Setup**: Install via `uvx` or one-line shell script.

---

## 🚀 Quick Start

### 1️⃣ Install MCP Server

Using `uvx` (Recommended):

```bash
codex mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push
```

### 2️⃣ Configure Auto-Notify Hook

Automatically receive alerts when long tasks finish.

```bash
# One-click install
curl -fsSL https://raw.githubusercontent.com/d4renk/mcp-push/main/install-hook.sh | bash
```

> **Note**: Requires `jq` for auto-configuration.

### 3️⃣ Setup Channels

Create a `config.sh` file to define your webhook credentials.

```bash
cp config.sh.example config.sh
vim config.sh
```

**Minimal Config Example:**

```bash
# DingTalk
export DD_BOT_TOKEN="your-token"
export DD_BOT_SECRET="your-secret"

# Lark
export FSKEY="your-webhook-key"

# Telegram
export TG_BOT_TOKEN="your-bot-token"
export TG_USER_ID="your-user-id"
```

*See [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md) for all supported channels.*

---

## 📡 Usage

### 1. Simple Notification (`notify_send`)
Best for general alerts or one-time messages.

```javascript
// MCP Tool Call
use_mcp_tool("notify_send", {
  "title": "🚀 Build Success",
  "content": "Deployment finished in 3m 20s."
});
```

### 2. Event Tracking (`notify_event`)
Best for structured logs and task lifecycle tracking (Start -> Update -> End).

```javascript
// MCP Tool Call
use_mcp_tool("notify_event", {
  "run_id": "task-2024-001",
  "event": "end",  // Options: start | update | end | error
  "message": "Analysis completed",
  "data": {
    "files_processed": 150,
    "errors_found": 0
  }
});
```

---

## 🔌 Supported Channels

| Service | Config Variable | Docs |
| :--- | :--- | :--- |
| **DingTalk** | `DD_BOT_TOKEN`, `DD_BOT_SECRET` | [Official](https://developers.dingtalk.com/document/app/custom-robot-access) |
| **Lark** | `FSKEY` | [Official](https://www.feishu.cn/hc/zh-CN/articles/360024984973) |
| **WeCom** | `QYWX_KEY` | [Official](https://work.weixin.qq.com/api/doc/90000/90136/91770) |
| **Telegram** | `TG_BOT_TOKEN`, `TG_USER_ID` | [Official](https://core.telegram.org/bots) |
| **Bark (iOS)** | `BARK_PUSH` | [Official](https://bark.day.app) |
| **ServerChan** | `PUSH_KEY` | [Official](https://sct.ftqq.com) |
| **Email** | `SMTP_SERVER`, `SMTP_USER`... | - |
| **Custom Webhook** | `WEBHOOK_URL` | - |

*Full list available in [config.sh.example](config.sh.example).*

---

## ⚙️ Advanced Configuration

### Hook Behavior

Customize how the Hook interacts with the MCP server via `config.sh`:

```bash
# Enable structured event notifications (Default: true)
export MCP_PUSH_STRUCTURED=true

# MCP Call Timeout (Default: 10s)
export MCP_PUSH_TIMEOUT_SEC=10

# Error Log Path
export MCP_PUSH_HOOK_LOG_PATH="/tmp/mcp-push-hook.log"
```

### Environment Loading
Configuration is loaded in the following order (higher priority overrides lower):
1.  **System Env** (`export VAR=...`)
2.  **Local Config** (`./config.sh`)
3.  **Project Config** (`/path/to/mcp-push/config.sh`)

---

## 🛠️ Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_mcp_push.py

# Test Hook integration
python test-hook-integration.py
```

### Contributing
Pull Requests are welcome! Please ensure you add relevant tests for new channels.

---

## 🗑️ Uninstall

```bash
# Remove Hook
curl -fsSL https://raw.githubusercontent.com/d4renk/mcp-push/main/uninstall-hook.sh | bash

# Remove MCP server
codex mcp remove mcp-push
```

---

## 📄 License
MIT License. See [LICENSE](LICENSE) for details.
