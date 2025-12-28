# MCP Push Usage

仅在以下两种情况下调用 mcp-push（notify_send 或 notify_event）：

1. 任务完成 (Task Finished)：当长耗时（大于60s）任务执行结束（无论成功或失败）时。
2. 需要用户确认 (User Action Needed)：当流程暂停，等待用户决策或授权时。
