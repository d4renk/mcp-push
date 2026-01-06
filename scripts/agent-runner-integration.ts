/**
 * AgentRunner 集成示例
 *
 * 演示如何在 Claude Code 的 AgentRunner 中集成 CompletionHook
 */

import { CompletionHook, onRunEvent, createRunContextWithPush } from './runner-completion-hook';
import type { MCPClient } from './runner-completion-hook';

// ============================================================================
// 示例 1: 使用 CompletionHook 类（推荐）
// ============================================================================

export class AgentRunner {
  private completionHook: CompletionHook;
  private mcpClient: MCPClient;

  constructor(mcpClient: MCPClient) {
    this.mcpClient = mcpClient;
    this.completionHook = new CompletionHook(mcpClient);
  }

  /**
   * 运行任务
   */
  async run(task: string): Promise<void> {
    console.log(`[Runner] Starting task: ${task}`);
    console.log(`[Runner] Run ID: ${this.completionHook.getRunId()}`);

    try {
      // 执行任务
      const result = await this.executeTask(task);

      // 任务成功完成 - 触发 completion hook
      await this.completionHook.onSuccess(
        `Task completed successfully: ${result}`
      );

      console.log(`[Runner] Task completed in ${this.completionHook.getElapsedTime()}ms`);
    } catch (error) {
      // 任务失败 - 触发 error hook
      await this.completionHook.onError(error as Error);

      console.error(`[Runner] Task failed after ${this.completionHook.getElapsedTime()}ms`);
      throw error;
    }
  }

  /**
   * 请求用户确认
   */
  async askUserConfirmation(prompt: string): Promise<boolean> {
    // 触发 needs_user_action hook
    await this.completionHook.onNeedsUserAction(prompt);

    // 等待用户输入
    const answer = await this.waitForUserInput(prompt);
    return answer === 'yes';
  }

  /**
   * 执行危险操作（需要用户确认）
   */
  async executeDangerousOperation(operation: string): Promise<void> {
    const confirmed = await this.askUserConfirmation(
      `检测到危险操作：${operation}。是否继续？`
    );

    if (!confirmed) {
      throw new Error('User cancelled the operation');
    }

    // 继续执行...
  }

  private async executeTask(task: string): Promise<string> {
    // 模拟任务执行
    await new Promise((resolve) => setTimeout(resolve, 2000));
    return 'Task result';
  }

  private async waitForUserInput(prompt: string): Promise<string> {
    // 实际的用户输入逻辑
    return 'yes';
  }
}

// ============================================================================
// 示例 2: 使用函数式 API（更灵活）
// ============================================================================

export class FlexibleRunner {
  private mcpClient: MCPClient;

  constructor(mcpClient: MCPClient) {
    this.mcpClient = mcpClient;
  }

  async run(task: string): Promise<void> {
    const runId = this.generateRunId();
    const startedAt = Date.now();
    const ctx = createRunContextWithPush(runId, startedAt, this.mcpClient);

    try {
      const result = await this.executeTask(task);

      // 直接调用 onRunEvent
      await onRunEvent(ctx, 'end', `Task completed: ${result}`);
    } catch (error) {
      await onRunEvent(ctx, 'error', (error as Error).message);
      throw error;
    }
  }

