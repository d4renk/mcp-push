#!/bin/bash
# MCP-Push Hook 卸载脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/d4renk/mcp-push/main/uninstall-hook.sh | bash
#      或: bash uninstall-hook.sh
# Version: 1.0.1

set -e
set -o pipefail

echo "=================================="
echo "MCP-Push Hook 卸载脚本"
echo "=================================="
echo ""

HOOKS_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"

# 检查是否已安装
if [ ! -d "$HOOKS_DIR" ]; then
    echo "⚠ Hook 目录不存在，可能未安装"
    exit 0
fi

# 删除 Hook 脚本文件
echo "→ 删除 Hook 脚本文件..."
REMOVED_FILES=()

if [ -f "$HOOKS_DIR/completion-hook-linux.sh" ]; then
    rm -f "$HOOKS_DIR/completion-hook-linux.sh"
    REMOVED_FILES+=("completion-hook-linux.sh")
fi

if [ -f "$HOOKS_DIR/mcp-call.py" ]; then
    rm -f "$HOOKS_DIR/mcp-call.py"
    REMOVED_FILES+=("mcp-call.py")
fi

if [ ${#REMOVED_FILES[@]} -eq 0 ]; then
    echo "  未找到需要删除的 Hook 文件"
else
    for file in "${REMOVED_FILES[@]}"; do
        echo "  ✓ 已删除: $HOOKS_DIR/$file"
    done
fi

# 清理 settings.json 中的 Hook 配置
if [ -f "$SETTINGS_FILE" ]; then
    echo ""
    echo "→ 清理 settings.json 配置..."

    if command -v jq &> /dev/null; then
        # 使用 jq 移除 Stop Hook 配置
        TMP_FILE=$(mktemp)

        # 移除包含 completion-hook-linux.sh 的 Stop Hook 配置
        jq 'if .hooks.Stop then
              .hooks.Stop = [.hooks.Stop[] |
                select(.hooks |
                  any(.command |
                    contains("completion-hook-linux.sh") | not
                  )
                )
              ] | if .hooks.Stop == [] then .hooks.Stop = null else . end
            else . end' "$SETTINGS_FILE" > "$TMP_FILE"

        mv "$TMP_FILE" "$SETTINGS_FILE"
        echo "  ✓ 已从 settings.json 移除 Hook 配置"
    else
        echo "  ⚠ 未安装 jq，请手动编辑 settings.json"
        echo ""
        echo "  请移除包含 'completion-hook-linux.sh' 的 Stop Hook 配置"
        echo "  文件位置: $SETTINGS_FILE"
    fi
fi

# 可选：删除日志文件
echo ""
if [ -t 0 ]; then
    # 仅在交互式终端时提示
    read -p "是否删除 Hook 日志文件? (y/N): " -n 1 -r
    echo ""
else
    # 非交互式时默认不删除
    REPLY="n"
    echo "→ 跳过日志文件删除（非交互式模式）"
fi
if [[ $REPLY =~ ^[Yy]$ ]]; then
    LOG_FILES=(
        "/tmp/mcp-push-hook.log"
        "/var/log/mcp-push-hook.log"
    )

    for log_file in "${LOG_FILES[@]}"; do
        if [ -f "$log_file" ]; then
            rm -f "$log_file"
            echo "  ✓ 已删除: $log_file"
        fi
    done
fi

echo ""
echo "=================================="
echo "✅ 卸载完成！"
echo "=================================="
echo ""
echo "已删除的内容:"
if [ ${#REMOVED_FILES[@]} -gt 0 ]; then
    echo "  - Hook 脚本: ${REMOVED_FILES[*]}"
fi
echo "  - settings.json 中的配置"
echo ""
echo "保留的内容:"
echo "  - ~/.claude/hooks/ 目录（如需删除请手动执行）"
echo "  - MCP 服务器配置（如需删除请手动执行 'codex mcp remove mcp-push'）"
echo ""
echo "如需完全卸载 MCP 服务器，请执行:"
echo "  codex mcp remove mcp-push"
echo ""
