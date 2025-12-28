# mcp-push

MCP notification bridge: send agent results to external channels (DingTalk, Feishu, Telegram, WeCom, email, etc.).

## Features

- MCP tools: `notify.send` and `notify.event`
- TypeScript server + Python worker (Unix socket)
- Parallel multi-channel delivery (best effort)
- Simple config via environment variables

## Requirements

- Node.js 16+
- Python 3.8+

## Install

```bash
npm install
npm run build
pip install -r tools/pytools/requirements.txt
```

## Register MCP server

```bash
claude mcp add mcp-push -s user --transport stdio -- node $(pwd)/apps/mcp-server/build/index.js
```

## Configure channels

Copy and edit config template:

```bash
cp config.sh.example config.sh
# edit config.sh to set tokens
```

Environment variables are loaded automatically. You can also export them in your shell.

## When to send notifications

Only call mcp-push in these cases:

1. Task Finished: when a long-running task (>60s) ends, success or failure.
2. User Action Needed: when the flow pauses and needs user decision or authorization.

Avoid start/update noise unless the user explicitly asks for progress.

## Tools

### notify.send

Simple notification for task finished or user confirmation.

```json
{
  "title": "Task finished",
  "content": "Report generated"
}
```

### notify.event

Structured event notification with run_id tracking.

```json
{
  "run_id": "job-001",
  "event": "end",
  "message": "Job completed",
  "data": {"artifact_url": "https://example.com/report"}
}
```

## HITOKOTO default

`HITOKOTO` controls the random quote append behavior. Default is `false` (disabled). Set to `true` to enable.

## Tests

- MCP server (Python stdio): `python3 test_mcp_push.py`
- Python worker socket: `python3 test_integration.py`
