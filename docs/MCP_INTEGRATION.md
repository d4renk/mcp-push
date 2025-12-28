# MCP 集成架构

本文档详细说明 mcp-push 的 Model Context Protocol (MCP) 集成架构设计。

## 架构概览

```
┌───────────────────────────────────────────────────────────────┐
│                        MCP Server Core                        │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Tool Registry & Router                     │  │
│  │  ┌───────────────┬───────────────┬──────────────────┐  │  │
│  │  │ notify_send   │ notify_event  │ notify.channel.* │  │  │
│  │  └───────────────┴───────────────┴──────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
│                              │                                │
│                              ▼                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │         Adapter Layer (Backward Compatibility)          │  │
│  │    ┌──────────────────┐    ┌──────────────────┐        │  │
│  │    │  send(title,     │◀──▶│  Event Envelope  │        │  │
│  │    │  content, **kw)  │    │  Transformer     │        │  │
│  │    └──────────────────┘    └──────────────────┘        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                              │                                │
│                              ▼                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Channel Dispatcher (Concurrent)            │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Thread Pool (Python) / Promise.all (JavaScript)   │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────┘  │
│                              │                                │
└──────────────────────────────┼────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
  ┌──────────┐          ┌──────────┐          ┌──────────┐
  │ Channel  │          │ Channel  │   ...    │ Channel  │
  │  #1      │          │  #2      │          │  #20+    │
  └──────────┘          └──────────┘          └──────────┘
   钉钉机器人              Telegram              企业微信
```

## MCP Server 实现

### 1. 工具注册表 (Tool Registry)

MCP Server 需要实现两个标准端点：

#### `tools/list` 端点

返回可用工具列表：

```json
{
  "tools": [
    {
      "name": "notify_send",
      "description": "向所有已配置渠道广播消息",
      "inputSchema": {
        "type": "object",
        "properties": {
          "title": {"type": "string", "description": "消息标题"},
          "content": {"type": "string", "description": "消息内容"}
        },
        "required": ["title", "content"]
      }
    },
    {
      "name": "notify_event",
      "description": "发送结构化事件流（支持进度追踪）",
      "inputSchema": {
        "type": "object",
        "properties": {
          "run_id": {"type": "string", "description": "任务唯一标识"},
          "event": {
            "type": "string",
            "enum": ["start", "update", "end", "error"],
            "description": "事件类型"
          },
          "message": {"type": "string", "description": "人类可读的状态描述"},
          "data": {
            "type": "object",
            "description": "附加数据（step, progress, artifact_url 等）"
          },
          "timestamp": {"type": "string", "format": "date-time"}
        },
        "required": ["run_id", "event", "message"]
      }
    }
  ]
}
```

#### `tools/call` 端点

执行工具调用：

```json
{
  "name": "notify_event",
  "arguments": {
    "run_id": "task-001",
    "event": "end",
    "message": "分析完成",
    "data": {"progress": 1.0}
  }
}
```

### 2. Event Envelope 协议

事件流推送使用标准化的信封结构：

```python
class EventEnvelope:
    run_id: str          # 任务唯一标识（必填）
    event: Literal["start", "update", "end", "error"]  # 事件类型（必填）
    message: str         # 人类可读描述（必填）
    data: dict          # 附加数据（可选）
    timestamp: str      # ISO-8601 时间戳（自动生成）
```

#### 字段说明

- **`run_id`**: 贯穿整个任务生命周期的唯一标识，用于关联多个事件
- **`event`**: 事件类型
  - `start`: 任务启动
  - `update`: 进度更新
  - `end`: 任务成功完成
  - `error`: 任务失败或异常
- **`message`**: 向用户展示的状态描述，支持 Markdown
- **`data`**: 结构化附加信息，常用字段：
  - `step`: 当前执行步骤名称
  - `progress`: 进度（0.0 - 1.0）
  - `artifact_url`: 生成的产物地址（报告、文件等）
  - `error_code`: 错误码（仅 error 事件）
  - `metadata`: 其他元数据
- **`timestamp`**: 自动填充为 ISO-8601 格式（如 `2024-01-01T12:00:00Z`）

#### 事件流示例

完整的任务生命周期：

