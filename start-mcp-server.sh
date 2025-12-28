#!/bin/bash

# Load configuration
if [ -f "$(dirname "$0")/config.sh" ]; then
  source "$(dirname "$0")/config.sh"
fi

# Start MCP server
exec node "$(dirname "$0")/apps/mcp-server/build/index.js"
