#!/usr/bin/env bash
# Claude Code Stop Hook (Linux)
# Read stdin JSON, parse transcript, and push notifications via mcp-push.

INPUT="$(cat)"

print_hook_json() {
  printf '{"continue": true, "suppressOutput": true}\n'
}

if [ -z "$INPUT" ]; then
  print_hook_json
  exit 0
fi

STOP_HOOK_ACTIVE="$(echo "$INPUT" | jq -r '.stop_hook_active // false')"
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  print_hook_json
  exit 0
fi

SESSION_ID="$(echo "$INPUT" | jq -r '.session_id // empty')"
TRANSCRIPT_PATH="$(echo "$INPUT" | jq -r '.transcript_path // empty')"

if [ -z "$TRANSCRIPT_PATH" ]; then
  print_hook_json
  exit 0
fi

if [[ "$TRANSCRIPT_PATH" == "~/"* ]]; then
  TRANSCRIPT_PATH="${HOME}/${TRANSCRIPT_PATH#~/}"
fi

if [ ! -f "$TRANSCRIPT_PATH" ]; then
  print_hook_json
  exit 0
fi

TRANSCRIPT_JSON="$(jq -s '.' "$TRANSCRIPT_PATH" 2>/dev/null || true)"
if [ -z "$TRANSCRIPT_JSON" ]; then
  print_hook_json
  exit 0
fi

STARTED_AT_RAW="$(echo "$TRANSCRIPT_JSON" | jq -r '
  (map(select(.started_at?)) | .[0].started_at) //
  (map(select(.start_time?)) | .[0].start_time) //
  (map(select(.session_start?.timestamp?)) | .[0].session_start.timestamp) //
  (map(select(.timestamp?)) | .[0].timestamp) //
  (map(select(.created_at?)) | .[0].created_at) //
  empty
')"

STARTED_AT_MS=""
if [[ "$STARTED_AT_RAW" =~ ^[0-9]+$ ]]; then
  if [ "${#STARTED_AT_RAW}" -le 10 ]; then
    STARTED_AT_MS="$((STARTED_AT_RAW * 1000))"
  else
    STARTED_AT_MS="$STARTED_AT_RAW"
  fi
elif [ -n "$STARTED_AT_RAW" ]; then
  STARTED_AT_MS="$(date -d "$STARTED_AT_RAW" +%s%3N 2>/dev/null || true)"
fi

if [ -z "$STARTED_AT_MS" ]; then
  FILE_MTIME_SEC="$(stat -c %Y "$TRANSCRIPT_PATH" 2>/dev/null || true)"
  if [ -n "$FILE_MTIME_SEC" ]; then
    STARTED_AT_MS="$((FILE_MTIME_SEC * 1000))"
  fi
fi

CURRENT_TIME="$(date +%s%3N)"
if [ -z "$STARTED_AT_MS" ]; then
  STARTED_AT_MS="$CURRENT_TIME"
fi

ELAPSED_MS=$((CURRENT_TIME - STARTED_AT_MS))
THRESHOLD=60000

if [ "$ELAPSED_MS" -lt "$THRESHOLD" ]; then
  print_hook_json
  exit 0
fi

EVENT_TYPE="end"
MESSAGE="Task completed."

LAST_ERROR="$(echo "$TRANSCRIPT_JSON" | jq -r '
  map(select(.type=="error" or .error? or .level=="error")) |
  last |
  (.message // .error.message // .error // .detail // .text // empty)
')"
if [ -n "$LAST_ERROR" ]; then
  EVENT_TYPE="error"
  MESSAGE="$LAST_ERROR"
else
  LAST_NOTIFICATION="$(echo "$TRANSCRIPT_JSON" | jq -r '
    map(select(.type=="notification" and .message?)) | last | .message // empty
  ')"
  if [ -n "$LAST_NOTIFICATION" ]; then
    EVENT_TYPE="needs_user_action"
    MESSAGE="$LAST_NOTIFICATION"
  else
    LAST_ASSISTANT="$(echo "$TRANSCRIPT_JSON" | jq -r '
      map(select((.role=="assistant") or (.type=="assistant") or (.type=="message" and .role=="assistant"))) |
      last |
      (.message // .content // .text // empty)
    ')"
    if [ -n "$LAST_ASSISTANT" ]; then
      MESSAGE="$LAST_ASSISTANT"
    fi
  fi
fi

MESSAGE="${MESSAGE//$'\n'/ }"
MESSAGE="${MESSAGE//$'\r'/ }"

RUN_ID="$SESSION_ID"
if [ -z "$RUN_ID" ]; then
  RUN_ID="session-unknown"
fi

MCP_SERVER="mcp-push"
MCP_CALL="/home/sun/mcp-push/mcp-call.py"

case "$EVENT_TYPE" in
  "needs_user_action")
    TITLE="等待批准"
    "$MCP_CALL" "$MCP_SERVER" notify_send \
      --title "$TITLE" \
      --content "$MESSAGE" 2>&1 >/dev/null
    ;;
  "end")
    TITLE="任务完成"
    "$MCP_CALL" "$MCP_SERVER" notify_send \
      --title "$TITLE" \
      --content "$MESSAGE" 2>&1 >/dev/null
    "$MCP_CALL" "$MCP_SERVER" notify_event \
      --run_id "$RUN_ID" \
      --event "end" \
      --message "$MESSAGE" \
      --data "{\"duration_ms\": $ELAPSED_MS}" 2>&1 >/dev/null
    ;;
  "error")
    TITLE="任务失败"
    "$MCP_CALL" "$MCP_SERVER" notify_send \
      --title "$TITLE" \
      --content "$MESSAGE" 2>&1 >/dev/null
    "$MCP_CALL" "$MCP_SERVER" notify_event \
      --run_id "$RUN_ID" \
      --event "error" \
      --message "$MESSAGE" \
      --data "{\"duration_ms\": $ELAPSED_MS}" 2>&1 >/dev/null
    ;;
esac

print_hook_json
