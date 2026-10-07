"""Regression checks for the local pre-submission review; no real GitHub calls."""

from __future__ import annotations

import json
import time
from email.utils import formatdate
from http import HTTPStatus

import github
import httpx
import pytest
from fastmcp import Client
from jsonschema import Draft202012Validator
from models import Token
from oauth import TokenStore
from server import mcp

from . import constants as T
from .conftest import issue, write_token
from .test_tools import call, error_of


@pytest.mark.parametrize("failure", [T.TIMEOUT_FAILURE, T.SERVER_FAILURE])
async def test_uncertain_issue_creation_must_not_be_retried(fake, server_env, monkeypatch, failure):
    """Do not recommend duplicate writes after losing the creation response.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        monkeypatch: Replaces the HTTP request for the timeout case.
        failure: Simulated failure after dispatching the write.
    """
    sent = []
    request = httpx.AsyncClient.request

    async def lose_response(client, method, url, **kwargs):
        """Drop the response only after the fake has accepted the write.

        Args:
            client: HTTP client.
            method: HTTP method.
            url: Endpoint path.
            **kwargs: Request options.

        Returns:
            The response for reads.
        """
        response = await request(client, method, url, **kwargs)
        if method == T.HTTP_POST and str(url).endswith(T.ISSUES_SUFFIX):
            sent.append(response.status_code)
            raise httpx.ReadTimeout(T.RESPONSE_LOST_MESSAGE)
        return response

    if failure == T.TIMEOUT_FAILURE:
        monkeypatch.setattr(httpx.AsyncClient, "request", lose_response)
    else:
        fake.route(
            T.HTTP_POST,
            T.ISSUES_PATH,
            {T.KEY_MESSAGE: T.RESPONSE_LOST_MESSAGE},
            HTTPStatus.BAD_GATEWAY,
        )
    error = error_of(
        await call(
            T.TOOL_CREATE_ISSUE,
            {T.KEY_REPO: T.REPO_NAME, T.KEY_TITLE: T.NEW_ISSUE_TITLE, T.KEY_DRY_RUN: False},
        )
    )
    assert len(fake.calls(T.HTTP_POST, T.ISSUES_PATH)) == 1
    assert error[T.KEY_ERROR] == T.ERROR_WRITE_OUTCOME_UNKNOWN
    assert error[T.KEY_RETRYABLE] is False and T.TOOL_SEARCH_ISSUES in error[T.KEY_HINT]
    if failure == T.TIMEOUT_FAILURE:
        assert sent == [HTTPStatus.CREATED]


@pytest.mark.parametrize(
    "status,body",
    [
        (HTTPStatus.TOO_MANY_REQUESTS, {T.KEY_MESSAGE: T.TOO_MANY_REQUESTS_MESSAGE}),
        (HTTPStatus.OK, [T.INVALID_TOKEN_RESPONSE]),
        (HTTPStatus.OK, {}),
    ],
)
async def test_temporary_oauth_failure_does_not_request_login(
    fake, server_env, tmp_path, status, body
):
    """Keep a valid refresh token when its endpoint is temporarily unavailable.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        tmp_path: Token-cache directory.
        status: Token-endpoint HTTP status.
        body: Token-endpoint JSON response.
    """
    write_token(tmp_path / T.TOKEN_FILENAME, expires_in=T.JUST_EXPIRED_SECONDS)
    before = (tmp_path / T.TOKEN_FILENAME).read_bytes()
    fake.route(
        T.HTTP_POST, T.TOKEN_PATH, body, status, {T.HEADER_RETRY_AFTER: str(T.RATE_LIMIT_WAIT)}
    )
    error = error_of(await call(T.TOOL_LIST_REPOS, {}))
    assert error[T.KEY_RETRYABLE] is True and error[T.KEY_ERROR] != T.ERROR_AUTH_REQUIRED
    assert (tmp_path / T.TOKEN_FILENAME).read_bytes() == before
    if status == HTTPStatus.TOO_MANY_REQUESTS:
        assert error[T.KEY_RETRY_AFTER_SECONDS] == T.RATE_LIMIT_WAIT


