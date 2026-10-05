"""Regression checks for the local pre-submission review; no real GitHub calls."""

from __future__ import annotations

from email.utils import formatdate
import json
import time

import httpx
import pytest
from conftest import REPO, issue, write_token
from fastmcp import Client
from jsonschema import Draft202012Validator
from test_tools import call, error_of

import github
from oauth import Token, TokenStore
from server import mcp


@pytest.mark.parametrize("failure", ["timeout", "server_error"])
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
        if method == "POST" and str(url).endswith("/issues"):
            sent.append(response.status_code)
            raise httpx.ReadTimeout("response lost")
        return response

    if failure == "timeout":
        monkeypatch.setattr(httpx.AsyncClient, "request", lose_response)
    else:
        fake.route("POST", "/repos/alice/demo/issues", {"message": "response lost"}, 502)
    error = error_of(await call("create_issue", {"repo": "alice/demo", "title": "New bug", "dry_run": False}))
    assert len(fake.calls("POST", "/repos/alice/demo/issues")) == 1
    assert error["error"] == "write_outcome_unknown"
    assert error["retryable"] is False and "search_issues" in error["hint"]
    if failure == "timeout":
        assert sent == [201]


@pytest.mark.parametrize("status,body", [
    (429, {"message": "too many requests"}),
    (200, ["invalid token response"]),
    (200, {}),
])
async def test_temporary_oauth_failure_does_not_request_login(fake, server_env, tmp_path, status, body):
    """Keep a valid refresh token when its endpoint is temporarily unavailable.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        tmp_path: Token-cache directory.
        status: Token-endpoint HTTP status.
        body: Token-endpoint JSON response.
    """
    write_token(tmp_path / "token.json", expires_in=-1)
    before = (tmp_path / "token.json").read_bytes()
    fake.route("POST", "/login/oauth/access_token", body, status, {"retry-after": "42"})
    error = error_of(await call("list_repos", {}))
    assert error["retryable"] is True and error["error"] != "auth_required"
    assert (tmp_path / "token.json").read_bytes() == before
    if status == 429:
        assert error["retry_after_seconds"] == 42


async def test_labels_beyond_first_page_are_valid(fake, server_env):
    """Accept a label from page two without creating an issue during preview.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    pages = [[{"name": f"label-{n}"} for n in range(100)], [{"name": "last-label"}]]
    fake.routes[("GET", "/repos/alice/demo/labels")] = lambda req: (
        200, pages[int(req["query"].get("page", "1")) - 1], {}
    )
    result = await call("create_issue", {"repo": "alice/demo", "title": "Bug", "labels": ["last-label"]})
    assert not result.is_error
    assert result.structured_content["created"] is False
    assert len(fake.calls("GET", "/repos/alice/demo/labels")) == 2
    assert fake.calls("POST", "/repos/alice/demo/issues") == []


async def test_repo_pagination_does_not_silently_stop_at_500(fake, server_env):
    """Include a recently pushed repository after the fifth API page.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    repos = [{**REPO, "full_name": f"alice/repo-{i}", "pushed_at": "2020-01-01T00:00:00Z"} for i in range(500)]
    repos.append({**REPO, "full_name": "alice/newest"})
    fake.routes[("GET", "/user/installations/1/repositories")] = lambda req: (
        200, {"repositories": repos[(int(req["query"].get("page", "1")) - 1) * 100:int(req["query"].get("page", "1")) * 100]}, {}
    )
    result = (await call("list_repos", {"limit": 1})).structured_content
    assert result["total_accessible"] == 501
    assert result["repos"][0]["full_name"] == "alice/newest"
    assert "501" in result["note"] and "limit" in result["note"]


async def test_schema_errors_use_the_structured_contract(fake, server_env):
    """Reject invalid input before HTTP with an actionable JSON tool error.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    error = error_of(await call("get_issue", {"repo": "alice/demo", "number": 0}))
    assert error["error"] == "invalid_arguments" and error["retryable"] is False
    assert "number" in json.dumps(error["details"])
    assert fake.requests == []


async def test_whitespace_title_is_rejected_by_schema(fake, server_env):
    """Do not approve an empty-looking issue in a dry run.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    result = await call("create_issue", {"repo": "alice/demo", "title": "  "})
    assert result.is_error and fake.requests == []


