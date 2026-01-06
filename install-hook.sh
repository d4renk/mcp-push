#!/bin/bash
# MCP-Push Hook 自动安装脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/d4renk/mcp-push/main/install-hook.sh | bash

set -e

echo "=================================="
echo "MCP-Push Hook 安装脚本"
echo "=================================="

# 检测系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    HOOK_SCRIPT="completion-hook-linux.sh"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    HOOK_SCRIPT="completion-hook.sh"
else
    echo "❌ 不支持的操作系统: $OSTYPE"
    exit 1
fi

echo "✓ 检测到系统: $OSTYPE"
echo "✓ 使用脚本: $HOOK_SCRIPT"

# 创建 hooks 目录
HOOKS_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOKS_DIR"
echo "✓ 创建 hooks 目录: $HOOKS_DIR"

# 下载 hook 脚本
REPO_URL="https://raw.githubusercontent.com/d4renk/mcp-push/main"

echo "→ 下载 $HOOK_SCRIPT..."
curl -fsSL "$REPO_URL/$HOOK_SCRIPT" -o "$HOOKS_DIR/completion-hook-linux.sh"
chmod +x "$HOOKS_DIR/completion-hook-linux.sh"

echo "→ 下载 mcp-call.py..."
curl -fsSL "$REPO_URL/mcp-call.py" -o "$HOOKS_DIR/mcp-call.py"
chmod +x "$HOOKS_DIR/mcp-call.py"

echo "✓ Hook 脚本安装完成"

# 配置 settings.json
SETTINGS_FILE="$HOME/.claude/settings.json"

if [ ! -f "$SETTINGS_FILE" ]; then
    echo "{}" > "$SETTINGS_FILE"
    chmod 600 "$SETTINGS_FILE"
fi

# 检查是否已配置 Stop Hook
if grep -q "completion-hook-linux.sh" "$SETTINGS_FILE" 2>/dev/null; then
    echo "⚠ Stop Hook 已配置，跳过"
else
    echo "→ 配置 Stop Hook..."

    # 使用 jq 合并配置（如果没有 jq 则提示手动配置）
    if command -v jq &> /dev/null; then
        TMP_FILE=$(mktemp)
        jq '.hooks.Stop = [{"hooks": [{"type": "command", "command": "~/.claude/hooks/completion-hook-linux.sh", "timeout": 30}]}]' "$SETTINGS_FILE" > "$TMP_FILE"
        mv "$TMP_FILE" "$SETTINGS_FILE"
        echo "✓ Stop Hook 配置完成"
    else
        echo "⚠ 未安装 jq，请手动配置 settings.json"
        echo ""
        echo "请将以下内容添加到 $SETTINGS_FILE:"
        echo ""
        cat << 'EOF'
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
EOF
    fi
fi

echo ""
echo "=================================="
echo "✅ 安装完成！"
echo "=================================="
echo ""
echo "已安装文件:"
echo "  - $HOOKS_DIR/completion-hook-linux.sh"
echo "  - $HOOKS_DIR/mcp-call.py"
echo ""
echo "配置文件:"
echo "  - $SETTINGS_FILE"
echo ""
echo "下一步:"
echo "  1. 安装 MCP 服务器:"
echo "     codex mcp add mcp-push -- uvx --from git+https://github.com/d4renk/mcp-push.git mcp-push"
echo ""
echo "  2. 配置环境变量（参考 https://github.com/d4renk/mcp-push#configuration）"
echo ""
echo "  3. 测试推送:"
echo "     python3 $HOME/.claude/hooks/mcp-call.py mcp-push notify_send --title \"测试\" --content \"Hello\""
echo ""