async def test_labels_beyond_first_page_are_valid(fake, server_env):
    """Accept a label from page two without creating an issue during preview.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    pages = [
        [{T.KEY_NAME: T.LABEL_PAGE_NAME.format(number=n)} for n in range(T.PAGE_SIZE)],
        [{T.KEY_NAME: T.LAST_LABEL}],
    ]
    fake.routes[(T.HTTP_GET, T.LABELS_PATH)] = lambda req: (
        HTTPStatus.OK,
        pages[int(req[T.KEY_QUERY].get(T.KEY_PAGE, str(1))) - 1],
        {},
    )
    result = await call(
        T.TOOL_CREATE_ISSUE,
        {T.KEY_REPO: T.REPO_NAME, T.KEY_TITLE: T.BUG_TITLE, T.KEY_LABELS: [T.LAST_LABEL]},
    )
    assert not result.is_error
    assert result.structured_content[T.KEY_CREATED] is False
    assert len(fake.calls(T.HTTP_GET, T.LABELS_PATH)) == 2
    assert fake.calls(T.HTTP_POST, T.ISSUES_PATH) == []


async def test_repo_pagination_does_not_silently_stop_at_500(fake, server_env):
    """Include a recently pushed repository after the fifth API page.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    repos = [
        {
            **T.REPO,
            T.KEY_FULL_NAME: T.REPO_PAGE_NAME.format(number=i),
            T.KEY_PUSHED_AT: T.ARCHIVE_PUSHED_AT,
        }
        for i in range(T.LONG_REPO_COUNT)
    ]
    repos.append({**T.REPO, T.KEY_FULL_NAME: T.NEWEST_REPO_NAME})
    fake.routes[(T.HTTP_GET, T.INSTALLATION_REPOS_PATH)] = lambda req: (
        HTTPStatus.OK,
        {
            T.KEY_REPOSITORIES: repos[
                (int(req[T.KEY_QUERY].get(T.KEY_PAGE, str(1))) - 1) * T.PAGE_SIZE : int(
                    req[T.KEY_QUERY].get(T.KEY_PAGE, str(1))
                )
                * T.PAGE_SIZE
            ]
        },
        {},
    )
    result = (await call(T.TOOL_LIST_REPOS, {T.KEY_LIMIT: 1})).structured_content
    assert result[T.KEY_TOTAL_ACCESSIBLE] == T.TOTAL_REPO_COUNT
    assert result[T.KEY_REPOS][0][T.KEY_FULL_NAME] == T.NEWEST_REPO_NAME
    assert str(T.TOTAL_REPO_COUNT) in result[T.KEY_NOTE] and T.KEY_LIMIT in result[T.KEY_NOTE]


async def test_schema_errors_use_the_structured_contract(fake, server_env):
    """Reject invalid input before HTTP with an actionable JSON tool error.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    error = error_of(await call(T.TOOL_GET_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_NUMBER: 0}))
    assert error[T.KEY_ERROR] == T.ERROR_INVALID_ARGUMENTS and error[T.KEY_RETRYABLE] is False
    assert T.KEY_NUMBER in json.dumps(error[T.KEY_DETAILS])
    assert fake.requests == []


async def test_whitespace_title_is_rejected_by_schema(fake, server_env):
    """Do not approve an empty-looking issue in a dry run.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    result = await call(
        T.TOOL_CREATE_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_TITLE: T.WHITESPACE_TITLE}
    )
    assert result.is_error and fake.requests == []


