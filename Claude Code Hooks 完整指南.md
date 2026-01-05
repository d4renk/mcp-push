# Claude Code Hooks 完整指南

> 透过注册 shell 命令，客制化并扩展您的 Claude Code 工作流程。

## 📖 目录

- [总览](#总览)
  - [什么是 Hooks？](#什么是-hooks)
  - [为什么要使用 Hooks？](#为什么要使用-hooks)
- [入门教学](#入门教学)
  - [步骤 1：您的第一个 Hook - 档案变更日志](#步骤-1您的第一个-hook---档案变更日志)
  - [步骤 2：加入条件 - 使用匹配器](#步骤-2加入条件---使用匹配器)
  - [步骤 3：与 Claude 互动 - 记录执行的命令](#步骤-3与-claude-互动---记录执行的命令)
- [核心概念](#核心概念)
  - [Hook 事件生命周期](#hook-事件生命周期)
  - [Hook 的输入 (stdin)](#hook-的输入-stdin)
  - [Hook 的输出与控制](#hook-的输出与控制)
  - [设定档位置](#设定档位置)
- [实用范例库](#实用范例库)
  - [程式码自动格式化](#1-程式码自动格式化)
  - [进阶：使用 Python 脚本进行智慧验证](#2-进阶使用-python-脚本进行智慧验证)
  - [自订通知系统](#3-自订通知系统)
  - [安全防护范例](#4-安全防护范例)
  - [官方范例：Bash 命令验证](#5-官方范例bash-命令验证)
  - [官方范例：使用者提示验证与上下文添加](#6-官方范例使用者提示验证与上下文添加)
  - [智慧备份系统](#7-智慧备份系统)
  - [自动测试执行](#8-自动测试执行)
- [Hook 执行细节](#hook-执行细节)
  - [执行环境与限制](#执行环境与限制)
  - [Hook 匹配规则](#hook-匹配规则)
  - [常见工具匹配器](#常见工具匹配器)
- [进阶功能](#进阶功能)
  - [MCP 工具整合](#mcp-工具整合)
  - [使用外部脚本](#使用外部脚本)
- [安全考量](#安全考量)
  - [免责声明](#免责声明)
  - [重要安全原则](#重要安全原则)
  - [具体防护措施](#具体防护措施)
  - [专案设定安全性](#专案设定安全性)
- [疑难排解](#疑难排解)
  - [常见问题及解决方案](#常见问题及解决方案)
  - [除错工具](#除错工具)
- [最佳实践总结](#最佳实践总结)
  - [推荐做法](#推荐做法)
  - [避免事项](#避免事项)
  - [进阶技巧](#进阶技巧)
- [结语](#结语)
- [参考资源](#参考资源)

## 总览

### 什么是 Hooks？

Hooks 是您定义的 shell 命令，它们会在 Claude Code 生命周期的特定时间点自动执行。您可以把它们想像成是为您的 AI 程式设计伙伴设定的「自动化规则」或「触发器」。

与其在提示中反复告诉 Claude 要遵守某些规则，不如将这些规则编码为 Hooks，使其成为您开发环境中可靠且自动化的一部分。

### 为什么要使用 Hooks？

Hooks 让您能够对 Claude Code 的行为进行确定性的控制，确保某些动作总是会发生。常见的使用情境包括：

*   **✍️ 自动格式化**: 在 Claude 每次编辑完毕后，自动对 `.ts` 档案执行 `prettier`，或对 `.go` 档案执行 `gofmt`。
*   **🔔 自订通知**: 当 Claude 等待您的指令或执行权限时，透过系统通知或声音提醒您。
*   **🛡️ 安全防护**: 阻止 Claude 执行危险的命令（例如 `rm -rf`）或修改生产环境的设定档。
*   **📝 合规性记录**: 追踪所有由 Claude 执行的 shell 命令，以满足稽核或除错需求。
*   **💡 自动回馈**: 当 Claude 产生的程式码不符合您的专案规范时，自动向它提供修正建议。


## 入门教学

本教学将引导您建立三个 Hooks，从简单到复杂，逐步掌握核心概念。

### 步骤 1：您的第一个 Hook - 档案变更日志

我们的第一个 Hook 非常简单：每当 Claude 储存一个档案时，我们就在一个日志档中记录下来。这个范例不需要任何外部工具。

1.  在终端机中执行 `/hooks` 命令，打开 Hooks 设定介面。
2.  从事件列表中选择 `PostToolUse`。这个事件会在 Claude 成功执行工具**之后**触发。
3.  选择 `+ Add new matcher…`，输入 `Write|Edit|MultiEdit` 来匹配档案操作工具。
4.  选择 `+ Add new hook…`，然后输入以下命令：
    ```bash
    echo "Claude edited a file at $(date)" >> ~/.claude/file-edit-log.txt
    ```
5.  按 `Enter` 储存 Hook。系统会询问您储存位置，选择 `User settings`（使用者设定），这样这个 Hook 就会在您所有的专案中生效。
6.  按 `Esc` 退出设定介面。

**验证一下**：现在，请 Claude 随意修改您专案中的任何一个档案。完成后，检查日志档的内容：

```bash
cat ~/.claude/file-edit-log.txt
```

您应该会看到类似 "Claude edited a file at [日期时间]" 的讯息。恭喜，您已经成功建立了第一个 Hook！

### 步骤 2：加入条件 - 使用匹配器

上一个 Hook 会在**任何**档案被编辑后触发。如果我们只想在特定工具被使用时触发呢？这时就需要使用「匹配器」。

1.  再次执行 `/hooks`，选择 `PostToolUse` 事件。
2.  选择 `+ Add new matcher…`，输入 `Bash`。这样 Hook 就只会在 Claude 执行 shell 命令后触发。
3.  新增一个 Hook 命令：
    ```bash
    echo "Claude ran a bash command at $(date)" >> ~/.claude/bash-log.txt
    ```
4.  储存设定并退出。

**验证一下**：
*   请 Claude 执行一个 shell 命令，例如「列出目前目录的档案」。检查 `~/.claude/bash-log.txt`，您会发现新增了一条日志。
*   再请 Claude 编辑一个档案。这次只会在 `file-edit-log.txt` 中看到记录，而不会在 `bash-log.txt` 中看到。

匹配器让您可以精准控制 Hook 的触发时机与对象。

### 步骤 3：与 Claude 互动 - 记录执行的命令

现在，我们来挑战一个更进阶的 Hook：记录 Claude 尝试执行的所有 shell 命令详细资讯。这个 Hook 会读取 Claude 传递的资料，并需要 `jq` 工具来解析 JSON。

**先决条件**：请确保您已安装 `jq`。如果没有，请使用您的套件管理器安装：
- macOS: `brew install jq`
- Ubuntu/Debian: `sudo apt-get install jq`
- Windows: 下载自 https://stedolan.github.io/jq/

1.  执行 `/hooks`，这次选择 `PreToolUse` 事件。这个事件在 Claude **准备**执行一个工具（如 `bash` 命令）**之前**触发。
2.  为这个 Hook 新增一个匹配器，输入 `Bash`，这样它就只会监控 shell 命令。
3.  选择 `+ Add new hook…` 并输入以下命令：
    ```bash
    jq -r '"COMMAND: \(.tool_input.command) | DESCRIPTION: \(.tool_input.description // "None")"' >> ~/.claude/bash-command-log.txt
    ```
    这个命令会从传入的 JSON 资料中提取 `command` 和 `description` 栏位，并将其格式化后写入日志档。
4.  储存为 `User settings` 并退出。

**验证一下**：请 Claude 执行一个 shell 命令，例如「列出目前目录的所有档案」。在您授权 Claude 执行之前，这个 Hook 就已经被触发了。检查日志档：

```bash
cat ~/.claude/bash-command-log.txt
```

您应该会看到类似 `COMMAND: ls -l | DESCRIPTION: List all files in the current directory` 的记录。

透过这个教学，您已经学会了：
*   如何在特定事件上建立 Hook
*   如何使用匹配器来过滤事件
*   如何读取 Claude 传递的上下文资料

## 核心概念

### Hook 事件生命周期

Hooks 可以在 Claude Code 生命周期的多个时间点触发。以下是主要的事件类型：

| 事件名称 | 触发时机 | 常见用途 | 可阻止操作 |
|----------|----------|----------|------------|
| `UserPromptSubmit` | 使用者提交提示后，Claude 处理**之前** | 验证提示、根据提示内容注入额外上下文 | ✅ 是 |
| `PreToolUse` | 在工具（如 `Bash`）被执行**之前** | 阻止危险命令、记录意图、修改命令 | ✅ 是 |
| `PostToolUse` | 在工具执行**之后** | 记录执行结果、基于结果触发下一步 | ❌ 否 |
| `Notification` | 当需要发送通知时 | 自订通知方式、声音提醒 | ❌ 否 |
| `Stop` | 当 Claude 完成任务或遇到错误时 | 清理工作、后续处理 | ✅ 是 |
| `SubagentStop` | 当子代理（Task 工具）完成时 | 针对子任务的后续处理 | ✅ 是 |
| `PreCompact` | 在 Claude 执行上下文压缩**之前** | 根据压缩类型执行不同操作、备份重要上下文 | ❌ 否 |

### Hook 的输入 (stdin)

每个 Hook 在执行时，都会透过标准输入（`stdin`）接收一个包含上下文资讯的 JSON 物件。您可以使用 `jq` 或其他工具来解析它。

**通用栏位:**
```json
{
  "session_id": "string",
  "transcript_path": "string", // 对话记录档路径
  "cwd": "string",             // Hook 被调用时的当前工作目录
  "hook_event_name": "string"  // 触发的 Hook 事件名称
}
```

**`PreToolUse` 的输入范例:**
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/path/to/project",
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "ls -a",
    "description": "List all files, including hidden ones."
  }
}
```

**`PostToolUse` 的输入范例:**
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/path/to/project",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.ts",
    "content": "console.log('Hello World');"
  },
  "tool_response": {
    "filePath": "/path/to/file.ts",
    "success": true
  }
}
```

**`Notification` 的输入范例:**
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/path/to/project",
  "hook_event_name": "Notification",
  "message": "Claude needs your permission to use Bash"
}
```

**`UserPromptSubmit` 的输入范例:**
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/path/to/project",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "Write a function to calculate the factorial of a number"
}
```

**`Stop` / `SubagentStop` 的输入范例:**
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/path/to/project",
  "hook_event_name": "Stop",
  "stop_hook_active": true
}
```
> `stop_hook_active` 为 `true` 表示 Claude 正在因为前一个 `Stop` Hook 的结果而继续执行。您可以检查此值以避免无限循环。

**`PreCompact` 的输入范例:**
```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../session.jsonl",
  "cwd": "/path/to/project",
  "hook_event_name": "PreCompact",
  "trigger": "manual",
  "custom_instructions": ""
}
```
> - `trigger`: 压缩触发原因
>   - `"manual"`: 由使用者透过 `/compact` 命令手动触发
>   - `"auto"`: 由于上下文视窗已满而自动触发
> - `custom_instructions`: 对于 `manual` 触发，包含使用者传递给 `/compact` 的自订指令；对于 `auto` 触发，此栏位为空字串

### Hook 的输出与控制

Hook 可以透过两种方式影响 Claude Code 的行为：**简单的退出码**或**进阶的 JSON 输出**。输出主要用来沟通是否要阻止操作，以及应该向 Claude 和使用者显示什么回馈。

#### 1. 简单控制：退出代码 (Exit Code)

这是最基本的回馈机制。
- **退出代码 0**: 成功。`stdout` 的内容会以一般资讯的形式显示给使用者（在 transcript 模式下可见），但 Claude **不会**看到。
- **退出代码 2**: 阻挡性错误。`stderr` 的内容会作为回馈**提供给 Claude** 进行处理。不同事件的具体行为不同（见下表）。
- **其他退出代码**: 非阻挡性错误。`stderr` 的内容只会显示给使用者，操作会继续执行。

**退出代码 2 的行为细节**

| Hook 事件 | 阻挡行为 |
| ------------------ | ------------------------------------------------------------------ |
| `PreToolUse` | 阻挡工具执行，并将 `stderr` 内容交给 Claude 分析。 |
| `PostToolUse` | 工具已经执行，但会将 `stderr` 内容交给 Claude 进行后续修正。 |
| `UserPromptSubmit` | 阻挡使用者提示的处理，清除该提示，并将 `stderr` 显示给使用者。 |
| `Stop` / `SubagentStop` | 阻挡 Claude 停止，并将 `stderr` 内容交给 Claude 以决定下一步。 |
| `Notification` / `PreCompact` | 无特殊阻挡效果，仅将 `stderr` 显示给使用者。 |


⚠️ **重要提醒**: 当退出代码为 0 时，Claude **不会看到** `stdout` 的内容。只有 `stderr` 在退出代码为 2 时才会被 Claude 处理。

#### 2. 进阶控制：JSON 输出

为了进行更精细的控制，Hook 可以透过 `stdout` 返回一个 JSON 物件。

**通用 JSON 栏位 (适用于所有事件):**
```json
{
  "continue": true,
  "stopReason": "使用者要求的操作已终止",
  "suppressOutput": true
}
```
- `continue` (`boolean`, 预设 `true`): 设为 `false` 可在 Hook 执行后完全终止 Claude 的后续处理。
- `stopReason` (`string`): 当 `continue` 为 `false` 时，向使用者显示的停止原因（**不会**显示给 Claude）。
- `suppressOutput` (`boolean`, 预设 `false`): 设为 `true` 可以隐藏 Hook 的 `stdout`，使其不在 transcript 模式中显示。

**重要行为说明:**
- 当 `continue` 为 `false` 时，会优先于任何 `"decision": "block"` 设定
- 对于 `PreToolUse`，这与 `"decision": "block"` 不同 - 后者只阻挡特定工具呼叫并提供自动回馈给 Claude
- 对于 `PostToolUse`，这与 `"decision": "block"` 不同 - 后者提供自动回馈给 Claude
- 对于 `UserPromptSubmit`，这会阻止提示被处理
- 对于 `Stop` 和 `SubagentStop`，这会优先于任何 `"decision": "block"` 输出

**特定事件的决策控制 (`decision`):**

- **`PreToolUse`**: 控制工具是否执行。
  ```json
  {
    "decision": "approve" | "block",
    "reason": "批准原因或阻挡原因"
  }
  ```
  - `"approve"`: 绕过权限询问，直接执行。`reason` 显示给使用者。
  - `"block"`: 阻止工具执行。`reason` 会**提供给 Claude**。
  - `undefined`: 保持预设的权限询问流程。

- **`PostToolUse` / `Stop` / `SubagentStop`**: 控制是否需要 Claude 进行后续处理。
  ```json

  {
    "decision": "block",
    "reason": "需要 Claude 处理的回馈资讯"
  }
  ```
  - `"block"`: 提示 Claude 根据 `reason` 继续工作。例如，在 `PostToolUse` 中指出程式码格式问题，或在 `Stop` 中要求 Claude 继续执行下一步。

- **`UserPromptSubmit`**: 控制使用者提示是否被处理。
  ```json
  {
    "decision": "block",
    "reason": "向使用者显示的阻挡原因"
  }
  ```
  - `"block"`: 阻止提示被处理，并清除该提示。`reason` 只会显示给使用者。

### 设定档位置

Claude Code 的设定档结构如下，您可以将 Hooks 设定放在其中：

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```
- `matcher`: 工具名称模式匹配（例如 `Edit|Write`），支援简单字串精确匹配和正规表示式，对大小写敏感。如果省略或为空字串，则会对所有工具生效。
- `hooks`: 一组要执行的命令。
- `command`: 要执行的 shell 命令。
- `timeout` (可选): 命令执行的超时时间（秒）。

**设定档层级:**

*   **使用者设定** (`~/.claude/settings.json`): 在这里设定的 Hooks 会在您所有的专案中生效。适合通用规则，如通知、日志记录。
*   **专案设定** (`<project_root>/.claude/settings.json`): 在这里设定的 Hooks **仅**对当前专案生效。适合专案特定的规则，如程式码格式化、特定于专案的安全防护。
*   **本地专案设定** (`<project_root>/.claude/settings.local.json`): 本地设定，不会被版本控制。
*   **企业管理政策设定**: 如果您在企业环境中，管理员可能已配置全域策略设定。


⚠️ **重要提醒**: `"matcher": "*"` 是无效的语法。如果要匹配所有工具，请省略 `matcher` 栏位或使用 `"matcher": ""`。

## 实用范例库

这里有一些可以直接使用的范例，帮助您快速提升效率。

### 1. 程式码自动格式化

#### TypeScript/JavaScript (Prettier)

在 Claude 每次修改完档案后，自动执行 Prettier 格式化。

**设定:**
- **事件**: `PostToolUse`
- **匹配器**: `Edit|MultiEdit|Write`
- **Hook 命令**:
```bash
# 检查是否为 JS/TS 档案并执行 prettier
file_path=$(jq -r '.tool_input.file_path // ""')
if [[ "$file_path" =~ \.(js|jsx|ts|tsx)$ ]] && [[ -f "$file_path" ]] && [[ -f "package.json" ]]; then
    npx --no-install prettier --write "$file_path"
    echo "✨ 已自动格式化档案: $file_path"
fi
```

#### Go 程式码格式化

**设定:**
- **事件**: `PostToolUse`
- **匹配器**: `Edit|MultiEdit|Write`
- **Hook 命令**:
```bash
# 检查是否为 Go 档案并执行 gofmt
file_path=$(jq -r '.tool_input.file_path // ""')
if [[ "$file_path" =~ \.go$ ]] && [[ -f "$file_path" ]]; then
    gofmt -w "$file_path"
    echo "✨ 已自动格式化 Go 档案: $file_path"
fi
```

### 2. 进阶：使用 Python 脚本进行智慧验证

这个范例展示了如何使用 Python 脚本，在 Claude 执行 `Bash` 命令前进行验证，并使用 **JSON 输出** 提供结构化的回馈。

**设定:**
- **事件**: `PreToolUse`
- **匹配器**: `Bash`
- **Hook 命令**: `python .claude/hooks/validate_bash.py`

**建立脚本 (`.claude/hooks/validate_bash.py`):**
```python
#!/usr/bin/env python3
import json
import re
import sys

# 定义验证规则 (正规表示式, 建议讯息)
VALIDATION_RULES = [
    (
        r"\bgrep\b(?!.*\|)",
        "请改用 'rg' (ripgrep)，它在专案范围内的搜寻效能更好。",
    ),
    (
        r"\bfind\s+\S+\s+-name\b",
        "建议使用 'rg --files | rg <pattern>' 或 'rg -g '<pattern>'' 来取代 'find -name'，速度更快。",
    ),
]

def validate_command(command: str) -> list[str]:
    issues = []
    for pattern, message in VALIDATION_RULES:
        if re.search(pattern, command):
            issues.append(message)
    return issues

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(1) # 无法解析 JSON，静默退出

command = input_data.get("tool_input", {}).get("command", "")
if not command:
    sys.exit(0) # 如果没有命令，则不进行任何操作

issues = validate_command(command)

if issues:
    # 如果发现问题，使用 JSON 输出格式来阻挡并提供回馈
    response = {
        "decision": "block",
        "reason": "发现以下可以改进的地方：\n- " + "\n- ".join(issues)
    }
    print(json.dumps(response))
else:
    # 如果没有问题，可以明确批准或不输出任何东西让流程继续
    print(json.dumps({"decision": "approve", "reason": "命令检查通过"}))

sys.exit(0)
```

### 3. 自订通知系统

#### macOS 语音通知

当 Claude 等待您授权时，发出语音提醒。

**设定:**
- **事件**: `Notification`
- **匹配器**: (留空，适用于所有通知)
- **Hook 命令**:
```bash
message=$(jq -r '.message // "Claude Code notification"')
say "Claude says: $message"
```

#### Linux 桌面通知

**设定:**
- **事件**: `Notification`
- **匹配器**: (留空)
- **Hook 命令**:
```bash
# 需要安装 libnotify-bin
title=$(jq -r '.title // "Claude Code"')
message=$(jq -r '.message // "Notification from Claude"')
notify-send "$title" "$message"
```

### 4. 安全防护范例

#### 防止危险命令执行

阻止 Claude 执行可能危险的命令。

**设定:**
- **事件**: `PreToolUse`
- **匹配器**: `Bash`
- **Hook 命令**:
```bash
command=$(jq -r '.tool_input.command // ""')

# 检查危险命令模式
dangerous_patterns=("rm -rf" "sudo rm" "dd if=" "mkfs" "fdisk" "> /dev/")

for pattern in "${dangerous_patterns[@]}"; do
    if [[ "$command" == *"$pattern"* ]]; then
        # 使用退出码 2 来阻挡操作，并将 stderr 的内容传递给 Claude
        echo "🚫 安全警告: 已阻止潜在危险命令: $command" >&2
        echo "💡 建议: 请使用更安全的替代方案或明确指定档案" >&2
        exit 2
    fi
done

echo "✅ 命令安全检查通过: $command"
```

#### 保护敏感档案

防止 Claude 修改重要的设定档案。

**设定:**
- **事件**: `PreToolUse`
- **匹配器**: `Edit|MultiEdit|Write`
- **Hook 命令**:
```bash
file_path=$(jq -r '.tool_input.file_path // ""')

# 敏感档案模式
sensitive_files=(".env" ".env.local" ".env.production" "id_rsa" "id_ed25519" "package-lock.json" "yarn.lock")

for pattern in "${sensitive_files[@]}"; do
    if [[ "$file_path" == *"$pattern"* ]]; then
        reason=""
        case "$pattern" in
            "package-lock.json"|"yarn.lock")
                reason="💡 提示: 如需更新依赖，请让 Claude 使用 'npm install' 或 'yarn install'"
                ;;
            ".env"*)
                reason="💡 提示: 环境变数档案包含敏感资讯，请手动编辑"
                ;;
            "id_rsa"|"id_ed25519")
                reason="💡 提示: SSH 金钥档案不应被 Claude 修改"
                ;;
            *)
                reason="🔒 安全限制: 不允许 Claude 修改敏感档案: $file_path"
                ;;
        esac
        # 使用 JSON 输出阻挡操作
        jq -n --arg reason "$reason" '{decision: "block", reason: $reason}'
        exit 0
    fi
done
```

### 5. 自动测试执行

在程式码修改后自动执行测试。

**设定:**
- **事件**: `PostToolUse`
- **匹配器**: `Edit|MultiEdit|Write`
- **Hook 命令**:
```bash
file_path=$(jq -r '.tool_input.file_path // ""')

# 检查是否为测试相关档案或源码档案
if [[ "$file_path" =~ \.(test|spec)\. ]] || [[ "$file_path" =~ /src/ ]]; then
    echo "🧪 检测到程式码变更，执行相关测试..."
    
    # 检查专案类型并执行适当的测试命令
    if [ -f "package.json" ]; then
        # --no-install 避免在没有 node_modules 时的交互提示
        if jq -e '.scripts.test' package.json > /dev/null; then
            npm test -- --testPathPattern="$(basename "$file_path" | sed 's/\.[^.]*$//')"
        fi
    elif [ -f "go.mod" ]; then
        go test ./...
    elif [ -f "Cargo.toml" ]; then
        cargo test
    elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
        python -m pytest -xvs
    fi
fi
```

### 5. 官方范例：Bash 命令验证

以下是官方提供的 Python 脚本范例，展示如何使用 JSON 输出进行 Bash 命令验证：

**设定:**
- **事件**: `PreToolUse`
- **匹配器**: `Bash`
- **Hook 命令**: `python /path/to/bash-validator.py`

**脚本内容 (`bash-validator.py`):**
```python
#!/usr/bin/env python3
import json
import re
import sys

# 定义验证规则为 (正规表示式模式, 讯息) 的元组列表
VALIDATION_RULES = [
    (
        r"\bgrep\b(?!.*\|)",
        "建议使用 'rg' (ripgrep) 而非 'grep'，效能和功能都更好",
    ),
    (
        r"\bfind\s+\S+\s+-name\b",
        "建议使用 'rg --files | rg pattern' 或 'rg --files -g pattern' 而非 'find -name'，效能更好",
    ),
]

def validate_command(command: str) -> list[str]:
    issues = []
    for pattern, message in VALIDATION_RULES:
        if re.search(pattern, command):
            issues.append(message)
    return issues

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f"错误: 无效的 JSON 输入: {e}", file=sys.stderr)
    sys.exit(1)

tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})
command = tool_input.get("command", "")

if tool_name != "Bash" or not command:
    sys.exit(1)

# 验证命令
issues = validate_command(command)

if issues:
    for message in issues:
        print(f"• {message}", file=sys.stderr)
    # 退出代码 2 阻挡工具执行并将 stderr 传递给 Claude
    sys.exit(2)
```

### 6. 官方范例：使用者提示验证与上下文添加

**设定:**
- **事件**: `UserPromptSubmit`
- **Hook 命令**: `python /path/to/prompt-validator.py`

**脚本内容 (`prompt-validator.py`):**
```python
#!/usr/bin/env python3
import json
import sys
import re
import datetime

# 从 stdin 载入输入
try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f"错误: 无效的 JSON 输入: {e}", file=sys.stderr)
    sys.exit(1)

prompt = input_data.get("prompt", "")

# 检查敏感模式
sensitive_patterns = [
    (r"(?i)\b(password|secret|key|token)\s*[:=]", "提示包含潜在的机密资讯"),
]

for pattern, message in sensitive_patterns:
    if re.search(pattern, prompt):
        # 使用 JSON 输出阻挡并提供特定原因
        output = {
            "decision": "block",
            "reason": f"安全政策违规: {message}。请重新表述您的请求，不要包含敏感资讯。"
        }
        print(json.dumps(output))
        sys.exit(0)

# 添加当前时间到上下文
context = f"当前时间: {datetime.datetime.now()}"
print(context)

# 允许提示继续处理，并包含额外的上下文
sys.exit(0)
```

### 7. 智慧备份系统

在重要档案被修改前自动建立备份。

**设定:**
- **事件**: `PreToolUse`
- **匹配器**: `Edit|MultiEdit|Write`
- **Hook 命令**:
```bash
file_path=$(jq -r '.tool_input.file_path // ""')

# 需要备份的重要档案模式
important_patterns=("config" "settings" ".json" ".yaml" ".yml" "Dockerfile" "Makefile")

should_backup=false
for pattern in "${important_patterns[@]}"; do
    if [[ "$file_path" == *"$pattern"* ]]; then
        should_backup=true
        break
    fi
done

if [ "$should_backup" = true ] && [ -f "$file_path" ]; then
    backup_dir="$(dirname "$file_path")/.claude-backups"
    mkdir -p "$backup_dir"
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="$backup_dir/$(basename "$file_path").backup.$timestamp"
    
    cp "$file_path" "$backup_file"
    echo "💾 已建立备份: $backup_file"
fi
```

## Hook 执行细节

### 执行环境与限制

- **执行超时**: 预设 60 秒执行限制，可针对个别命令设定 `timeout` 参数
  - 个别命令的超时不会影响其他命令
- **并行执行**: 所有匹配的 Hooks 会并行执行
- **执行环境**: 在当前目录中执行，使用 Claude Code 的环境变数
- **输入方式**: 透过 stdin 接收 JSON 资料
- **输出处理**:
  - `PreToolUse`/`PostToolUse`/`Stop`: 进度显示在 transcript 模式 (Ctrl-R)
  - `Notification`: 仅记录在除错日志中 (`--debug`)

### Hook 匹配规则

**对于 `PreToolUse` 和 `PostToolUse` 事件:**
- `matcher` 是必要的，用于指定要监控的工具
- 支援精确字串匹配：`"Write"` 只匹配 Write 工具
- 支援正规表示式：`"Edit|Write"` 或 `"Notebook.*"`
- 大小写敏感
- 如果省略或为空字串，则匹配所有工具

**对于其他事件:**
- `UserPromptSubmit`, `Notification`, `Stop`, `SubagentStop`, `PreCompact` 不使用 matcher
- 可以省略 `matcher` 栏位或将其设为空字串

### 常见工具匹配器

以下是可以在 `PreToolUse` 和 `PostToolUse` 中使用的常见工具名称：

- `Task` - 代理任务
- `Bash` - Shell 命令
- `Glob` - 档案模式匹配
- `Grep` - 内容搜寻
- `Read` - 档案读取
- `Edit`, `MultiEdit` - 档案编辑
- `Write` - 档案写入
- `WebFetch`, `WebSearch` - 网路操作

## 进阶功能

### MCP 工具整合

Claude Code 支援 MCP (Model Context Protocol) 工具，您也可以为这些工具设定 Hooks。MCP 工具遵循 `mcp__<server>__<tool>` 的命名模式。

**范例：监控记忆体操作**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__memory__.*",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Memory operation: ' $(jq -r '.tool_name') >> ~/.claude/memory-log.txt"
          }
        ]
      }
    ]
  }
}
```

### 使用外部脚本

对于复杂的逻辑，建议建立独立的脚本档案：

**建立脚本档案** (`.claude/hooks/security_check.js`):
```javascript
#!/usr/bin/env node

async function main() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }

  const toolData = JSON.parse(Buffer.concat(chunks).toString());
  const command = toolData.tool_input?.command || "";
  
  // 复杂的安全检查逻辑
  const dangerousPatterns = [
    /rm\s+-rf\s+\//, // 删除根目录
    /sudo\s+rm/, // sudo 删除
    /chmod\s+777/, // 过于宽松的权限
  ];
  
  for (const pattern of dangerousPatterns) {
    if (pattern.test(command)) {
      console.error(`🚫 检测到危险命令模式: ${command}`);
      process.exit(2);
    }
  }
  
  console.log(`✅ 安全检查通过`);
  process.exit(0);
}

main().catch(console.error);
```

**在 Hook 中使用脚本**:
```bash
# 方式一：使用 node 命令执行（推荐）
node .claude/hooks/security_check.js

# 方式二：直接执行（需要 shebang 行和执行权限）
# 确保脚本第一行包含: #!/usr/bin/env node
# 并设定执行权限: chmod +x .claude/hooks/security_check.js
.claude/hooks/security_check.js
```

## 安全考量

### ⚠️ 免责声明

**风险自负**: Claude Code Hooks 会在您的系统上自动执行任意 shell 命令。使用 Hooks 表示您确认：

* 您对配置的命令承担全部责任
* Hooks 可以修改、删除或存取您的使用者帐户能存取的任何档案
* 恶意或编写不当的 Hooks 可能导致资料遗失或系统损害
* Anthropic 不提供任何保证，并且不对 Hook 使用导致的任何损害承担责任
* 您应该在生产环境使用前，在安全环境中彻底测试 Hooks

在添加到您的配置之前，请务必审查并理解任何 Hook 命令。

### 🛡️ 重要安全原则

1. **最小权限原则**: 只授予 Hook 完成任务所需的最小权限
2. **输入验证**: 始终验证来自 Claude 的输入资料
3. **避免命令注入**: 如果使用来自 Claude 的资料建构命令，请正确转义
4. **定期审查**: 定期检查您的 Hook 设定和执行日志
5. **使用绝对路径**: 在脚本中尽量使用绝对路径指定命令，避免 PATH 被劫持
6. **避开敏感档案**: 设定规则以跳过 `.env`, `.git/`, SSH 金钥等档案

### 具体防护措施

#### 输入清理范例
```bash
# 安全地处理档案路径
file_path=$(jq -r '.tool_input.file_path // ""' | sed 's/[^a-zA-Z0-9._/-]//g')

# 防止路径遍历攻击
if [[ "$file_path" == *".."* ]]; then
    echo "❌ 不允许路径遍历操作"
    exit 2
fi
```

#### 权限检查
```bash
# 检查档案是否在允许的目录中
allowed_dirs=("/home/user/projects" "/tmp")
file_path=$(jq -r '.tool_input.file_path // ""')

is_allowed=false
for dir in "${allowed_dirs[@]}"; do
    if [[ "$file_path" == "$dir"* ]]; then
        is_allowed=true
        break
    fi
done

if [ "$is_allowed" = false ]; then
    echo "❌ 档案路径不在允许的目录中: $file_path"
    exit 2
fi
```

### 专案设定安全性

当您载入包含专案级别 Hooks 的专案时，Claude Code 会显示警告并要求您确认。这是为了防止恶意设定档。

#### 配置安全机制

对设定档的直接编辑不会立即生效。Claude Code 采用以下安全措施：

1. **启动时快照**: Claude Code 在启动时撷取 Hooks 设定的快照
2. **全程使用快照**: 整个对话期间使用该快照
3. **外部变更警告**: 如果 Hooks 设定档被外部修改，Claude Code 会发出警告
4. **需要审查确认**: 变更后的 Hooks 需要在 `/hooks` 管理介面中审查后才能生效

这可以防止恶意 Hook 修改在您目前的对话期间生效。

**请务必：**

1. **仔细检查** `.claude/settings.json` 中的所有 Hook 命令
2. **理解每个命令的作用**，特别是那些您不熟悉的
3. **在沙盒环境中测试**未知的 Hook 配置
4. **不要盲目信任**来自网路的专案设定

## 疑难排解

### 常见问题及解决方案

#### Hook 没有执行

**可能原因及解决方法：**

1. **事件类型或匹配器错误**
   ```bash
   # 检查设定档语法
   cat ~/.claude/settings.json | jq .
   ```

2. **命令路径问题**
   ```bash
   # 使用绝对路径
   /usr/bin/echo "test" >> ~/.claude/debug.log
   ```

3. **权限问题**
   ```bash
   # 检查脚本权限
   chmod +x .claude/hooks/your-script.sh
   ```

#### 调试 Hook 执行

**在 Hook 中加入调试输出：**
```bash
# 在命令开头加入
set -x # 打开 shell 的详细执行日志
echo "Hook executed at $(date)" >> ~/.claude/hook-debug.log
echo "Input: $(cat)" >> ~/.claude/hook-debug.log
set +x # 关闭详细日志
```

**检查 Claude 传递的资料：**
```bash
# 将完整输入保存到档案
cat > /tmp/claude-hook-input-$(date +%s).json
```

#### JSON 解析错误

**安全的 JSON 处理：**
```bash
# 检查 JSON 是否有效
if echo "$input" | jq . > /dev/null 2>&1; then
    # JSON 有效，继续处理
    command=$(echo "$input" | jq -r '.tool_input.command // ""')
else
    echo "❌ 无效的 JSON 输入" >&2
    exit 1
fi
```

### 除错工具

#### 基本除错步骤

如果您的 Hooks 无法正常运作，请依序检查：

1. **检查配置** - 执行 `/hooks` 查看您的 Hook 是否已注册
2. **验证语法** - 确保 JSON 设定有效
3. **测试命令** - 先手动执行 Hook 命令
4. **检查权限** - 确保脚本档案具有执行权限
5. **查看日志** - 使用 `claude --debug` 查看详细的 Hook 执行资讯

**常见问题:**
- **引号未跳脱** - JSON 字串中使用 `\"` 
- **匹配器错误** - 检查工具名称是否精确匹配（大小写敏感）
- **命令找不到** - 使用脚本的完整路径

#### 启用详细日志
使用 `--debug` 标志启动 Claude Code 以查看详细的日志输出：
```bash
claude --debug
```
您将会看到类似以下的日志：
```
[DEBUG] Executing hooks for PostToolUse:Write
[DEBUG] Getting matching hook commands for PostToolUse with query: Write
[DEBUG] Found 1 hook matchers in settings
[DEBUG] Matched 1 hooks for query "Write"
[DEBUG] Found 1 hook commands to execute
[DEBUG] Executing hook command: <Your command> with timeout 60000ms
[DEBUG] Hook command completed with status 0: <Your stdout>
```

进度讯息会出现在 transcript 模式 (Ctrl-R) 中，显示：
- 正在执行哪个 Hook
- 执行的命令
- 成功/失败状态
- 输出或错误讯息

#### 进阶除错技巧

对于复杂的 Hook 问题：

1. **检查 Hook 执行** - 使用 `claude --debug` 查看详细的 Hook 执行过程
2. **验证 JSON Schema** - 使用外部工具测试 Hook 输入/输出
3. **检查环境变数** - 验证 Claude Code 的环境是否正确
4. **测试边缘情况** - 尝试 Hook 处理异常档案路径或输入
5. **监控系统资源** - 检查 Hook 执行期间是否有资源耗尽
6. **使用结构化记录** - 在 Hook 脚本中实作日志记录

#### Hook 执行监控
```bash
# 建立全域监控 Hook
echo 'echo "$(date): Hook executed" >> ~/.claude/all-hooks.log' > ~/.claude/hooks/monitor.sh
chmod +x ~/.claude/hooks/monitor.sh
```

## 最佳实践总结

### ✅ 推荐做法

1. **从简单开始**: 先实作基本的日志记录，再逐步加入复杂功能
2. **分层设定**: 通用规则放在使用者设定，专案特定规则放在专案设定
3. **充分测试**: 在安全环境中测试所有 Hook 再部署到生产环境
4. **详细注释**: 在设定档中为每个 Hook 添加说明注释
5. **定期维护**: 定期检查和更新 Hook 设定，移除不需要的规则

### ❌ 避免事项

1. **过度复杂化**: 避免在单一 Hook 中包含过多逻辑
2. **忽略错误处理**: 确保 Hook 能够妥善处理异常情况
3. **硬编码路径**: 使用相对路径或环境变数而非绝对路径
4. **忽略效能**: 避免在 Hook 中执行耗时操作
5. **盲目信任**: 不要无条件信任来自外部的 Hook 设定

### 🚀 进阶技巧

1. **条件执行**: 使用环境变数控制 Hook 行为
   ```bash
   if [ "$CLAUDE_ENV" = "production" ]; then
       # 生产环境专用逻辑
   fi
   ```

2. **并行处理**: 对于独立的操作，可以使用背景执行
   ```bash
   long_running_task &
   echo "Task started in background"
   ```

3. **状态追踪**: 使用暂存档案追踪 Hook 状态
   ```bash
   echo "$(date): Hook started" > /tmp/claude-hook-status
   ```

4. **整合外部服务**: 透过 API 与外部服务整合
   ```bash
   curl -X POST "https://api.slack.com/..." -d "text=Claude completed task"
   ```

## 结语

Claude Code Hooks 是一个强大的自动化工具，能够显著提升您的开发效率和程式码品质。透过合理的设定和使用，您可以：

- 🎯 **自动化重复性任务**: 格式化程式码、执行测试、产生文件
- 🛡️ **增强安全性**: 防止危险操作、保护敏感档案
- 📊 **提升可见度**: 记录操作历史、监控系统状态
- 🔄 **优化工作流程**: 整合现有工具链、自订通知机制

记住，Hooks 的真正价值在于让您专注于创造性的工作，而将重复性的、规则化的任务交给自动化系统处理。

开始您的 Claude Code Hooks 之旅，让 AI 助手成为您开发团队中最可靠的成员！

---

## 参考资源

- [Claude Code 官方文件](https://docs.anthropic.com/zh-TW/docs/claude-code/hooks)
- [jq 官方教学](https://stedolan.github.io/jq/tutorial/)
- [Shell 脚本最佳实践](https://google.github.io/styleguide/shellguide.html)
- [JSON Schema 验证](https://json-schema.org/)
