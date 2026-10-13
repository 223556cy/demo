"""launch_agentdebug_inspect.py — 启动 AgentDebugX inspect web UI"""
import sys
from pathlib import Path

sys.path.insert(0, r"D:/tmp_agentdebugx/AgentDebugX/src")
from agentdebug.cli.main import main

sys.argv = [
    "agentdebug",
    "inspect",
    "--store-sqlite", r"D:/tmp_agentdebugx/trace_store.sqlite",
    "--host", "127.0.0.1",
    "--port", "7788",
]
sys.exit(main())
