# Claude Code Completion Hook 实现指南

## 概述

实现一个自动化的任务完成通知机制：
- **60 秒阈值**：仅当任务运行超过 60 秒时推送通知
- **三种事件**：`end`（成功）、`error`（失败）、`needs_user_action`（等待确认）
- **自动调用 mcp-push**：由 runner 自动触发，模型无需关心

## 架构设计

```
┌─────────────────┐
│  AgentRunner    │
│  ┌───────────┐  │
│  │ startedAt │  │  记录开始时间
│  └───────────┘  │
└────────┬────────┘
         │
         ▼
    任务执行中...
         │
         ▼
┌────────┴────────┐
│  任务结束判断   │
│  ┌───────────┐  │
│  │elapsed>60s│──┼──No──▶ 不推送
│  └─────┬─────┘  │
│        │Yes     │
└────────┼────────┘
         ▼
┌────────┴────────┐
│  Hook Executor  │
│  ┌───────────┐  │
│  │ Shell脚本 │  │
│  └─────┬─────┘  │
└────────┼────────┘
         ▼
┌────────┴────────┐
│   mcp-push      │
│  notify_send /  │
│  notify_event   │
└─────────────────┘
```

## 文件说明

### 1. `completion-hook.sh`
Shell 脚本，负责：
- 接收 runner 传递的参数（event, message, run_id, started_at）
- 计算任务耗时
- 判断是否超过 60 秒
- 调用 mcp-push 的 notify_send / notify_event

**使用方式**：
```bash
# 安装到用户 hooks 目录
mkdir -p ~/.claude/hooks
cp completion-hook.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/completion-hook.sh
```

### 2. `completion-hook-linux.sh`
Linux 版 Stop Hook 脚本，负责：
- 从 stdin 读取 Stop 事件 JSON 输入
- 从 transcript 解析任务状态（成功/失败/需确认）
- 从 session 解析开始时间并计算耗时
- 使用 `codex mcp call` 调用 mcp-push

**使用方式**：
```bash
mkdir -p ~/.claude/hooks
cp completion-hook-linux.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/completion-hook-linux.sh
```

### 3. `stop-hook-config.json`
Stop 事件的配置示例（Claude Code Hooks 标准格式）。

### 4. `claude-code-hook-example.json`
Claude Code 的 settings.json 配置示例，定义三个 hook：
- `run-complete`: 任务成功完成
- `run-error`: 任务失败
- `run-needs-action`: 需要用户确认

**集成方式**：
```bash
# 合并到 ~/.claude/settings.json
cat claude-code-hook-example.json >> ~/.claude/settings.json
```

### 5. `completion-hook-runner.ts`
TypeScript 实现，用于修改 Claude Code 源码：
- `CompletionHookRunner`: Hook 执行器
- `AgentRunner`: 集成示例

**集成位置**：
- 在 Claude Code 的 `runner/executor` 主循环中
- 在任务开始时记录 `startedAt`
- 在任务结束/失败/等待用户时调用 `onRunEvent()`

## 实现步骤

### 方案 A：使用 Stop Hook（Linux + Codex CLI）**推荐**

使用 Claude Code 内建 `Stop` 事件，无需改源码。

1. 安装脚本：
```bash
mkdir -p ~/.claude/hooks
cp completion-hook-linux.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/completion-hook-linux.sh
```

2. 配置 Stop Hook（示例见 `stop-hook-config.json`）：
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/completion-hook-linux.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

3. 确保已安装 `jq` 且 `codex` CLI 可用。

### 方案 B：仅使用配置（无需改源码）

如果 Claude Code 已经支持这些 hook 事件：

1. 安装 shell 脚本：
```bash
mkdir -p ~/.claude/hooks
cp completion-hook.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/completion-hook.sh
```

2. 配置 settings.json：
```json
{
  "hooks": {
    "run-complete": {
      "command": "~/.claude/hooks/completion-hook.sh",
      "args": ["end", "{{message}}", "{{run_id}}", "{{started_at}}"]
    },
    "run-error": {
      "command": "~/.claude/hooks/completion-hook.sh",
      "args": ["error", "{{message}}", "{{run_id}}", "{{started_at}}"]
    },
    "run-needs-action": {
      "command": "~/.claude/hooks/completion-hook.sh",
      "args": ["needs_user_action", "{{message}}", "{{run_id}}", "{{started_at}}"]
    }
  }
}
```

### 方案 C：修改 Claude Code 源码

如果 Claude Code 尚未支持这些 hook 事件：

#### 1. 找到 runner 入口文件

