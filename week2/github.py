"""Thin GitHub REST client that turns every failure into a ToolFailure an agent can act on."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from oauth import (
    LOGIN_COMMAND,
    AuthRequired,
    AuthUnavailable,
    NotConfigured,
    Settings,
    TokenManager,
)


@dataclass
class ToolFailure(Exception):
    """A failure reported to the agent as data. ``retryable`` is the key field."""

    error: str
    message: str
    retryable: bool
    retry_after_seconds: int | None = None
    hint: str | None = None
    details: list[str] = field(default_factory=list)

    def payload(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "error": self.error,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.retry_after_seconds is not None:
            out["retry_after_seconds"] = self.retry_after_seconds
        if self.details:
            out["details"] = self.details
        if self.hint:
            out["hint"] = self.hint
        return out


def auth_failure(reason: str) -> ToolFailure:
    return ToolFailure(
        error="auth_required",
        message=f"GitHub authorization is missing or no longer valid ({reason}).",
        retryable=False,
        hint=(
            f"Do not retry. Ask the user to run `{LOGIN_COMMAND}` in a terminal, "
            "then call the tool again."
        ),
    )


def _rate_limit_wait(resp: httpx.Response) -> int | None:
    """Seconds to wait if this response is a rate limit, else None."""
    if "retry-after" in resp.headers:
        value = resp.headers["retry-after"]
        return int(value) if value.isdigit() else 60
    if resp.headers.get("x-ratelimit-remaining") == "0":
        reset = int(resp.headers.get("x-ratelimit-reset", time.time() + 60))
        return max(1, reset - int(time.time()))
    if resp.status_code == 429:
        return 60
    return None


def _github_messages(resp: httpx.Response) -> tuple[str, list[str]]:
    try:
        body = resp.json()
    except ValueError:
        return resp.text[:200], []
    details = [
        e.get("message") or f"{e.get('field')}: {e.get('code')}"
        for e in body.get("errors", [])
        if isinstance(e, dict)
    ]
    return body.get("message", ""), details


def failure_from_response(resp: httpx.Response) -> ToolFailure:
    message, details = _github_messages(resp)
    status = resp.status_code
    wait = _rate_limit_wait(resp) if status in (403, 429) else None
    if wait is not None:
        return ToolFailure(
            "rate_limited",
            f"GitHub rate limit hit: {message}",
            retryable=True,
            retry_after_seconds=wait,
            hint=f"Wait {wait}s, then retry the same call unchanged.",
        )
    if status == 403:
        return ToolFailure(
            "forbidden",
            f"GitHub refused access: {message}",
            retryable=False,
            hint=(
                "The GitHub App is probably not installed on this repository, or lacks the "
                "permission. Call list_repos to see which repositories this server can use."
            ),
        )
    if status == 404:
        return ToolFailure("not_found", f"GitHub returned 404: {message}", retryable=False)
    if status == 410:
        return ToolFailure("gone", f"GitHub returned 410: {message}", retryable=False)
    if status == 422:
        return ToolFailure(
            "invalid_request",
            f"GitHub rejected the request: {message}",
            retryable=False,
            details=details,
            hint="Fix the arguments using the details above; retrying unchanged will fail again.",
        )
    if status >= 500:
        return ToolFailure(
            "upstream_error",
            f"GitHub returned HTTP {status}.",
            retryable=True,
            retry_after_seconds=5,
            hint="Transient GitHub failure. Retry once after a short wait.",
        )
    return ToolFailure("http_error", f"GitHub returned HTTP {status}: {message}", retryable=False)


class GitHub:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.from_env()
        self.tokens = TokenManager(self.settings)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> httpx.Response:
        try:
            token = await self.tokens.access_token()
            resp = await self._send(method, path, token, params, json)
            if resp.status_code == 401:
                # Revoked or expired early. Refresh once and retry; a second 401 is final.
                token = await self.tokens.access_token(rejected=token)
                resp = await self._send(method, path, token, params, json)
                if resp.status_code == 401:
                    raise auth_failure("GitHub rejected the refreshed token")
        except AuthRequired as exc:
            raise auth_failure(str(exc)) from exc
        except NotConfigured as exc:
            raise ToolFailure(
                "not_configured",
                f"The MCP server is missing its GitHub App credentials ({exc}).",
                retryable=False,
                hint=(
                    "Do not retry. Ask the user to set them in week2/.env or in the env block "
                    "of .mcp.json, then restart the MCP server."
                ),
            ) from exc
        except AuthUnavailable as exc:
            raise ToolFailure(
                "network_error", str(exc), retryable=True, retry_after_seconds=5
            ) from exc
        if resp.status_code >= 400:
            raise failure_from_response(resp)
        return resp

    async def get(self, path: str, **params: Any) -> Any:
        return (await self.request("GET", path, params=params or None)).json()

    async def _send(self, method, path, token, params, json) -> httpx.Response:
        try:
            async with httpx.AsyncClient(base_url=self.settings.api_url, timeout=20) as http:
                return await http.request(
                    method,
                    path,
                    params=params,
                    json=json,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                )
        except httpx.TimeoutException as exc:
            raise ToolFailure(
                "network_error",
                "GitHub did not respond in time.",
                retryable=True,
                retry_after_seconds=5,
            ) from exc
        except httpx.HTTPError as exc:
            raise ToolFailure(
                "network_error",
                f"Could not reach GitHub: {type(exc).__name__}",
                retryable=True,
                retry_after_seconds=5,
            ) from exc
