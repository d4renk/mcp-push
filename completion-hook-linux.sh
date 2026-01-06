#!/usr/bin/env bash
# Claude Code Stop Hook (Linux)
# Read stdin JSON, parse transcript, and push notifications via mcp-push.

INPUT="$(cat)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load config.sh only when MCP_PUSH_STRUCTURED is not set in the environment.
if [ -z "${MCP_PUSH_STRUCTURED+x}" ]; then
  if [ -f "./config.sh" ]; then
    # shellcheck source=/dev/null
    . "./config.sh"
  elif [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/config.sh" ]; then
    # shellcheck source=/dev/null
    . "$SCRIPT_DIR/config.sh"
  fi
fi

MCP_PUSH_STRUCTURED="${MCP_PUSH_STRUCTURED:-true}"
MCP_PUSH_TIMEOUT_SEC="${MCP_PUSH_TIMEOUT_SEC:-10}"
MCP_PUSH_HOOK_LOG_PATH="${MCP_PUSH_HOOK_LOG_PATH:-}"

if ! [[ "$MCP_PUSH_TIMEOUT_SEC" =~ ^[0-9]+$ ]]; then
  MCP_PUSH_TIMEOUT_SEC="10"
fi

log_error() {
  if [ -n "$MCP_PUSH_HOOK_LOG_PATH" ]; then
    printf '[%s] %s\n' "$(date +%Y-%m-%dT%H:%M:%S%z)" "$*" >> "$MCP_PUSH_HOOK_LOG_PATH" 2>/dev/null || true
  fi
}

is_truthy() {
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
    1|true|yes|y) return 0 ;;
    *) return 1 ;;
  esac
}

mcp_call() {
  local tool="$1"
  shift
  local -a cmd
  cmd=("$MCP_CALL" "$MCP_SERVER" "$tool" "$@")

  if command -v timeout > /dev/null 2>&1; then
    timeout "${MCP_PUSH_TIMEOUT_SEC}s" "${cmd[@]}" >/dev/null 2>&1
  else
    "${cmd[@]}" >/dev/null 2>&1
  fi
}

notify_send() {
  local title="$1"
  local content="$2"
  mcp_call notify_send --title "$title" --content "$content"
  local rc=$?
  if [ $rc -ne 0 ]; then
    log_error "notify_send failed (rc=$rc)"
  fi
  return $rc
}

notify_event() {
  local event="$1"
  local content="$2"
  mcp_call notify_event \
    --run_id "$RUN_ID" \
    --event "$event" \
    --message "$content" \
    --data "$EVENT_DATA_JSON"
  local rc=$?
  if [ $rc -ne 0 ]; then
    log_error "notify_event failed (event=$event, rc=$rc)"
  fi
  return $rc
}

notify_with_fallback() {
  local title="$1"
  local event="$2"
  local content="$3"

  if is_truthy "$MCP_PUSH_STRUCTURED"; then
    if notify_event "$event" "$content"; then
      return 0
    fi
  fi

  notify_send "$title" "$content" || true
}

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
STARTED_AT_ISO="$(date -d "@$((STARTED_AT_MS / 1000))" -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || true)"
EVENT_DATA_JSON="$(jq -n --arg duration_ms "$ELAPSED_MS" --arg started_at_ms "$STARTED_AT_MS" --arg started_at "$STARTED_AT_ISO" '{duration_ms: ($duration_ms|tonumber), started_at_ms: ($started_at_ms|tonumber), started_at: $started_at}' 2>/dev/null || printf '{}')"

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
    notify_with_fallback "$TITLE" "needs_user_action" "$MESSAGE"
    ;;
  "end")
    TITLE="任务完成"
    notify_with_fallback "$TITLE" "end" "$MESSAGE"
    ;;
  "error")
    TITLE="任务失败"
    notify_with_fallback "$TITLE" "error" "$MESSAGE"
    ;;
esac

print_hook_json
