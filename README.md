# mcp-push

> 🔔 通用 MCP 推送服务 - 为 Claude Code、Gemini、Codex 等 AI Agent 提供统一的消息推送能力

[![MCP](https://img.shields.io/badge/MCP-Server-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.8+-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## 📖 简介

mcp-push 是一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 的推送通知服务，旨在为 AI Agent（如 Claude Code、Gemini、Codex）提供标准化的消息推送能力。支持 20+ 推送渠道，让您在 AI 完成任务或需要确认时及时收到通知。

### 核心特性

- 🌐 **多渠道支持**: 支持 20+ 推送渠道（钉钉、飞书、Telegram、企业微信、Bark、Server酱等）
- 🔌 **MCP 标准协议**: 完全兼容 MCP 协议，可被任何支持 MCP 的 AI Agent 调用
- 🎯 **智能推送规则**: 仅在任务完成或需要用户确认时推送，避免打扰
- 🛡️ **线程安全**: 支持多渠道并发推送，确保消息可达
- ⚙️ **灵活配置**: 支持环境变量、配置文件多种配置方式
- 🔄 **事件流支持**: 提供结构化事件推送，支持进度追踪

## 📦 安装

### 前置要求

- Python 3.8+
- pip

### 快速安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/mcp-push.git
cd mcp-push

# 安装依赖
pip install -r requirements.txt
```

## 🚀 快速开始

### 1. 配置推送渠道

复制配置示例文件并编辑：

```bash
cp config.sh.example config.sh
```

在 `config.sh` 中配置您需要的推送渠道（至少配置一个）：

```bash
# 钉钉机器人
export DD_BOT_TOKEN="your_token"
export DD_BOT_SECRET="your_secret"

# 飞书机器人
export FSKEY="your_fskey"

# Telegram Bot
export TG_BOT_TOKEN="your_bot_token"
export TG_USER_ID="your_user_id"

# 更多渠道配置请参考 config.sh.example
```

### 2. 配置 MCP 客户端

在您的 AI Agent 配置中添加 mcp-push 服务器：

**Claude Code 配置** (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "mcp-push": {
      "command": "python",
      "args": ["/path/to/mcp-push/src/server.py"],
      "env": {
        "MCP_PUSH_DEBUG": "0"
      }
    }
  }
}
```

**Gemini 配置** (类似配置):

```json
{
  "mcpServers": {
    "mcp-push": {
      "command": "python",
      "args": ["/path/to/mcp-push/src/server.py"]
    }
  }
}
```

### 3. 测试推送

启动 MCP 服务器后，可以通过以下方式测试：

```bash
# 使用 mcp-call.py 测试
python mcp-call.py
```

或在 Claude Code 中直接调用：

```python
# 简单消息推送
await mcp.call_tool("notify_send", {
  "title": "测试通知",
  "content": "这是一条测试消息"
})

# 结构化事件推送
await mcp.call_tool("notify_event", {
  "run_id": "test-001",
  "event": "end",
  "message": "测试任务已完成"
})
```

## 📚 使用指南

### MCP 工具

mcp-push 提供两个核心 MCP 工具：

#### 1. notify_send - 简单消息推送

**用途**: 发送一次性通知，适用于任务完成或请求确认场景。

**参数**:
- `title` (string, 必填): 消息标题
- `content` (string, 必填): 消息内容
- `ignore_default_config` (boolean, 可选): 是否忽略默认配置

**示例**:

```python
# 任务完成通知
await mcp.call_tool("notify_send", {
  "title": "✅ 数据分析完成",
  "content": "共处理 10,000 条记录\n发现 127 个异常事件\n详情: https://example.com/report"
})

# 需要用户确认
await mcp.call_tool("notify_send", {
  "title": "⚠️ 等待批准",
  "content": "检测到敏感文件删除操作，请确认是否继续？"
})
```

#### 2. notify_event - 结构化事件推送

**用途**: 发送任务的结构化状态事件，支持进度追踪。

**参数**:
- `run_id` (string, 必填): 任务唯一标识
- `event` (string, 必填): 事件类型 (`start` | `update` | `end` | `error`)
- `message` (string, 必填): 状态描述
- `data` (object, 可选): 附加数据（如进度、链接等）
- `timestamp` (string, 可选): 时间戳（自动生成）

**示例**:

```python
# 任务完成
await mcp.call_tool("notify_event", {
  "run_id": "data-analysis-20240101-001",
  "event": "end",
  "message": "分析完成，共发现 127 个异常事件",
  "data": {
    "progress": 1.0,
    "artifact_url": "https://example.com/reports/001.html",
    "total_records": 10000,
    "anomalies": 127
  }
})

# 任务失败
await mcp.call_tool("notify_event", {
  "run_id": "data-analysis-20240101-002",
  "event": "error",
  "message": "任务失败：连接数据库超时",
  "data": {
    "error_code": "DB_TIMEOUT",
    "retry_count": 3
  }
})
```

### 推送规则建议

根据项目最佳实践，推荐以下推送规则：

**✅ 务必推送的场景**:
1. **任务完成** - 长耗时任务（预计 >60s）执行结束（成功或失败）
2. **需要用户确认** - 流程暂停，等待用户决策或授权

**❌ 不推送的场景**:
- 任务启动阶段（`start` 事件）
- 任务进行中的更新（`update` 事件）
- 短时间内即可完成的操作（<60s）

### Claude Code 集成示例

在 `~/.claude/CLAUDE.md` 中配置推送规范：

```markdown
**推送规范（mcp-push）**
- 仅两种情形必须推送：
  1) 任务完成（成功/失败均推送）
  2) 需要用户确认（流程暂停，等待决策/授权）
- 禁止在 start/update 阶段频繁推送，除非用户明确要求追踪进度
```

## 🔧 支持的推送渠道

| 渠道 | 配置变量 | 说明 |
|------|---------|------|
| 钉钉机器人 | `DD_BOT_TOKEN`, `DD_BOT_SECRET` | [官方文档](https://developers.dingtalk.com/document/app/custom-robot-access) |
| 飞书机器人 | `FSKEY` | [官方文档](https://www.feishu.cn/hc/zh-CN/articles/360024984973) |
| Telegram Bot | `TG_BOT_TOKEN`, `TG_USER_ID` | [官方文档](https://core.telegram.org/bots) |
| 企业微信机器人 | `QYWX_KEY` | [官方文档](https://work.weixin.qq.com/api/doc/90000/90136/91770) |
| 企业微信应用 | `QYWX_AM` | 格式: `corpid,corpsecret,touser,agentid[,media_id]` |
| Bark | `BARK_PUSH` | [官方文档](https://bark.day.app) |
| Server酱 | `PUSH_KEY` | [官方文档](https://sct.ftqq.com) |
| PushPlus | `PUSH_PLUS_TOKEN` | [官方文档](http://www.pushplus.plus) |
| PushDeer | `DEER_KEY` | [官方文档](https://www.pushdeer.com) |
| Gotify | `GOTIFY_URL`, `GOTIFY_TOKEN` | [官方文档](https://gotify.net) |
| Ntfy | `NTFY_URL`, `NTFY_TOPIC` | [官方文档](https://ntfy.sh) |
| WxPusher | `WXPUSHER_APP_TOKEN` | [官方文档](https://wxpusher.zjiecode.com/docs) |

完整配置选项请参考 [config.sh.example](config.sh.example)

## 📁 项目结构

```
mcp-push/
├── src/
│   ├── server.py          # MCP 服务器实现
│   ├── notify.py          # 推送渠道实现
│   └── __init__.py
├── scripts/               # 工具脚本
│   ├── completion-hook-runner.ts
│   └── agent-runner-integration.ts
├── examples/              # 示例配置
│   └── claude-code-hook-example.json
├── docs/                  # 文档目录
│   └── CHANNEL_CONFIG.md  # 渠道配置详细说明
├── config.sh.example      # 配置文件示例
├── requirements.txt       # Python 依赖
├── prompt.json            # MCP 提示词
└── README.md             # 本文件
```

## 🔍 高级用法

### 自定义推送渠道

如果内置渠道不满足需求，可以使用自定义 Webhook：

```bash
export WEBHOOK_URL="https://your-webhook.com/notify"
export WEBHOOK_METHOD="POST"
export WEBHOOK_CONTENT_TYPE="application/json"
export WEBHOOK_BODY='{"title": "$title", "content": "$content"}'
export WEBHOOK_HEADERS='Content-Type: application/json'
```

### 环境变量加载

mcp-push 支持多种配置加载方式（优先级从高到低）：

1. 环境变量 (`export VAR=value`)
2. 当前目录的 `config.sh`
3. 项目目录的 `config.sh`
4. Shell 环境变量（自动加载）

可通过设置 `MCP_PUSH_SHELL_ENV=0` 禁用自动加载 Shell 环境变量。

### 调试模式

启用调试模式以查看详细日志：

```bash
export MCP_PUSH_DEBUG=1
export MCP_PUSH_DEBUG_PATH="/tmp/mcp-push.debug.log"

python src/server.py
```

## 🛠️ 开发

### 运行测试

```bash
# 单元测试
python test_mcp_push.py

# Hook 集成测试
python test-hook-integration.py
```

### 手动测试 MCP 调用

```bash
python mcp-call.py
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 基于 [Model Context Protocol](https://modelcontextprotocol.io) 构建
- 推送渠道实现参考了多个开源项目
- 感谢所有贡献者的支持

## 📞 联系方式

如有问题或建议，欢迎：

- 提交 [Issue](https://github.com/yourusername/mcp-push/issues)
- 发送邮件至: your.email@example.com
- 访问项目主页: https://github.com/yourusername/mcp-push

---

⭐ 如果这个项目对您有帮助，请给个 Star 支持一下！
