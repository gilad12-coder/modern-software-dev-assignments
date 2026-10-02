"""Tool behavior through an in-process MCP client (real protocol messages, no subprocess)."""

from __future__ import annotations

import asyncio
import json
import time

import pytest
from conftest import issue, write_token
from fastmcp import Client

from server import mcp


async def call(name: str, args: dict):
    async with Client(mcp) as client:
        return await client.call_tool(name, args, raise_on_error=False)


def error_of(result) -> dict:
    assert result.is_error, result
    return json.loads(result.content[0].text)


async def test_list_repos_sorts_and_shapes(fake, server_env):
    result = await call("list_repos", {"limit": 5})
    data = result.structured_content
    assert [r["full_name"] for r in data["repos"]] == ["alice/demo", "alice/old"]
    assert set(data["repos"][0]) == {
        "full_name", "description", "private", "has_issues", "open_issues_and_prs", "pushed_at"
    }


async def test_list_repos_empty_is_explicit(fake, server_env):
    fake.route("GET", "/user/installations", {"installations": []})
    data = (await call("list_repos", {})).structured_content
    assert data["repos"] == [] and data["note"].startswith("0 repositories")


async def test_search_builds_query_and_drops_raw_fields(fake, server_env):
    result = await call(
        "search_issues",
        {"repo": "alice/demo", "query": "crash", "labels": ["good first issue"], "state": "all"},
    )
    q = fake.calls("GET", "/search/issues")[0]["query"]["q"]
    assert q == 'repo:alice/demo is:issue label:"good first issue" crash'
    item = result.structured_content["items"][0]
    assert item["number"] == 7 and item["repo"] == "alice/demo" and item["labels"] == ["bug"]
    assert "body" not in item and "reactions" not in item and "node_id" not in item


async def test_empty_search_points_at_list_repos(fake, server_env):
    fake.route("GET", "/search/issues", {"total_count": 0, "items": []})
    data = (await call("search_issues", {"repo": "alice/demo"})).structured_content
    assert data["items"] == [] and "call list_repos" in data["note"]


async def test_get_issue_returns_newest_comments(fake, server_env):
    fake.route("GET", "/repos/alice/demo/issues/7", issue(7, "Crash", comments=3, body="x" * 5000))
    fake.route(
        "GET",
        "/repos/alice/demo/issues/7/comments",
        [
            {"user": {"login": f"u{i}"}, "created_at": f"2026-09-0{i}T00:00:00Z", "body": f"c{i}"}
            for i in (1, 2, 3)
        ],
    )
    data = (await call("get_issue", {"repo": "alice/demo", "number": 7, "max_comments": 2}))
    data = data.structured_content
    assert [c["body"] for c in data["recent_comments"]] == ["c2", "c3"]
    assert data["comments_omitted"] == 1
    assert data["body_truncated"] and len(data["body"]) == 4001


async def test_unknown_issue_is_not_retryable_and_points_at_search(fake, server_env):
    err = error_of(await call("get_issue", {"repo": "alice/demo", "number": 999}))
    assert err["error"] == "not_found" and err["retryable"] is False
    assert "search_issues" in err["hint"]


async def test_search_unknown_repo_maps_422_to_not_found(fake, server_env):
    fake.route(
        "GET",
        "/search/issues",
        {"message": "Validation Failed", "errors": [{"message": "The listed users and "
         "repositories cannot be searched either because the resources do not exist"}]},
        status=422,
    )
    err = error_of(await call("search_issues", {"repo": "alice/nope"}))
    assert err["error"] == "not_found" and "list_repos" in err["hint"]


async def test_rate_limit_is_retryable_with_wait(fake, server_env):
    reset = int(time.time()) + 42
    fake.route(
        "GET",
        "/search/issues",
        {"message": "API rate limit exceeded"},
        status=403,
        headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(reset)},
    )
    err = error_of(await call("search_issues", {"repo": "alice/demo"}))
    assert err["error"] == "rate_limited" and err["retryable"] is True
    assert 40 <= err["retry_after_seconds"] <= 42


async def test_forbidden_is_not_retryable(fake, server_env):
    fake.route("GET", "/repos/alice/demo/issues/7", {"message": "Resource not accessible"}, 403)
    err = error_of(await call("get_issue", {"repo": "alice/demo", "number": 7}))
    assert err["error"] == "forbidden" and err["retryable"] is False


async def test_server_error_is_retryable(fake, server_env):
    fake.route("GET", "/repos/alice/demo/issues/7", {"message": "boom"}, 502)
    err = error_of(await call("get_issue", {"repo": "alice/demo", "number": 7}))
    assert err["error"] == "upstream_error" and err["retryable"] is True


async def test_network_down_is_retryable(fake, server_env, monkeypatch):
    monkeypatch.setenv("GITHUB_API_URL", "http://127.0.0.1:9")
    err = error_of(await call("list_repos", {}))
    assert err["error"] == "network_error" and err["retryable"] is True


