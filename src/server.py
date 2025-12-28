#!/usr/bin/env python3
"""
MCP Server for mcp-push
Provides standardized MCP tool interface for notification channels
"""

import builtins
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

_DEBUG_PATH = os.environ.get("MCP_PUSH_DEBUG_PATH", "/tmp/mcp-push.debug.log")
_DEBUG_ENABLED = os.environ.get("MCP_PUSH_DEBUG") not in (None, "", "0", "false", "False")


def _debug_log(message: str) -> None:
    if not _DEBUG_ENABLED:
        return
    try:
        with open(_DEBUG_PATH, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
    except Exception:
        pass


class MCPAdapter:
    """适配器层：实现传统 send() 与 Event Envelope 的双向转换"""

    @staticmethod
    def send_to_event(title: str, content: str) -> Dict[str, Any]:
        """将传统 send() 调用转换为 Event Envelope"""
        return {
            "run_id": f"legacy-{uuid.uuid4().hex[:8]}",
            "event": "end",
            "message": f"{title}\n\n{content}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    @staticmethod
    def event_to_send(envelope: Dict[str, Any]) -> tuple:
        """将 Event Envelope 转换为传统 send() 参数"""
        title = f"[{envelope['event'].upper()}] {envelope.get('run_id', 'N/A')}"
        content = envelope['message']

        if envelope.get('data'):
            data_str = json.dumps(envelope['data'], indent=2, ensure_ascii=False)
            content += f"\n\n**附加数据:**\n```json\n{data_str}\n```"

        return title, content


class MCPServer:
    """MCP Server 核心实现"""

    def __init__(self):
        self.tools = self._register_tools()
        self.prompt_text = self._load_prompt_text()
        self.server_info = {"name": "mcp-push", "version": "1.0.0"}
        self.capabilities = {"tools": {}, "prompts": {}}
        self._notify = None
        self._notify_error = None

    def _get_notify(self):
        if self._notify is not None or self._notify_error is not None:
            if self._notify_error is not None:
                raise self._notify_error
            return self._notify
        try:
            try:
                from . import notify  # type: ignore
            except ImportError:
                # Allow running as a script - add parent dir to path
                import os
                parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if parent not in sys.path:
                    sys.path.insert(0, parent)
                from src import notify  # type: ignore
            if hasattr(notify, "_print"):
                def _stderr_print(*args, **kw):
                    if "file" not in kw:
                        kw["file"] = sys.stderr
                    return builtins.print(*args, **kw)
                notify._print = _stderr_print
            self._notify = notify
            return notify
        except Exception as exc:
            self._notify_error = exc
            raise

    def _notify_error_response(self, message: str) -> Dict[str, Any]:
        return {
            "isError": True,
            "content": [{"type": "text", "text": message}],
        }

    def _register_tools(self) -> List[Dict[str, Any]]:
        """注册 MCP 工具"""
        return [
            {
                "name": "notify_send",
                "description": "向所有已配置渠道广播消息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "消息标题"},
                        "content": {"type": "string", "description": "消息内容"},
                        "ignore_default_config": {
                            "type": "boolean",
                            "description": "忽略默认配置（仅使用传入配置）"
                        }
                    },
                    "required": ["title", "content"]
                }
            },
            {
                "name": "notify_event",
                "description": "发送结构化事件流（支持进度追踪）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "run_id": {"type": "string", "description": "任务唯一标识"},
                        "event": {
                            "type": "string",
                            "enum": ["start", "update", "end", "error"],
                            "description": "事件类型"
                        },
                        "message": {"type": "string", "description": "人类可读的状态描述"},
                        "data": {
                            "type": "object",
                            "description": "附加数据（step, progress, artifact_url 等）"
                        },
                        "timestamp": {"type": "string", "format": "date-time"}
                    },
                    "required": ["run_id", "event", "message"]
                }
            }
        ]

    def handle_tools_list(self) -> Dict[str, Any]:
        """处理 tools/list 请求"""
        return {"tools": self.tools}

    def handle_prompts_list(self) -> Dict[str, Any]:
        """处理 prompts/list 请求"""
        return {
            "prompts": [
                {
                    "name": "mcp-push-guidelines",
                    "title": "mcp-push usage guidelines",
                    "description": "When to notify via mcp-push",
                }
            ]
        }

    def handle_prompts_get(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 prompts/get 请求"""
        name = request.get("name")
        if name != "mcp-push-guidelines":
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown prompt: {name}"}],
            }
        return {
            "description": "Guidelines for when to send notifications via mcp-push.",
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": self.prompt_text}],
                }
            ],
        }

    def handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 initialize 请求"""
        _ = request
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": self.capabilities,
            "serverInfo": self.server_info,
        }

    def handle_tools_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 tools/call 请求"""
        tool_name = request.get("name")
        arguments = request.get("arguments", {})
        normalized_name = {
            "notify_send": "notify_send",
            "notify_event": "notify_event",
        }.get(tool_name, tool_name)

        if normalized_name == "notify_send":
            return self._execute_send(arguments)
        elif normalized_name == "notify_event":
            return self._execute_event(arguments)
        else:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
            }

    def _execute_send(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行 notify_send 工具"""
        try:
            notify = self._get_notify()
        except Exception as exc:
            return self._notify_error_response(f"notify 模块加载失败: {str(exc)}")
        title = args.get("title", "")
        content = args.get("content", "")
        ignore_default_config = bool(args.get("ignore_default_config", False))

        if not title or not content:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "title 和 content 为必填字段"}]
            }

        try:
            result = notify.send(title, content, ignore_default_config=ignore_default_config)
            if not isinstance(result, dict):
                result = {"errors": {"unknown": "notify.send returned no result"}, "channels": 0}
            errors = result.get("errors", {})
            channels = int(result.get("channels", 0) or 0)
            status = self._status_from_errors(errors, channels)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "status": status,
                                "message": "消息已推送" if status == "success" else "消息推送未完全成功",
                                "channels_count": channels,
                                "errors": errors,
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                    }
                ],
                "isError": status == "error",
            }
        except Exception as e:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"推送失败: {str(e)}"}]
            }

    def _execute_event(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行 notify_event 工具"""
        try:
            notify = self._get_notify()
        except Exception as exc:
            return self._notify_error_response(f"notify 模块加载失败: {str(exc)}")
        run_id = args.get("run_id")
        event = args.get("event")
        message = args.get("message")
        data = args.get("data", {})

        if not all([run_id, event, message]):
            return {
                "isError": True,
                "content": [{"type": "text", "text": "run_id, event, message 为必填字段"}]
            }

        if event not in ["start", "update", "end", "error"]:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"无效的 event 类型: {event}"}]
            }

        # 自动填充时间戳
        if "timestamp" not in args:
            args["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # 转换为传统 send() 调用
        title, content = MCPAdapter.event_to_send(args)

        try:
            result = notify.send(title, content)
            if not isinstance(result, dict):
                result = {"errors": {"unknown": "notify.send returned no result"}, "channels": 0}
            errors = result.get("errors", {})
            channels = int(result.get("channels", 0) or 0)
            status = self._status_from_errors(errors, channels)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": status,
                            "run_id": run_id,
                            "event": event,
                            "message": "事件已推送" if status == "success" else "事件推送未完全成功",
                            "timestamp": args["timestamp"],
                            "channels_count": channels,
                            "errors": errors,
                        }, ensure_ascii=False, indent=2)
                    }
                ],
                "isError": status == "error",
            }
        except Exception as e:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"事件推送失败: {str(e)}"}]
            }

    def _get_active_channels(self) -> List[str]:
        """获取当前激活的推送渠道列表"""
        try:
            notify = self._get_notify()
        except Exception:
            return []
        channels = []
        if notify.push_config.get("DD_BOT_TOKEN") and notify.push_config.get("DD_BOT_SECRET"):
            channels.append("dingding_bot")
        if notify.push_config.get("FSKEY"):
            channels.append("feishu_bot")
        if notify.push_config.get("TG_BOT_TOKEN") and notify.push_config.get("TG_USER_ID"):
            channels.append("telegram_bot")
        if notify.push_config.get("QYWX_KEY"):
            channels.append("wecom_bot")
        if notify.push_config.get("QYWX_AM"):
            channels.append("wecom_app")
        if notify.push_config.get("BARK_PUSH"):
            channels.append("bark")
        if notify.push_config.get("PUSH_KEY"):
            channels.append("serverJ")
        if notify.push_config.get("PUSH_PLUS_TOKEN"):
            channels.append("pushplus_bot")
        if notify.push_config.get("DEER_KEY"):
            channels.append("pushdeer")
        if notify.push_config.get("GOTIFY_URL") and notify.push_config.get("GOTIFY_TOKEN"):
            channels.append("gotify")
        if notify.push_config.get("NTFY_TOPIC"):
            channels.append("ntfy")
        return channels

    @staticmethod
    def _load_prompt_text() -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), "提示词.json")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return "Use mcp-push only for task completion (>60s) or when user confirmation is needed."

    @staticmethod
    def _status_from_errors(errors: Dict[str, str], channels: int) -> str:
        if not errors:
            return "success"
        if channels > 0 and len(errors) < channels:
            return "partial_success"
        return "error"

    def run_stdio(self):
        """通过 stdio 运行 MCP Server"""
        _debug_log("mcp-push: run_stdio start")
        reader = sys.stdin.buffer
        while True:
            try:
                parsed = self._read_request(reader)
                if parsed is None:
                    _debug_log("mcp-push: EOF received, exiting")
                    break
                request, framed = parsed
                method = request.get("method")
                request_id = request.get("id")
                use_jsonrpc = "jsonrpc" in request or "id" in request
                _debug_log(f"mcp-push: request method={method} framed={framed} jsonrpc={use_jsonrpc} id={request_id}")

                response = None
                error = None
                if method == "initialize":
                    params = request.get("params", {})
                    response = self.handle_initialize(params)
                elif method == "initialized":
                    response = None
                elif method == "notifications/initialized":
                    response = None
                elif method == "tools/list":
                    response = self.handle_tools_list()
                elif method == "prompts/list":
                    response = self.handle_prompts_list()
                elif method == "prompts/get":
                    params = request.get("params", {})
                    response = self.handle_prompts_get(params)
                elif method == "tools/call":
                    params = request.get("params", {})
                    response = self.handle_tools_call(params)
                else:
                    error = {"code": -32601, "message": f"Method not found: {method}"}

                if not (use_jsonrpc and request_id is None):
                    self._write_response(
                        response,
                        framed,
                        use_jsonrpc=use_jsonrpc,
                        request_id=request_id,
                        error=error,
                    )

            except json.JSONDecodeError as e:
                error_response = {
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                }
                _debug_log(f"mcp-push: JSON decode error: {e}")
                self._write_response(error_response, framed=False)
            except Exception as e:
                error_response = {
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                }
                _debug_log(f"mcp-push: internal error: {e}")
                self._write_response(error_response, framed=False)

    @staticmethod
    def _read_request(reader) -> Optional[tuple]:
        line = reader.readline()
        if not line:
            return None
        if line in (b"\n", b"\r\n"):
            return MCPServer._read_request(reader)

        if line.lower().startswith(b"content-length:"):
            body = MCPServer._read_framed_body(reader, first_line=line)
            return json.loads(body.decode("utf-8")), True

        return json.loads(line.decode("utf-8").strip()), False

    @staticmethod
    def _read_framed_body(reader, first_line: bytes) -> bytes:
        headers = {}

        def add_header(header_line: bytes) -> None:
            try:
                name, value = header_line.decode("ascii").split(":", 1)
            except ValueError:
                return
            headers[name.strip().lower()] = value.strip()

        add_header(first_line)
        while True:
            line = reader.readline()
            if not line:
                raise ValueError("Connection closed before headers complete")
            if line in (b"\n", b"\r\n"):
                break
            add_header(line)

        length_str = headers.get("content-length")
        if not length_str:
            raise ValueError("Missing Content-Length header")
        length = int(length_str)
        if length < 0 or length > 10 * 1024 * 1024:
            raise ValueError(f"Invalid Content-Length: {length}")

        body = reader.read(length)
        if len(body) != length:
            raise ValueError("Connection closed before reading full frame")
        return body

    @staticmethod
    def _write_response(
        response: Optional[Dict[str, Any]],
        framed: bool,
        use_jsonrpc: bool = False,
        request_id: Optional[Any] = None,
        error: Optional[Dict[str, Any]] = None,
    ) -> None:
        if response is None and error is None:
            return
        payload_obj: Dict[str, Any]
        if use_jsonrpc:
            if error:
                payload_obj = {"jsonrpc": "2.0", "id": request_id, "error": error}
            else:
                payload_obj = {"jsonrpc": "2.0", "id": request_id, "result": response}
        else:
            payload_obj = response or {"error": error}

        payload = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")
        if framed:
            header = f"Content-Length: {len(payload)}\r\n\r\n".encode("ascii")
            sys.stdout.buffer.write(header + payload)
            sys.stdout.buffer.flush()
        else:
            print(payload.decode("utf-8"), flush=True)
        _debug_log(f"mcp-push: response sent framed={framed} jsonrpc={use_jsonrpc} id={request_id}")


def main():
    server = MCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
