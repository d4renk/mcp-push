/**
 * Claude Code Runner Completion Hook - 直接集成版本
 *
 * 使用方式：
 * 1. 将此文件复制到 Claude Code 源码的 runner 目录
 * 2. 在 AgentRunner 类中导入并使用
 * 3. 在任务启动时记录 startedAt
 * 4. 在任务结束/错误/需要用户确认时调用 onRunEvent
 */

// ============================================================================
// 类型定义
// ============================================================================

type RunEvent = "end" | "error" | "needs_user_action";

interface RunContext {
  runId: string;
  startedAt: number;
  mcpClient: MCPClient; // 假设 Claude Code 有 MCP 客户端
}

interface MCPClient {
  callTool(server: string, tool: string, params: any): Promise<any>;
}

interface NotifySendParams {
  title: string;
  content: string;
  ignore_default_config?: boolean;
}

interface NotifyEventParams {
  run_id: string;
  event: "start" | "update" | "end" | "error";
  message: string;
  timestamp?: string;
  data?: {
    duration_ms?: number;
    step?: string;
    progress?: number;
    artifact_url?: string;
    error_code?: string;
    [key: string]: any;
  };
}

// ============================================================================
// 核心实现
// ============================================================================

/**
 * 任务完成时的核心 hook 逻辑
 *
 * @param ctx - 运行上下文
 * @param event - 事件类型
 * @param msg - 消息内容
 */
async function onRunEvent(
  ctx: RunContext,
  event: RunEvent,
  msg: string
): Promise<void> {
  const elapsedMs = Date.now() - ctx.startedAt;
  const isLongRun = elapsedMs > 60_000;

  // 小于 60s 不推送任何通知
  if (!isLongRun) return;

  // 需要用户确认的场景
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

// ============================================================================
// RunContext 辅助方法扩展
// ============================================================================

/**
 * 为 RunContext 添加 push 方法
 */
function createRunContextWithPush(
  runId: string,
  startedAt: number,
  mcpClient: MCPClient
): RunContext & { push: PushFunction } {
  const ctx: RunContext = {
    runId,
    startedAt,
    mcpClient,
  };

  return {
    ...ctx,
    push: createPushFunction(mcpClient),
  };
}

type PushFunction = (
  tool: "notify_send" | "notify_event",
  params: NotifySendParams | NotifyEventParams
) => Promise<void>;

/**
 * 创建 push 函数，用于调用 mcp-push 工具
 */
function createPushFunction(mcpClient: MCPClient): PushFunction {
  return async (tool, params) => {
    try {
      await mcpClient.callTool("mcp-push", tool, params);
    } catch (error) {
      console.error(`[CompletionHook] Failed to call ${tool}:`, error);
      // 不抛出错误，避免影响主流程
    }
  };
}

// ============================================================================
// 完整的 CompletionHook 类（可选，更面向对象的实现）
// ============================================================================

export class CompletionHook {
  private runId: string;
  private startedAt: number;
  private mcpClient: MCPClient;
  private context: RunContext & { push: PushFunction };

  constructor(mcpClient: MCPClient) {
    this.mcpClient = mcpClient;
    this.runId = this.generateRunId();
    this.startedAt = Date.now();
    this.context = createRunContextWithPush(
      this.runId,
      this.startedAt,
      mcpClient
    );
  }

  /**
   * 任务完成时调用
   */
  async onSuccess(message: string): Promise<void> {
    await onRunEvent(this.context, "end", message);
  }

  /**
   * 任务失败时调用
   */
  async onError(error: Error | string): Promise<void> {
    const message = typeof error === "string" ? error : error.message;
    await onRunEvent(this.context, "error", message);
  }

  /**
   * 需要用户确认时调用
   */
  async onNeedsUserAction(prompt: string): Promise<void> {
    await onRunEvent(this.context, "needs_user_action", prompt);
  }

  /**
   * 获取当前运行时长（毫秒）
   */
  getElapsedTime(): number {
    return Date.now() - this.startedAt;
  }

  /**
   * 获取运行 ID
   */
  getRunId(): string {
    return this.runId;
  }

  /**
   * 重置计时器（用于子任务）
   */
  reset(): void {
    this.startedAt = Date.now();
    this.runId = this.generateRunId();
    this.context = createRunContextWithPush(
      this.runId,
      this.startedAt,
      this.mcpClient
    );
  }

  private generateRunId(): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 11);
    return `run-${timestamp}-${random}`;
  }
}

// ============================================================================
// 导出
// ============================================================================

export {
  onRunEvent,
  createRunContextWithPush,
  createPushFunction,
  type RunEvent,
  type RunContext,
  type MCPClient,
  type NotifySendParams,
  type NotifyEventParams,
  type PushFunction,
};
