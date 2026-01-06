# mcp-push

Multi-channel notification server for AI agents (Claude, Codex, Gemini)
AI 智能体多渠道通知推送服务

[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Server-blue)](https://modelcontextprotocol.io)

Standard MCP server for sending notifications to 20+ channels: DingTalk, Lark, Telegram, WeCom, Email, etc.
标准 MCP 服务器，支持钉钉、飞书、Telegram、企业微信、邮件等 20+ 渠道推送。

## 📋 依赖要求 / Dependencies

### 必需依赖 / Required
- **Python 3.8+** - MCP 服务器运行环境 / MCP server runtime
- **pip** - Python 包管理器 / Python package manager
- **requests** - HTTP 请求库 / HTTP library (`pip install requests>=2.31.0`)

### 可选依赖 / Optional
- **jq** - 自动配置 Hook 设置 / Auto-configure Hook settings
  ```bash
  # macOS
  brew install jq

  # Ubuntu/Debian
  sudo apt-get install jq

  # CentOS/RHEL
  sudo yum install jq
  ```
- **curl** - 在线安装脚本 / Online installation
- **git** - 克隆仓库（本地安装）/ Clone repo (local install)

## 🚀 快速开始 / Quick Start

### 1️⃣ 安装 MCP 服务器 / Install MCP Server

```bash
codex mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push
```

### 2️⃣ 🤖 配置自动通知 / Setup Auto-Notification

安装 Claude Code Stop Hook，自动配置任务完成推送：
Install Claude Code Stop Hook - automatically configures task completion notifications:

```bash
# 在线一键安装 / Online one-click install
curl -fsSL https://raw.githubusercontent.com/d4renk/mcp-push/main/install-hook.sh | bash

# 或本地安装 / Or local install
git clone https://github.com/d4renk/mcp-push.git
cd mcp-push
bash install-hook.sh
```

脚本会自动完成：
The script automatically:
- ✅ 下载 Hook 脚本到 `~/.claude/hooks/` / Downloads Hook script
- ✅ 自动配置 `~/.claude/settings.json` / Auto-configures settings.json
- ✅ 设置正确的文件权限 / Sets correct permissions

> **提示 / Note**: 需要安装 `jq` 工具来自动配置。如果没有 jq，脚本会提示手动配置步骤。
> Requires `jq` for auto-config. Without jq, manual steps will be shown.

**Hook 功能 / Hook Features:**
- ✅ 自动检测长耗时任务（>60s）/ Auto-detect long-running tasks (>60s)
- 🔔 任务完成时自动推送 / Auto-notify on task completion
- ⚠️ 错误发生时立即通知 / Instant notification on errors
- 👤 需要用户确认时提醒 / Alert when user action needed

### 3️⃣ 配置通知渠道 / Configure Channels

编辑配置文件 / Edit configuration:

```bash
cp config.sh.example config.sh
vim config.sh
```

**示例配置 / Example Configuration:**

```bash
# 钉钉机器人 / DingTalk Bot
export DD_BOT_TOKEN="your-dingtalk-token"
export DD_BOT_SECRET="your-dingtalk-secret"

# 飞书机器人 / Lark Bot
export FSKEY="your-lark-webhook-key"

# Telegram Bot
export TG_BOT_TOKEN="your-telegram-bot-token"
export TG_USER_ID="your-telegram-user-id"

# 企业微信机器人 / WeCom Bot
export QYWX_KEY="your-wecom-webhook-key"

# Bark (iOS)
export BARK_PUSH="https://api.day.app/your-device-code"

# Server酱 / ServerChan
export PUSH_KEY="your-server-chan-key"
```

**完整渠道配置 / Full channel list:** [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md)

### 4️⃣ 测试推送 / Test Notification

```bash
# Python 测试 / Python test
python test_mcp_push.py

# 或通过 Hook 测试 / Or test via Hook
python ~/.claude/hooks/mcp-call.py mcp-push notify_send \
  --title "测试 / Test" \
  --content "Hello from mcp-push!"
```

## 📡 使用方法 / Usage

### notify_send - 简单消息 / Simple Alerts

适用于一次性通知、任务完成提醒
For one-time alerts and task completion notices

```javascript
use_mcp_tool("notify_send", {
  "title": "构建成功 / Build Success",
  "content": "部署完成，耗时 3m42s / Deployment completed in 3m42s"
});
```

**Python 示例 / Python Example:**

```python
await mcp.call_tool("notify_send", {
  "title": "✅ 数据分析完成",
  "content": "共处理 10,000 条记录\n发现 127 个异常\n报告: https://..."
})
```

### notify_event - 事件追踪 / Task Tracking

适用于追踪长时间运行任务的状态
For tracking long-running task states

```javascript
use_mcp_tool("notify_event", {
  "run_id": "data-analysis-001",
  "event": "end",  // start | update | end | error
  "message": "分析完成，发现 127 个异常 / Analysis complete, 127 anomalies found",
  "data": {
    "total_records": 10000,
    "anomalies": 127,
    "duration_ms": 222000
  }
});
```

**事件类型 / Event Types:**
- `start` - 任务开始 / Task started
- `update` - 进度更新 / Progress update
- `end` - 任务完成 / Task completed
- `error` - 任务失败 / Task failed

## 🔧 支持的推送渠道 / Supported Channels

| 渠道 / Channel | 配置变量 / Config | 文档 / Docs |
|------|---------|------|
| 钉钉机器人 / DingTalk | `DD_BOT_TOKEN`, `DD_BOT_SECRET` | [官方文档](https://developers.dingtalk.com/document/app/custom-robot-access) |
| 飞书机器人 / Lark | `FSKEY` | [官方文档](https://www.feishu.cn/hc/zh-CN/articles/360024984973) |
| Telegram Bot | `TG_BOT_TOKEN`, `TG_USER_ID` | [官方文档](https://core.telegram.org/bots) |
| 企业微信机器人 / WeCom | `QYWX_KEY` | [官方文档](https://work.weixin.qq.com/api/doc/90000/90136/91770) |
| Bark (iOS) | `BARK_PUSH` | [官方网站](https://bark.day.app) |
| Server酱 / ServerChan | `PUSH_KEY` | [官方网站](https://sct.ftqq.com) |
| PushPlus | `PUSH_PLUS_TOKEN` | [官方网站](http://www.pushplus.plus) |
| Gotify | `GOTIFY_URL`, `GOTIFY_TOKEN` | [官方网站](https://gotify.net) |
| Ntfy | `NTFY_URL`, `NTFY_TOPIC` | [官方网站](https://ntfy.sh) |
| WxPusher | `WXPUSHER_APP_TOKEN` | [官方网站](https://wxpusher.zjiecode.com) |
| Email (SMTP) | `SMTP_SERVER`, `SMTP_EMAIL` | - |

**20+ 渠道完整配置 / Full 20+ channels:** [config.sh.example](config.sh.example)

## 📚 进阶配置 / Advanced Configuration

### 环境变量加载 / Environment Loading

配置加载优先级（从高到低）/ Priority order (high to low):

1. 环境变量 / Environment variables: `export VAR=value`
2. 当前目录配置 / Current directory: `./config.sh`
3. 项目目录配置 / Project directory: `<project>/config.sh`
4. Shell 环境自动加载 / Auto-load from shell

禁用自动加载 / Disable auto-load:
```bash
export MCP_PUSH_SHELL_ENV=0
```

### 自定义 Webhook / Custom Webhook

```bash
export WEBHOOK_URL="https://your-webhook.com/notify"
export WEBHOOK_METHOD="POST"
export WEBHOOK_CONTENT_TYPE="application/json"
export WEBHOOK_BODY='{"title": "$title", "content": "$content"}'
export WEBHOOK_HEADERS='Content-Type: application/json'
```

### 调试模式 / Debug Mode

```bash
export MCP_PUSH_DEBUG=1
export MCP_PUSH_DEBUG_PATH="/tmp/mcp-push.debug.log"

# 启动服务 / Start server
python src/server.py
```

## 📁 项目结构 / Project Structure

```
mcp-push/
├── src/
│   ├── server.py              # MCP 服务器实现 / MCP server implementation
│   ├── notify.py              # 推送渠道实现 / Channel implementations
│   └── __init__.py
├── docs/
│   └── CHANNEL_CONFIG.md      # 渠道配置详细说明 / Detailed channel config
├── examples/
│   └── claude-code-hook-example.json
├── scripts/                   # 工具脚本 / Utility scripts
├── completion-hook-linux.sh   # Stop Hook 脚本 / Stop Hook script
├── install-hook.sh            # Hook 自动安装 / Hook auto-installer
├── mcp-call.py               # MCP 调用工具 / MCP call utility
├── config.sh.example         # 配置示例 / Config template
├── requirements.txt          # Python 依赖 / Dependencies
└── README.md                 # 本文件 / This file
```

## 🛠️ 开发 / Development

### 运行测试 / Run Tests

```bash
# 单元测试 / Unit tests
python test_mcp_push.py

# Hook 集成测试 / Hook integration test
python test-hook-integration.py

# 手动 MCP 调用 / Manual MCP call
python mcp-call.py
```

### 添加新渠道 / Add New Channel

1. 在 `src/notify.py` 中实现推送函数 / Implement function in `src/notify.py`
2. 在 `add_notify_function()` 中注册 / Register in `add_notify_function()`
3. 在 `config.sh.example` 中添加配置示例 / Add config example
4. 更新文档 / Update documentation

## 🤝 贡献 / Contributing

欢迎提交 Issue 和 Pull Request！
Issues and Pull Requests are welcome!

1. Fork 本仓库 / Fork the repository
2. 创建特性分支 / Create feature branch: `git checkout -b feature/AmazingFeature`
3. 提交更改 / Commit changes: `git commit -m 'Add AmazingFeature'`
4. 推送到分支 / Push to branch: `git push origin feature/AmazingFeature`
5. 开启 Pull Request / Open Pull Request

## 📄 许可证 / License

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件
This project is licensed under the MIT License - see [LICENSE](LICENSE)

## 🙏 致谢 / Acknowledgments

- Built on [Model Context Protocol](https://modelcontextprotocol.io)
- Inspired by multiple open-source notification projects
- Thanks to all contributors

## 📞 联系 / Contact

- Issues: https://github.com/d4renk/mcp-push/issues
- Repository: https://github.com/d4renk/mcp-push

---

⭐ **If this project helps you, please give it a star!**
⭐ **如果这个项目对您有帮助，请给个 Star 支持一下！**