  private generateRunId(): string {
    return `run-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
  }

  private async executeTask(task: string): Promise<string> {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    return 'Task result';
  }
}

// ============================================================================
// 示例 3: 集成到现有 Runner（最小化修改）
// ============================================================================

/**
 * 假设这是现有的 AgentRunner 类
 */
export class ExistingAgentRunner {
  private mcpClient: MCPClient;
  private completionHook: CompletionHook | null = null;

  constructor(mcpClient: MCPClient) {
    this.mcpClient = mcpClient;
  }

  /**
   * 现有的 run 方法，只需添加少量代码
   */
  async run(task: string): Promise<void> {
    // ✅ 添加：初始化 completion hook
    this.completionHook = new CompletionHook(this.mcpClient);

    try {
      // 现有的任务执行逻辑
      const result = await this.doSomething(task);
      await this.doSomethingElse(result);

      // ✅ 添加：任务成功完成
      await this.completionHook.onSuccess('All tasks completed successfully');
    } catch (error) {
      // ✅ 添加：任务失败
      await this.completionHook.onError(error as Error);
      throw error;
    }
  }

  /**
   * 现有的用户交互方法，只需添加一行
   */
  async promptUser(message: string): Promise<string> {
    // ✅ 添加：触发 needs_user_action hook
    if (this.completionHook) {
      await this.completionHook.onNeedsUserAction(message);
    }

    // 现有的用户输入逻辑
    return this.readUserInput(message);
  }

  // 现有方法保持不变
  private async doSomething(task: string): Promise<any> {
    return {};
  }

  private async doSomethingElse(result: any): Promise<void> {}

  private readUserInput(message: string): Promise<string> {
    return Promise.resolve('user input');
  }
}

// ============================================================================
// 示例 4: 批量任务处理
// ============================================================================

export class BatchRunner {
  private mcpClient: MCPClient;

  constructor(mcpClient: MCPClient) {
    this.mcpClient = mcpClient;
  }

  async runBatch(tasks: string[]): Promise<void> {
    const completionHook = new CompletionHook(this.mcpClient);

    try {
      const results = await Promise.all(
        tasks.map((task) => this.executeTask(task))
      );

      await completionHook.onSuccess(
        `Batch completed: ${results.length} tasks processed`
      );
    } catch (error) {
      await completionHook.onError(error as Error);
      throw error;
    }
  }

  private async executeTask(task: string): Promise<string> {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return `Result for ${task}`;
  }
}

// ============================================================================
// 示例 5: 子任务追踪（重置计时器）
// ============================================================================

export class SubTaskRunner {
  private mcpClient: MCPClient;
  private completionHook: CompletionHook;

  constructor(mcpClient: MCPClient) {
    this.mcpClient = mcpClient;
    this.completionHook = new CompletionHook(mcpClient);
  }

  async runMainTask(): Promise<void> {
    try {
      // 主任务
      await this.executeSubTask('subtask-1');
      await this.executeSubTask('subtask-2');

      await this.completionHook.onSuccess('Main task completed');
    } catch (error) {
      await this.completionHook.onError(error as Error);
      throw error;
    }
  }

  private async executeSubTask(name: string): Promise<void> {
    // 为子任务重置计时器（可选）
    this.completionHook.reset();

    console.log(`[SubTask] ${name} started, Run ID: ${this.completionHook.getRunId()}`);

    // 执行子任务...
    await new Promise((resolve) => setTimeout(resolve, 30000)); // 30 秒

    console.log(`[SubTask] ${name} completed in ${this.completionHook.getElapsedTime()}ms`);
  }
}

// ============================================================================
// Mock MCP Client（用于测试）
// ============================================================================

class MockMCPClient implements MCPClient {
  async callTool(server: string, tool: string, params: any): Promise<any> {
    console.log(`[MockMCP] ${server}.${tool}(${JSON.stringify(params, null, 2)})`);
    return { success: true };
  }
}

// ============================================================================
// 测试代码
// ============================================================================

async function testRunner() {
  const mcpClient = new MockMCPClient();
  const runner = new AgentRunner(mcpClient);

  console.log('\n=== Test 1: Short task (< 60s) ===');
  await runner.run('Short task');
  // 预期：不推送通知

  console.log('\n=== Test 2: Long task (> 60s) ===');
  // 模拟长时间任务
  const longRunner = new AgentRunner(mcpClient);
  (longRunner as any).completionHook.startedAt = Date.now() - 70000; // 70 秒前
  await longRunner.run('Long task');
  // 预期：推送"任务完成"通知

  console.log('\n=== Test 3: Task with user confirmation ===');
  await runner.askUserConfirmation('Delete all files?');
  // 预期：推送"等待批准"通知（如果 > 60s）

  console.log('\n=== Test 4: Failed task ===');
  const failRunner = new AgentRunner(mcpClient);
  (failRunner as any).completionHook.startedAt = Date.now() - 90000; // 90 秒前
  try {
    (failRunner as any).executeTask = async () => {
      throw new Error('Task failed');
    };
    await failRunner.run('Failing task');
  } catch (error) {
    // 预期：推送"任务失败"通知
  }
}

// 运行测试（如果直接执行此文件）
if (require.main === module) {
  testRunner().catch(console.error);
}
