import json
import os
import subprocess
import sys
import time

def test_mcp_server():
    print("Starting MCP Server test...")
    
    # Prepare environment
    env = os.environ.copy()
    env["CONSOLE"] = "true"
    env["HITOKOTO"] = "false" # Disable hitokoto to make output predictable
    
    # Try to load config.sh
    config_path = "config.sh"
    if os.path.exists(config_path):
        print(f"Loading environment variables from {config_path}...")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("export "):
                        # Remove 'export ' and split by first '='
                        parts = line[7:].split("=", 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            # Remove quotes if present
                            value = parts[1].strip()
                            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                                value = value[1:-1]
                            
                            env[key] = value
                            # Mask partial value for log safety
                            masked_val = value[:4] + "***" if len(value) > 4 else "***"
                            print(f"  Loaded: {key}")
        except Exception as e:
            print(f"Warning: Failed to load config.sh: {e}")
    
    # Start server process
    process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        bufsize=1 # Line buffered
    )

    def send_request(req):
        print(f"\n[Client] Sending: {json.dumps(req, ensure_ascii=False)}")
        process.stdin.write(json.dumps(req) + "\n")
        process.stdin.flush()

    def read_response():
        while True:
            line = process.stdout.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                continue
            
            # Try to parse as JSON (MCP response)
            try:
                data = json.loads(line)
                print(f"[Client] Received JSON: {json.dumps(data, ensure_ascii=False)}")
                return data
            except json.JSONDecodeError:
                # Likely console output from notify.py
                print(f"[Client] Received LOG: {line}")
                # We return it as a special type or just continue reading if we only want JSON
                # For this test, we want to see logs too, but 'read_response' intends to get the RPC response.
                # So we keep reading until we get JSON.
                pass

    try:
        # 1. List Tools
        send_request({"jsonrpc": "2.0", "method": "tools/list", "id": 1})
        resp = read_response()
        if resp and "tools" in resp:
             print("✅ tools/list successful")
        else:
             print("❌ tools/list failed or unexpected response")

        # 2. Call notify_send
        print("\n--- Testing notify_send ---")
        send_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 2,
            "params": {
                "name": "notify_send",
                "arguments": {
                    "title": "Test Title",
                    "content": "Test Content from MCP"
                }
            }
        })
        # Expect logs then response
        resp = read_response()
        if resp and "content" in resp and not resp.get("isError"):
            print("✅ notify_send successful")
        else:
            print("❌ notify_send failed")

        # 3. Call notify_event (Sequence)
        print("\n--- Testing notify_event Sequence ---")
        run_id = "test-run-001"
        
        # Start
        send_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 3,
            "params": {
                "name": "notify_event",
                "arguments": {
                    "run_id": run_id,
                    "event": "start",
                    "message": "Task started"
                }
            }
        })
        read_response()

        # Update
        send_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 4,
            "params": {
                "name": "notify_event",
                "arguments": {
                    "run_id": run_id,
                    "event": "update",
                    "message": "Task processing",
                    "data": {"progress": 0.5}
                }
            }
        })
        read_response()

        # End
        send_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 5,
            "params": {
                "name": "notify_event",
                "arguments": {
                    "run_id": run_id,
                    "event": "end",
                    "message": "Task finished"
                }
            }
        })
        read_response()
        
        print("\n✅ All tests completed.")

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
    finally:
        process.terminate()

if __name__ == "__main__":
    test_mcp_server()