async def test_secondary_rate_limit_without_headers_is_retryable(fake, server_env):
    """Recognize GitHub's secondary-limit message even without rate headers.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    fake.route(
        T.HTTP_GET,
        T.SEARCH_ISSUES_PATH,
        {T.KEY_MESSAGE: T.SECONDARY_LIMIT_FULL_MESSAGE},
        HTTPStatus.FORBIDDEN,
    )
    error = error_of(await call(T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: T.REPO_NAME}))
    assert (
        error[T.KEY_ERROR] == T.ERROR_RATE_LIMITED
        and error[T.KEY_RETRY_AFTER_SECONDS] >= T.FALLBACK_RETRY_WAIT
    )


async def test_retry_after_http_date_uses_actual_delay(fake, server_env, monkeypatch):
    """Honor an HTTP-date delay instead of always substituting one minute.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        monkeypatch: Freezes the clock used for rate-limit calculations.
    """
    now = int(time.time())
    monkeypatch.setattr(github.time, "time", lambda: now)
    fake.route(
        T.HTTP_GET,
        T.SEARCH_ISSUES_PATH,
        {T.KEY_MESSAGE: T.THROTTLE_MESSAGE},
        HTTPStatus.TOO_MANY_REQUESTS,
        {T.HEADER_RETRY_AFTER: formatdate(now + T.DATE_RETRY_WAIT, usegmt=True)},
    )
    error = error_of(await call(T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: T.REPO_NAME}))
    assert error[T.KEY_RETRY_AFTER_SECONDS] == T.DATE_RETRY_WAIT


def test_token_save_does_not_reuse_an_insecure_temporary_file(tmp_path):
    """Keep the final cache private when an old temporary file has broad permissions.

    Args:
        tmp_path: Isolated cache directory.
    """
    stale = tmp_path / T.STALE_TOKEN_FILENAME
    stale.write_text(T.STALE_CACHE_CONTENT)
    stale.chmod(T.PUBLIC_FILE_MODE)
    path = tmp_path / T.TOKEN_FILENAME
    TokenStore(path).save(
        Token(
            T.STORED_ACCESS_TOKEN,
            T.STORED_ACCESS_EXPIRY,
            T.STORED_REFRESH_TOKEN,
            T.STORED_REFRESH_EXPIRY,
        )
    )
    assert path.stat().st_mode & T.FILE_MODE_MASK == T.PRIVATE_FILE_MODE


async def test_search_reports_partial_results(fake, server_env):
    """Do not present an incomplete upstream search as a definitive empty result.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    fake.route(
        T.HTTP_GET,
        T.SEARCH_ISSUES_PATH,
        {T.KEY_TOTAL_COUNT: 0, T.KEY_ITEMS: [], T.KEY_INCOMPLETE_RESULTS: True},
    )
    result = (await call(T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: T.REPO_NAME})).structured_content
    assert result[T.KEY_INCOMPLETE_RESULTS] is True
    assert T.INCOMPLETE_NOTE in result[T.KEY_NOTE].lower()


async def test_search_text_cannot_change_repository_scope(fake, server_env):
    """Keep qualifier-looking text inside the phrase being searched.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    await call(T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: T.REPO_NAME, T.KEY_QUERY: T.SCOPE_QUERY})
    query = fake.calls(T.HTTP_GET, T.SEARCH_ISSUES_PATH)[0][T.KEY_QUERY][T.KEY_Q]
    assert query == T.EXPECTED_SCOPE_QUERY


@pytest.mark.parametrize(
    "arguments",
    [
        {T.KEY_QUERY: T.QUOTED_SCOPE_QUERY},
        {T.KEY_LABELS: [T.QUOTED_SCOPE_LABEL]},
    ],
)
async def test_search_rejects_ambiguous_quoted_text(fake, server_env, arguments):
    """Reject text that could end a search phrase and introduce new qualifiers.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        arguments: A query or label containing an embedded quote.
    """
    error = error_of(await call(T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: T.REPO_NAME, **arguments}))
    assert error[T.KEY_ERROR] == T.ERROR_INVALID_ARGUMENTS and fake.requests == []


async def test_preview_warns_when_duplicate_search_is_incomplete(fake, server_env):
    """Make an incomplete duplicate check visible before the user approves a write.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    fake.route(
        T.HTTP_GET,
        T.SEARCH_ISSUES_PATH,
        {T.KEY_TOTAL_COUNT: 0, T.KEY_ITEMS: [], T.KEY_INCOMPLETE_RESULTS: True},
    )
    data = (
        await call(T.TOOL_CREATE_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_TITLE: T.BUG_TITLE})
    ).structured_content
    assert any(T.INCOMPLETE_NOTE in warning.lower() for warning in data[T.KEY_WARNINGS])
    assert fake.calls(T.HTTP_POST, T.ISSUES_PATH) == []


