# mcp-push

MCP 通知桥接：将 Agent 结果推送到外部渠道 NOTE: DingTalk, Feishu, Telegram, WeCom, Email 等。

## 功能

- MCP 工具：`notify_send`、`notify_event`
- TypeScript 服务器 + Python Worker (Unix socket)
- 多渠道并行推送（尽最大努力）
- 环境变量配置即可使用

## 环境要求

- Node.js 16+
- Python 3.8+

## 安装

```bash
npm install
npm run build
pip install -r tools/pytools/requirements.txt
```

## 注册 MCP 服务器

Codex:

```bash
codex mcp add mcp-push -- node $(pwd)/apps/mcp-server/build/index.js
```

Claude:

```bash
claude mcp add mcp-push -- node $(pwd)/apps/mcp-server/build/index.js
```

Gemini:

```bash
gemini mcp add mcp-push -- node $(pwd)/apps/mcp-server/build/index.js
```

如果你的 CLI 版本需要显式传输参数，请在 `--` 前追加 `--transport stdio`。

Codex 通过 uvx 安装:

```bash
codex mcp add mcp-push --transport stdio -- uvx --from git+https://github.com/d4renk/mcp-push.git codexmcp
```

Claude 通过 uvx 安装:

```bash
claude mcp add mcp-push --transport stdio -- uvx --from git+https://github.com/d4renk/mcp-push.git claudemcp
```

Gemini 通过 uvx 安装:

```bash
gemini mcp add mcp-push --transport stdio -- uvx --from git+https://github.com/d4renk/mcp-push.git geminimcp
```

## 配置渠道

复制并编辑配置模板：

```bash
cp config.sh.example config.sh
# 编辑 config.sh 填写各渠道 token
```

环境变量会自动加载，也可直接在 shell 中 export。

## 一次性发送（不走 MCP）

- Python：`python3 -c "from notify import send; send('任务完成','任务完成')"`（确保 `PYTHONPATH` 或在项目根目录）
- Node：`node -e "require('./sendNotify').sendNotify('任务完成','任务完成')"`

## 什么时候发送通知

只在以下两种场景调用 mcp-push：

1. 任务完成：长任务 (>60s) 结束，无论成功或失败。
2. 需要用户操作：流程暂停，等待用户决策或授权。

除非用户要求，否则不要发送开始/进度的噪音通知。

## 工具

### notify_send

任务完成或用户确认时的简单通知。

```json
{
  "title": "任务完成",
  "content": "报告已生成"
}
```

### notify_event

带 run_id 的结构化事件通知。

```json
{
  "run_id": "job-001",
  "event": "end",
  "message": "任务完成",
  "data": {"artifact_url": "https://example.com/report"}
}
```

历史别名：`notify.send`、`notify.event`（仍可调用，但为兼容某些 MCP 客户端的命名规则不再对外声明）。

## HITOKOTO 默认值

`HITOKOTO` 控制是否追加随机句子，默认 `false`（关闭）。设为 `true` 开启。

## 测试

- MCP server (Python stdio): `python3 test_mcp_push.py`
- Python worker socket: `python3 test_integration.py`
