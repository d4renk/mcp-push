# mcp-push

**Agent 执行结果 → 实时推送到外部系统的标准化 MCP 桥接**

将 AI Agent 的执行过程和结果，通过事件流实时推送到 20+ 通知渠道（钉钉、飞书、Telegram、企业微信、邮件等）。可作为工作流编排、异步任务系统和通知平台的桥梁。

## 核心特性

- **MCP 标准化接口**：符合 Model Context Protocol 规范的工具集成
- **混合架构设计**：TypeScript 协议层 + Python 通知实现层，Unix socket 通信
- **事件流架构**：支持 `start|update|end|error` 四种事件类型
- **多渠道并发**：20+ 通知渠道并行推送，最佳努力交付
- **企业级安全**：帧大小限制、Socket 权限控制、超时管理
- **零侵入集成**：保留原有 API，向后完全兼容

---

## 安装与配置

### 1. 环境准备

- **Node.js**: 需要 Node.js 16+ 版本（TypeScript 协议层）
- **Python**: 需要 Python 3.8+ 版本（通知实现层）
- **Claude Desktop**: 确保已安装并登录 Claude Desktop 应用

### 2. 获取代码

```bash
git clone https://github.com/d4renk/mcp-push.git
cd mcp-push
```

### 3. 安装依赖与构建

```bash
# 安装 TypeScript 依赖并构建
npm install
npm run build

# 安装 Python 依赖
pip install -r tools/pytools/requirements.txt
```

### 4. 注册 MCP 工具

使用 Claude CLI 将 mcp-push 注册到 Claude Desktop：

```bash
claude mcp add mcp-push -s user --transport stdio -- node $(pwd)/apps/mcp-server/build/index.js
```

或直接编辑 Claude Desktop 配置文件（`~/Library/Application Support/Claude/claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "mcp-push": {
      "command": "node",
      "args": ["/path/to/mcp-push/apps/mcp-server/build/index.js"]
    }
  }
}
```

### 5. 配置通知渠道

复制配置模板并编辑：

```bash
cp config.sh.example config.sh
# 使用文本编辑器打开 config.sh 填入你的通知渠道 Token/Secret
nano config.sh 
```

> `config.sh` 中的变量会被自动加载。你也可以直接将环境变量添加到 `~/.bashrc` 或 `.zshrc` 中。

### 6. 验证安装

```bash
claude mcp list
```

看到 `mcp-push: ... - ✓ Connected` 说明安装成功。

你也可以运行集成测试脚本来验证通信是否正常：

```bash
python3 test_integration.py
```

---

<details>
<summary><strong>🤖 MCP Agent 集成指南 (Core Instruction) - 点击展开</strong></summary>

```markdown
本章节是 **mcp-push** 的核心使用指南，专为 Agent 和 MCP 客户端设计。

### 调用时机与策略

**仅在以下两种情况下触发推送：**

1. **任务完成 (Task Finished)**：当长耗时任务执行结束（无论成功或失败）时。
2. **需要用户确认 (User Action Needed)**：当流程暂停，等待用户决策或授权时。

> **注意**：禁止在任务启动 (`start`) 或中间过程 (`update`) 频繁推送，以免打扰用户，除非用户明确要求追踪进度。

### 可用工具详解

#### 1. `notify.send` - 简单消息推送

**用途**：发送一次性通知，用于“任务完成”或“请求确认”。

**参数**：
- `title` (string, 必选): 消息标题（如 `✅ 部署完成` 或 `⚠️ 等待批准`）
- `content` (string, 必选): 消息内容（支持换行符 `\n`）

**调用示例**：

```python
# 场景 1: 任务完成
await mcp_client.call_tool("notify.send", {
  "title": "任务完成",
  "content": "数据分析已完成，共处理 10000 条记录"
})

# 场景 2: 需要用户确认
await mcp_client.call_tool("notify.send", {
  "title": "等待批准",
  "content": "检测到敏感文件删除操作，请确认是否继续？"
})
```

#### 2. `notify.event` - 结构化事件推送

**用途**：发送任务的最终状态（`end` 或 `error`）。除非用户明确要求实时监控，否则**不要**发送 `start` 或 `update` 事件。

**参数**：
- `run_id` (string, 必选): 任务唯一标识符
- `event` (string, 必选): 事件类型，**通常仅使用 `end` 或 `error`**
- `message` (string, 必选): 状态描述
- `data` (object, 可选): 附加数据（step, progress, artifact_url 等）

**调用示例**：

**任务完成 (End)**

```python
await mcp_client.call_tool("notify.event", {
  "run_id": "data-analysis-20240101-001",
  "event": "end",
  "message": "分析完成，共发现 127 个异常事件",
  "data": {
    "progress": 1.0,
    "artifact_url": "https://example.com/reports/20240101-001.html"
  }
})
```

**任务失败 (Error)**

```python
await mcp_client.call_tool("notify.event", {
  "run_id": "data-analysis-20240101-001",
  "event": "error",
  "message": "任务失败：连接数据库超时",
  "data": {
    "error_code": "DB_TIMEOUT"
  }
})
```

### 调用规范与注意事项

1. **最小打扰原则**：默认不通知过程，只通知结果。
2. **错误处理**：推送是异步的最佳努力交付，单个渠道失败不影响其他渠道。
```

