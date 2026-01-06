# Claude Code Runner Completion Hook - 直接集成方案

## 概述

这是一个**直接在 Claude Code runner 中实现**的 completion hook 方案，无需外部 shell 脚本，由程序自动判断任务耗时并调用 mcp-push 推送通知。

### 核心思路

```
模型（不计时，不推送）
        ↓
    执行任务
        ↓
Runner（记录 startedAt）
        ↓
任务结束/失败/等待用户
        ↓
   判断耗时 > 60s？
        ↓
   自动推送通知
```

## 文件说明

### 1. `runner-completion-hook.ts` - 核心实现

包含：
- **类型定义**：`RunEvent`, `RunContext`, `MCPClient` 等
- **核心函数**：`onRunEvent()` - 60 秒阈值判断和推送逻辑
- **CompletionHook 类**：面向对象封装，提供 `onSuccess()`, `onError()`, `onNeedsUserAction()` 方法
- **辅助函数**：`createRunContextWithPush()`, `createPushFunction()`

### 2. `agent-runner-integration.ts` - 集成示例

提供 5 种集成方式：
1. **使用 CompletionHook 类**（推荐）
2. **使用函数式 API**（更灵活）
3. **最小化修改现有 Runner**
4. **批量任务处理**
5. **子任务追踪**

## 快速开始

### 步骤 1: 复制文件到 Claude Code 源码

```bash
# 假设 Claude Code 源码路径为 ~/claude-code
cp runner-completion-hook.ts ~/claude-code/src/runner/
cp agent-runner-integration.ts ~/claude-code/src/runner/
```

### 步骤 2: 修改 AgentRunner

找到 `AgentRunner` 类（假设在 `src/runner/agent-runner.ts`），添加以下代码：

```typescript
// 在文件开头导入
import { CompletionHook } from './runner-completion-hook';

export class AgentRunner {
  private completionHook: CompletionHook;

  constructor(mcpClient: MCPClient) {
    // ✅ 初始化 completion hook
    this.completionHook = new CompletionHook(mcpClient);
  }

  async run(task: string): Promise<void> {
    try {
      // 现有的任务执行逻辑...
      const result = await this.executeTask(task);

      // ✅ 任务成功 - 触发 hook
      await this.completionHook.onSuccess('Task completed successfully');
    } catch (error) {
      // ✅ 任务失败 - 触发 hook
      await this.completionHook.onError(error as Error);
      throw error;
    }
  }

  async promptUser(message: string): Promise<string> {
    // ✅ 需要用户确认 - 触发 hook
    await this.completionHook.onNeedsUserAction(message);

    // 现有的用户输入逻辑...
    return this.getUserInput(message);
  }
}
```

### 步骤 3: 配置 MCP 客户端

确保 Claude Code 的 MCP 客户端可以调用 `mcp-push` 服务器：

```typescript
// 在 MCPClient 实现中
class MCPClientImpl implements MCPClient {
  async callTool(server: string, tool: string, params: any): Promise<any> {
    // 调用 MCP 服务器的工具
    return await this.servers[server].invoke(tool, params);
  }
}
```

### 步骤 4: 重新编译

```bash
cd ~/claude-code
npm run build
```

## 核心 API

### CompletionHook 类

```typescript
class CompletionHook {
  constructor(mcpClient: MCPClient);

  // 任务成功完成
  async onSuccess(message: string): Promise<void>;

  // 任务失败
  async onError(error: Error | string): Promise<void>;

  // 需要用户确认
  async onNeedsUserAction(prompt: string): Promise<void>;

  // 获取运行时长（毫秒）
  getElapsedTime(): number;

  // 获取运行 ID
  getRunId(): string;

  // 重置计时器（用于子任务）
  reset(): void;
}
```

### onRunEvent 函数

```typescript
async function onRunEvent(
  ctx: RunContext,
  event: RunEvent,
  msg: string
): Promise<void>;
```

