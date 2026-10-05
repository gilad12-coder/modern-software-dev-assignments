"""Tool behavior through an in-process MCP client (real protocol messages, no subprocess)."""

from __future__ import annotations

import asyncio
import json
import time
from http import HTTPStatus

import pytest
from fastmcp import Client
from server import mcp

from . import constants as T
from .conftest import issue, write_token


async def call(name: str, args: dict):
    """Call a tool through an in-process MCP client.

    Args:
        name: Tool name.
        args: Tool arguments.

    Returns:
        The call result; tool errors are returned, not raised.
    """
    async with Client(mcp) as client:
        return await client.call_tool(name, args, raise_on_error=False)


def error_of(result) -> dict:
    """Assert a tool call failed and decode its error payload.

    Args:
        result: A tool call result.

    Returns:
        The JSON error body.
    """
    assert result.is_error, result
    return json.loads(result.content[0].text)


async def test_list_repos_sorts_and_shapes(fake, server_env):
    """Repos come back newest push first, with only the shaped fields.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    result = await call(T.TOOL_LIST_REPOS, {T.KEY_LIMIT: T.SMALL_REPO_LIMIT})
    data = result.structured_content
    assert [r[T.KEY_FULL_NAME] for r in data[T.KEY_REPOS]] == [T.REPO_NAME, T.OLD_REPO_NAME]
    assert set(data[T.KEY_REPOS][0]) == {
        T.KEY_FULL_NAME,
        T.KEY_DESCRIPTION,
        T.KEY_PRIVATE,
        T.KEY_HAS_ISSUES,
        T.KEY_OPEN_ISSUES_AND_PRS,
        T.KEY_PUSHED_AT,
    }


async def test_list_repos_empty_is_explicit(fake, server_env):
    """No installations gives an empty list plus a note saying why.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    fake.route(T.HTTP_GET, T.INSTALLATIONS_PATH, {T.KEY_INSTALLATIONS: []})
    data = (await call(T.TOOL_LIST_REPOS, {})).structured_content
    assert data[T.KEY_REPOS] == [] and data[T.KEY_NOTE].startswith(T.NO_REPOS_PREFIX)


async def test_search_builds_query_and_drops_raw_fields(fake, server_env):
    """Arguments become one search query and raw-only fields are dropped.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    result = await call(
        T.TOOL_SEARCH_ISSUES,
        {
            T.KEY_REPO: T.REPO_NAME,
            T.KEY_QUERY: T.SEARCH_QUERY,
            T.KEY_LABELS: [T.STARTER_LABEL],
            T.KEY_STATE: T.STATE_ALL,
        },
    )
    q = fake.calls(T.HTTP_GET, T.SEARCH_ISSUES_PATH)[0][T.KEY_QUERY][T.KEY_Q]
    assert q == T.EXPECTED_LABEL_QUERY
    item = result.structured_content[T.KEY_ITEMS][0]
    assert (
        item[T.KEY_NUMBER] == T.ISSUE_NUMBER
        and item[T.KEY_REPO] == T.REPO_NAME
        and item[T.KEY_LABELS] == [T.BUG_LABEL]
    )
    assert T.KEY_BODY not in item and T.KEY_REACTIONS not in item and T.KEY_NODE_ID not in item


async def test_empty_search_points_at_list_repos(fake, server_env):
    """An empty search result tells the agent to check list_repos.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    fake.route(T.HTTP_GET, T.SEARCH_ISSUES_PATH, {T.KEY_TOTAL_COUNT: 0, T.KEY_ITEMS: []})
    data = (await call(T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: T.REPO_NAME})).structured_content
    assert data[T.KEY_ITEMS] == [] and T.DISCOVERY_HINT in data[T.KEY_NOTE]


