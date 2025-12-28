"""Tool dispatcher for MCP push worker."""

from datetime import datetime
import json
from typing import Any, Dict, Callable

from . import notify_lib


def _require_fields(params: Dict[str, Any], fields: list) -> None:
    """Validate required fields in params."""
    missing = [field for field in fields if not params.get(field)]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")


def _status_from_errors(errors: Dict[str, str], channels: int) -> str:
    """Derive status from errors and channel count."""
    if not errors:
        return "success"
    if channels > 0 and len(errors) < channels:
        return "partial_success"
    return "error"


def handle_notify_send(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle notify.send tool invocation."""
    _require_fields(params, ["title", "content"])
    result = notify_lib.send(
        params["title"],
        params["content"],
        ignore_default_config=params.get("ignore_default_config", False),
    )
    errors = result.get("errors", {})
    channels = int(result.get("channels", 0) or 0)
    return {
        "status": _status_from_errors(errors, channels),
        "errors": errors,
        "channels": channels,
    }


def handle_notify_event(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle notify.event tool invocation."""
    _require_fields(params, ["run_id", "event", "message"])
    event = params["event"]
    if event not in {"start", "update", "end", "error"}:
        raise ValueError(f"Invalid event type: {event}")

    timestamp = params.get("timestamp") or datetime.utcnow().isoformat() + "Z"
    data = params.get("data")
    title = f"[{event.upper()}] {params['run_id']}"
    content = params["message"]

    if data:
        data_str = json.dumps(data, indent=2, ensure_ascii=False)
        content += f"\n\nAdditional data:\n```json\n{data_str}\n```"

    result = notify_lib.send(title, content)
    errors = result.get("errors", {})
    channels = int(result.get("channels", 0) or 0)
    return {
        "status": _status_from_errors(errors, channels),
        "run_id": params["run_id"],
        "event": event,
        "timestamp": timestamp,
        "errors": errors,
        "channels": channels,
    }


TOOL_MAP: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "notify.send": handle_notify_send,
    "notify.event": handle_notify_event,
}


def dispatch(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatch tool call to appropriate handler."""
    handler = TOOL_MAP.get(method)
    if not handler:
        raise ValueError(f"Unknown method: {method}")
    return handler(params or {})