**参数**：
- `ctx.runId`: 任务唯一 ID
- `ctx.startedAt`: 任务开始时间戳（毫秒）
- `ctx.push`: 推送函数（调用 notify_send / notify_event）
- `event`: `"end"` | `"error"` | `"needs_user_action"`
- `msg`: 消息内容

**逻辑**：
```typescript
const elapsedMs = Date.now() - ctx.startedAt;

if (elapsedMs < 60_000) {
  return; // 不推送
}

if (event === "needs_user_action") {
  await ctx.push("notify_send", {
    title: "等待批准",
    content: msg,
  });
  return;
}

// 任务完成/失败
await ctx.push("notify_send", {
  title: event === "end" ? "任务完成" : "任务失败",
  content: msg,
});

await ctx.push("notify_event", {
  run_id: ctx.runId,
  event,
  message: msg,
  data: { duration_ms: elapsedMs },
});
```

## 集成模式

### 模式 1: 面向对象（推荐）

```typescript
class AgentRunner {
  private completionHook: CompletionHook;

  constructor(mcpClient: MCPClient) {
    this.completionHook = new CompletionHook(mcpClient);
  }

  async run(task: string) {
    try {
      await this.executeTask(task);
      await this.completionHook.onSuccess('Done');
    } catch (error) {
      await this.completionHook.onError(error);
      throw error;
    }
  }
}
```

**优点**：
- 清晰易读
- 自动管理 runId 和 startedAt
- 提供辅助方法（getElapsedTime, reset 等）

### 模式 2: 函数式

```typescript
async function runTask(mcpClient: MCPClient, task: string) {
  const ctx = createRunContextWithPush(
    generateRunId(),
    Date.now(),
    mcpClient
  );

  try {
    const result = await executeTask(task);
    await onRunEvent(ctx, 'end', 'Task completed');
  } catch (error) {
    await onRunEvent(ctx, 'error', error.message);
  }
}
```

**优点**：
- 更灵活
- 可以在不同位置调用
- 适合现有函数式代码

### 模式 3: 最小化修改

```typescript
class ExistingRunner {
  async run(task: string) {
    const hook = new CompletionHook(this.mcpClient);

    try {
      // 现有代码保持不变
      await this.doExistingStuff(task);

      // 仅添加一行
      await hook.onSuccess('Done');
    } catch (error) {
      await hook.onError(error);
      throw error;
    }
  }
}
```

**优点**：
- 对现有代码侵入性最小
- 易于回滚

## 推送示例

### 场景 1: 短任务（30 秒）

```typescript
const hook = new CompletionHook(mcpClient);
await sleep(30000);
await hook.onSuccess('Quick task done');
```

**结果**：不推送（< 60 秒）

### 场景 2: 长任务（90 秒，成功）

```typescript
const hook = new CompletionHook(mcpClient);
await sleep(90000);
await hook.onSuccess('Long task completed');
```

**推送**：
```json
// notify_send
{
  "title": "任务完成",
  "content": "Long task completed"
}

// notify_event
{
  "run_id": "run-1735468800000-a1b2c3",
  "event": "end",
  "message": "Long task completed",
  "data": { "duration_ms": 90123 }
}
```

### 场景 3: 长任务（120 秒，失败）

```typescript
const hook = new CompletionHook(mcpClient);
await sleep(120000);
await hook.onError(new Error('Database connection failed'));
```

**推送**：
```json
// notify_send
{
  "title": "任务失败",
  "content": "Database connection failed"
}

// notify_event
{
  "run_id": "run-1735468800000-x9y8z7",
  "event": "error",
  "message": "Database connection failed",
  "data": { "duration_ms": 120456 }
}
```

### 场景 4: 需要用户确认（70 秒）

```typescript
const hook = new CompletionHook(mcpClient);
await sleep(70000);
await hook.onNeedsUserAction('Delete all files?');
```

**推送**：
```json
// 仅 notify_send（不发送 notify_event）
{
  "title": "等待批准",
  "content": "Delete all files?"
}
```

## 测试

### 单元测试