@pytest.mark.parametrize(
    "status,code,retryable,wait",
    [
        (HTTPStatus.UNAUTHORIZED, T.ERROR_AUTH_REQUIRED, False, None),
        (HTTPStatus.TOO_MANY_REQUESTS, T.ERROR_RATE_LIMITED, True, T.RATE_LIMIT_WAIT),
        (HTTPStatus.SERVICE_UNAVAILABLE, T.ERROR_UPSTREAM_ERROR, True, T.TRANSIENT_RETRY_WAIT),
    ],
)
async def test_duplicate_check_failure_preserves_recovery(
    fake, server_env, status, code, retryable, wait
):
    """Return recovery instructions when a preview's duplicate lookup fails.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        status: Duplicate-search HTTP failure.
        code: Expected structured error code.
        retryable: Whether the unchanged call can be retried.
        wait: Expected retry delay, if any.
    """
    fake.route(
        T.HTTP_GET,
        T.SEARCH_ISSUES_PATH,
        {T.KEY_MESSAGE: T.LOOKUP_FAILED_MESSAGE},
        status,
        {T.HEADER_RETRY_AFTER: str(T.RATE_LIMIT_WAIT)}
        if status == HTTPStatus.TOO_MANY_REQUESTS
        else {},
    )
    error = error_of(
        await call(T.TOOL_CREATE_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_TITLE: T.BUG_TITLE})
    )
    assert error[T.KEY_ERROR] == code and error[T.KEY_RETRYABLE] is retryable
    if wait is None:
        assert T.LOGIN_HINT in error[T.KEY_HINT]
    else:
        assert error[T.KEY_RETRY_AFTER_SECONDS] == wait and error[T.KEY_HINT]
    assert fake.calls(T.HTTP_POST, T.ISSUES_PATH) == []


async def test_redirected_issue_uses_destination_repo_and_comments(fake, server_env):
    """Read a transferred issue and chain its current repository and number.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    destination = T.RENAMED_ISSUE_PATH
    fake.route(
        T.HTTP_GET,
        T.ISSUE_PATH,
        {T.KEY_MESSAGE: T.MOVED_PERMANENTLY_MESSAGE},
        HTTPStatus.MOVED_PERMANENTLY,
        {T.KEY_LOCATION: destination},
    )
    fake.route(
        T.HTTP_GET,
        destination,
        issue(
            T.TRANSFERRED_ISSUE_NUMBER,
            T.TRANSFERRED_TITLE,
            repository_url=f"{fake.url}{T.RENAMED_REPO_PATH}",
            comments=1,
            html_url=T.RENAMED_ISSUE_URL,
        ),
    )
    fake.route(
        T.HTTP_GET,
        destination + T.COMMENTS_SUFFIX,
        [
            {
                T.KEY_USER: {T.KEY_LOGIN: T.OWNER},
                T.KEY_CREATED_AT: T.TRANSFERRED_COMMENT_AT,
                T.KEY_BODY: T.TRANSFERRED_COMMENT,
            }
        ],
    )
    result = await call(T.TOOL_GET_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_NUMBER: T.ISSUE_NUMBER})
    assert not result.is_error
    data = result.structured_content
    assert (data[T.KEY_REPO], data[T.KEY_NUMBER]) == (
        T.RENAMED_REPO_NAME,
        T.TRANSFERRED_ISSUE_NUMBER,
    )
    assert data[T.KEY_RECENT_COMMENTS][0][T.KEY_BODY] == T.TRANSFERRED_COMMENT
    assert len(fake.calls(T.HTTP_GET, destination)) == 1


async def test_redirected_write_is_not_replayed(fake, server_env):
    """Return a destination check instead of silently replaying an issue POST.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    destination = T.RENAMED_ISSUES_PATH
    fake.route(
        T.HTTP_POST,
        T.ISSUES_PATH,
        {T.KEY_MESSAGE: T.MOVED_MESSAGE},
        HTTPStatus.TEMPORARY_REDIRECT,
        {T.KEY_LOCATION: destination},
    )
    error = error_of(
        await call(
            T.TOOL_CREATE_ISSUE,
            {
                T.KEY_REPO: T.REPO_NAME,
                T.KEY_TITLE: T.BUG_TITLE,
                T.KEY_DRY_RUN: False,
            },
        )
    )
    assert error[T.KEY_ERROR] == T.ERROR_REDIRECT_REQUIRED and error[T.KEY_RETRYABLE] is False
    assert T.TOOL_LIST_REPOS in error[T.KEY_HINT]
    assert len(fake.calls(T.HTTP_POST, T.ISSUES_PATH)) == 1
    assert fake.calls(T.HTTP_POST, destination) == []


