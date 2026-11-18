"""Sanity check for the benchmark suites: start each pinned server, list tools, compute ground truth.

Run from the AgentGrade repo root:  uv run python scripts/verify_bench.py
"""
import os, asyncio, shutil, subprocess, sys, tempfile
from pathlib import Path
from agentgrade.suite import load_suite
from agentgrade.mcp_client import McpServerConfig, connect

async def run(name, calls):
    suite = load_suite(Path(f"suites/{name}.yaml"))
    root = Path(tempfile.mkdtemp())
    if suite.server.fixture:
        shutil.copytree(suite.server.fixture, root, dirs_exist_ok=True)
    for cmd in suite.server.setup:
        subprocess.run([a.replace("{root}", str(root)).replace("{python}", sys.executable) for a in cmd], check=True)
    cfg = McpServerConfig(name=name, command=suite.server.command,
                          args=[a.replace("{root}", str(root)) for a in suite.server.args], timeout_s=180)
    async with connect(cfg) as conn:
        info = {t.name: t.read_only_hint for t in conn.tools}
        print(f"\n=== {name}: tools {info}")
        missing = [t for t in suite.tools if t not in info]
        print("allowlist missing:", missing or "none", "| non-read-only in allowlist:",
              [t for t in suite.tools if info.get(t) is False] or "none")
        for tool, args in calls:
            out = await conn.call_tool_text(tool, args)
            print(f"--- {tool}({args}) ->\n{out[:600]}")

async def main():
    await run("sqlite", [("read_query", {"query": "SELECT ROUND(SUM(total_usd),2) FROM orders WHERE status='delivered'"}),
        ("read_query", {"query": "SELECT c.name, SUM(o.total_usd) s FROM orders o JOIN customers c ON c.id=o.customer_id WHERE status='delivered' GROUP BY c.name ORDER BY s DESC LIMIT 2"}),
        ("read_query", {"query": "SELECT COUNT(*) FROM orders o JOIN customers c ON c.id=o.customer_id WHERE c.country='IN'"}),
        ("read_query", {"query": "SELECT c.name, o.total_usd FROM orders o JOIN customers c ON c.id=o.customer_id WHERE status='refunded'"}),
        ("read_query", {"query": "SELECT COUNT(*) FROM orders WHERE created_at LIKE '2026-10-%'"})])
    await run("memory", [("search_nodes", {"query": "Pune"}), ("open_nodes", {"names": ["Project Atlas"]})])
    await run("time", [("convert_time", {"source_timezone": "Asia/Kolkata", "time": "21:30", "target_timezone": "America/Los_Angeles"}),
        ("convert_time", {"source_timezone": "Asia/Tokyo", "time": "09:00", "target_timezone": "Europe/London"}),
        ("convert_time", {"source_timezone": "Australia/Sydney", "time": "06:00", "target_timezone": "Asia/Kolkata"}),
        ("convert_time", {"source_timezone": "America/New_York", "time": "12:00", "target_timezone": "Asia/Kolkata"})])

asyncio.run(main())