async def test_secondary_rate_limit_without_headers_is_retryable(fake, server_env):
    """Recognize GitHub's secondary-limit message even without rate headers.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    fake.route("GET", "/search/issues", {"message": "You have exceeded a secondary rate limit."}, 403)
    error = error_of(await call("search_issues", {"repo": "alice/demo"}))
    assert error["error"] == "rate_limited" and error["retry_after_seconds"] >= 60


async def test_retry_after_http_date_uses_actual_delay(fake, server_env, monkeypatch):
    """Honor an HTTP-date delay instead of always substituting one minute.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        monkeypatch: Freezes the clock used for rate-limit calculations.
    """
    now = int(time.time())
    monkeypatch.setattr(github.time, "time", lambda: now)
    fake.route("GET", "/search/issues", {"message": "slow down"}, 429, {"retry-after": formatdate(now + 120, usegmt=True)})
    error = error_of(await call("search_issues", {"repo": "alice/demo"}))
    assert error["retry_after_seconds"] == 120


def test_token_save_does_not_reuse_an_insecure_temporary_file(tmp_path):
    """Keep the final cache private when an old temporary file has broad permissions.

    Args:
        tmp_path: Isolated cache directory.
    """
    stale = tmp_path / "token.tmp"
    stale.write_text("stale")
    stale.chmod(0o644)
    path = tmp_path / "token.json"
    TokenStore(path).save(Token("test-access", 123, "test-refresh", 456))
    assert path.stat().st_mode & 0o777 == 0o600


async def test_search_reports_partial_results(fake, server_env):
    """Do not present an incomplete upstream search as a definitive empty result.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    fake.route("GET", "/search/issues", {"total_count": 0, "items": [], "incomplete_results": True})
    result = (await call("search_issues", {"repo": "alice/demo"})).structured_content
    assert result["incomplete_results"] is True
    assert "incomplete" in result["note"].lower()


async def test_search_text_cannot_change_repository_scope(fake, server_env):
    """Keep qualifier-looking text inside the phrase being searched.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    await call("search_issues", {"repo": "alice/demo", "query": "crash OR repo:bob/other"})
    query = fake.calls("GET", "/search/issues")[0]["query"]["q"]
    assert query == 'repo:alice/demo is:issue in:title,body state:open "crash OR repo:bob/other"'


@pytest.mark.parametrize("arguments", [
    {"query": 'crash" OR repo:bob/other'},
    {"labels": ['bug" OR repo:bob/other']},
])
async def test_search_rejects_ambiguous_quoted_text(fake, server_env, arguments):
    """Reject text that could end a search phrase and introduce new qualifiers.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        arguments: A query or label containing an embedded quote.
    """
    error = error_of(await call("search_issues", {"repo": "alice/demo", **arguments}))
    assert error["error"] == "invalid_arguments" and fake.requests == []


async def test_preview_warns_when_duplicate_search_is_incomplete(fake, server_env):
    """Make an incomplete duplicate check visible before the user approves a write.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    fake.route("GET", "/search/issues", {"total_count": 0, "items": [], "incomplete_results": True})
    data = (await call("create_issue", {"repo": "alice/demo", "title": "Bug"})).structured_content
    assert any("incomplete" in warning.lower() for warning in data["warnings"])
    assert fake.calls("POST", "/repos/alice/demo/issues") == []


@pytest.mark.parametrize("status,code,retryable,wait", [
    (401, "auth_required", False, None),
    (429, "rate_limited", True, 42),
    (503, "upstream_error", True, 5),
])
async def test_duplicate_check_failure_preserves_recovery(fake, server_env, status, code, retryable, wait):
    """Return recovery instructions when a preview's duplicate lookup fails.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        status: Duplicate-search HTTP failure.
        code: Expected structured error code.
        retryable: Whether the unchanged call can be retried.
        wait: Expected retry delay, if any.
    """
    fake.route("GET", "/search/issues", {"message": "lookup failed"}, status,
               {"retry-after": "42"} if status == 429 else {})
    error = error_of(await call("create_issue", {"repo": "alice/demo", "title": "Bug"}))
    assert error["error"] == code and error["retryable"] is retryable
    if wait is None:
        assert "login.py" in error["hint"]
    else:
        assert error["retry_after_seconds"] == wait and error["hint"]
    assert fake.calls("POST", "/repos/alice/demo/issues") == []


