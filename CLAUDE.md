# Core Instruction for mcp-push MCP

在需要通知用户时刻，当你需要向用户发送通知或推送任务执行状态时，你必须思考如何调用 **mcp-push** 为你提供的 MCP 工具。

其中你**务必执行**以下几个步骤：

## 调用时机

**1** 当需要向用户推送简单消息时，使用 `notify.send` 工具。

**2** 当需要追踪长时间任务的执行进度时，使用 `notify.event` 工具发送结构化事件流。

**3** 任务开始时发送 `start` 事件，执行中发送 `update` 事件，完成时发送 `end` 事件，出错时发送 `error` 事件。

**4** mcp-push 会自动将消息并发推送到所有已配置的渠道（钉钉、Telegram、企业微信、邮件等），无需关心具体渠道细节。

---

## mcp-push Tool Invocation Specification

### 1. 工具概述

**mcp-push MCP** 提供了两个核心工具，用于向外部通知系统推送消息。该工具**通过 MCP 协议调用**，无需使用命令行。

**核心能力**：
- ✅ **多渠道并发推送**：自动推送到 20+ 已配置的通知渠道
- ✅ **事件流架构**：支持 start/update/end/error 四种事件类型
- ✅ **零配置使用**：用户已配置好通知渠道，直接调用即可
- ⚠️ **最佳努力交付**：单个渠道失败不影响其他渠道
- ❌ **无返回值依赖**：推送是异步的，不要依赖推送结果做后续逻辑

### 2. 可用工具

#### 工具 1: `notify.send` - 简单消息推送

**用途**：发送简单的标题+内容消息到所有已配置渠道

**参数**：
- `title` (string, 必选): 消息标题
- `content` (string, 必选): 消息内容（支持换行符 `\n`）

**返回值**：
```json
{
  "success": true,
  "message": "已向 X 个渠道发送通知"
}
```

**调用示例**：
```python
# 简单通知
await mcp_client.call_tool("notify.send", {
  "title": "任务完成",
  "content": "数据分析已完成，共处理 10000 条记录"
})

# 带详细信息的通知
await mcp_client.call_tool("notify.send", {
  "title": "系统告警",
  "content": "服务器 CPU 使用率：85%\n内存使用率：78%\n磁盘空间：剩余 20GB"
})
```

---

#### 工具 2: `notify.event` - 结构化事件推送

**用途**：发送带任务 ID、进度、状态的结构化事件，适合长时间运行的任务追踪

**参数**：
- `run_id` (string, 必选): 任务唯一标识符
- `event` (string, 必选): 事件类型，可选值：
  - `start`: 任务开始
  - `update`: 任务进度更新
  - `end`: 任务成功完成
  - `error`: 任务失败
- `message` (string, 必选): 人类可读的状态描述
- `data` (object, 可选): 附加数据，支持以下字段：
  - `step` (string): 当前执行步骤
  - `progress` (float): 进度百分比（0-1）
  - `artifact_url` (string): 生成的产物地址
  - 其他自定义字段
- `timestamp` (string, 可选): ISO 8601 格式时间戳，默认为当前时间

**返回值**：
```json
{
  "success": true,
  "message": "事件已推送",
  "event_type": "update"
}
```

**调用示例**：
```python
# 任务开始
await mcp_client.call_tool("notify.event", {
  "run_id": "data-analysis-20240101-001",
  "event": "start",
  "message": "开始分析 10GB 日志数据"
})

# 进度更新
await mcp_client.call_tool("notify.event", {
  "run_id": "data-analysis-20240101-001",
  "event": "update",
  "message": "已处理 3.2GB (32%)",
  "data": {
    "step": "data_parsing",
    "progress": 0.32
  }
})

# 任务完成
await mcp_client.call_tool("notify.event", {
  "run_id": "data-analysis-20240101-001",
  "event": "end",
  "message": "分析完成，共发现 127 个异常事件",
  "data": {
    "step": "generate_report",
    "progress": 1.0,
    "artifact_url": "https://example.com/reports/20240101-001.html"
  }
})

# 任务失败
await mcp_client.call_tool("notify.event", {
  "run_id": "deployment-002",
  "event": "error",
  "message": "部署失败：数据库连接超时",
  "data": {
    "step": "db_migration",
    "error_code": "ECONNREFUSED"
  }
})
```

---

### 3. 使用场景

#### ✅ 必须使用 notify.event（结构化事件）

以下场景**强制使用** `notify.event`：

1. **长时间任务追踪**（预计执行时间 > 30 秒）
   - 数据分析、报告生成、批量处理
   - 模型训练、代码编译、系统部署

2. **多步骤流程**（需要展示当前步骤）
   - CI/CD 流程、ETL 流水线
   - 多阶段数据处理

3. **进度可量化**（可计算百分比）
   - 文件上传/下载、数据库迁移
   - 批量 API 调用

**示例场景**：
```python
# 场景：执行数据库备份（预计 5 分钟）
# 步骤：连接数据库 → 导出数据 → 压缩文件 → 上传存储

# Step 1: 开始
await mcp_client.call_tool("notify.event", {
  "run_id": "backup-20240101-003",
  "event": "start",
  "message": "开始备份生产数据库"
})

# Step 2: 进度更新
await mcp_client.call_tool("notify.event", {
  "run_id": "backup-20240101-003",
  "event": "update",
  "message": "正在导出数据表 (15/50)",
  "data": {"step": "export_tables", "progress": 0.3}
})

# Step 3: 完成
await mcp_client.call_tool("notify.event", {
  "run_id": "backup-20240101-003",
  "event": "end",
  "message": "备份完成，文件大小 2.3GB",
  "data": {
    "artifact_url": "s3://backups/prod-20240101.sql.gz"
  }
})
```

