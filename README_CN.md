# mcp-push

**AI 智能体统一通知推送服务**

[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Server-blue)](https://modelcontextprotocol.io)

> 中文 | [English](README.md)

**mcp-push** 是一个标准的 MCP 服务器和 Hook 工具，旨在连接 AI 智能体（如 Claude Code, Cursor）与您的日常通讯工具。支持向钉钉、飞书、Telegram、企业微信、邮件等 **20+ 个渠道**发送通知。

---

## ✨ 核心特性

- **🔌 全渠道支持**: 钉钉、飞书、企业微信、Telegram、Email、Bark、Server酱等 20+ 渠道
- **🤖 零配置 Hook**: 自动检测 Claude Code 中的长耗时任务（>60s），完成或失败时自动通知
- **📊 结构化事件**: 支持结构化 JSON 日志记录（`notify_event`），用于详细任务追踪
- **🚀 极简安装**: 通过 `uvx` 或一行 shell 脚本即可安装

---

## 🚀 快速开始

### 1️⃣ 安装 MCP 服务器

使用 `uvx` 安装（推荐）：

```bash
codex mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push
```

### 2️⃣ 配置自动通知 Hook

在长耗时任务完成时自动接收通知。

```bash
# 一键安装
curl -fsSL https://raw.githubusercontent.com/d4renk/mcp-push/main/install-hook.sh | bash
```

> **注意**: 需要安装 `jq` 工具以进行自动配置。

### 3️⃣ 配置推送渠道

创建 `config.sh` 文件定义您的 Webhook 凭证。

```bash
cp config.sh.example config.sh
vim config.sh
```

**最小配置示例:**

```bash
# 钉钉
export DD_BOT_TOKEN="your-token"
export DD_BOT_SECRET="your-secret"

# 飞书
export FSKEY="your-webhook-key"

# Telegram
export TG_BOT_TOKEN="your-bot-token"
export TG_USER_ID="your-user-id"
```

*完整渠道列表请参考 [docs/CHANNEL_CONFIG.md](docs/CHANNEL_CONFIG.md)*

---

## 📡 使用指南

### 1. 简单通知 (`notify_send`)
适用于通用提醒或一次性消息。

```javascript
// MCP 工具调用
use_mcp_tool("notify_send", {
  "title": "🚀 构建成功",
  "content": "部署耗时 3分20秒"
});
```

### 2. 事件追踪 (`notify_event`)
适用于结构化日志和任务生命周期追踪（开始 -> 更新 -> 结束）。

```javascript
// MCP 工具调用
use_mcp_tool("notify_event", {
  "run_id": "task-2024-001",
  "event": "end",  // 选项: start | update | end | error
  "message": "分析完成",
  "data": {
    "files_processed": 150,
    "errors_found": 0
  }
});
```

---

## 🔌 支持渠道

| 服务 | 配置变量 | 文档 |
| :--- | :--- | :--- |
| **钉钉** | `DD_BOT_TOKEN`, `DD_BOT_SECRET` | [官方文档](https://developers.dingtalk.com/document/app/custom-robot-access) |
| **飞书** | `FSKEY` | [官方文档](https://www.feishu.cn/hc/zh-CN/articles/360024984973) |
| **企业微信** | `QYWX_KEY` | [官方文档](https://work.weixin.qq.com/api/doc/90000/90136/91770) |
| **Telegram** | `TG_BOT_TOKEN`, `TG_USER_ID` | [官方文档](https://core.telegram.org/bots) |
| **Bark (iOS)** | `BARK_PUSH` | [官方网站](https://bark.day.app) |
| **Server酱** | `PUSH_KEY` | [官方网站](https://sct.ftqq.com) |
| **Email** | `SMTP_SERVER`, `SMTP_USER`... | - |
| **自定义 Webhook** | `WEBHOOK_URL` | - |

*完整列表请参考 [config.sh.example](config.sh.example)*

---

## ⚙️ 进阶配置

### Hook 行为控制

通过 `config.sh` 自定义 Hook 与 MCP 服务器的交互方式：

```bash
# 启用结构化事件推送（默认开启，失败自动降级为简单通知）
export MCP_PUSH_STRUCTURED=true

# MCP 调用超时时间（默认 10 秒，防止阻塞主进程）
export MCP_PUSH_TIMEOUT_SEC=10

# 错误日志路径
export MCP_PUSH_HOOK_LOG_PATH="/tmp/mcp-push-hook.log"
```

### 环境变量加载

配置加载顺序（高优先级覆盖低优先级）：
1.  **系统环境变量** (`export VAR=...`)
2.  **本地配置** (`./config.sh`)
3.  **项目配置** (`/path/to/mcp-push/config.sh`)

---

## 🛠️ 开发与贡献

```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
python test_mcp_push.py

# 测试 Hook 集成
python test-hook-integration.py
```

### 贡献指南
欢迎提交 PR！添加新渠道时请确保包含相关测试。

---

## 🗑️ 卸载

```bash
# 卸载 Hook
curl -fsSL https://raw.githubusercontent.com/d4renk/mcp-push/main/uninstall-hook.sh | bash

# 卸载 MCP 服务器
codex mcp remove mcp-push
```

---

## 📄 许可证
MIT 许可证。详见 [LICENSE](LICENSE) 文件。