假设路径为 `claude-code/src/runner/agent-runner.ts`：

```typescript
import { CompletionHookRunner } from './completion-hook-runner';

export class AgentRunner {
  private startedAt: number = 0;
  private runId: string = '';
  private hookRunner: CompletionHookRunner;

  constructor(settings: Settings) {
    this.hookRunner = new CompletionHookRunner(settings);
  }

  async run(task: string): Promise<void> {
    this.startedAt = Date.now();
    this.runId = `run-${Date.now()}-${crypto.randomUUID()}`;

    try {
      const result = await this.executeTask(task);

      // 触发 run-complete hook
      await this.hookRunner.onRunEvent({
        runId: this.runId,
        startedAt: this.startedAt,
        message: `Task completed successfully`,
      }, 'end');
    } catch (error) {
      // 触发 run-error hook
      await this.hookRunner.onRunEvent({
        runId: this.runId,
        startedAt: this.startedAt,
        message: error.message,
      }, 'error');
    }
  }

  async askUser(prompt: string): Promise<void> {
    // 触发 run-needs-action hook
    await this.hookRunner.onRunEvent({
      runId: this.runId,
      startedAt: this.startedAt,
      message: prompt,
    }, 'needs_user_action');
  }
}
```

#### 2. 复制 `completion-hook-runner.ts` 到源码

```bash
cp completion-hook-runner.ts /path/to/claude-code/src/runner/
```

#### 3. 重新编译 Claude Code

```bash
cd /path/to/claude-code
npm run build
```

## 参数说明

Hook 脚本接收的参数：

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `$1` | event | 事件类型 | `end` / `error` / `needs_user_action` |
| `$2` | message | 消息内容 | `"Task completed successfully"` |
| `$3` | run_id | 任务唯一 ID | `"run-1735468800000-a1b2c3"` |
| `$4` | started_at | 开始时间戳（毫秒） | `1735468740000` |

### Stop Hook 输入（stdin JSON）

Stop 事件会透过 stdin 提供：
- `session_id`
- `transcript_path`
- `cwd`
- `hook_event_name`
- `stop_hook_active`

`completion-hook-linux.sh` 会：
- 使用 `session_id` 作为 `run_id`
- 从 `transcript_path` 解析开始时间与任务状态
- 输出 JSON 控制 Hook 行为（`suppressOutput: true`）

## 推送逻辑

### 场景 1: 任务耗时 < 60s
```
不推送任何通知
```

### 场景 2: 任务耗时 > 60s，成功完成
```
1. notify_send:
   title: "任务完成"
   content: "Task completed successfully"

2. notify_event:
   run_id: "run-xxx"
   event: "end"
   message: "Task completed successfully"
   data: { duration_ms: 75000 }
```

### 场景 3: 任务耗时 > 60s，失败
```
1. notify_send:
   title: "任务失败"
   content: "Error: connection timeout"

2. notify_event:
   run_id: "run-xxx"
   event: "error"
   message: "Error: connection timeout"
   data: { duration_ms: 120000 }
```

### 场景 4: 任务耗时 > 60s，需要用户确认
```
1. notify_send:
   title: "等待批准"
   content: "检测到敏感文件删除操作，请确认是否继续？"
```

## 测试

### 测试 shell 脚本
```bash
# 模拟一个耗时 90 秒的任务完成
STARTED_AT=$(date +%s%3N)
sleep 2  # 模拟延迟
STARTED_AT=$((STARTED_AT - 90000))  # 减去 90 秒

./completion-hook.sh "end" "Test task completed" "test-run-123" "$STARTED_AT"
```

### 测试 TypeScript 集成
```typescript
const runner = new AgentRunner(settings);
await runner.run("Long running task");  // 如果 > 60s，会自动推送
```

## 优势

1. **模型无感知**：模型不需要知道推送逻辑，专注于任务本身
2. **统一管理**：所有推送逻辑在 runner 层统一处理
3. **可配置**：通过 settings.json 灵活配置
4. **低侵入性**：仅在 runner 入口处添加 hook 调用
5. **可测试**：shell 脚本和 TypeScript 都可独立测试

## 注意事项

1. **时间戳精度**：使用毫秒级时间戳（`Date.now()`）
2. **错误处理**：hook 执行失败不应影响主流程
3. **异步执行**：hook 可以异步执行，避免阻塞主流程
4. **权限问题**：确保 shell 脚本有执行权限（`chmod +x`）
5. **MCP 服务器**：确保 mcp-push 已在 Claude Code 中配置