</details>

---

<details>
<summary><strong>📢 支持的通知渠道 (20+) - 点击展开</strong></summary>

只需配置相应渠道的环境变量即可自动启用。

| 渠道类型 | 环境变量 | 文档 |
| :--- | :--- | :--- |
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

</details>

## 配置示例

**最小配置（仅钉钉）**

```bash
export DD_BOT_TOKEN="your-token"
export DD_BOT_SECRET="your-secret"
```

**多渠道配置**

```bash
# 钉钉
export DD_BOT_TOKEN="token"
export DD_BOT_SECRET="secret"

# Telegram
export TG_BOT_TOKEN="123456:ABC-DEF"
export TG_USER_ID="987654321"

# 邮件
export SMTP_SERVER="smtp.example.com:465"
export SMTP_SSL="true"
export SMTP_EMAIL="notify@example.com"
export SMTP_PASSWORD="password"
```

**通用配置**

- `HITOKOTO`: 是否附加一言随机句子（默认 `true`，设为 `false` 关闭）
- `SKIP_PUSH_TITLE`: 跳过推送的标题列表（换行分隔）

## 文档索引

- [架构设计](docs/ARCHITECTURE.md) - TypeScript + Python 混合架构详解
- [MCP 集成架构](docs/MCP_INTEGRATION.md) - 技术实现细节
- [使用示例](docs/USAGE_EXAMPLES.md) - 更多实战案例
- [渠道配置指南](docs/CHANNEL_CONFIG.md) - 完整环境变量说明
- [迁移指南](docs/MIGRATION.md) - 从库模式迁移到 MCP 工具

## 开发指南

**项目结构**

```
mcp-push/
├── apps/mcp-server/           # TypeScript MCP 服务器
│   ├── src/
│   │   ├── index.ts          # 入口点
│   │   ├── server.ts         # MCP 工具注册
│   │   └── bridge/
│   │       └── pythonProc.ts # Unix socket 桥接
│   ├── package.json
│   └── tsconfig.json
├── tools/pytools/             # Python 通知工作进程
│   └── src/pytools/
│       ├── worker.py         # Unix socket 服务器
│       ├── dispatcher.py     # 工具路由
│       └── notify_lib.py     # 通知渠道封装
├── start_worker.py            # Worker 启动器
├── test_integration.py        # 集成测试
└── package.json               # Monorepo 根配置
```

**本地开发**

```bash
# 监听模式（TypeScript 自动重编译）
npm run dev

# 运行集成测试
python3 test_integration.py

# 重新构建
npm run build
```

## 许可证

MIT License

---

## 架构设计

**工作原理**

```
┌─────────────┐      ┌──────────────────┐      ┌──────────────┐      ┌────────────────┐
│  AI Agent   │─────▶│  TypeScript MCP  │─────▶│   Python     │─────▶│  Notification  │
│  (任务执行)  │ stdio│   Server Layer   │socket│   Worker     │ HTTP │  Channels (20+)│
└─────────────┘      └──────────────────┘      └──────────────┘      └────────────────┘
                             │                         │                      │
                             │                         │                      ├─────▶ 钉钉机器人
                    MCP Protocol              Unix Socket IPC                 ├─────▶ Telegram Bot
                    Tool Registration         Content-Length                  ├─────▶ SMTP 邮件
                    Zod Validation            Framing (JSON-RPC)              └─────▶ ... (并发推送)
```

**关键技术栈**

- **协议层** (`apps/mcp-server/`): TypeScript + @modelcontextprotocol/sdk + Zod
- **实现层** (`tools/pytools/`): Python 3.8+ + requests
- **通信机制**: Unix Domain Socket (`/tmp/mcp-push-{PID}.sock`)
- **消息格式**: Content-Length 帧封装的 JSON-RPC

**安全特性**

- Socket 权限限制为 0600（仅所有者可访问）
- 最大帧大小 10 MB 防止内存耗尽攻击
- 分段读取处理防止协议失步
- 超时管理防止内存泄漏
- 异常恢复机制防止服务崩溃
