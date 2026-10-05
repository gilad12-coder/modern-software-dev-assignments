"""End-to-end over the real stdio transport: spawn the server with the documented command."""

from __future__ import annotations

import json
import os

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from . import constants as T


def stdio_client(env: dict[str, str]) -> Client:
    """Build a client that spawns the server with the documented command.

    Args:
        env: Extra environment variables for the server process.

    Returns:
        An unconnected FastMCP client over stdio.
    """
    transport = StdioTransport(
        T.SERVER_COMMAND,
        T.SERVER_ARGS,
        env={**os.environ, **env},
        cwd=str(T.REPO_ROOT),
    )
    return Client(transport)


async def test_stdio_handshake_exposes_contract(server_env):
    """The handshake exposes the instructions, four tools, annotations and schemas.

    Args:
        server_env: Environment pointing at the fake GitHub.
    """
    async with stdio_client(server_env) as client:
        assert T.TOOL_LIST_REPOS in client.instructions
        tools = {t.name: t for t in await client.list_tools()}
    assert set(tools) == T.ALL_TOOLS
    for name in T.READ_TOOLS:
        assert tools[name].annotations.read_only_hint is True
    create = tools[T.TOOL_CREATE_ISSUE]
    assert create.annotations.read_only_hint is False
    assert create.input_schema[T.KEY_PROPERTIES][T.KEY_DRY_RUN][T.KEY_DEFAULT] is True
    state = tools[T.TOOL_SEARCH_ISSUES].input_schema[T.KEY_PROPERTIES][T.KEY_STATE]
    assert state[T.KEY_ENUM] == T.ISSUE_STATES
    assert T.KEY_PATTERN in tools[T.TOOL_GET_ISSUE].input_schema[T.KEY_PROPERTIES][T.KEY_REPO]
    assert tools[T.TOOL_GET_ISSUE].output_schema[T.KEY_PROPERTIES][T.KEY_RECENT_COMMENTS]


async def test_stdio_chain_and_error(fake, server_env):
    """The tools chain over stdio and a missing issue comes back as a tool error.

    Args:
        fake: The fake GitHub, to inspect the requests made.
        server_env: Environment pointing at the fake.
    """
    async with stdio_client(server_env) as client:
        repos = await client.call_tool(T.TOOL_LIST_REPOS, {})
        repo = repos.structured_content[T.KEY_REPOS][0][T.KEY_FULL_NAME]
        found = await client.call_tool(
            T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: repo, T.KEY_QUERY: T.SEARCH_QUERY}
        )
        number = found.structured_content[T.KEY_ITEMS][0][T.KEY_NUMBER]
        detail = await client.call_tool(T.TOOL_GET_ISSUE, {T.KEY_REPO: repo, T.KEY_NUMBER: number})
        assert detail.structured_content[T.KEY_TITLE] == T.ISSUE_TITLE

        missing = await client.call_tool(
            T.TOOL_GET_ISSUE,
            {T.KEY_REPO: repo, T.KEY_NUMBER: T.MISSING_ISSUE_NUMBER},
            raise_on_error=False,
        )
    assert missing.is_error
    assert json.loads(missing.content[0].text)[T.KEY_ERROR] == T.ERROR_NOT_FOUND
    assert [r[T.KEY_PATH] for r in fake.requests][
        : len(T.EXPECTED_CHAIN_PATHS)
    ] == T.EXPECTED_CHAIN_PATHS


async def test_stdio_preview_then_explicit_creation(fake, server_env):
    """Preview over stdio without writing, then create once on explicit commit.

    Args:
        fake: Local fake GitHub, used to inspect issue writes.
        server_env: Isolated credentials and endpoints for the subprocess.
    """
    arguments = {
        T.KEY_REPO: T.REPO_NAME,
        T.KEY_TITLE: T.REGRESSION_TITLE,
        T.KEY_LABELS: [T.BUG_LABEL],
    }
    async with stdio_client(server_env) as client:
        preview = await client.call_tool(T.TOOL_CREATE_ISSUE, arguments)
        assert preview.structured_content[T.KEY_CREATED] is False
        assert preview.structured_content[T.KEY_DRY_RUN] is True
        assert fake.calls(T.HTTP_POST, T.ISSUES_PATH) == []
        created = await client.call_tool(T.TOOL_CREATE_ISSUE, {**arguments, T.KEY_DRY_RUN: False})
    assert created.structured_content[T.KEY_CREATED] is True
    assert created.structured_content[T.KEY_ISSUE][T.KEY_NUMBER] == T.CREATED_ISSUE_NUMBER
    writes = fake.calls(T.HTTP_POST, T.ISSUES_PATH)
    assert len(writes) == 1
    assert writes[0][T.KEY_JSON] == {
        T.KEY_TITLE: T.REGRESSION_TITLE,
        T.KEY_BODY: "",
        T.KEY_LABELS: [T.BUG_LABEL],
    }
