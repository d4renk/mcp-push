#!/usr/bin/env python3
"""Entry point for MCP Push Python Worker."""

import sys
from pathlib import Path

# Add pytools to path
worker_dir = Path(__file__).parent / "tools" / "pytools" / "src"
sys.path.insert(0, str(worker_dir))

from pytools.worker import run

if __name__ == "__main__":
    run()
