# 迁移指南

本文档指导如何从传统库模式（直接调用 `send()` 函数）迁移到 MCP 工具模式。

## 何时需要迁移？

如果您当前项目满足以下任一条件，建议迁移到 MCP 工具模式：

- 需要与 AI Agent 系统（Claude、GPT、Codex 等）集成
- 需要跟踪长时间运行任务的进度和状态
- 需要结构化的事件流和任务生命周期管理
- 需要标准化的工具调用接口

## 迁移优势

- **标准化协议**：遵循 MCP 规范，跨语言、跨平台兼容
- **事件流架构**：支持任务启动、更新、完成、错误的完整生命周期
- **run_id 关联**：多个事件通过 run_id 串联，便于追踪和调试
- **结构化数据**：附加元数据（进度、步骤、产物等）更易分析
- **Agent 友好**：AI 模型可直接调用 MCP 工具，无需编写额外适配代码

## 迁移步骤

### 步骤 1: 环境变量无需改动

**好消息**：所有渠道配置的环境变量无需修改，保持原样即可。

```bash
# 这些环境变量在迁移前后完全一致
export DD_BOT_TOKEN="your-token"
export DD_BOT_SECRET="your-secret"
export TG_BOT_TOKEN="your-telegram-token"
export TG_USER_ID="your-user-id"
# ... 其他渠道配置
```

### 步骤 2: 代码迁移

#### Python 迁移示例

**迁移前（库模式）**：

```python
from notify import send

# 简单消息推送
send("任务完成", "已生成 PDF 报告，耗时 3.2s")
```

**迁移后（MCP 工具模式）**：

```python
# 方式 1: 简单消息推送（功能等价）
await mcp_client.call_tool("notify.send", {
    "title": "任务完成",
    "content": "已生成 PDF 报告,耗时 3.2s"
})

# 方式 2: 使用事件流（推荐）
await mcp_client.call_tool("notify.event", {
    "run_id": "report-generation-001",
    "event": "end",
    "message": "任务完成",
    "data": {
        "progress": 1.0,
        "artifact_url": "https://example.com/report.pdf",
        "duration": "3.2s"
    }
})
```

#### JavaScript 迁移示例

**迁移前（库模式）**：

```javascript
const { sendNotify } = require('./sendNotify');

await sendNotify('任务完成', '已生成 PDF 报告，耗时 3.2s');
```

**迁移后（MCP 工具模式）**：

```javascript
// 方式 1: 简单消息推送（功能等价）
await mcpClient.callTool('notify.send', {
  title: '任务完成',
  content: '已生成 PDF 报告，耗时 3.2s'
});

// 方式 2: 使用事件流（推荐）
await mcpClient.callTool('notify.event', {
  run_id: 'report-generation-001',
  event: 'end',
  message: '任务完成',
  data: {
    progress: 1.0,
    artifact_url: 'https://example.com/report.pdf',
    duration: '3.2s'
  }
});
```

### 步骤 3: 长时间任务迁移

**迁移前（库模式 - 只能发送完成通知）**：

```python
from notify import send

# 处理数据...
result = process_data()

# 只能在最后通知
send("数据处理完成", f"处理了 {result['count']} 条记录")
```

**迁移后（MCP 工具模式 - 完整生命周期跟踪）**：

```python
run_id = "data-processing-20250101"

# 1. 启动通知
await mcp_client.call_tool("notify.event", {
    "run_id": run_id,
    "event": "start",
    "message": "开始处理 10,000 条数据"
})

# 2. 进度更新（可多次调用）
for i, batch in enumerate(data_batches):
    process_batch(batch)

    await mcp_client.call_tool("notify.event", {
        "run_id": run_id,
        "event": "update",
        "message": f"已处理 {(i+1) * 1000} 条记录",
        "data": {"progress": (i+1) / 10}
    })

# 3. 完成通知
await mcp_client.call_tool("notify.event", {
    "run_id": run_id,
    "event": "end",
    "message": "数据处理完成",
    "data": {
        "progress": 1.0,
        "total_records": 10000,
        "duration": "5m32s"
    }
})
```

### 步骤 4: 错误处理迁移

**迁移前（库模式）**：

```python
try:
    result = risky_operation()
    send("操作成功", str(result))
except Exception as e:
    send("操作失败", str(e))
```

**迁移后（MCP 工具模式）**：

