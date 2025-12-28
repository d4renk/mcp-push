#!/usr/bin/env python3
"""Test Python Worker directly via Unix socket."""

import json
import socket
import sys
import time
import subprocess


def send_request(sock, method, params):
    """Send JSON-RPC request and receive response."""
    request = {
        "id": f"test-{time.time()}",
        "method": method,
        "params": params
    }

    body = json.dumps(request, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    sock.sendall(header + body)

    # Read response header
    headers = {}
    while True:
        line_bytes = b""
        while True:
            char = sock.recv(1)
            if not char:
                raise ConnectionError("Socket closed")
            line_bytes += char
            if line_bytes.endswith(b"\r\n") or line_bytes.endswith(b"\n"):
                break

        line = line_bytes.decode("ascii").strip()
        if not line:
            break

        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()

    # Read response body
    length = int(headers["content-length"])
    body = sock.recv(length)

    return json.loads(body.decode("utf-8"))


def main():
    # Start Python worker
    print("Starting Python worker...")
    worker_proc = subprocess.Popen(
        ["python3", "start_worker.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for socket path from stderr
    socket_path = None
    for i in range(50):
        line = worker_proc.stderr.readline()
        if "Worker listening on" in line:
            socket_path = line.split("Worker listening on ")[1].split()[0]
            print(f"Worker started: {socket_path}")
            break
        time.sleep(0.1)

    if not socket_path:
        print("Failed to start worker")
        worker_proc.kill()
        return 1

    try:
        # Connect to socket
        print(f"Connecting to {socket_path}...")
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(socket_path)
        print("Connected!")

        # Test 1: notify_send
        print("\n=== Test 1: notify_send ===")
        response = send_request(sock, "notify_send", {
            "title": "Test Notification",
            "content": "This is a test from integration test"
        })
        print(f"Response: {json.dumps(response, indent=2, ensure_ascii=False)}")

        # Test 2: notify_event
        print("\n=== Test 2: notify_event ===")
        response = send_request(sock, "notify_event", {
            "run_id": "test-integration-001",
            "event": "end",
            "message": "Integration test completed successfully",
            "data": {"test": True, "duration": 1.23}
        })
        print(f"Response: {json.dumps(response, indent=2, ensure_ascii=False)}")

        # Test 3: Invalid method
        print("\n=== Test 3: Invalid method ===")
        response = send_request(sock, "invalid.method", {})
        print(f"Response: {json.dumps(response, indent=2, ensure_ascii=False)}")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        sock.close()
        worker_proc.kill()
        worker_proc.wait()

    return 0


if __name__ == "__main__":
    sys.exit(main())