async def test_get_issue_returns_newest_comments(fake, server_env):
    """get_issue keeps the newest comments and clips a long body.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    fake.route(
        T.HTTP_GET,
        T.ISSUE_PATH,
        issue(
            T.ISSUE_NUMBER,
            T.SHORT_TITLE,
            comments=T.COMMENT_COUNT,
            body=T.PLACEHOLDER_TEXT * T.LONG_BODY_LENGTH,
        ),
    )
    fake.route(
        T.HTTP_GET,
        T.COMMENTS_PATH,
        [
            {
                T.KEY_USER: {T.KEY_LOGIN: T.COMMENT_AUTHOR.format(number=i)},
                T.KEY_CREATED_AT: T.COMMENT_DATE.format(number=i),
                T.KEY_BODY: T.COMMENT_BODY.format(number=i),
            }
            for i in range(1, T.COMMENT_COUNT + 1)
        ],
    )
    data = await call(
        T.TOOL_GET_ISSUE,
        {
            T.KEY_REPO: T.REPO_NAME,
            T.KEY_NUMBER: T.ISSUE_NUMBER,
            T.KEY_MAX_COMMENTS: T.RECENT_COMMENT_LIMIT,
        },
    )
    data = data.structured_content
    assert [c[T.KEY_BODY] for c in data[T.KEY_RECENT_COMMENTS]] == [
        T.SECOND_COMMENT,
        T.THIRD_COMMENT,
    ]
    assert data[T.KEY_COMMENTS_OMITTED] == 1
    assert data[T.KEY_BODY_TRUNCATED] and len(data[T.KEY_BODY]) == T.CLIPPED_BODY_LENGTH


async def test_unknown_issue_is_not_retryable_and_points_at_search(fake, server_env):
    """A missing issue is not retryable and the hint points at search_issues.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    err = error_of(
        await call(
            T.TOOL_GET_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_NUMBER: T.MISSING_ISSUE_NUMBER}
        )
    )
    assert err[T.KEY_ERROR] == T.ERROR_NOT_FOUND and err[T.KEY_RETRYABLE] is False
    assert T.TOOL_SEARCH_ISSUES in err[T.KEY_HINT]


async def test_search_unknown_repo_maps_422_to_not_found(fake, server_env):
    """GitHub's 422 for an unknown repo becomes not_found.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    fake.route(
        T.HTTP_GET,
        T.SEARCH_ISSUES_PATH,
        {
            T.KEY_MESSAGE: T.VALIDATION_MESSAGE,
            T.KEY_ERRORS: [{T.KEY_MESSAGE: T.UNSEARCHABLE_REPO_MESSAGE}],
        },
        status=HTTPStatus.UNPROCESSABLE_ENTITY,
    )
    err = error_of(await call(T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: T.MISSING_REPO_NAME}))
    assert err[T.KEY_ERROR] == T.ERROR_NOT_FOUND and T.TOOL_LIST_REPOS in err[T.KEY_HINT]


async def test_rate_limit_is_retryable_with_wait(fake, server_env):
    """A primary rate limit is retryable and reports the wait.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    reset = int(time.time()) + T.RATE_LIMIT_WAIT
    fake.route(
        T.HTTP_GET,
        T.SEARCH_ISSUES_PATH,
        {T.KEY_MESSAGE: T.RATE_LIMIT_MESSAGE},
        status=HTTPStatus.FORBIDDEN,
        headers={T.HEADER_RATE_REMAINING: str(0), T.HEADER_RATE_RESET: str(reset)},
    )
    err = error_of(await call(T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: T.REPO_NAME}))
    assert err[T.KEY_ERROR] == T.ERROR_RATE_LIMITED and err[T.KEY_RETRYABLE] is True
    assert T.RATE_LIMIT_WAIT_MIN <= err[T.KEY_RETRY_AFTER_SECONDS] <= T.RATE_LIMIT_WAIT


async def test_forbidden_is_not_retryable(fake, server_env):
    """A 403 that is not a rate limit is not retryable.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    fake.route(T.HTTP_GET, T.ISSUE_PATH, {T.KEY_MESSAGE: T.FORBIDDEN_MESSAGE}, HTTPStatus.FORBIDDEN)
    err = error_of(
        await call(T.TOOL_GET_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_NUMBER: T.ISSUE_NUMBER})
    )
    assert err[T.KEY_ERROR] == T.ERROR_FORBIDDEN and err[T.KEY_RETRYABLE] is False


async def test_server_error_is_retryable(fake, server_env):
    """A 5xx from GitHub is retryable.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    fake.route(
        T.HTTP_GET, T.ISSUE_PATH, {T.KEY_MESSAGE: T.UPSTREAM_ERROR_MESSAGE}, HTTPStatus.BAD_GATEWAY
    )
    err = error_of(
        await call(T.TOOL_GET_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_NUMBER: T.ISSUE_NUMBER})
    )
    assert err[T.KEY_ERROR] == T.ERROR_UPSTREAM_ERROR and err[T.KEY_RETRYABLE] is True


async def test_network_down_is_retryable(fake, server_env, monkeypatch):
    """An unreachable GitHub is a retryable network_error.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
        monkeypatch: Used to change environment variables.
    """
    monkeypatch.setenv(T.GITHUB_API_URL, T.UNREACHABLE_API_URL)
    err = error_of(await call(T.TOOL_LIST_REPOS, {}))
    assert err[T.KEY_ERROR] == T.ERROR_NETWORK_ERROR and err[T.KEY_RETRYABLE] is True