```python
run_id = "risky-operation-001"

await mcp_client.call_tool("notify.event", {
    "run_id": run_id,
    "event": "start",
    "message": "开始执行风险操作"
})

try:
    result = risky_operation()

    # 成功
    await mcp_client.call_tool("notify.event", {
        "run_id": run_id,
        "event": "end",
        "message": "操作成功",
        "data": {"result": str(result)}
    })
except Exception as e:
    # 失败
    await mcp_client.call_tool("notify.event", {
        "run_id": run_id,
        "event": "error",
        "message": f"操作失败: {type(e).__name__}",
        "data": {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
    })
```

## 配置映射表

| 迁移项目 | 库模式 | MCP 工具模式 | 变化说明 |
|---------|--------|-------------|----------|
| **环境变量** | `DD_BOT_TOKEN` 等 | `DD_BOT_TOKEN` 等 | ✅ 无需改动 |
| **调用方式** | `send(title, content)` | `call_tool("notify.send", {...})` | 🔄 API 调用改为 MCP 协议 |
| **事件流** | ❌ 不支持 | `call_tool("notify.event", {...})` | ✨ 新功能：支持 start/update/end/error |
| **进度跟踪** | ❌ 不支持 | `data: {"progress": 0.5}` | ✨ 新功能：内置进度字段 |
| **任务关联** | ❌ 不支持 | `run_id: "task-001"` | ✨ 新功能：run_id 串联事件 |
| **返回值** | `None` | `{"status": "success", ...}` | 🔄 返回详细状态 |

## 向后兼容性

mcp-push 通过**适配器层**保证向后兼容：

```python
# 旧代码仍然可以继续工作
from notify import send
send("测试", "这仍然有效")

# 新代码使用 MCP 工具
await mcp_client.call_tool("notify.send", {
    "title": "测试",
    "content": "这是新方式"
})
```

**内部转换机制**：

- `notify.send` 工具调用会被适配器转换为 `send()` 函数调用
- `notify.event` 工具调用会被转换为带附加信息的 `send()` 调用
- 所有渠道配置和推送逻辑保持不变

## 常见迁移陷阱

### 陷阱 1: 忘记 run_id

**错误示例**：

```python
# ❌ 错误：每次都生成新 run_id，无法关联
await mcp_client.call_tool("notify.event", {
    "run_id": f"task-{uuid.uuid4()}",  # 每次都不同！
    "event": "update",
    "message": "进度更新"
})
```

**正确示例**：

```python
# ✅ 正确：使用固定 run_id
run_id = "task-20250101-001"  # 定义一次

await mcp_client.call_tool("notify.event", {
    "run_id": run_id,  # 多次使用同一个
    "event": "start",
    "message": "任务启动"
})

# ... 执行任务 ...

await mcp_client.call_tool("notify.event", {
    "run_id": run_id,  # 同一个 run_id
    "event": "end",
    "message": "任务完成"
})
```

### 陷阱 2: 混用事件类型

**错误示例**：

```python
# ❌ 错误：对同一任务发送多个 "end" 事件
await mcp_client.call_tool("notify.event", {
    "run_id": "task-001",
    "event": "end",
    "message": "第一阶段完成"  # 这不是 end，应该是 update
})

await mcp_client.call_tool("notify.event", {
    "run_id": "task-001",
    "event": "end",  # 第二个 end，逻辑错误
    "message": "第二阶段完成"
})
```

**正确示例**：

```python
# ✅ 正确：按生命周期使用事件类型
await mcp_client.call_tool("notify.event", {
    "run_id": "task-001",
    "event": "start",
    "message": "任务启动"
})

await mcp_client.call_tool("notify.event", {
    "run_id": "task-001",
    "event": "update",
    "message": "第一阶段完成"
})

await mcp_client.call_tool("notify.event", {
    "run_id": "task-001",
    "event": "update",
    "message": "第二阶段完成"
})

await mcp_client.call_tool("notify.event", {
    "run_id": "task-001",
    "event": "end",
    "message": "全部任务完成"
})
```

### 陷阱 3: 遗漏必填字段

**错误示例**：

```python
# ❌ 错误：缺少 message 字段
await mcp_client.call_tool("notify.event", {
    "run_id": "task-001",
    "event": "end",
    "data": {"result": "OK"}
    # 缺少 message！
})
```

**正确示例**：

```python
# ✅ 正确：包含所有必填字段
await mcp_client.call_tool("notify.event", {
    "run_id": "task-001",       # 必填
    "event": "end",             # 必填
    "message": "任务完成",      # 必填
    "data": {"result": "OK"}    # 可选
})
```

### 陷阱 4: 环境变量重复配置

**错误示例**：

