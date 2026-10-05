"""End-to-end over the real stdio transport: spawn the server with the documented command."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

REPO_ROOT = Path(__file__).resolve().parents[2]


def stdio_client(env: dict[str, str]) -> Client:
    """Build a client that spawns the server with the documented command.

    Args:
        env: Extra environment variables for the server process.

    Returns:
        An unconnected FastMCP client over stdio.
    """
    transport = StdioTransport(
        "uv",
        ["run", "--directory", "week2", "python", "server.py"],
        env={**os.environ, **env},
        cwd=str(REPO_ROOT),
    )
    return Client(transport)


async def test_stdio_handshake_exposes_contract(server_env):
    """The handshake exposes the instructions, four tools, annotations and schemas.

    Args:
        server_env: Environment pointing at the fake GitHub.
    """
    async with stdio_client(server_env) as client:
        assert "list_repos" in client.instructions
        tools = {t.name: t for t in await client.list_tools()}
    assert set(tools) == {"list_repos", "search_issues", "get_issue", "create_issue"}
    for name in ("list_repos", "search_issues", "get_issue"):
        assert tools[name].annotations.read_only_hint is True
    create = tools["create_issue"]
    assert create.annotations.read_only_hint is False
    assert create.input_schema["properties"]["dry_run"]["default"] is True
    state = tools["search_issues"].input_schema["properties"]["state"]
    assert state["enum"] == ["open", "closed", "all"]
    assert "pattern" in tools["get_issue"].input_schema["properties"]["repo"]
    assert tools["get_issue"].output_schema["properties"]["recent_comments"]


async def test_stdio_chain_and_error(fake, server_env):
    """The tools chain over stdio and a missing issue comes back as a tool error.

    Args:
        fake: The fake GitHub, to inspect the requests made.
        server_env: Environment pointing at the fake.
    """
    async with stdio_client(server_env) as client:
        repos = await client.call_tool("list_repos", {})
        repo = repos.structured_content["repos"][0]["full_name"]
        found = await client.call_tool("search_issues", {"repo": repo, "query": "crash"})
        number = found.structured_content["items"][0]["number"]
        detail = await client.call_tool("get_issue", {"repo": repo, "number": number})
        assert detail.structured_content["title"] == "Crash on empty input"

        missing = await client.call_tool(
            "get_issue", {"repo": repo, "number": 999}, raise_on_error=False
        )
    assert missing.is_error
    assert json.loads(missing.content[0].text)["error"] == "not_found"
    assert [r["path"] for r in fake.requests][:3] == [
        "/user/installations",
        "/user/installations/1/repositories",
        "/search/issues",
    ]


async def test_stdio_preview_then_explicit_creation(fake, server_env):
    """Preview over stdio without writing, then create once on explicit commit.

    Args:
        fake: Local fake GitHub, used to inspect issue writes.
        server_env: Isolated credentials and endpoints for the subprocess.
    """
    arguments = {"repo": "alice/demo", "title": "Regression test", "labels": ["bug"]}
    async with stdio_client(server_env) as client:
        preview = await client.call_tool("create_issue", arguments)
        assert preview.structured_content["created"] is False
        assert preview.structured_content["dry_run"] is True
        assert fake.calls("POST", "/repos/alice/demo/issues") == []
        created = await client.call_tool("create_issue", {**arguments, "dry_run": False})
    assert created.structured_content["created"] is True
    assert created.structured_content["issue"]["number"] == 42
    writes = fake.calls("POST", "/repos/alice/demo/issues")
    assert len(writes) == 1
    assert writes[0]["json"] == {"title": "Regression test", "body": "", "labels": ["bug"]}
