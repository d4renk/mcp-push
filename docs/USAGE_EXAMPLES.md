# 使用示例

本文档提供 mcp-push 在实际场景中的完整使用示例。

## 场景 1: Agent 任务完成通知

### 1.1 简单任务完成

```python
# Python - 使用 MCP 工具
await mcp.call_tool("notify_send", {
    "title": "数据处理完成",
    "content": "已成功处理 10,000 条记录"
})
```

```javascript
// JavaScript - 直接调用库
const { sendNotify } = require('./sendNotify');
await sendNotify('数据处理完成', '已成功处理 10,000 条记录');
```

### 1.2 完整任务生命周期跟踪

```python
# 任务启动
await mcp.call_tool("notify_event", {
    "run_id": "data-pipeline-20250101-001",
    "event": "start",
    "message": "开始处理 10GB 原始数据"
})

# 执行中更新 - 第一阶段
await mcp.call_tool("notify_event", {
    "run_id": "data-pipeline-20250101-001",
    "event": "update",
    "message": "数据清洗完成，开始特征提取",
    "data": {
        "step": "feature_extraction",
        "progress": 0.35
    }
})

# 执行中更新 - 第二阶段
await mcp.call_tool("notify_event", {
    "run_id": "data-pipeline-20250101-001",
    "event": "update",
    "message": "模型训练中（Epoch 5/10）",
    "data": {
        "step": "model_training",
        "progress": 0.75
    }
})

# 任务成功完成
await mcp.call_tool("notify_event", {
    "run_id": "data-pipeline-20250101-001",
    "event": "end",
    "message": "任务完成，模型准确率 94.3%",
    "data": {
        "progress": 1.0,
        "artifact_url": "https://example.com/model-v2.pkl",
        "metadata": {
            "accuracy": 0.943,
            "duration": "3600s"
        }
    }
})
```

## 场景 2: 异常告警

### 2.1 任务失败通知

```python
# 错误事件
await mcp.call_tool("notify_event", {
    "run_id": "deployment-002",
    "event": "error",
    "message": "部署失败：数据库迁移超时",
    "data": {
        "step": "db_migration",
        "error_code": "MIGRATION_TIMEOUT",
        "metadata": {
            "timeout": "300s",
            "pending_migrations": 15
        }
    }
})
```

### 2.2 系统监控告警

```python
# 资源告警
await mcp.call_tool("notify_send", {
    "title": "⚠️ 系统告警",
    "content": """
**服务器**: production-01
**告警类型**: CPU 使用率过高
**当前值**: 87.3%
**阈值**: 80%
**时间**: 2025-01-01 10:30:00
"""
})
```

## 场景 3: 长时间运行任务的进度推送

### 3.1 批量数据迁移

```python
import time

run_id = "db-migration-20250101"

# 启动
await mcp.call_tool("notify_event", {
    "run_id": run_id,
    "event": "start",
    "message": "开始迁移 100 万条用户数据"
})

# 每处理 10% 推送一次更新
for i in range(1, 11):
    # 模拟数据处理
    time.sleep(60)

    await mcp.call_tool("notify_event", {
        "run_id": run_id,
        "event": "update",
        "message": f"已迁移 {i * 100000} 条记录",
        "data": {
            "progress": i / 10,
            "step": f"batch_{i}"
        }
    })

# 完成
await mcp.call_tool("notify_event", {
    "run_id": run_id,
    "event": "end",
    "message": "数据迁移完成，共迁移 1,000,000 条记录",
    "data": {
        "progress": 1.0,
        "total_records": 1000000,
        "duration": "10m"
    }
})
```

## 场景 4: 多渠道配置组合

### 4.1 钉钉 + Telegram 双渠道

```bash
# 环境变量配置
export DD_BOT_TOKEN="your-dingtalk-token"
export DD_BOT_SECRET="your-dingtalk-secret"
export TG_BOT_TOKEN="your-telegram-token"
export TG_USER_ID="your-telegram-id"
```

```python
# 自动推送到两个渠道
from notify import send
send("部署成功", "应用版本 v2.0.1 已部署到生产环境")
```

