"""Thin GitHub REST client that turns every failure into a ToolFailure an agent can act on."""

from __future__ import annotations

import time
from email.utils import parsedate_to_datetime
from http import HTTPStatus
from math import ceil
from typing import Any

import config
import constants as C
import httpx
from models import Settings, ToolFailure
from oauth import (
    AuthRequired,
    AuthUnavailable,
    NotConfigured,
    TokenManager,
)


def auth_failure(reason: str) -> ToolFailure:
    """Build the failure that tells the agent a human must log in again.

    Args:
        reason: Why the token is unusable, shown in the message.

    Returns:
        A non-retryable ``auth_required`` failure whose hint names the login command.
    """
    return ToolFailure(
        error=C.ERROR_AUTH_REQUIRED,
        message=f"GitHub authorization is missing or no longer valid ({reason}).",
        retryable=False,
        hint=(
            f"Do not retry. Ask the user to run `{C.LOGIN_COMMAND}` in a terminal, "
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
    if C.HEADER_RETRY_AFTER in resp.headers:
        value = resp.headers[C.HEADER_RETRY_AFTER]
        if value.isdigit():
            return max(config.MIN_RETRY_SECONDS, int(value))
        try:
            return max(
                config.MIN_RETRY_SECONDS,
                ceil(parsedate_to_datetime(value).timestamp() - time.time()),
            )
        except (ValueError, TypeError, OverflowError):
            return config.RATE_LIMIT_RETRY_SECONDS
    if resp.headers.get(C.HEADER_RATE_REMAINING) == C.RATE_LIMIT_EXHAUSTED:
        reset = int(
            resp.headers.get(C.HEADER_RATE_RESET, time.time() + config.RATE_LIMIT_RETRY_SECONDS)
        )
        return max(config.MIN_RETRY_SECONDS, reset - int(time.time()))
    if resp.status_code == HTTPStatus.TOO_MANY_REQUESTS:
        return config.RATE_LIMIT_RETRY_SECONDS
    if C.SECONDARY_RATE_LIMIT_MARKER in _github_messages(resp)[0].lower():
        return config.RATE_LIMIT_RETRY_SECONDS
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
        return resp.text[: config.ERROR_BODY_LIMIT], []
    details = [
        e.get(C.KEY_MESSAGE) or f"{e.get(C.KEY_FIELD)}: {e.get(C.KEY_CODE)}"
        for e in body.get(C.KEY_ERRORS, [])
        if isinstance(e, dict)
    ]
    return body.get(C.KEY_MESSAGE, ""), details


def failure_from_response(resp: httpx.Response) -> ToolFailure:
    """Map a GitHub error response to a failure the agent can act on.

    Args:
        resp: A response with status 400 or higher.

    Returns:
        A ToolFailure whose ``error`` and ``retryable`` match the HTTP status.
    """
    message, details = _github_messages(resp)
    status = resp.status_code
    wait = (
        _rate_limit_wait(resp)
        if status in (HTTPStatus.FORBIDDEN, HTTPStatus.TOO_MANY_REQUESTS)
        else None
    )
    if wait is not None:
        return ToolFailure(
            C.ERROR_RATE_LIMITED,
            f"GitHub rate limit hit: {message}",
            retryable=True,
            retry_after_seconds=wait,
            hint=f"Wait {wait}s, then retry the same call unchanged.",
        )
    if status == HTTPStatus.FORBIDDEN:
        return ToolFailure(
            C.ERROR_FORBIDDEN,
            f"GitHub refused access: {message}",
            retryable=False,
            hint=(C.FORBIDDEN_HINT),
        )
    if status == HTTPStatus.NOT_FOUND:
        return ToolFailure(C.ERROR_NOT_FOUND, f"GitHub returned 404: {message}", retryable=False)
    if status == HTTPStatus.GONE:
        return ToolFailure(C.ERROR_GONE, f"GitHub returned 410: {message}", retryable=False)
    if status == HTTPStatus.UNPROCESSABLE_ENTITY:
        return ToolFailure(
            C.ERROR_INVALID_REQUEST,
            f"GitHub rejected the request: {message}",
            retryable=False,
            details=details,
            hint=C.INVALID_REQUEST_HINT,
        )
    if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
        return ToolFailure(
            C.ERROR_UPSTREAM_ERROR,
            f"GitHub returned HTTP {status}.",
            retryable=True,
            retry_after_seconds=config.TRANSIENT_RETRY_SECONDS,
            hint=C.UPSTREAM_ERROR_HINT,
        )
    return ToolFailure(
        C.ERROR_HTTP_ERROR, f"GitHub returned HTTP {status}: {message}", retryable=False
    )


def _unknown_write_outcome() -> ToolFailure:
    """Prevent automatic retries when an issue may already have been created."""
    return ToolFailure(
        C.ERROR_WRITE_OUTCOME_UNKNOWN,
        C.UNKNOWN_WRITE_MESSAGE,
        retryable=False,
        hint=(C.UNKNOWN_WRITE_HINT),
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
        self.settings = settings or config.load_settings()
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
            if resp.status_code == HTTPStatus.UNAUTHORIZED:
                # Revoked or expired early. Refresh once and retry; a second 401 is final.
                token = await self.tokens.access_token(rejected=token)
                resp = await self._send(method, path, token, params, json)
                if resp.status_code == HTTPStatus.UNAUTHORIZED:
                    raise auth_failure(C.REJECTED_REFRESH_MESSAGE)
        except ToolFailure as failure:
            if method == C.HTTP_POST and failure.error == C.ERROR_NETWORK_ERROR:
                raise _unknown_write_outcome() from failure
            raise
        except AuthRequired as exc:
            raise auth_failure(str(exc)) from exc
        except NotConfigured as exc:
            raise ToolFailure(
                C.ERROR_NOT_CONFIGURED,
                f"The GitHub App credentials are missing or invalid ({exc}).",
                retryable=False,
                hint=(C.NOT_CONFIGURED_HINT),
            ) from exc
        except AuthUnavailable as exc:
            raise ToolFailure(
                C.ERROR_NETWORK_ERROR,
                str(exc),
                retryable=True,
                retry_after_seconds=exc.retry_after_seconds,
                hint=f"Wait {exc.retry_after_seconds}s, then retry. No browser login is needed.",
            ) from exc
        if HTTPStatus.MULTIPLE_CHOICES <= resp.status_code < HTTPStatus.BAD_REQUEST:
            raise ToolFailure(
                C.ERROR_REDIRECT_REQUIRED,
                f"GitHub returned HTTP {resp.status_code} instead of the resource.",
                retryable=False,
                hint=(C.REDIRECT_HINT),
            )
        if resp.status_code >= HTTPStatus.BAD_REQUEST:
            if method == C.HTTP_POST and resp.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
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
        return (await self.request(C.HTTP_GET, path, params=params or None)).json()

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
                base_url=self.settings.api_url,
                timeout=config.API_TIMEOUT_SECONDS,
                follow_redirects=method in {C.HTTP_GET, C.HTTP_HEAD},
            ) as http:
                return await http.request(
                    method,
                    path,
                    params=params,
                    json=json,
                    headers={
                        C.HEADER_AUTHORIZATION: f"{C.BEARER_PREFIX}{token}",
                        C.HEADER_ACCEPT: C.GITHUB_MEDIA_TYPE,
                        C.HEADER_API_VERSION: C.GITHUB_API_VERSION,
                    },
                )
        except httpx.TimeoutException as exc:
            raise ToolFailure(
                C.ERROR_NETWORK_ERROR,
                C.NETWORK_TIMEOUT_MESSAGE,
                retryable=True,
                retry_after_seconds=config.TRANSIENT_RETRY_SECONDS,
            ) from exc
        except httpx.HTTPError as exc:
            raise ToolFailure(
                C.ERROR_NETWORK_ERROR,
                f"Could not reach GitHub: {type(exc).__name__}",
                retryable=True,
                retry_after_seconds=config.TRANSIENT_RETRY_SECONDS,
            ) from exc
