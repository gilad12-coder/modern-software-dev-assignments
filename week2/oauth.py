"""GitHub App OAuth: settings, token cache, silent refresh, and the one-time login flow.

The MCP server only ever *refreshes* tokens. Getting the first token needs a browser,
so that lives in ``login.py`` and is never triggered from inside a tool call.
"""

from __future__ import annotations

import asyncio
import fcntl
import json
import os
import time
import weakref
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

# Refresh a little early so a token never expires between our check and GitHub's.
EXPIRY_SKEW_SECONDS = 120
LOGIN_COMMAND = "uv run --directory week2 python login.py"


@dataclass(frozen=True)
class Settings:
    client_id: str | None
    client_secret: str | None
    token_file: Path
    api_url: str
    oauth_url: str
    callback_port: int

    @classmethod
    def from_env(cls) -> Settings:
        default_token = Path.home() / ".config" / "github-issues-mcp" / "token.json"
        return cls(
            client_id=os.environ.get("GITHUB_CLIENT_ID") or None,
            client_secret=os.environ.get("GITHUB_CLIENT_SECRET") or None,
            token_file=Path(os.environ.get("GH_MCP_TOKEN_FILE") or default_token).expanduser(),
            api_url=os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/"),
            oauth_url=os.environ.get("GITHUB_OAUTH_URL", "https://github.com").rstrip("/"),
            callback_port=int(os.environ.get("GH_MCP_CALLBACK_PORT", "8765")),
        )

    @property
    def redirect_uri(self) -> str:
        return f"http://127.0.0.1:{self.callback_port}/callback"


class AuthRequired(Exception):
    """No usable token, and the only fix is a human running the login command."""


class NotConfigured(Exception):
    """The server was started without the GitHub App's client credentials."""


class AuthUnavailable(Exception):
    """The token endpoint could not be reached. The token itself may still be fine."""


@dataclass(frozen=True)
class Token:
    access_token: str
    expires_at: float
    refresh_token: str
    refresh_expires_at: float

    @classmethod
    def from_response(cls, data: dict, now: float | None = None) -> Token:
        now = time.time() if now is None else now
        return cls(
            access_token=data["access_token"],
            expires_at=now + int(data["expires_in"]),
            refresh_token=data["refresh_token"],
            refresh_expires_at=now + int(data["refresh_token_expires_in"]),
        )


class TokenStore:
    """JSON token cache outside the repo, written atomically with mode 0600."""

    def __init__(self, path: Path):
        self.path = path

    def load(self) -> Token | None:
        try:
            return Token(**json.loads(self.path.read_text()))
        except FileNotFoundError:
            return None
        except (ValueError, TypeError):
            return None

    def save(self, token: Token) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        tmp = self.path.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(asdict(token), f)
        os.replace(tmp, self.path)


async def exchange(settings: Settings, payload: dict) -> Token:
    """POST to GitHub's token endpoint. Used for both the code exchange and refresh."""
    payload = {"client_id": settings.client_id, "client_secret": settings.client_secret, **payload}
    try:
        async with httpx.AsyncClient(timeout=15) as http:
            resp = await http.post(
                f"{settings.oauth_url}/login/oauth/access_token",
                data=payload,
                headers={"Accept": "application/json"},
            )
    except httpx.HTTPError as exc:
        raise AuthUnavailable(f"could not reach GitHub's token endpoint: {exc}") from exc
    if resp.status_code >= 500:
        raise AuthUnavailable(f"GitHub's token endpoint returned HTTP {resp.status_code}")
    data = resp.json()
    # GitHub reports OAuth failures as HTTP 200 with an "error" field.
    if "error" in data or "access_token" not in data:
        raise AuthRequired(f"{data.get('error', 'no_token')}: {data.get('error_description', '')}")
    if "refresh_token" not in data:
        raise AuthRequired(
            "GitHub returned a token without a refresh token. Enable 'Expire user "
            "authorization tokens' in the GitHub App settings."
        )
    return Token.from_response(data)


_locks: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()


def _loop_lock() -> asyncio.Lock:
    loop = asyncio.get_running_loop()
    if loop not in _locks:
        _locks[loop] = asyncio.Lock()
    return _locks[loop]


class TokenManager:
    """Hands out a valid access token, refreshing silently. Never opens a browser."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = TokenStore(settings.token_file)

    async def access_token(self, rejected: str | None = None) -> str:
        """Return a usable access token.

        ``rejected`` is a token GitHub just answered 401 to. If the cache still holds it
        we refresh even though it hasn't reached its expiry time.
        """
        if not (self.settings.client_id and self.settings.client_secret):
            raise NotConfigured("GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET are not set")
        # GitHub refresh tokens are single-use, so two refreshes racing each other would
        # leave one caller holding a dead token. Serialize within this process (asyncio
        # lock) and across processes sharing the cache file (flock on a sidecar file).
        async with _loop_lock():
            lock_path = self.settings.token_file.with_suffix(".lock")
            lock_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with open(lock_path, "w") as lock_file:
                await asyncio.to_thread(fcntl.flock, lock_file, fcntl.LOCK_EX)
                try:
                    return await self._fresh_token(rejected)
                finally:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)

    async def _fresh_token(self, rejected: str | None) -> str:
        token = self.store.load()
        if token is None:
            raise AuthRequired("no cached token")
        now = time.time()
        still_valid = token.expires_at - EXPIRY_SKEW_SECONDS > now
        if still_valid and token.access_token != rejected:
            return token.access_token
        if token.refresh_expires_at <= now:
            raise AuthRequired("the refresh token expired (they last 6 months)")
        new = await exchange(
            self.settings, {"grant_type": "refresh_token", "refresh_token": token.refresh_token}
        )
        self.store.save(new)
        return new.access_token