async def test_schema_rejects_bad_arguments_before_any_request(fake, server_env):
    """Schema validation rejects bad arguments before GitHub is called.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    for name, args in [
        (T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: T.REPO_WEB_URL}),
        (T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: T.REPO_NAME, T.KEY_STATE: T.INVALID_STATE}),
        (T.TOOL_GET_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_NUMBER: 0}),
        (T.TOOL_CREATE_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_TITLE: ""}),
    ]:
        assert (await call(name, args)).is_error
    assert fake.requests == []


async def test_create_issue_dry_run_writes_nothing_and_flags_duplicates(fake, server_env):
    """The default dry run posts nothing and warns about similar issues.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    data = await call(
        T.TOOL_CREATE_ISSUE,
        {T.KEY_REPO: T.REPO_NAME, T.KEY_TITLE: T.SHORT_TITLE, T.KEY_LABELS: [T.BUG_LABEL]},
    )
    data = data.structured_content
    assert data[T.KEY_DRY_RUN] and not data[T.KEY_CREATED] and data[T.KEY_ISSUE] is None
    assert any(T.DUPLICATE_WARNING in w for w in data[T.KEY_WARNINGS])
    assert T.COMMIT_HINT in data[T.KEY_NEXT_STEP]
    assert fake.calls(T.HTTP_POST, T.ISSUES_PATH) == []


async def test_create_issue_commit_posts_once(fake, server_env):
    """dry_run=false posts exactly once with the previewed fields.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    args = {
        T.KEY_REPO: T.REPO_NAME,
        T.KEY_TITLE: T.NEW_ISSUE_TITLE,
        T.KEY_BODY: T.NEW_ISSUE_BODY,
        T.KEY_LABELS: [T.BUG_LABEL],
    }
    data = (await call(T.TOOL_CREATE_ISSUE, {**args, T.KEY_DRY_RUN: False})).structured_content
    posts = fake.calls(T.HTTP_POST, T.ISSUES_PATH)
    assert len(posts) == 1 and posts[0][T.KEY_JSON] == {
        T.KEY_TITLE: T.NEW_ISSUE_TITLE,
        T.KEY_BODY: T.NEW_ISSUE_BODY,
        T.KEY_LABELS: [T.BUG_LABEL],
    }
    assert data[T.KEY_CREATED] and data[T.KEY_ISSUE][T.KEY_NUMBER] == T.CREATED_ISSUE_NUMBER


async def test_create_issue_rejects_unknown_labels_even_on_commit(fake, server_env):
    """Unknown labels fail before any write, even with dry_run=false.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    args = {
        T.KEY_REPO: T.REPO_NAME,
        T.KEY_TITLE: T.PLACEHOLDER_TEXT,
        T.KEY_LABELS: [T.UNKNOWN_LABEL],
        T.KEY_DRY_RUN: False,
    }
    err = error_of(await call(T.TOOL_CREATE_ISSUE, args))
    assert err[T.KEY_ERROR] == T.ERROR_UNKNOWN_LABELS and T.BUG_LABEL in err[T.KEY_HINT]
    assert fake.calls(T.HTTP_POST, T.ISSUES_PATH) == []


async def test_create_issue_refuses_repo_with_issues_disabled(fake, server_env):
    """A repo with issues turned off is refused.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    fake.route(T.HTTP_GET, T.REPO_PATH, {T.KEY_FULL_NAME: T.REPO_NAME, T.KEY_HAS_ISSUES: False})
    err = error_of(
        await call(T.TOOL_CREATE_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_TITLE: T.PLACEHOLDER_TEXT})
    )
    assert err[T.KEY_ERROR] == T.ERROR_ISSUES_DISABLED


# ---------- OAuth: caching, silent refresh, mid-session death ----------


async def test_cached_token_is_reused_without_refresh(fake, server_env):
    """A valid cached token is reused without refreshing.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    await call(T.TOOL_LIST_REPOS, {})
    await call(T.TOOL_LIST_REPOS, {})
    assert fake.refresh_calls == 0