```python
# 1. 启动事件
{
  "run_id": "data-pipeline-001",
  "event": "start",
  "message": "开始处理 10GB 原始数据",
  "timestamp": "2024-01-01T10:00:00Z"
}

# 2. 进度更新
{
  "run_id": "data-pipeline-001",
  "event": "update",
  "message": "数据清洗完成，开始特征提取",
  "data": {
    "step": "feature_extraction",
    "progress": 0.35
  },
  "timestamp": "2024-01-01T10:15:00Z"
}

# 3. 再次更新
{
  "run_id": "data-pipeline-001",
  "event": "update",
  "message": "模型训练中（Epoch 5/10）",
  "data": {
    "step": "model_training",
    "progress": 0.75
  },
  "timestamp": "2024-01-01T10:45:00Z"
}

# 4. 成功完成
{
  "run_id": "data-pipeline-001",
  "event": "end",
  "message": "任务完成，模型准确率 94.3%",
  "data": {
    "progress": 1.0,
    "artifact_url": "https://example.com/model-v2.pkl",
    "metadata": {"accuracy": 0.943, "duration": "3600s"}
  },
  "timestamp": "2024-01-01T11:00:00Z"
}
```

#### 错误处理示例

```python
# 任务失败
{
  "run_id": "deployment-002",
  "event": "error",
  "message": "部署失败：数据库迁移超时",
  "data": {
    "step": "db_migration",
    "error_code": "MIGRATION_TIMEOUT",
    "metadata": {"timeout": "300s", "pending_migrations": 15}
  },
  "timestamp": "2024-01-01T12:30:00Z"
}
```

### 3. 适配器层 (Adapter Layer)

实现向后兼容的关键组件：

```python
# Python 实现示例
import uuid
import json
from datetime import datetime

class MCPAdapter:
    @staticmethod
    def send_to_event(title: str, content: str) -> dict:
        """将传统 send() 调用转换为 Event Envelope"""
        return {
            "run_id": f"legacy-{uuid.uuid4().hex[:8]}",
            "event": "end",  # 简单消息视为已完成事件
            "message": f"{title}\n\n{content}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    @staticmethod
    def event_to_send(envelope: dict) -> tuple:
        """将 Event Envelope 转换为传统 send() 参数"""
        title = f"[{envelope['event'].upper()}] {envelope.get('run_id', 'N/A')}"
        content = envelope['message']

        if envelope.get('data'):
            data_str = json.dumps(envelope['data'], indent=2)
            content += f"\n\n**附加数据:**\n```json\n{data_str}\n```"

        return title, content
```

```javascript
// JavaScript 实现示例
class MCPAdapter {
  static sendToEvent(text, desp) {
    return {
      run_id: `legacy-${crypto.randomUUID().slice(0, 8)}`,
      event: 'end',
      message: `${text}\n\n${desp}`,
      timestamp: new Date().toISOString()
    };
  }

  static eventToSend(envelope) {
    const title = `[${envelope.event.toUpperCase()}] ${envelope.run_id || 'N/A'}`;
    let content = envelope.message;

    if (envelope.data) {
      content += `\n\n**附加数据:**\n\`\`\`json\n${JSON.stringify(envelope.data, null, 2)}\n\`\`\``;
    }

    return { title, content };
  }
}
```

## 并发处理机制

### Python 实现

```python
import threading
from typing import List, Callable

def dispatch_concurrent(
    notify_functions: List[Callable],
    title: str,
    content: str
) -> dict:
    """并发执行所有渠道推送"""
    results = {}
    lock = threading.Lock()

    def worker(func):
        try:
            func(title, content)
            with lock:
                results[func.__name__] = {"status": "success"}
        except Exception as e:
            with lock:
                results[func.__name__] = {"status": "error", "error": str(e)}

    threads = [
        threading.Thread(target=worker, args=(func,), name=func.__name__)
        for func in notify_functions
    ]

    [t.start() for t in threads]
    [t.join() for t in threads]

    return results
