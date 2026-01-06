# mcp-push

> Multi-channel notification server for AI agents (Claude, Codex, Gemini)
> AI 智能体多渠道通知推送服务

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/) [![MCP](https://img.shields.io/badge/MCP-Standard-orange.svg)](https://modelcontextprotocol.io/)

Standard MCP server for sending notifications to 20+ channels: DingTalk, Lark, Telegram, WeCom, Email, etc.
标准 MCP 服务器，支持钉钉、飞书、Telegram、企业微信、邮件等 20+ 渠道推送。

---

## 🚀 快速开始 / Quick Start

```bash
# 安装 MCP 服务器 / Install MCP server
codex mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push

# 配置通知渠道（示例）/ Configure channels (example)
export DD_BOT_TOKEN="your-dingtalk-token"      # 钉钉 / DingTalk
export TG_BOT_TOKEN="your-telegram-token"      # Telegram
export TG_USER_ID="your-telegram-user-id"

# 测试推送 / Test
python test_mcp_push.py
```

**支持的渠道 / Supported channels**: [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md)

---

## 📡 使用方法 / Usage

### notify_send - 简单消息 / Simple alerts
```javascript
// 适用于一次性通知、任务完成提醒
// For one-time alerts and task completion notices
use_mcp_tool("notify_send", {
  "title": "构建成功 / Build Success",
  "content": "部署完成 / Deployment completed"
});
```

### notify_event - 事件追踪 / Task tracking
```javascript
// 适用于追踪长时间运行任务的状态
// For tracking long-running task states
use_mcp_tool("notify_event", {
  "run_id": "job-001",
  "event": "end",  // start|update|end|error
  "message": "分析完成 / Analysis complete",
  "data": {"count": 500}
});
```

---

## 🤖 自动通知（可选）/ Auto-Notification (Optional)

自动推送长耗时任务（>60秒），无需手动调用。
Auto-push for long tasks (>60s) without manual calls.

### 一键安装 / One-line install
```bash
curl -fsSL https://raw.githubusercontent.com/d4renk/mcp-push/main/install-hook.sh | bash
```

### 手动安装 / Manual install
```bash
# 1. 安装 MCP 服务器（如果还没装）
#    Install MCP server (if not installed yet)
codex mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push

# 2. 克隆仓库 / Clone repository
git clone https://github.com/d4renk/mcp-push.git
cd mcp-push

# 3. 安装 Hook 脚本 / Install hook scripts
mkdir -p ~/.claude/hooks
cp completion-hook-linux.sh ~/.claude/hooks/  # Linux
# 或 macOS: cp completion-hook.sh ~/.claude/hooks/
cp mcp-call.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/completion-hook-linux.sh
chmod +x ~/.claude/hooks/mcp-call.py

# 4. 配置 Stop Hook / Configure Stop Hook
cat stop-hook-config.json >> ~/.claude/settings.json
```

### 工作原理 / How it works
Claude Code Stop Hook 检测任务结束 → 自动推送
Claude Code Stop Hook detects task completion → auto-push

### 推送规则 / Notification rules
- 任务 < 60秒 / Task < 60s: 不推送 / No push
- 任务 > 60秒（成功/失败）/ Task > 60s (success/failure): 推送通知 + 事件 / Push notification + event
- 需要用户确认 / User action needed: 仅推送通知 / Push notification only

详见 / See details: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)

---

## ⚙️ 配置 / Configuration

**环境变量 / Environment variables**:
```bash
# 钉钉 / DingTalk
export DD_BOT_TOKEN="xxx"

# Telegram
export TG_BOT_TOKEN="xxx"
export TG_USER_ID="xxx"

# 飞书 / Lark
export FSKEY="xxx"

# 企业微信 / WeCom
export QYWX_KEY="xxx"

# 邮件 / Email
export SMTP_SERVER="smtp.gmail.com"
export SMTP_USER="user@gmail.com"
export SMTP_PASSWORD="xxx"
export SMTP_TO="receiver@example.com"
```

完整列表 / Full list: [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md)

---

## 📚 文档 / Documentation

- [渠道配置 / Channel Configuration](docs/CHANNEL_CONFIG.md) - 全部 20+ 渠道配置 / All 20+ channels setup
- [集成指南 / Integration Guide](INTEGRATION_GUIDE.md) - 自动通知配置 / Auto-notification setup
- [Claude Code Hooks 完整指南](Claude%20Code%20Hooks%20完整指南.md) - Hook 用法详解（中文）

---

## 🤝 贡献 / Contributing

欢迎提交 Issue 和 PR！
Issues and PRs welcome!

## 📜 许可证 / License

MIT License