async def test_expired_token_is_refreshed_silently_and_rotated(fake, server_env, tmp_path):
    """An expired token is refreshed silently and the new pair is saved as 0600.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
        tmp_path: Directory holding the token file.
    """
    write_token(tmp_path / T.TOKEN_FILENAME, expires_in=T.EXPIRED_SECONDS)
    fake.valid_tokens = {T.UNKNOWN_ACCESS_TOKEN}
    result = await call(T.TOOL_LIST_REPOS, {})
    assert not result.is_error
    assert fake.refresh_calls == 1
    cached = json.loads((tmp_path / T.TOKEN_FILENAME).read_text())
    assert (
        cached[T.KEY_ACCESS_TOKEN] == T.ROTATED_ACCESS_TOKEN
        and cached[T.KEY_REFRESH_TOKEN] == T.ROTATED_REFRESH_TOKEN
    )
    assert (tmp_path / T.TOKEN_FILENAME).stat().st_mode & T.FILE_MODE_MASK == T.PRIVATE_FILE_MODE


async def test_401_mid_session_refreshes_once_and_retries(fake, server_env):
    """A 401 on a token that looked valid triggers one refresh and a retry.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    fake.valid_tokens = {T.REVOKED_ACCESS_TOKEN}
    result = await call(T.TOOL_GET_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_NUMBER: T.ISSUE_NUMBER})
    assert not result.is_error and fake.refresh_calls == 1


async def test_dead_refresh_token_returns_auth_required(fake, server_env):
    """A dead refresh token gives auth_required with the login command.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
    """
    fake.valid_tokens = set()
    fake.refresh_tokens = set()
    err = error_of(await call(T.TOOL_LIST_REPOS, {}))
    assert err[T.KEY_ERROR] == T.ERROR_AUTH_REQUIRED and err[T.KEY_RETRYABLE] is False
    assert T.LOGIN_HINT in err[T.KEY_HINT]


async def test_missing_token_file_returns_auth_required(fake, server_env, tmp_path):
    """No token file gives auth_required without calling GitHub.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
        tmp_path: Directory holding the token file.
    """
    (tmp_path / T.TOKEN_FILENAME).unlink()
    err = error_of(await call(T.TOOL_LIST_REPOS, {}))
    assert err[T.KEY_ERROR] == T.ERROR_AUTH_REQUIRED
    assert fake.requests == []


async def test_missing_client_credentials_is_not_configured(fake, server_env, monkeypatch):
    """Missing client credentials give not_configured.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
        monkeypatch: Used to change environment variables.
    """
    monkeypatch.delenv(T.GITHUB_CLIENT_SECRET)
    err = error_of(await call(T.TOOL_LIST_REPOS, {}))
    assert err[T.KEY_ERROR] == T.ERROR_NOT_CONFIGURED and err[T.KEY_RETRYABLE] is False


async def test_concurrent_calls_refresh_only_once(fake, server_env, tmp_path):
    """Five parallel calls with an expired token share a single refresh.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
        tmp_path: Directory holding the token file.
    """
    # GitHub refresh tokens are single-use: a second refresh with the same one would fail.
    write_token(tmp_path / T.TOKEN_FILENAME, expires_in=T.EXPIRED_SECONDS)
    async with Client(mcp) as client:
        results = await asyncio.gather(
            *[
                client.call_tool(T.TOOL_LIST_REPOS, {}, raise_on_error=False)
                for _ in range(T.CONCURRENT_CALLS)
            ]
        )
    assert not any(r.is_error for r in results)
    assert fake.refresh_calls == 1


@pytest.mark.parametrize(
    "retry_after,expected_wait",
    [(str(T.NUMERIC_RETRY_WAIT), T.NUMERIC_RETRY_WAIT), (T.INVALID_DATE, T.FALLBACK_RETRY_WAIT)],
)
async def test_secondary_rate_limit_retry_after(fake, server_env, retry_after, expected_wait):
    """Honor a numeric Retry-After and fall back safely for a malformed date.

    Args:
        fake: The fake GitHub, to set routes and inspect requests.
        server_env: Environment pointing the server at the fake.
        retry_after: The Retry-After header value.
        expected_wait: The requested delay or the one-minute fallback.
    """
    fake.route(
        T.HTTP_GET,
        T.SEARCH_ISSUES_PATH,
        {T.KEY_MESSAGE: T.SECONDARY_LIMIT_MESSAGE},
        HTTPStatus.FORBIDDEN,
        {T.HEADER_RETRY_AFTER: retry_after},
    )
    err = error_of(await call(T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: T.REPO_NAME}))
    assert (
        err[T.KEY_ERROR] == T.ERROR_RATE_LIMITED and err[T.KEY_RETRY_AFTER_SECONDS] == expected_wait
    )
