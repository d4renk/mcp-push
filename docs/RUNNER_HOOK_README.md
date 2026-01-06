# Claude Code Runner Completion Hook

直接在 Claude Code runner 中实现的任务完成通知系统。

## 文件说明

### 核心实现
- **`runner-completion-hook.ts`** - 核心 hook 实现
  - `onRunEvent()` 函数：60 秒阈值判断和推送逻辑
  - `CompletionHook` 类：面向对象封装
  - TypeScript 类型定义

### 集成示例
- **`agent-runner-integration.ts`** - AgentRunner 集成示例
  - 5 种集成模式
  - 单元测试示例
  - Mock MCP 客户端

### 文档
- **`RUNNER_INTEGRATION.md`** - 详细集成文档
  - 快速开始指南
  - API 文档
  - 推送场景示例
  - 常见问题

### 备选方案
- **`completion-hook.sh`** - Shell 脚本版本
- **`claude-code-hook-example.json`** - Settings 配置示例
- **`INTEGRATION_GUIDE.md`** - 通用集成指南

## 快速开始

### 1. 复制核心文件

```bash
cp runner-completion-hook.ts ~/claude-code/src/runner/
```

### 2. 修改 AgentRunner

```typescript
import { CompletionHook } from './runner-completion-hook';

export class AgentRunner {
  private completionHook: CompletionHook;

  constructor(mcpClient: MCPClient) {
    this.completionHook = new CompletionHook(mcpClient);
  }

  async run(task: string): Promise<void> {
    try {
      await this.executeTask(task);
      await this.completionHook.onSuccess('Task completed');
    } catch (error) {
      await this.completionHook.onError(error);
      throw error;
    }
  }

  async promptUser(message: string): Promise<string> {
    await this.completionHook.onNeedsUserAction(message);
    return this.getUserInput(message);
  }
}
```

### 3. 重新编译

```bash
cd ~/claude-code
npm run build
```

## 核心逻辑

```typescript
async function onRunEvent(ctx: RunContext, event: RunEvent, msg: string) {
  const elapsedMs = Date.now() - ctx.startedAt;
  const isLongRun = elapsedMs > 60_000;

  if (!isLongRun) return; // 小于 60s 不推送

  if (event === "needs_user_action") {
    await ctx.push("notify_send", {
      title: "等待批准",
      content: msg,
    });
    return;
  }

  // 任务完成/失败且耗时 > 60s
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
}
```

## 推送规则

| 场景 | 耗时 | 推送 |
|------|------|------|
| 任务成功 | < 60s | ❌ 不推送 |
| 任务成功 | > 60s | ✅ notify_send + notify_event |
| 任务失败 | < 60s | ❌ 不推送 |
| 任务失败 | > 60s | ✅ notify_send + notify_event |
| 等待用户 | > 60s | ✅ 仅 notify_send |

## 优势

- ✅ **模型无感知**：模型专注任务，runner 负责推送
- ✅ **自动判断**：无需手动计时，自动 60 秒阈值
- ✅ **类型安全**：完整的 TypeScript 类型定义
- ✅ **易于集成**：最小化代码修改
- ✅ **容错性好**：推送失败不影响主流程

## 文档

查看 `RUNNER_INTEGRATION.md` 获取：
- 完整 API 文档
- 集成模式对比
- 推送场景示例
- 测试方法
- 常见问题

## 许可

与 mcp-push 项目一致
