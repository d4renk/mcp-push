# mcp-push

> Multi-channel notification server for AI agents (Claude, Codex, Gemini)
> AI 智能体多渠道通知推送服务

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/) [![MCP](https://img.shields.io/badge/MCP-Standard-orange.svg)](https://modelcontextprotocol.io/)

Standard MCP server for sending notifications to 20+ channels: DingTalk, Lark, Telegram, WeCom, Email, etc.
标准 MCP 服务器，支持钉钉、飞书、Telegram、企业微信、邮件等 20+ 渠道推送。

---

## 🚀 Quick Start

```bash
# Install MCP server
codex mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push

# Configure channels (example)
export DD_BOT_TOKEN="your-dingtalk-token"
export TG_BOT_TOKEN="your-telegram-token"

# Test
python test_mcp_push.py
```

**Supported channels**: [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md)

---

## 📡 Usage

### notify_send - Simple alerts
```javascript
use_mcp_tool("notify_send", {
  "title": "Build Success",
  "content": "Deployment completed"
});
```

### notify_event - Task tracking
```javascript
use_mcp_tool("notify_event", {
  "run_id": "job-001",
  "event": "end",  // start|update|end|error
  "message": "Analysis complete",
  "data": {"count": 500}
});
```

---

## 🤖 Auto-Notification (Optional)

Auto-push for long tasks (>60s) without manual calls.
自动推送长耗时任务（>60秒），无需手动调用。

```bash
# One-line install
curl -fsSL https://raw.githubusercontent.com/d4renk/mcp-push/main/install-hook.sh | bash
```

**How it works**: Claude Code Stop Hook detects task completion → auto-push.
**工作原理**：Claude Code Stop Hook 检测任务结束 → 自动推送。

**Notification rules**:
- Task < 60s: No push
- Task > 60s (success/failure): Push notification + event
- User action needed: Push notification only

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for details.

---

## ⚙️ Configuration

**Environment variables**:
```bash
# DingTalk
export DD_BOT_TOKEN="xxx"

# Telegram
export TG_BOT_TOKEN="xxx"
export TG_USER_ID="xxx"

# Lark
export FSKEY="xxx"

# Email
export SMTP_SERVER="smtp.gmail.com"
export SMTP_USER="user@gmail.com"
export SMTP_PASSWORD="xxx"
export SMTP_TO="receiver@example.com"
```

Full list: [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md)

---

## 📚 Documentation

- [Channel Configuration](docs/CHANNEL_CONFIG.md) - All 20+ channels setup
- [Integration Guide](INTEGRATION_GUIDE.md) - Auto-notification setup
- [Claude Code Hooks Guide](Claude%20Code%20Hooks%20完整指南.md) - Hook usage (中文)

---

## 🤝 Contributing

Issues and PRs welcome!

## 📜 License

MIT License
