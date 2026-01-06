#!/bin/bash
# Claude Code Completion Hook
# 仅在运行时长 > 60s 时推送通知

# 参数：
# $1 - event type: "end" | "error" | "needs_user_action"
# $2 - message
# $3 - run_id
# $4 - started_at (timestamp in ms)

EVENT_TYPE="$1"
MESSAGE="$2"
RUN_ID="$3"
STARTED_AT="$4"

# 计算耗时
CURRENT_TIME=$(date +%s%3N)
ELAPSED_MS=$((CURRENT_TIME - STARTED_AT))

# 60 秒阈值（60000 毫秒）
THRESHOLD=60000

if [ "$ELAPSED_MS" -lt "$THRESHOLD" ]; then
  exit 0  # 小于 60s，不推送
fi

# 通知脚本路径
NOTIFY_CLI="$(dirname "$0")/notify-cli.js"

# 根据事件类型决定推送内容
case "$EVENT_TYPE" in
  "needs_user_action")
    TITLE="等待批准"
    node "$NOTIFY_CLI" --title "$TITLE" --content "$MESSAGE" 2>&1 >/dev/null
    ;;

  "end")
    TITLE="任务完成"
    CONTENT="$MESSAGE (耗时: ${ELAPSED_MS}ms)"
    node "$NOTIFY_CLI" --title "$TITLE" --content "$CONTENT" 2>&1 >/dev/null
    ;;

  "error")
    TITLE="任务失败"
    CONTENT="$MESSAGE (耗时: ${ELAPSED_MS}ms)"
    node "$NOTIFY_CLI" --title "$TITLE" --content "$CONTENT" 2>&1 >/dev/null
    ;;

  *)
    echo "Unknown event type: $EVENT_TYPE" >&2
    exit 1
    ;;
esac
