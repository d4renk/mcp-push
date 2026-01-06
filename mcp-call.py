#!/usr/bin/env python3
"""
MCP 工具调用包装器
用法: mcp-call.py <server> <tool> <args...>
"""
import subprocess
import sys
import json

def main():
    if len(sys.argv) < 3:
        print("用法: mcp-call.py <server> <tool> <args...>", file=sys.stderr)
        sys.exit(1)

    server = sys.argv[1]
    tool = sys.argv[2]
    args = sys.argv[3:]

    # 解析参数为键值对
    params = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                value = args[i + 1]
                # 尝试解析 JSON
                try:
                    params[key] = json.loads(value)
                except:
                    params[key] = value
                i += 2
            else:
                params[key] = True
                i += 1
        else:
            i += 1

    # 构造 JSON-RPC 请求
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool,
            "arguments": params
        }
    }

    # 调用 MCP 服务器
    try:
        result = subprocess.run(
            ["python3", f"/home/sun/mcp-push/src/server.py"],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # 解析响应
            try:
                response = json.loads(result.stdout)
                if "result" in response:
                    content = response["result"].get("content", [])
                    if content and isinstance(content, list):
                        print(content[0].get("text", ""))
                    sys.exit(0)
            except:
                pass

        print(f"MCP 调用失败: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