### 4.2 企业微信 + 邮件组合

```bash
export QYWX_KEY="your-wecom-webhook-key"
export SMTP_SERVER="smtp.example.com:465"
export SMTP_SSL="true"
export SMTP_EMAIL="notify@example.com"
export SMTP_PASSWORD="your-password"
export SMTP_NAME="AI Agent"
```

```python
# 同时推送到企业微信和邮件
await mcp.call_tool("notify_send", {
    "title": "周报生成完成",
    "content": "已生成第 52 周团队周报，请查收"
})
```

## 场景 5: AI Agent 集成示例

### 5.1 Claude Agent 调用

```python
# Claude SDK 示例
import anthropic

client = anthropic.Anthropic()

# 定义 MCP 工具
tools = [{
    "name": "notify_event",
    "description": "发送结构化事件流到通知渠道",
    "input_schema": {
        "type": "object",
        "properties": {
            "run_id": {"type": "string"},
            "event": {"type": "string", "enum": ["start", "update", "end", "error"]},
            "message": {"type": "string"},
            "data": {"type": "object"}
        },
        "required": ["run_id", "event", "message"]
    }
}]

# Agent 执行任务
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "分析这份数据并通知我"}]
)

# 处理工具调用
for block in response.content:
    if block.type == "tool_use" and block.name == "notify_event":
        # 调用实际的 MCP 工具
        await mcp.call_tool("notify_event", block.input)
```

### 5.2 OpenAI GPT 调用

```python
# OpenAI SDK 示例
import openai

client = openai.OpenAI()

tools = [{
    "type": "function",
    "function": {
        "name": "notify_send",
        "description": "向所有已配置渠道广播消息",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["title", "content"]
        }
    }
}]

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "完成报告并通知我"}],
    tools=tools
)

# 处理函数调用
for choice in response.choices:
    if choice.message.tool_calls:
        for tool_call in choice.message.tool_calls:
            if tool_call.function.name == "notify_send":
                import json
                args = json.loads(tool_call.function.arguments)
                await mcp.call_tool("notify_send", args)
```

### 5.3 Codex MCP 直接调用

```python
# 通过 Codex MCP 服务器调用
# Codex 已经内置支持 MCP 协议

# 方式 1: 在 Codex 任务中直接调用
"""
Codex Task: 分析日志文件并在完成时通知我

Codex 将自动:
1. 读取日志文件
2. 执行分析
3. 调用 notify_event 工具推送结果
"""

# 方式 2: 通过 CLI 注册 MCP 服务器
# Codex / Claude / Gemini
# codex mcp add mcp-push -- node $(pwd)/apps/mcp-server/build/index.js
# claude mcp add mcp-push -- node $(pwd)/apps/mcp-server/build/index.js
# gemini mcp add mcp-push -- node $(pwd)/apps/mcp-server/build/index.js
# 如果 CLI 需要显式传输参数，可在 `--` 前追加: --transport stdio
# 也可使用 uvx 直接安装并注册:
# gemini mcp add mcp-push --transport stdio -- uvx --from git+https://github.com/d4renk/mcp-push.git geminimcp
```

## 场景 6: 错误处理与重试

### 6.1 优雅的错误处理

```python
try:
    await mcp.call_tool("notify_event", {
        "run_id": "task-001",
        "event": "end",
        "message": "任务完成"
    })
except Exception as e:
    # 即使通知失败，也不影响主任务
    print(f"通知发送失败（非致命）: {e}")
```

### 6.2 Python 库模式的状态聚合

```python
from notify import send

# send() 函数内部已实现渠道隔离
# 单个渠道失败不影响其他渠道
send("任务完成", "详细内容...")

# 检查控制台输出以查看各渠道状态:
# "钉钉机器人 推送成功！"
# "Telegram 推送失败！"  # 不会中断其他渠道
# "企业微信机器人推送成功！"
```

## 场景 7: 自定义渠道扩展

### 7.1 添加自定义 Webhook

