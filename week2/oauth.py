"""GitHub App OAuth: token cache, silent refresh, and the one-time login flow.

The MCP server only ever *refreshes* tokens. Getting the first token needs a browser,
so that lives in ``login.py`` and is never triggered from inside a tool call.
"""

from __future__ import annotations

import asyncio
import fcntl
import json
import math
import os
import tempfile
import time
import weakref
from dataclasses import asdict
from http import HTTPStatus
from pathlib import Path

import config
import constants as C
import httpx
from models import Settings, Token


class AuthRequired(Exception):
    """No usable token, and the only fix is a human running the login command."""


class NotConfigured(Exception):
    """The GitHub App's client credentials are missing or invalid."""


class AuthUnavailable(Exception):
    """The token endpoint could not be reached. The token itself may still be fine."""

    def __init__(self, message: str, retry_after_seconds: int = config.TRANSIENT_RETRY_SECONDS):
        """Record a temporary failure and when it is safe to retry.

        Args:
            message: Explanation of the temporary failure.
            retry_after_seconds: Minimum wait before another attempt.
        """
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class TokenStore:
    """JSON token cache outside the repo, written atomically with mode 0600."""

    def __init__(self, path: Path):
        """Create a store backed by one file.

        Args:
            path: Location of the JSON token file.
        """
        self.path = path

    def load(self) -> Token | None:
        """Read the cached token.

        Returns:
            The token, or None if the file is missing, unreadable, or invalid.
        """
        try:
            token = Token(**json.loads(self.path.read_text()))
            if any(
                not isinstance(value, str) or not value.strip()
                for value in (token.access_token, token.refresh_token)
            ):
                return None
            if any(
                type(value) not in (int, float) or not math.isfinite(value)
                for value in (token.expires_at, token.refresh_expires_at)
            ):
                return None
            return token
        except (OSError, ValueError, TypeError, OverflowError):
            return None

    def save(self, token: Token) -> None:
        """Write the token atomically, readable only by the current user.

        Args:
            token: The token to cache.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=C.PRIVATE_DIRECTORY_MODE)
        fd, name = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        tmp = Path(name)
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(asdict(token), f)
            os.replace(tmp, self.path)
        finally:
            tmp.unlink(missing_ok=True)


async def exchange(settings: Settings, payload: dict) -> Token:
    """POST to GitHub's token endpoint. Used for both the code exchange and refresh.

    Args:
        settings: Supplies the client credentials and OAuth URL.
        payload: Grant-specific fields, e.g. ``grant_type`` and ``refresh_token``.

    Returns:
        The new token pair.

    Raises:
        AuthUnavailable: The endpoint is unreachable, rate limited, or temporarily unusable.
        AuthRequired: GitHub refused the grant, or sent no refresh token.
        NotConfigured: GitHub rejected the app's client credentials.
    """
    payload = {
        C.KEY_CLIENT_ID: settings.client_id,
        C.KEY_CLIENT_SECRET: settings.client_secret,
        **payload,
    }
    try:
        async with httpx.AsyncClient(timeout=config.TOKEN_TIMEOUT_SECONDS) as http:
            resp = await http.post(
                f"{settings.oauth_url}{C.OAUTH_TOKEN_PATH}",
                data=payload,
                headers={C.HEADER_ACCEPT: C.JSON_MEDIA_TYPE},
            )
    except httpx.HTTPError as exc:
        raise AuthUnavailable(f"could not reach GitHub's token endpoint: {exc}") from exc
    if resp.status_code == HTTPStatus.TOO_MANY_REQUESTS:
        delay = resp.headers.get(C.HEADER_RETRY_AFTER, str(config.RATE_LIMIT_RETRY_SECONDS))
        raise AuthUnavailable(
            C.OAUTH_RATE_LIMIT_MESSAGE,
            retry_after_seconds=max(config.MIN_RETRY_SECONDS, int(delay))
            if delay.isdigit()
            else config.RATE_LIMIT_RETRY_SECONDS,
        )
    if resp.status_code >= HTTPStatus.INTERNAL_SERVER_ERROR:
        raise AuthUnavailable(f"GitHub's token endpoint returned HTTP {resp.status_code}")
    try:
        data = resp.json()
    except ValueError as exc:
        raise AuthUnavailable(C.OAUTH_INVALID_JSON_MESSAGE) from exc
    if not isinstance(data, dict):
        raise AuthUnavailable(C.OAUTH_UNEXPECTED_RESPONSE_MESSAGE)
    # GitHub reports OAuth failures as HTTP 200 with an "error" field.
    if data.get(C.KEY_ERROR) in {C.OAUTH_TEMPORARILY_UNAVAILABLE, C.OAUTH_SERVER_ERROR}:
        raise AuthUnavailable(C.OAUTH_UNAVAILABLE_MESSAGE)
    if data.get(C.KEY_ERROR) in {C.OAUTH_BAD_CREDENTIALS, C.OAUTH_INVALID_CLIENT}:
        raise NotConfigured(C.OAUTH_REJECTED_CREDENTIALS_MESSAGE)
    if C.KEY_ERROR in data:
        raise AuthRequired(f"{data[C.KEY_ERROR]}: {data.get(C.KEY_ERROR_DESCRIPTION, '')}")
    if C.KEY_ACCESS_TOKEN not in data:
        raise AuthUnavailable(C.OAUTH_NO_ACCESS_MESSAGE)
    if C.KEY_REFRESH_TOKEN not in data:
        raise AuthRequired(C.OAUTH_NO_REFRESH_MESSAGE)
    try:
        return Token.from_response(data)
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthUnavailable(C.OAUTH_INCOMPLETE_TOKEN_MESSAGE) from exc


_locks: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()


def _loop_lock() -> asyncio.Lock:
    """Get the refresh lock for the running event loop, creating it on first use.

    Returns:
        One asyncio lock per event loop.
    """
    loop = asyncio.get_running_loop()
    if loop not in _locks:
        _locks[loop] = asyncio.Lock()
    return _locks[loop]


class TokenManager:
    """Hands out a valid access token, refreshing silently. Never opens a browser."""

    def __init__(self, settings: Settings):
        """Create a manager for the token file named in ``settings``.

        Args:
            settings: Supplies client credentials and the token file path.
        """
        self.settings = settings
        self.store = TokenStore(settings.token_file)

    async def access_token(self, rejected: str | None = None) -> str:
        """Return a usable access token.

        Args:
            rejected: A token GitHub just answered 401 to. If the cache still holds it
                we refresh even though it hasn't reached its expiry time.

        Returns:
            An access token that should be accepted by GitHub.

        Raises:
            NotConfigured: The client ID or secret is not set.
            AuthRequired: There is no token, or it cannot be refreshed.
            AuthUnavailable: The token endpoint could not be reached.
        """
        if not (self.settings.client_id and self.settings.client_secret):
            raise NotConfigured(C.MISSING_CREDENTIALS_MESSAGE)
        # GitHub refresh tokens are single-use, so two refreshes racing each other would
        # leave one caller holding a dead token. Serialize within this process (asyncio
        # lock) and across processes sharing the cache file (flock on a sidecar file).
        async with _loop_lock():
            lock_path = self.settings.token_file.with_suffix(C.TOKEN_LOCK_SUFFIX)
            lock_path.parent.mkdir(parents=True, exist_ok=True, mode=C.PRIVATE_DIRECTORY_MODE)
            with open(lock_path, "w") as lock_file:
                await asyncio.to_thread(fcntl.flock, lock_file, fcntl.LOCK_EX)
                try:
                    return await self._fresh_token(rejected)
                finally:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)

    async def _fresh_token(self, rejected: str | None) -> str:
        """Return the cached token, refreshing it first if expired or rejected.

        Args:
            rejected: A token GitHub just refused, or None.

        Returns:
            A usable access token.

        Raises:
            AuthRequired: There is no cached token or the refresh token expired.
        """
        token = self.store.load()
        if token is None:
            raise AuthRequired(C.NO_TOKEN_MESSAGE)
        now = time.time()
        still_valid = token.expires_at - config.EXPIRY_SKEW_SECONDS > now
        if still_valid and token.access_token != rejected:
            return token.access_token
        if token.refresh_expires_at <= now:
            raise AuthRequired(C.REFRESH_EXPIRED_MESSAGE)
        new = await exchange(
            self.settings,
            {C.KEY_GRANT_TYPE: C.KEY_REFRESH_TOKEN, C.KEY_REFRESH_TOKEN: token.refresh_token},
        )
        self.store.save(new)
        return new.access_token