```

### JavaScript 实现

```javascript
async function dispatchConcurrent(notifyFunctions, text, desp) {
  const results = await Promise.allSettled(
    notifyFunctions.map(async (func) => {
      try {
        await func(text, desp);
        return { channel: func.name, status: 'success' };
      } catch (error) {
        return { channel: func.name, status: 'error', error: error.message };
      }
    })
  );

  return results.reduce((acc, result, index) => {
    const funcName = notifyFunctions[index].name;
    acc[funcName] = result.status === 'fulfilled'
      ? result.value
      : { status: 'error', error: result.reason };
    return acc;
  }, {});
}
```

## 错误处理策略

### 1. 渠道隔离

单个渠道失败不影响其他渠道：

```python
# 错误被捕获并记录，不会抛出异常
try:
    dingding_bot(title, content)
    print("钉钉推送成功")
except Exception as e:
    print(f"钉钉推送失败: {e}")
finally:
    # 继续执行其他渠道
    pass
```

### 2. 状态聚合

返回每个渠道的执行状态：

```json
{
  "summary": {
    "total": 5,
    "success": 4,
    "failed": 1
  },
  "details": {
    "dingding_bot": {"status": "success"},
    "telegram_bot": {"status": "success"},
    "wecom_bot": {"status": "error", "error": "Connection timeout"},
    "smtp": {"status": "success"},
    "bark": {"status": "success"}
  }
}
```

### 3. 重试机制（可选）

对于临时性失败（网络超时等），可配置自动重试：

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(delay * (attempt + 1))
        return wrapper
    return decorator

@retry(max_attempts=3)
def telegram_bot(title, content):
    # 实现代码...
    pass
```

## MCP 环境变量

除了渠道配置外，可新增 MCP 特定配置：

```bash
# 启用 MCP Server 模式
export MCP_SERVER_ENABLED=true

# MCP Server 监听地址
export MCP_SERVER_HOST=0.0.0.0
export MCP_SERVER_PORT=8080

# 启用结构化日志输出（JSON Lines 格式）
export MCP_STRUCTURED_LOGGING=true

# 最大并发推送数（限制资源占用）
export MCP_MAX_CONCURRENT_CHANNELS=10

# 全局推送超时（秒）
export MCP_GLOBAL_TIMEOUT=30
```

## 安全考虑

### 1. 凭据管理

- 所有敏感信息（Token、Secret、密码）**仅**通过环境变量传递
- 严禁在代码中硬编码凭据
- 建议使用密钥管理服务（如 AWS Secrets Manager、Vault）

### 2. 输入验证

```python
def validate_event_envelope(data: dict) -> bool:
    """验证 Event Envelope 结构"""
    required_fields = ['run_id', 'event', 'message']
    if not all(field in data for field in required_fields):
        raise ValueError("缺少必填字段")

    if data['event'] not in ['start', 'update', 'end', 'error']:
        raise ValueError("无效的事件类型")

    if len(data['run_id']) > 128:
        raise ValueError("run_id 过长")

    return True
```

### 3. 速率限制

防止 API 滥用：

```python
from time import time

class RateLimiter:
    def __init__(self, max_calls=10, period=60):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def allow(self) -> bool:
        now = time()
        self.calls = [t for t in self.calls if now - t < self.period]

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False
```

## 性能优化

### 1. 连接池复用

对于 HTTP 请求（如 Webhook），复用连接：

```python
import requests

session = requests.Session()
session.headers.update({'User-Agent': 'mcp-push/1.0'})

def webhook_notify(title, content):
    response = session.post(WEBHOOK_URL, json={
        'title': title,
        'content': content
    })
```

### 2. 异步 I/O（JavaScript）

```javascript
const { fetch } = require('undici');  // 使用高性能 HTTP 客户端

async function webhookNotify(title, content) {
  await fetch(WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, content })
  });
}
```

### 3. 渠道优先级

允许配置高优先级渠道先执行：

```python
# 配置渠道优先级
CHANNEL_PRIORITY = {
    'telegram_bot': 1,    # 高优先级
    'dingding_bot': 1,
    'smtp': 2,            # 低优先级
    'bark': 2
}

# 按优先级分组执行
high_priority = [func for func in notify_functions if CHANNEL_PRIORITY.get(func.__name__, 2) == 1]
low_priority = [func for func in notify_functions if CHANNEL_PRIORITY.get(func.__name__, 2) == 2]

# 先执行高优先级
dispatch_concurrent(high_priority, title, content)
# 再执行低优先级
dispatch_concurrent(low_priority, title, content)
```

