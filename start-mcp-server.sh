#!/bin/bash

# Load configuration
if [ -f "$(dirname "$0")/config.sh" ]; then
  source "$(dirname "$0")/config.sh"
fi

# Start MCP server
exec python3 "$(dirname "$0")/src/server.py"
