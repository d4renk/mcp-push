/**
 * Claude Code Runner Completion Hook
 *
 * 集成位置：在 Claude Code 的 runner/executor 主循环中
 * 触发时机：任务完成、失败或需要用户确认时
 *
 * 功能：
 * 1. 记录任务开始时间
 * 2. 在任务结束时判断耗时
 * 3. 超过 60 秒则调用配置的 hook 脚本
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';

const execAsync = promisify(exec);

type RunEvent = 'end' | 'error' | 'needs_user_action';

interface RunContext {
  runId: string;
  startedAt: number;
  message: string;
}

interface HookConfig {
  command: string;
  args: string[];
  description?: string;
}

interface Settings {
  hooks?: {
    'run-complete'?: HookConfig;
    'run-error'?: HookConfig;
    'run-needs-action'?: HookConfig;
  };
}

export class CompletionHookRunner {
  private settings: Settings;

  constructor(settings: Settings) {
    this.settings = settings;
  }

  /**
   * 在任务完成、失败或需要用户确认时调用
   */
  async onRunEvent(ctx: RunContext, event: RunEvent): Promise<void> {
    const elapsedMs = Date.now() - ctx.startedAt;
    const isLongRun = elapsedMs > 60_000;

    // 小于 60 秒不触发 hook
    if (!isLongRun) {
      return;
    }

    const hookConfig = this.getHookConfig(event);
    if (!hookConfig) {
      return; // 未配置 hook
    }

    await this.executeHook(hookConfig, ctx, event);
  }

  /**
   * 获取对应事件的 hook 配置
   */
  private getHookConfig(event: RunEvent): HookConfig | null {
    const hookMap: Record<RunEvent, keyof Settings['hooks']> = {
      end: 'run-complete',
      error: 'run-error',
      needs_user_action: 'run-needs-action',
    };

    const hookName = hookMap[event];
    return this.settings.hooks?.[hookName] || null;
  }

  /**
   * 执行 hook 脚本
   */
  private async executeHook(
    hookConfig: HookConfig,
    ctx: RunContext,
    event: RunEvent
  ): Promise<void> {
    try {
      // 替换参数占位符
      const args = hookConfig.args.map((arg) =>
        this.replacePlaceholders(arg, ctx, event)
      );

      const command = `${hookConfig.command} ${args.map((a) => `"${a}"`).join(' ')}`;

      console.log(`[Hook] Executing: ${command}`);
      const { stdout, stderr } = await execAsync(command);

      if (stdout) console.log(`[Hook stdout] ${stdout}`);
      if (stderr) console.error(`[Hook stderr] ${stderr}`);
    } catch (error) {
      console.error(`[Hook Error] Failed to execute hook:`, error);
    }
  }

  /**
   * 替换参数中的占位符
   */
  private replacePlaceholders(
    template: string,
    ctx: RunContext,
    event: RunEvent
  ): string {
    return template
      .replace('{{message}}', ctx.message)
      .replace('{{run_id}}', ctx.runId)
      .replace('{{started_at}}', ctx.startedAt.toString())
      .replace('{{event}}', event);
  }
}

/**
 * 使用示例：在 AgentRunner 中集成
 */
export class AgentRunner {
  private startedAt: number = 0;
  private runId: string = '';
  private hookRunner: CompletionHookRunner;

  constructor(settings: Settings) {
    this.hookRunner = new CompletionHookRunner(settings);
  }

  async run(task: string): Promise<void> {
    // 记录开始时间
    this.startedAt = Date.now();
    this.runId = this.generateRunId();

    try {
      // 执行任务...
      const result = await this.executeTask(task);

      // 任务成功完成
      await this.hookRunner.onRunEvent(
        {
          runId: this.runId,
          startedAt: this.startedAt,
          message: `Task completed: ${result}`,
        },
        'end'
      );
    } catch (error) {
      // 任务失败
      await this.hookRunner.onRunEvent(
        {
          runId: this.runId,
          startedAt: this.startedAt,
          message: `Task failed: ${error.message}`,
        },
        'error'
      );
    }
  }

  async requestUserAction(prompt: string): Promise<void> {
    // 需要用户确认
    await this.hookRunner.onRunEvent(
      {
        runId: this.runId,
        startedAt: this.startedAt,
        message: prompt,
      },
      'needs_user_action'
    );

    // 等待用户输入...
  }

  private generateRunId(): string {
    return `run-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private async executeTask(task: string): Promise<string> {
    // 实际任务执行逻辑
    return 'Task result';
  }
}