```typescript
import { CompletionHook } from './runner-completion-hook';

describe('CompletionHook', () => {
  it('should not push for short tasks', async () => {
    const mockClient = new MockMCPClient();
    const hook = new CompletionHook(mockClient);

    await hook.onSuccess('Quick task');

    expect(mockClient.calls).toHaveLength(0);
  });

  it('should push for long tasks', async () => {
    const mockClient = new MockMCPClient();
    const hook = new CompletionHook(mockClient);

    // 模拟 70 秒前开始
    (hook as any).startedAt = Date.now() - 70000;

    await hook.onSuccess('Long task');

    expect(mockClient.calls).toHaveLength(2); // notify_send + notify_event
  });
});
```

### 集成测试

```bash
# 运行示例代码
npm run test:integration

# 或直接执行
npx ts-node agent-runner-integration.ts
```

## 调试

启用调试日志：

```typescript
// 在 onRunEvent 中添加
console.log(`[CompletionHook] Event: ${event}, Elapsed: ${elapsedMs}ms`);

// 在 push 函数中添加
console.log(`[CompletionHook] Calling ${tool} with:`, params);
```

查看推送记录：

```bash
# 如果 mcp-push 有日志
tail -f ~/.mcp-push/logs/notify.log
```

## 常见问题

### Q1: 如何调整 60 秒阈值？

在 `onRunEvent` 函数中修改：

```typescript
const isLongRun = elapsedMs > 120_000; // 改为 120 秒
```

### Q2: 如何为不同任务设置不同阈值？

```typescript
class CompletionHook {
  constructor(
    mcpClient: MCPClient,
    private threshold: number = 60_000 // 可配置
  ) {
    // ...
  }

  async onSuccess(message: string): Promise<void> {
    const elapsedMs = Date.now() - this.startedAt;
    if (elapsedMs < this.threshold) return;
    // ...
  }
}

// 使用
const hook = new CompletionHook(mcpClient, 120_000); // 120 秒
```

### Q3: 如何避免重复推送？

```typescript
class CompletionHook {
  private hasNotified = false;

  async onSuccess(message: string): Promise<void> {
    if (this.hasNotified) return;
    // ...
    this.hasNotified = true;
  }
}
```

### Q4: 如何处理子任务？

```typescript
const mainHook = new CompletionHook(mcpClient);

for (const subtask of subtasks) {
  // 为每个子任务创建新的 hook
  const subHook = new CompletionHook(mcpClient);
  await executeSubtask(subtask);
  await subHook.onSuccess(`Subtask ${subtask} done`);
}

await mainHook.onSuccess('All subtasks done');
```

## 性能考虑

- **异步推送**：hook 调用不会阻塞主流程（使用 `await` 但捕获错误）
- **失败容错**：推送失败不影响任务执行
- **最小开销**：仅在任务结束时判断，无需轮询

## 迁移指南

从旧的实现迁移：

```typescript
// 旧代码
class OldRunner {
  async run() {
    try {
      await this.task();
      await this.sendNotification('Done'); // 模型决定是否推送
    } catch (error) {
      await this.sendNotification('Failed');
    }
  }
}

// 新代码
class NewRunner {
  async run() {
    const hook = new CompletionHook(this.mcpClient);
    try {
      await this.task();
      await hook.onSuccess('Done'); // runner 自动判断
    } catch (error) {
      await hook.onError(error);
    }
  }
}
```

## 下一步

1. 复制文件到 Claude Code 源码
2. 在 AgentRunner 中集成
3. 编译测试
4. 运行长任务验证推送
5. 根据需要调整阈值和消息格式

## 文件清单

- ✅ `runner-completion-hook.ts` - 核心实现
- ✅ `agent-runner-integration.ts` - 集成示例
- ✅ `RUNNER_INTEGRATION.md` - 本文档
- ✅ `completion-hook.sh` - Shell 脚本版本（备选）
- ✅ `INTEGRATION_GUIDE.md` - 通用集成指南
