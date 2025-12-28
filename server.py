#!/usr/bin/env python3
"""
MCP Server for mcp-push
Provides standardized MCP tool interface for notification channels
"""

import json
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from notify import send, push_config


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

    def _register_tools(self) -> List[Dict[str, Any]]:
        """注册 MCP 工具"""
        return [
            {
                "name": "notify.send",
                "description": "向所有已配置渠道广播消息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "消息标题"},
                        "content": {"type": "string", "description": "消息内容"}
                    },
                    "required": ["title", "content"]
                }
            },
            {
                "name": "notify.event",
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

    def handle_tools_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 tools/call 请求"""
        tool_name = request.get("name")
        arguments = request.get("arguments", {})

        if tool_name == "notify.send":
            return self._execute_send(arguments)
        elif tool_name == "notify.event":
            return self._execute_event(arguments)
        else:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]
            }

    def _execute_send(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行 notify.send 工具"""
        title = args.get("title", "")
        content = args.get("content", "")

        if not title or not content:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "title 和 content 为必填字段"}]
            }

        try:
            send(title, content)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "success",
                            "message": f"消息已推送到所有配置渠道",
                            "channels_count": len(self._get_active_channels())
                        }, ensure_ascii=False, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"推送失败: {str(e)}"}]
            }

    def _execute_event(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """执行 notify.event 工具"""
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
            send(title, content)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "status": "success",
                            "run_id": run_id,
                            "event": event,
                            "message": "事件已推送",
                            "timestamp": args["timestamp"],
                            "channels_count": len(self._get_active_channels())
                        }, ensure_ascii=False, indent=2)
                    }
                ]
            }
        except Exception as e:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"事件推送失败: {str(e)}"}]
            }

    def _get_active_channels(self) -> List[str]:
        """获取当前激活的推送渠道列表"""
        channels = []
        if push_config.get("DD_BOT_TOKEN") and push_config.get("DD_BOT_SECRET"):
            channels.append("dingding_bot")
        if push_config.get("FSKEY"):
            channels.append("feishu_bot")
        if push_config.get("TG_BOT_TOKEN") and push_config.get("TG_USER_ID"):
            channels.append("telegram_bot")
        if push_config.get("QYWX_KEY"):
            channels.append("wecom_bot")
        if push_config.get("QYWX_AM"):
            channels.append("wecom_app")
        if push_config.get("BARK_PUSH"):
            channels.append("bark")
        if push_config.get("PUSH_KEY"):
            channels.append("serverJ")
        if push_config.get("PUSH_PLUS_TOKEN"):
            channels.append("pushplus_bot")
        if push_config.get("DEER_KEY"):
            channels.append("pushdeer")
        if push_config.get("GOTIFY_URL") and push_config.get("GOTIFY_TOKEN"):
            channels.append("gotify")
        if push_config.get("NTFY_TOPIC"):
            channels.append("ntfy")
        return channels

    def run_stdio(self):
        """通过 stdio 运行 MCP Server"""
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                method = request.get("method")

                if method == "tools/list":
                    response = self.handle_tools_list()
                elif method == "tools/call":
                    params = request.get("params", {})
                    response = self.handle_tools_call(params)
                else:
                    response = {
                        "error": {"code": -32601, "message": f"Method not found: {method}"}
                    }

                # 发送响应
                print(json.dumps(response, ensure_ascii=False), flush=True)

            except json.JSONDecodeError as e:
                error_response = {
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                error_response = {
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
                }
                print(json.dumps(error_response), flush=True)


def main():
    server = MCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
