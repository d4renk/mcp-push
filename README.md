# mcp-push

**Unified Notification Gateway for AI Agents**
**AI 智能体统一通知推送服务**

[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Server-blue)](https://modelcontextprotocol.io)

**mcp-push** is a standard MCP server and hook utility designed to bridge AI Agents (like Claude Code, Cursor) with your daily communication tools. It supports sending notifications to **20+ channels** including DingTalk, Lark, Telegram, WeCom, and Email.
**mcp-push** 是一个标准的 MCP 服务器和 Hook 工具，旨在连接 AI 智能体（如 Claude Code, Cursor）与您的日常通讯工具。支持向钉钉、飞书、Telegram、企业微信、邮件等 **20+ 个渠道**发送通知。

---

## ✨ Key Features / 核心特性

- **🔌 20+ Channels / 全渠道支持**: DingTalk, Lark, WeCom, Telegram, Email, Bark, ServerChan, and more.
- **🤖 Zero-Config Hook / 零配置 Hook**: Automatically detects long-running tasks (>60s) in Claude Code and notifies you upon completion or failure.
- **📊 Structured Events / 结构化事件**: Supports structured JSON logging (`notify_event`) for detailed task tracking.
- **🚀 Easy Setup / 极简安装**: Install via `uvx` or one-line shell script.

---

## 🚀 Quick Start / 快速开始

### 1️⃣ Install MCP Server / 安装 MCP 服务器

Using `uvx` (Recommended):
使用 `uvx` 安装（推荐）：

```bash
codex mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push
```

### 2️⃣ Configure Auto-Notify Hook / 配置自动通知 Hook

Automatically receive alerts when long tasks finish.
在长耗时任务完成时自动接收通知。

```bash
# One-click install / 一键安装
curl -fsSL https://raw.githubusercontent.com/d4renk/mcp-push/main/install-hook.sh | bash
```

> **Note**: Requires `jq` for auto-configuration.
> **注意**: 需要安装 `jq` 工具以进行自动配置。

### 3️⃣ Setup Channels / 配置推送渠道

Create a `config.sh` file to define your webhook credentials.
创建 `config.sh` 文件定义您的 Webhook 凭证。

```bash
cp config.sh.example config.sh
vim config.sh
```

**Minimal Config Example / 最小配置示例:**

```bash
# DingTalk / 钉钉
export DD_BOT_TOKEN="your-token"
export DD_BOT_SECRET="your-secret"

# Lark / 飞书
export FSKEY="your-webhook-key"

# Telegram
export TG_BOT_TOKEN="your-bot-token"
export TG_USER_ID="your-user-id"
```

*See [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md) for all supported channels.*

---

## 📡 Usage / 使用指南

### 1. Simple Notification / 简单通知 (`notify_send`)
Best for general alerts or one-time messages.
适用于通用提醒或一次性消息。

```javascript
// MCP Tool Call
use_mcp_tool("notify_send", {
  "title": "🚀 Build Success / 构建成功",
  "content": "Deployment finished in 3m 20s. / 部署耗时 3分20秒"
});
```

### 2. Event Tracking / 事件追踪 (`notify_event`)
Best for structured logs and task lifecycle tracking (Start -> Update -> End).
适用于结构化日志和任务生命周期追踪。

```javascript
// MCP Tool Call
use_mcp_tool("notify_event", {
  "run_id": "task-2024-001",
  "event": "end",  // Options: start | update | end | error
  "message": "Analysis completed / 分析完成",
  "data": {
    "files_processed": 150,
    "errors_found": 0
  }
});
```

---

## 🔌 Supported Channels / 支持渠道

| Service / 服务 | Config Variable / 配置变量 | Docs / 文档 |
| :--- | :--- | :--- |
| **DingTalk (钉钉)** | `DD_BOT_TOKEN`, `DD_BOT_SECRET` | [Official](https://developers.dingtalk.com/document/app/custom-robot-access) |
| **Lark (飞书)** | `FSKEY` | [Official](https://www.feishu.cn/hc/zh-CN/articles/360024984973) |
| **WeCom (企微)** | `QYWX_KEY` | [Official](https://work.weixin.qq.com/api/doc/90000/90136/91770) |
| **Telegram** | `TG_BOT_TOKEN`, `TG_USER_ID` | [Official](https://core.telegram.org/bots) |
| **Bark (iOS)** | `BARK_PUSH` | [Official](https://bark.day.app) |
| **ServerChan (Server酱)** | `PUSH_KEY` | [Official](https://sct.ftqq.com) |
| **Email** | `SMTP_SERVER`, `SMTP_USER`... | - |
| **Custom Webhook** | `WEBHOOK_URL` | - |

*Full list available in [config.sh.example](config.sh.example).*

---

## ⚙️ Advanced Configuration / 进阶配置

### Hook Behavior / Hook 行为控制

Customize how the Hook interacts with the MCP server via `config.sh`:

```bash
# Enable structured event notifications (Default: true)
# 启用结构化事件推送（默认开启，失败自动降级为简单通知）
export MCP_PUSH_STRUCTURED=true

# MCP Call Timeout (Default: 10s)
# MCP 调用超时时间（防止阻塞主进程）
export MCP_PUSH_TIMEOUT_SEC=10

# Error Log Path
# 错误日志路径
export MCP_PUSH_HOOK_LOG_PATH="/tmp/mcp-push-hook.log"
```

### Environment Loading / 环境变量加载
Configuration is loaded in the following order (higher priority overrides lower):
配置加载顺序（高优先级覆盖低优先级）：
1.  **System Env** (`export VAR=...`)
2.  **Local Config** (`./config.sh`)
3.  **Project Config** (`/path/to/mcp-push/config.sh`)

---

## 🛠️ Development / 开发与贡献

```bash
# Install dependencies / 安装依赖
pip install -r requirements.txt

# Run tests / 运行测试
python test_mcp_push.py

# Test Hook integration / 测试 Hook 集成
python test-hook-integration.py
```

### Contributing
Pull Requests are welcome! Please ensure you add relevant tests for new channels.
欢迎提交 PR！添加新渠道时请确保包含相关测试。

## 📄 License
MIT License. See [LICENSE](LICENSE) for details.