@pytest.mark.parametrize("provider_error", [T.OAUTH_BAD_CREDENTIALS, T.OAUTH_INVALID_CLIENT])
async def test_rejected_client_credentials_need_configuration(
    fake, server_env, tmp_path, provider_error
):
    """Tell the user to repair app credentials before retrying authorization.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        tmp_path: Token-cache directory.
        provider_error: Rejected-client error from the token endpoint.
    """
    token_file = tmp_path / T.TOKEN_FILENAME
    write_token(token_file, expires_in=T.JUST_EXPIRED_SECONDS)
    before = token_file.read_bytes()
    fake.route(T.HTTP_POST, T.TOKEN_PATH, {T.KEY_ERROR: provider_error})
    error = error_of(await call(T.TOOL_LIST_REPOS, {}))
    assert error[T.KEY_ERROR] == T.ERROR_NOT_CONFIGURED and error[T.KEY_RETRYABLE] is False
    assert T.GITHUB_CLIENT_SECRET in error[T.KEY_HINT] and T.RESTART_HINT in error[T.KEY_HINT]
    assert token_file.read_bytes() == before
    assert fake.calls(T.HTTP_GET, T.INSTALLATIONS_PATH) == []


@pytest.mark.parametrize(
    "tool,arguments",
    [
        (T.TOOL_LIST_REPOS, {T.KEY_LIMIT: 1.0}),
        (T.TOOL_SEARCH_ISSUES, {T.KEY_REPO: T.REPO_NAME, T.KEY_LIMIT: 1.0}),
        (
            T.TOOL_GET_ISSUE,
            {T.KEY_REPO: T.REPO_NAME, T.KEY_NUMBER: float(T.ISSUE_NUMBER), T.KEY_MAX_COMMENTS: 0.0},
        ),
    ],
)
async def test_schema_integer_representations_work(fake, server_env, tool, arguments):
    """Accept integral JSON numbers wherever the advertised schema allows them.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        tool: Tool with integer parameters.
        arguments: Valid arguments using integral decimal numbers.
    """
    async with Client(mcp) as client:
        schemas = {item.name: item.input_schema for item in await client.list_tools()}
        Draft202012Validator(schemas[tool]).validate(arguments)
        result = await client.call_tool(tool, arguments, raise_on_error=False)
    assert not result.is_error
    if tool == T.TOOL_LIST_REPOS:
        assert len(result.structured_content[T.KEY_REPOS]) == 1
    elif tool == T.TOOL_SEARCH_ISSUES:
        assert fake.calls(T.HTTP_GET, T.SEARCH_ISSUES_PATH)[0][T.KEY_QUERY][T.KEY_PER_PAGE] == str(
            1
        )
    else:
        assert result.structured_content[T.KEY_NUMBER] == T.ISSUE_NUMBER
        assert result.structured_content[T.KEY_RECENT_COMMENTS] == []


