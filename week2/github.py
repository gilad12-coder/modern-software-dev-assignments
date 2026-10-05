"""Thin GitHub REST client that turns every failure into a ToolFailure an agent can act on."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from math import ceil
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
    """A failure reported to the agent as data. ``retryable`` is the key field.

    Attributes:
        error: Short machine-readable code such as ``not_found`` or ``auth_required``.
        message: Human-readable description of what went wrong.
        retryable: Whether repeating the same call unchanged can succeed.
        retry_after_seconds: How long to wait before retrying, when known.
        hint: The next step the agent should take instead of retrying blindly.
        details: Per-field messages GitHub attached to a 422 response.
    """

    error: str
    message: str
    retryable: bool
    retry_after_seconds: int | None = None
    hint: str | None = None
    details: list[str] = field(default_factory=list)

    def payload(self) -> dict[str, Any]:
        """Build the JSON body sent to the agent as the tool error.

        Returns:
            The failure as a dict, leaving out optional fields that are unset.
        """
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
    """Build the failure that tells the agent a human must log in again.

    Args:
        reason: Why the token is unusable, shown in the message.

    Returns:
        A non-retryable ``auth_required`` failure whose hint names the login command.
    """
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
    """Work out how long to wait if this response is a rate limit.

    Args:
        resp: A 403 or 429 response from GitHub.

    Returns:
        Seconds to wait, or None when the response is not a rate limit.
    """
    if "retry-after" in resp.headers:
        value = resp.headers["retry-after"]
        if value.isdigit():
            return max(1, int(value))
        try:
            return max(1, ceil(parsedate_to_datetime(value).timestamp() - time.time()))
        except (ValueError, TypeError, OverflowError):
            return 60
    if resp.headers.get("x-ratelimit-remaining") == "0":
        reset = int(resp.headers.get("x-ratelimit-reset", time.time() + 60))
        return max(1, reset - int(time.time()))
    if resp.status_code == 429:
        return 60
    if "secondary rate limit" in _github_messages(resp)[0].lower():
        return 60
    return None


def _github_messages(resp: httpx.Response) -> tuple[str, list[str]]:
    """Pull GitHub's error message and per-field details out of a response.

    Args:
        resp: An error response from GitHub.

    Returns:
        The top-level message and a list of detail strings (empty if none).
    """
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
    """Map a GitHub error response to a failure the agent can act on.

    Args:
        resp: A response with status 400 or higher.

    Returns:
        A ToolFailure whose ``error`` and ``retryable`` match the HTTP status.
    """
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


def _unknown_write_outcome() -> ToolFailure:
    """Prevent automatic retries when an issue may already have been created."""
    return ToolFailure(
        "write_outcome_unknown",
        "GitHub may have created the issue, but its confirmation was lost.",
        retryable=False,
        hint=(
            "Do not repeat create_issue. Use search_issues with the same repo and a short "
            "phrase from the title to check for an existing issue; ask the user before any retry."
        ),
    )


class GitHub:
    """Authenticated GitHub REST client used by every tool.

    Attributes:
        settings: API URL and OAuth settings.
        tokens: Hands out a valid access token, refreshing it when needed.
    """

    def __init__(self, settings: Settings | None = None):
        """Create a client.

        Args:
            settings: Settings to use; read from the environment when None.
        """
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
        """Send an authenticated request, refreshing the token once on a 401.

        Args:
            method: HTTP method such as ``GET`` or ``POST``.
            path: API path starting with ``/``.
            params: Query string parameters.
            json: JSON request body.

        Returns:
            The successful (2xx) response.

        Raises:
            ToolFailure: For every failure, including auth, network and HTTP errors.
        """
        try:
            token = await self.tokens.access_token()
            resp = await self._send(method, path, token, params, json)
            if resp.status_code == 401:
                # Revoked or expired early. Refresh once and retry; a second 401 is final.
                token = await self.tokens.access_token(rejected=token)
                resp = await self._send(method, path, token, params, json)
                if resp.status_code == 401:
                    raise auth_failure("GitHub rejected the refreshed token")
        except ToolFailure as failure:
            if method == "POST" and failure.error == "network_error":
                raise _unknown_write_outcome() from failure
            raise
        except AuthRequired as exc:
            raise auth_failure(str(exc)) from exc
        except NotConfigured as exc:
            raise ToolFailure(
                "not_configured",
                f"The GitHub App credentials are missing or invalid ({exc}).",
                retryable=False,
                hint=(
                    "Do not retry. Ask the user to correct GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET "
                    "in week2/.env or the env block of .mcp.json, then restart the MCP server."
                ),
            ) from exc
        except AuthUnavailable as exc:
            raise ToolFailure(
                "network_error", str(exc), retryable=True,
                retry_after_seconds=exc.retry_after_seconds,
                hint=f"Wait {exc.retry_after_seconds}s, then retry. No browser login is needed.",
            ) from exc
        if 300 <= resp.status_code < 400:
            raise ToolFailure(
                "redirect_required", f"GitHub returned HTTP {resp.status_code} instead of the resource.",
                retryable=False,
                hint=(
                    "Call list_repos to find the current repository name. "
                    "For a write, confirm the destination with the user before trying again."
                ),
            )
        if resp.status_code >= 400:
            if method == "POST" and resp.status_code >= 500:
                raise _unknown_write_outcome()
            raise failure_from_response(resp)
        return resp

    async def get(self, path: str, **params: Any) -> Any:
        """Send a GET request and decode the JSON body.

        Args:
            path: API path starting with ``/``.
            **params: Query string parameters.

        Returns:
            The decoded JSON response.

        Raises:
            ToolFailure: For every failure, as in ``request``.
        """
        return (await self.request("GET", path, params=params or None)).json()

    async def _send(self, method, path, token, params, json) -> httpx.Response:
        """Make one HTTP request to GitHub with the given token.

        Args:
            method: HTTP method.
            path: API path starting with ``/``.
            token: OAuth access token for the Authorization header.
            params: Query string parameters, or None.
            json: JSON request body, or None.

        Returns:
            The raw response, whatever its status.

        Raises:
            ToolFailure: When GitHub times out or cannot be reached.
        """
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.api_url, timeout=20, follow_redirects=method in {"GET", "HEAD"},
            ) as http:
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
