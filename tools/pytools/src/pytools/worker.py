#!/usr/bin/env python3
"""Unix socket worker for MCP tool execution."""

import json
import logging
import os
import socket
import sys
from typing import Optional

from . import dispatcher

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

MAX_FRAME_SIZE = 10 * 1024 * 1024  # 10 MB limit


def _read_frame(reader) -> Optional[bytes]:
    """Read Content-Length framed message with size limits."""
    headers = {}
    while True:
        line = reader.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        try:
            name, value = line.decode("ascii").split(":", 1)
        except ValueError:
            continue
        headers[name.strip().lower()] = value.strip()

    length_str = headers.get("content-length")
    if not length_str:
        raise ValueError("Missing Content-Length header")

    length = int(length_str)
    if length > MAX_FRAME_SIZE:
        raise ValueError(f"Frame size {length} exceeds maximum {MAX_FRAME_SIZE}")

    # Read full body with loop to handle partial reads
    body = b""
    remaining = length
    while remaining > 0:
        chunk = reader.read(remaining)
        if not chunk:
            raise ValueError("Connection closed before reading full frame")
        body += chunk
        remaining -= len(chunk)

    return body


def _write_frame(conn: socket.socket, payload: dict) -> None:
    """Write Content-Length framed message."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    conn.sendall(header + body)


def _handle_connection(conn: socket.socket) -> None:
    """Handle single client connection with error recovery."""
    try:
        with conn, conn.makefile("rb") as reader:
            while True:
                try:
                    body = _read_frame(reader)
                    if body is None:
                        break
                except (ValueError, UnicodeDecodeError) as exc:
                    logger.error("Frame read error: %s", exc)
                    try:
                        _write_frame(
                            conn, {"id": None, "result": None, "error": {"message": str(exc)}}
                        )
                    except Exception:
                        pass
                    break

                try:
                    request = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError as exc:
                    _write_frame(
                        conn, {"id": None, "result": None, "error": {"message": str(exc)}}
                    )
                    continue

                req_id = request.get("id")
                method = request.get("method")
                params = request.get("params", {})

                try:
                    result = dispatcher.dispatch(method, params)
                    response = {"id": req_id, "result": result, "error": None}
                except Exception as exc:
                    logger.exception("Error dispatching %s", method)
                    response = {
                        "id": req_id,
                        "result": None,
                        "error": {"message": str(exc)},
                    }
                _write_frame(conn, response)
    except Exception as exc:
        logger.error("Connection handler error: %s", exc)


def run() -> str:
    """Start Unix socket server with restricted permissions."""
    socket_path = f"/tmp/mcp-push-{os.getpid()}.sock"
    if os.path.exists(socket_path):
        os.unlink(socket_path)

    # Set umask to restrict socket permissions
    old_umask = os.umask(0o077)
    try:
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(socket_path)
        server.listen(5)
        logger.info("Worker listening on %s (PID: %d)", socket_path, os.getpid())
    finally:
        os.umask(old_umask)

    try:
        while True:
            conn, _ = server.accept()
            _handle_connection(conn)
    except KeyboardInterrupt:
        logger.info("Worker shutting down")
    finally:
        server.close()
        if os.path.exists(socket_path):
            os.unlink(socket_path)
    return socket_path


if __name__ == "__main__":
    run()
