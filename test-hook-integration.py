#!/usr/bin/env python3
"""
测试脚本：模拟 hook 调用 mcp-push 服务
"""
import subprocess
import sys
import json

def test_notify_send(title, content):
    """测试 notify_send"""
    print(f"\n✅ 测试 notify_send:")
    print(f"  标题: {title}")
    print(f"  内容: {content}")

    try:
        # 直接使用 Python 调用 MCP 服务器
        result = subprocess.run(
            ["python3", "/home/sun/mcp-push/src/server.py"],
            input=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "notify_send",
                    "arguments": {
                        "title": title,
                        "content": content
                    }
                }
            }),
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"  ✓ 推送成功")
            if result.stdout:
                print(f"  响应: {result.stdout[:200]}")
        else:
            print(f"  ✗ 推送失败: {result.stderr}")
    except Exception as e:
        print(f"  ✗ 错误: {e}")

def test_notify_event(run_id, event, message, data):
    """测试 notify_event"""
    print(f"\n✅ 测试 notify_event:")
    print(f"  run_id: {run_id}")
    print(f"  event: {event}")
    print(f"  message: {message}")
    print(f"  data: {data}")

    try:
        result = subprocess.run(
            ["python3", "/home/sun/mcp-push/src/server.py"],
            input=json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "notify_event",
                    "arguments": {
                        "run_id": run_id,
                        "event": event,
                        "message": message,
                        "data": data
                    }
                }
            }),
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"  ✓ 推送成功")
            if result.stdout:
                print(f"  响应: {result.stdout[:200]}")
        else:
            print(f"  ✗ 推送失败: {result.stderr}")
    except Exception as e:
        print(f"  ✗ 错误: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("MCP-PUSH Hook 集成测试")
    print("=" * 60)

    # 测试场景 1: 任务成功完成
    print("\n【场景 1】任务成功完成（耗时 75 秒）")
    test_notify_send("任务完成", "Task completed successfully")
    test_notify_event("test-run-123", "end", "Task completed successfully", {"duration_ms": 75000})

    # 测试场景 2: 任务失败
    print("\n【场景 2】任务失败（耗时 120 秒）")
    test_notify_send("任务失败", "Error: connection timeout")
    test_notify_event("test-run-456", "error", "Error: connection timeout", {"duration_ms": 120000})

    # 测试场景 3: 需要用户确认
    print("\n【场景 3】需要用户确认")
    test_notify_send("等待批准", "检测到敏感文件删除操作，请确认是否继续？")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