```bash
export WEBHOOK_URL="https://api.example.com/notify?title=\$title&content=\$content"
export WEBHOOK_METHOD="POST"
export WEBHOOK_CONTENT_TYPE="application/json"
export WEBHOOK_HEADERS="Authorization: Bearer your-token"
export WEBHOOK_BODY="title: \$title
content: \$content"
```

```python
# 自动推送到自定义 Webhook
send("测试通知", "这是一条测试消息")
```

### 7.2 Python 渠道扩展示例

```python
# 在 notify.py 中添加新渠道
def custom_channel(title: str, content: str) -> None:
    """
    自定义渠道实现模板
    """
    if not push_config.get("CUSTOM_CHANNEL_TOKEN"):
        return

    print("自定义渠道服务启动")

    url = "https://api.custom.com/send"
    data = {
        "token": push_config.get("CUSTOM_CHANNEL_TOKEN"),
        "title": title,
        "content": content
    }

    response = requests.post(url, json=data, timeout=15).json()

    if response.get("code") == 200:
        print("自定义渠道推送成功！")
    else:
        print(f"自定义渠道推送失败：{response.get('message')}")

# 在 add_notify_function() 中注册
def add_notify_function():
    notify_function = []
    # ... 其他渠道
    if push_config.get("CUSTOM_CHANNEL_TOKEN"):
        notify_function.append(custom_channel)
    return notify_function
```

## 场景 8: 条件通知

### 8.1 跳过特定标题

```bash
# 配置跳过列表（换行分隔）
export SKIP_PUSH_TITLE="测试通知
调试消息
开发环境告警"
```

```python
# 这些通知会被自动跳过
send("测试通知", "这条不会发送")
send("调试消息", "这条也不会发送")

# 这条会正常发送
send("生产环境告警", "这条会正常发送")
```

### 8.2 关闭一言功能

```bash
export HITOKOTO="false"
```

```python
# 推送内容不会附加随机句子
send("通知", "纯粹的通知内容")
```

## 场景 9: Docker 容器化部署

### 9.1 Dockerfile 示例

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY notify.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 环境变量通过 docker run -e 传入
CMD ["python", "-m", "mcp_server"]
```

### 9.2 Docker Compose 示例

```yaml
version: '3.8'
services:
  mcp-push:
    build: .
    environment:
      - DD_BOT_TOKEN=${DD_BOT_TOKEN}
      - DD_BOT_SECRET=${DD_BOT_SECRET}
      - TG_BOT_TOKEN=${TG_BOT_TOKEN}
      - TG_USER_ID=${TG_USER_ID}
      - HITOKOTO=false
    ports:
      - "8080:8080"
```

## 场景 10: 测试与调试

### 10.1 简单测试

```python
# Python
from notify import send
send("测试通知", "如果你收到这条消息，说明配置成功")
```

```bash
# JavaScript
node -e "require('./sendNotify').sendNotify('测试通知', '配置成功')"
```

### 10.2 单个渠道测试

```python
# 只测试钉钉
from notify import dingding_bot
dingding_bot("测试", "钉钉推送测试")

# 只测试 Telegram
from notify import telegram_bot
telegram_bot("测试", "Telegram 推送测试")
```

### 10.3 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 启用详细日志
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1

from notify import send
send("调试测试", "查看详细请求日志")
```

## 总结

### 选择推送方式

| 场景 | 推荐方式 | 原因 |
|------|---------|------|
| AI Agent 集成 | MCP 工具 (`notify_event`) | 标准化协议，支持事件流 |
| 脚本任务通知 | 库模式 (`send()`) | 简单直接，零配置 |
| 进度跟踪 | MCP 工具 (`notify_event`) | 结构化数据，支持 run_id 关联 |
| 简单告警 | 库模式 (`send()`) | 快速集成 |
| 多语言环境 | MCP 工具 | 语言无关协议 |

### 最佳实践

1. **环境变量管理**: 使用密钥管理服务（如 AWS Secrets Manager）
2. **错误处理**: 通知失败不应中断主业务逻辑
3. **消息格式**: 保持简洁，关键信息优先
4. **渠道选择**: 根据紧急程度选择合适渠道
5. **测试验证**: 生产环境前务必测试所有配置渠道