async def test_schema_rejects_bad_arguments_before_any_request(fake, server_env):
    for name, args in [
        ("search_issues", {"repo": "https://github.com/alice/demo"}),
        ("search_issues", {"repo": "alice/demo", "state": "opened"}),
        ("get_issue", {"repo": "alice/demo", "number": 0}),
        ("create_issue", {"repo": "alice/demo", "title": ""}),
    ]:
        assert (await call(name, args)).is_error
    assert fake.requests == []


async def test_create_issue_dry_run_writes_nothing_and_flags_duplicates(fake, server_env):
    data = (await call("create_issue", {"repo": "alice/demo", "title": "Crash", "labels": ["bug"]}))
    data = data.structured_content
    assert data["dry_run"] and not data["created"] and data["issue"] is None
    assert any("Possible duplicate: #7" in w for w in data["warnings"])
    assert "dry_run=false" in data["next_step"]
    assert fake.calls("POST", "/repos/alice/demo/issues") == []


async def test_create_issue_commit_posts_once(fake, server_env):
    args = {"repo": "alice/demo", "title": "New bug", "body": "details", "labels": ["bug"]}
    data = (await call("create_issue", {**args, "dry_run": False})).structured_content
    posts = fake.calls("POST", "/repos/alice/demo/issues")
    assert len(posts) == 1 and posts[0]["json"] == {"title": "New bug", "body": "details", "labels": ["bug"]}
    assert data["created"] and data["issue"]["number"] == 42


async def test_create_issue_rejects_unknown_labels_even_on_commit(fake, server_env):
    args = {"repo": "alice/demo", "title": "x", "labels": ["bugg"], "dry_run": False}
    err = error_of(await call("create_issue", args))
    assert err["error"] == "unknown_labels" and "bug" in err["hint"]
    assert fake.calls("POST", "/repos/alice/demo/issues") == []


async def test_create_issue_refuses_repo_with_issues_disabled(fake, server_env):
    fake.route("GET", "/repos/alice/demo", {"full_name": "alice/demo", "has_issues": False})
    err = error_of(await call("create_issue", {"repo": "alice/demo", "title": "x"}))
    assert err["error"] == "issues_disabled"


# ---------- OAuth: caching, silent refresh, mid-session death ----------


async def test_cached_token_is_reused_without_refresh(fake, server_env):
    await call("list_repos", {})
    await call("list_repos", {})
    assert fake.refresh_calls == 0


async def test_expired_token_is_refreshed_silently_and_rotated(fake, server_env, tmp_path):
    write_token(tmp_path / "token.json", expires_in=-10)
    fake.valid_tokens = {"some-token-the-server-does-not-have"}
    result = await call("list_repos", {})
    assert not result.is_error
    assert fake.refresh_calls == 1
    cached = json.loads((tmp_path / "token.json").read_text())
    assert cached["access_token"] == "ghu_new1" and cached["refresh_token"] == "ghr_new1"
    assert oct((tmp_path / "token.json").stat().st_mode)[-3:] == "600"


async def test_401_mid_session_refreshes_once_and_retries(fake, server_env):
    fake.valid_tokens = {"revoked-elsewhere"}
    result = await call("get_issue", {"repo": "alice/demo", "number": 7})
    assert not result.is_error and fake.refresh_calls == 1


async def test_dead_refresh_token_returns_auth_required(fake, server_env):
    fake.valid_tokens = set()
    fake.refresh_tokens = set()
    err = error_of(await call("list_repos", {}))
    assert err["error"] == "auth_required" and err["retryable"] is False
    assert "login.py" in err["hint"]


async def test_missing_token_file_returns_auth_required(fake, server_env, tmp_path):
    (tmp_path / "token.json").unlink()
    err = error_of(await call("list_repos", {}))
    assert err["error"] == "auth_required"
    assert fake.requests == []


async def test_missing_client_credentials_is_not_configured(fake, server_env, monkeypatch):
    monkeypatch.delenv("GITHUB_CLIENT_SECRET")
    err = error_of(await call("list_repos", {}))
    assert err["error"] == "not_configured" and err["retryable"] is False


async def test_concurrent_calls_refresh_only_once(fake, server_env, tmp_path):
    # GitHub refresh tokens are single-use: a second refresh with the same one would fail.
    write_token(tmp_path / "token.json", expires_in=-10)
    async with Client(mcp) as client:
        results = await asyncio.gather(
            *[client.call_tool("list_repos", {}, raise_on_error=False) for _ in range(5)]
        )
    assert not any(r.is_error for r in results)
    assert fake.refresh_calls == 1


@pytest.mark.parametrize("retry_after", ["7", "Wed, 21 Oct 2026 07:28:00 GMT"])
async def test_secondary_rate_limit_retry_after(fake, server_env, retry_after):
    fake.route("GET", "/search/issues", {"message": "secondary rate limit"}, 403,
               {"retry-after": retry_after})
    err = error_of(await call("search_issues", {"repo": "alice/demo"}))
    assert err["error"] == "rate_limited" and err["retry_after_seconds"] in (7, 60)