---

#### ✅ 可以使用 notify.send（简单消息）

以下场景使用 `notify.send` 即可：

1. **即时通知**（执行时间 < 5 秒）
   - 系统告警、异常提醒
   - 简单任务完成通知

2. **无需追踪**（一次性消息）
   - 定时任务执行结果
   - 系统状态快照

3. **无进度概念**（无法量化进度）
   - 用户操作日志
   - 简单信息同步

**示例场景**：
```python
# 场景：定时检查磁盘空间
await mcp_client.call_tool("notify.send", {
  "title": "磁盘空间告警",
  "content": "服务器 prod-01 磁盘使用率 92%，剩余 8GB"
})

# 场景：API 调用失败
await mcp_client.call_tool("notify.send", {
  "title": "API 调用失败",
  "content": "第三方服务 payment-api 返回 500 错误\n错误信息：Internal Server Error\n时间：2024-01-01 14:32:15"
})
```

---

### 4. 调用规范

**必须遵守**：

1. **run_id 命名规范**（使用 `notify.event` 时）
   - 格式：`{任务类型}-{日期}-{序号}`
   - 示例：`backup-20240101-001`, `deployment-prod-003`
   - **同一任务的所有事件必须使用相同的 run_id**

2. **event 状态转换**（使用 `notify.event` 时）
   - 正常流程：`start` → `update` (多次) → `end`
   - 异常流程：`start` → `update` (多次) → `error`
   - **禁止跳过 start 事件**
   - **禁止在 end/error 后继续发送 update**

3. **progress 取值范围**（使用 `notify.event` 时）
   - 必须在 `0.0` 到 `1.0` 之间（0% 到 100%）
   - `start` 事件可省略或设为 `0.0`
   - `end` 事件必须设为 `1.0`
   - `error` 事件应反映失败时的实际进度

4. **消息长度限制**
   - `title`: 建议 < 100 字符
   - `content` / `message`: 建议 < 2000 字符
   - 超长内容会被部分渠道截断

5. **调用频率**
   - `notify.send`: 无限制，但建议避免短时间大量调用
   - `notify.event`: 同一 `run_id` 的 `update` 事件建议间隔 > 5 秒

---

### 5. 注意事项

#### 错误处理
- **推送失败不影响主流程**：mcp-push 的推送是异步的，即使所有渠道都失败，也不应阻塞任务执行
- **无需检查返回值**：工具返回的 `success` 字段仅表示推送请求已接受，不代表所有渠道推送成功

#### 内容格式
- **支持换行**：`\n` 会被转换为实际换行（部分渠道如钉钉需要 `\n\n` 才能换行）
- **Markdown 支持**：部分渠道（如 PushDeer、PushPlus）支持 Markdown 格式
- **特殊字符**：避免使用过多特殊符号，可能被某些渠道转义
---

### 6. 完整工作流示例

#### 示例 1：代码编译部署流程

```python
run_id = "deploy-frontend-20240101-005"

# 1. 开始
await mcp_client.call_tool("notify.event", {
  "run_id": run_id,
  "event": "start",
  "message": "开始部署前端应用到生产环境"
})

# 2. 安装依赖
await mcp_client.call_tool("notify.event", {
  "run_id": run_id,
  "event": "update",
  "message": "正在安装 npm 依赖...",
  "data": {"step": "npm_install", "progress": 0.2}
})

# 3. 构建
await mcp_client.call_tool("notify.event", {
  "run_id": run_id,
  "event": "update",
  "message": "正在构建生产版本...",
  "data": {"step": "build", "progress": 0.5}
})

# 4. 上传
await mcp_client.call_tool("notify.event", {
  "run_id": run_id,
  "event": "update",
  "message": "正在上传到 CDN...",
  "data": {"step": "upload_cdn", "progress": 0.8}
})

# 5. 完成
await mcp_client.call_tool("notify.event", {
  "run_id": run_id,
  "event": "end",
  "message": "部署成功！新版本已上线",
  "data": {
    "progress": 1.0,
    "artifact_url": "https://app.example.com"
  }
})
```

---

#### 示例 2：异常处理流程

```python
run_id = "backup-database-20240101-007"

try:
    # 开始备份
    await mcp_client.call_tool("notify.event", {
      "run_id": run_id,
      "event": "start",
      "message": "开始备份数据库"
    })

    # 执行备份操作...
    # 假设在 60% 时发生错误

except DatabaseConnectionError as e:
    # 发送错误事件
    await mcp_client.call_tool("notify.event", {
      "run_id": run_id,
      "event": "error",
      "message": f"备份失败：{str(e)}",
      "data": {
        "step": "export_data",
        "progress": 0.6,
        "error_code": "DB_CONNECTION_TIMEOUT"
      }
    })
```

**核心原则**：mcp-push 是你的**异步通知助手**，用于在关键节点告知用户任务状态，让用户无需盯着屏幕等待。善用事件流可以极大提升用户体验。