async def test_redirected_issue_uses_destination_repo_and_comments(fake, server_env):
    """Read a transferred issue and chain its current repository and number.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    destination = "/repos/alice/renamed/issues/9"
    fake.route("GET", "/repos/alice/demo/issues/7", {"message": "Moved Permanently"},
               301, {"location": destination})
    fake.route("GET", destination, issue(
        9, "Transferred issue", repository_url=f"{fake.url}/repos/alice/renamed", comments=1,
        html_url="https://github.com/alice/renamed/issues/9",
    ))
    fake.route("GET", destination + "/comments", [{
        "user": {"login": "alice"}, "created_at": "2026-10-04T12:00:00Z", "body": "Moved too",
    }])
    result = await call("get_issue", {"repo": "alice/demo", "number": 7})
    assert not result.is_error
    data = result.structured_content
    assert (data["repo"], data["number"]) == ("alice/renamed", 9)
    assert data["recent_comments"][0]["body"] == "Moved too"
    assert len(fake.calls("GET", destination)) == 1


async def test_redirected_write_is_not_replayed(fake, server_env):
    """Return a destination check instead of silently replaying an issue POST.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
    """
    destination = "/repos/alice/renamed/issues"
    fake.route("POST", "/repos/alice/demo/issues", {"message": "Moved"},
               307, {"location": destination})
    error = error_of(await call("create_issue", {
        "repo": "alice/demo", "title": "Bug", "dry_run": False,
    }))
    assert error["error"] == "redirect_required" and error["retryable"] is False
    assert "list_repos" in error["hint"]
    assert len(fake.calls("POST", "/repos/alice/demo/issues")) == 1
    assert fake.calls("POST", destination) == []


@pytest.mark.parametrize("provider_error", ["incorrect_client_credentials", "invalid_client"])
async def test_rejected_client_credentials_need_configuration(fake, server_env, tmp_path, provider_error):
    """Tell the user to repair app credentials before retrying authorization.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        tmp_path: Token-cache directory.
        provider_error: Rejected-client error from the token endpoint.
    """
    token_file = tmp_path / "token.json"
    write_token(token_file, expires_in=-1)
    before = token_file.read_bytes()
    fake.route("POST", "/login/oauth/access_token", {"error": provider_error})
    error = error_of(await call("list_repos", {}))
    assert error["error"] == "not_configured" and error["retryable"] is False
    assert "GITHUB_CLIENT_SECRET" in error["hint"] and "restart" in error["hint"]
    assert token_file.read_bytes() == before
    assert fake.calls("GET", "/user/installations") == []


@pytest.mark.parametrize("tool,arguments", [
    ("list_repos", {"limit": 1.0}),
    ("search_issues", {"repo": "alice/demo", "limit": 1.0}),
    ("get_issue", {"repo": "alice/demo", "number": 7.0, "max_comments": 0.0}),
])
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
    if tool == "list_repos":
        assert len(result.structured_content["repos"]) == 1
    elif tool == "search_issues":
        assert fake.calls("GET", "/search/issues")[0]["query"]["per_page"] == "1"
    else:
        assert result.structured_content["number"] == 7
        assert result.structured_content["recent_comments"] == []


@pytest.mark.parametrize("tool,arguments", [
    ("get_issue", {"repo": "alice/demo", "number": "7"}),
    ("get_issue", {"repo": "alice/demo", "number": True}),
    ("get_issue", {"repo": "alice/demo", "number": 7.5}),
    ("list_repos", {"limit": 101.0}),
    ("create_issue", {"repo": "alice/demo", "title": "Bug", "dry_run": "false"}),
    ("create_issue", {"repo": "alice/demo", "title": "Bug", "dry_run": 0}),
])
async def test_schema_integer_normalization_keeps_strict_validation(fake, server_env, tool, arguments):
    """Keep type and bound failures from reaching GitHub after normalizing integers.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        tool: Tool receiving invalid arguments.
        arguments: Inputs that must not be coerced or accepted.
    """
    error = error_of(await call(tool, arguments))
    assert error["error"] == "invalid_arguments"
    assert fake.requests == []


@pytest.mark.parametrize("field", ["query", "labels"])
@pytest.mark.parametrize("control", ["\x7f", "\x85", "\x9f"])
async def test_search_control_characters_are_rejected_by_schema(fake, server_env, field, control):
    """Reject DEL and C1 controls in both the published schema and tool dispatch.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        field: Search field receiving the control character.
        control: Forbidden control character.
    """
    value = "bug" + control
    arguments = {"repo": "alice/demo", field: [value] if field == "labels" else value}
    async with Client(mcp) as client:
        schema = next(item.input_schema for item in await client.list_tools() if item.name == "search_issues")
        assert not Draft202012Validator(schema).is_valid(arguments)
        result = await client.call_tool("search_issues", arguments, raise_on_error=False)
    assert error_of(result)["error"] == "invalid_arguments"
    assert fake.requests == []


@pytest.mark.parametrize("corruption", [
    {"expires_at": "bad"}, {"refresh_expires_at": None}, {"expires_at": True},
    {"expires_at": float("inf")}, {"refresh_expires_at": float("nan")},
    {"access_token": ""}, {"refresh_token": 123},
])
async def test_corrupt_token_cache_requests_login(fake, server_env, tmp_path, corruption):
    """Use the login recovery path for invalid cache types and nonfinite expiries.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and API URLs.
        tmp_path: Token-cache directory.
        corruption: Invalid fields to write into the cache.
    """
    token_file = tmp_path / "token.json"
    data = json.loads(token_file.read_text())
    token_file.write_text(json.dumps({**data, **corruption}))
    before = token_file.read_bytes()
    error = error_of(await call("list_repos", {}))
    assert error["error"] == "auth_required" and error["retryable"] is False
    assert "login.py" in error["hint"]
    assert fake.requests == []
    assert token_file.read_bytes() == before