@pytest.mark.parametrize(
    "tool,arguments",
    [
        (T.TOOL_GET_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_NUMBER: str(T.ISSUE_NUMBER)}),
        (T.TOOL_GET_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_NUMBER: True}),
        (T.TOOL_GET_ISSUE, {T.KEY_REPO: T.REPO_NAME, T.KEY_NUMBER: T.NONINTEGER_ISSUE_NUMBER}),
        (T.TOOL_LIST_REPOS, {T.KEY_LIMIT: T.REPO_LIMIT_OVERFLOW}),
        (
            T.TOOL_CREATE_ISSUE,
            {T.KEY_REPO: T.REPO_NAME, T.KEY_TITLE: T.BUG_TITLE, T.KEY_DRY_RUN: T.SERIALIZED_FALSE},
        ),
        (
            T.TOOL_CREATE_ISSUE,
            {T.KEY_REPO: T.REPO_NAME, T.KEY_TITLE: T.BUG_TITLE, T.KEY_DRY_RUN: 0},
        ),
    ],
)
async def test_schema_integer_normalization_keeps_strict_validation(
    fake, server_env, tool, arguments
):
    """Keep type and bound failures from reaching GitHub after normalizing integers.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        tool: Tool receiving invalid arguments.
        arguments: Inputs that must not be coerced or accepted.
    """
    error = error_of(await call(tool, arguments))
    assert error[T.KEY_ERROR] == T.ERROR_INVALID_ARGUMENTS
    assert fake.requests == []


@pytest.mark.parametrize("field", [T.KEY_QUERY, T.KEY_LABELS])
@pytest.mark.parametrize("control", T.CONTROL_CHARACTERS)
async def test_search_control_characters_are_rejected_by_schema(fake, server_env, field, control):
    """Reject DEL and C1 controls in both the published schema and tool dispatch.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        field: Search field receiving the control character.
        control: Forbidden control character.
    """
    value = T.BUG_LABEL + control
    arguments = {T.KEY_REPO: T.REPO_NAME, field: [value] if field == T.KEY_LABELS else value}
    async with Client(mcp) as client:
        schema = next(
            item.input_schema
            for item in await client.list_tools()
            if item.name == T.TOOL_SEARCH_ISSUES
        )
        assert not Draft202012Validator(schema).is_valid(arguments)
        result = await client.call_tool(T.TOOL_SEARCH_ISSUES, arguments, raise_on_error=False)
    assert error_of(result)[T.KEY_ERROR] == T.ERROR_INVALID_ARGUMENTS
    assert fake.requests == []


@pytest.mark.parametrize(
    "corruption",
    [
        {T.KEY_EXPIRES_AT: T.CORRUPT_EXPIRY},
        {T.KEY_REFRESH_EXPIRES_AT: None},
        {T.KEY_EXPIRES_AT: True},
        {T.KEY_EXPIRES_AT: float("inf")},
        {T.KEY_REFRESH_EXPIRES_AT: float("nan")},
        {T.KEY_ACCESS_TOKEN: ""},
        {T.KEY_REFRESH_TOKEN: T.CORRUPT_REFRESH_TOKEN},
    ],
)
async def test_corrupt_token_cache_requests_login(fake, server_env, tmp_path, corruption):
    """Use the login recovery path for invalid cache types and nonfinite expiries.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        tmp_path: Token-cache directory.
        corruption: Invalid fields to write into the cache.
    """
    token_file = tmp_path / T.TOKEN_FILENAME
    data = json.loads(token_file.read_text())
    token_file.write_text(json.dumps({**data, **corruption}))
    before = token_file.read_bytes()
    error = error_of(await call(T.TOOL_LIST_REPOS, {}))
    assert error[T.KEY_ERROR] == T.ERROR_AUTH_REQUIRED and error[T.KEY_RETRYABLE] is False
    assert T.LOGIN_HINT in error[T.KEY_HINT]
    assert fake.requests == []
    assert token_file.read_bytes() == before