## 扩展性

### 新增渠道实现模板

```python
def new_channel(title: str, content: str) -> None:
    """
    新渠道推送实现模板

    Args:
        title: 消息标题
        content: 消息内容（支持 Markdown）

    Raises:
        Exception: 推送失败时抛出异常，会被自动捕获和记录
    """
    # 1. 检查环境变量配置
    if not push_config.get("NEW_CHANNEL_TOKEN"):
        return  # 未配置则跳过

    print("新渠道服务启动")

    # 2. 构造请求
    url = f"https://api.newchannel.com/send"
    data = {
        "token": push_config.get("NEW_CHANNEL_TOKEN"),
        "title": title,
        "content": content
    }

    # 3. 发送请求
    response = requests.post(url, json=data, timeout=15).json()

    # 4. 检查响应
    if response.get("code") == 200:
        print("新渠道推送成功！")
    else:
        print(f"新渠道推送失败：{response.get('message')}")
```

### 插件化架构（未来）

```python
# 通过配置文件动态加载渠道
import importlib

def load_channels_from_config(config_file):
    with open(config_file) as f:
        config = json.load(f)

    channels = []
    for channel_spec in config['channels']:
        module = importlib.import_module(channel_spec['module'])
        func = getattr(module, channel_spec['function'])
        channels.append(func)

    return channels
```

## 测试策略

### 单元测试

```python
import unittest
from unittest.mock import patch, MagicMock

class TestNotifyChannels(unittest.TestCase):
    @patch('requests.post')
    def test_telegram_success(self, mock_post):
        mock_post.return_value.json.return_value = {"ok": True}

        telegram_bot("测试标题", "测试内容")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('sendMessage', args[0])

    @patch('requests.post')
    def test_telegram_failure(self, mock_post):
        mock_post.side_effect = Exception("Network error")

        # 不应抛出异常，而是打印错误日志
        telegram_bot("测试标题", "测试内容")
```

### 集成测试

```bash
# 设置测试环境变量
export DD_BOT_TOKEN="test-token"
export DD_BOT_SECRET="test-secret"
export TG_BOT_TOKEN="test-bot-token"
export TG_USER_ID="123456789"

# 运行测试
python -m pytest tests/
```

## 监控和可观测性

### 结构化日志

```python
import json
import logging

logger = logging.getLogger('mcp-push')

def structured_log(event: str, **kwargs):
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'event': event,
        **kwargs
    }
    logger.info(json.dumps(log_data))

# 使用示例
structured_log('channel_push_start', channel='telegram', run_id='task-001')
structured_log('channel_push_end', channel='telegram', status='success', duration_ms=234)
```

### 指标收集

```python
from prometheus_client import Counter, Histogram

# 定义指标
push_total = Counter('mcp_push_total', 'Total push attempts', ['channel', 'status'])
push_duration = Histogram('mcp_push_duration_seconds', 'Push duration', ['channel'])

# 记录指标
with push_duration.labels(channel='telegram').time():
    telegram_bot(title, content)
    push_total.labels(channel='telegram', status='success').inc()
```

## 部署建议

### Docker 容器化

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY notify.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import notify; print('OK')" || exit 1

CMD ["python", "-m", "mcp_server"]  # 启动 MCP Server
```

### Kubernetes 部署

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-push-config
data:
  DD_BOT_TOKEN: "your-token"
  DD_BOT_SECRET: "your-secret"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-push
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: mcp-push
        image: mcp-push:latest
        envFrom:
        - configMapRef:
            name: mcp-push-config
        resources:
          limits:
            memory: "256Mi"
            cpu: "500m"
```

## 故障排查

### 常见问题

1. **推送未触发**
   - 检查环境变量是否正确配置：`env | grep PUSH`
   - 检查渠道是否在 `add_notify_function()` 中被注册

2. **部分渠道失败**
   - 查看具体渠道的错误日志
   - 验证网络连通性：`curl -I https://api.telegram.org`
   - 检查 Token/Secret 是否过期

3. **推送延迟**
   - 检查并发数配置 `MCP_MAX_CONCURRENT_CHANNELS`
   - 查看网络延迟：`ping api.telegram.org`
   - 考虑使用代理或 CDN

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 启用详细日志
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1
```