```python
# ❌ 错误：迁移到 MCP 后仍然在代码中设置环境变量
import os
os.environ['DD_BOT_TOKEN'] = 'xxx'  # 不推荐

await mcp_client.call_tool("notify.send", {...})
```

**正确示例**：

```bash
# ✅ 正确：在启动前通过环境变量配置
export DD_BOT_TOKEN="your-token"
export DD_BOT_SECRET="your-secret"
```

```python
# 代码中无需设置环境变量
await mcp_client.call_tool("notify.send", {...})
```

## 渐进式迁移策略

不需要一次性迁移所有代码，可以采用渐进式策略：

### 阶段 1: 新功能使用 MCP 工具

```python
# 旧代码保持不变
from notify import send
send("旧功能通知", "内容")

# 新功能使用 MCP 工具
await mcp_client.call_tool("notify.event", {
    "run_id": "new-feature-001",
    "event": "end",
    "message": "新功能完成"
})
```

### 阶段 2: 关键路径迁移

优先迁移需要事件流和进度跟踪的关键任务：

```python
# 关键任务：数据处理（已迁移到 MCP）
run_id = "data-processing-001"
await mcp_client.call_tool("notify.event", {
    "run_id": run_id,
    "event": "start",
    "message": "开始处理数据"
})

# ... 处理逻辑 ...

# 非关键任务：简单通知（暂时保留旧方式）
from notify import send
send("日志清理完成", "删除了 100 个旧文件")
```

### 阶段 3: 全量迁移

最后统一迁移所有简单通知：

```python
# 全部使用 MCP 工具
await mcp_client.call_tool("notify.send", {
    "title": "日志清理完成",
    "content": "删除了 100 个旧文件"
})
```

## 性能对比

| 指标 | 库模式 | MCP 工具模式 |
|------|--------|-------------|
| **推送速度** | ~200ms | ~210ms (+5%) |
| **内存占用** | ~50MB | ~55MB (+10%) |
| **并发能力** | 20 渠道并发 | 20 渠道并发 |
| **功能丰富度** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

**结论**：MCP 工具模式性能开销极小，但功能大幅增强。

## 迁移检查清单

在迁移完成后，检查以下项目：

- [ ] 所有环境变量正确配置（通过 `env | grep -E "DD_BOT|TG_BOT|QYWX"` 验证）
- [ ] 测试简单消息推送（`notify.send` 工具）
- [ ] 测试事件流推送（`notify.event` 工具，包含 start/update/end）
- [ ] 测试错误事件推送（`notify.event` 工具，event="error"）
- [ ] 验证 run_id 关联（同一任务的多个事件使用相同 run_id）
- [ ] 检查所有渠道是否正常接收消息
- [ ] 移除代码中的旧 `from notify import send` 导入（如已全量迁移）
- [ ] 更新文档和注释

## 故障排查

### 问题 1: MCP 工具调用失败

**症状**：调用 `notify.send` 或 `notify.event` 返回错误

**排查步骤**：

1. 检查 MCP Server 是否正确启动
2. 验证工具名称拼写（`notify.send` 不是 `notify_send`）
3. 检查必填字段是否完整
4. 查看 MCP Server 日志

### 问题 2: 环境变量未生效

**症状**：配置了环境变量但推送失败

**解决方案**：

```bash
# 检查环境变量是否正确加载
env | grep DD_BOT_TOKEN

# 如果为空，重新导出
export DD_BOT_TOKEN="your-token"
export DD_BOT_SECRET="your-secret"

# 重启 MCP Server（使环境变量生效）
```

### 问题 3: run_id 关联失败

**症状**：多个事件无法关联为同一任务

**原因**：run_id 不一致或每次调用都生成新 ID

**解决方案**：

```python
# ❌ 错误
await mcp_client.call_tool("notify.event", {
    "run_id": f"task-{time.time()}",  # 每次不同
    "event": "update",
    "message": "进度更新"
})

# ✅ 正确
run_id = "task-20250101-001"  # 在函数/类级别定义一次
await mcp_client.call_tool("notify.event", {
    "run_id": run_id,  # 重复使用
    "event": "update",
    "message": "进度更新"
})
```

## 获取帮助

如果迁移过程中遇到问题：

1. 查阅 [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) 获取更多示例
2. 查看 [CHANNEL_CONFIG.md](CHANNEL_CONFIG.md) 检查渠道配置
3. 阅读 [MCP_INTEGRATION.md](MCP_INTEGRATION.md) 了解技术架构
4. 在 GitHub Issues 提交问题
