"""One-time interactive login: authorization-code flow with PKCE and a loopback redirect.

Run from the repo root:  uv run --directory week2 python login.py
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import http.server
import secrets
import sys
import threading
import urllib.parse
import webbrowser
from http import HTTPStatus

import config
import constants as C
import httpx
from models import Settings
from oauth import AuthRequired, AuthUnavailable, NotConfigured, TokenStore, exchange


def pkce_pair() -> tuple[str, str]:
    """Generate a PKCE verifier and its S256 challenge.

    Returns:
        The secret verifier and the challenge to put in the authorize URL.
    """
    verifier = secrets.token_urlsafe(C.PKCE_ENTROPY_BYTES)[: C.PKCE_VERIFIER_LENGTH]
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def authorize_url(settings: Settings, state: str, challenge: str) -> str:
    """Build the GitHub page URL where the user approves the app.

    Args:
        settings: Supplies the client ID, redirect URI and OAuth URL.
        state: Random value checked on the callback to block CSRF.
        challenge: PKCE S256 challenge.

    Returns:
        The full authorize URL.
    """
    query = urllib.parse.urlencode(
        {
            C.KEY_CLIENT_ID: settings.client_id,
            C.KEY_REDIRECT_URI: settings.redirect_uri,
            C.KEY_STATE: state,
            C.KEY_CODE_CHALLENGE: challenge,
            C.KEY_CODE_CHALLENGE_METHOD: C.PKCE_METHOD,
        }
    )
    return f"{settings.oauth_url}{C.OAUTH_AUTHORIZE_PATH}?{query}"


def wait_for_code(
    port: int,
    expected_state: str,
    timeout: float = config.LOGIN_TIMEOUT_SECONDS,
    *,
    browser_url: str | None = None,
) -> str:
    """Serve one request on 127.0.0.1:<port>/callback and return the ``code`` it carries.

    Args:
        port: Loopback port to listen on.
        expected_state: The ``state`` sent in the authorize URL.
        timeout: Seconds to wait for the browser before giving up.
        browser_url: Authorization page to open once the callback listener is bound.

    Returns:
        The authorization code from GitHub.

    Raises:
        SystemExit: The state did not match, GitHub sent an error, or time ran out.
    """
    result: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        """Receives GitHub's redirect and records the code or the error."""

        def do_GET(self):
            """Check the callback's state, store the result and stop the server."""
            url = urllib.parse.urlparse(self.path)
            params = dict(urllib.parse.parse_qsl(url.query))
            if url.path != C.OAUTH_CALLBACK_PATH:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            if params.get(C.KEY_STATE) != expected_state:
                result[C.KEY_ERROR] = C.STATE_MISMATCH_MESSAGE
            elif C.KEY_ERROR in params:
                result[C.KEY_ERROR] = (
                    f"{params[C.KEY_ERROR]}: {params.get(C.KEY_ERROR_DESCRIPTION, '')}"
                )
            elif not params.get(C.KEY_CODE):
                result[C.KEY_ERROR] = C.MISSING_CODE_MESSAGE
            else:
                result[C.KEY_CODE] = params[C.KEY_CODE]
            ok = C.KEY_CODE in result
            self.send_response(HTTPStatus.OK if ok else HTTPStatus.BAD_REQUEST)
            self.send_header(C.HEADER_CONTENT_TYPE, C.TEXT_MEDIA_TYPE)
            self.end_headers()
            msg = C.AUTHORIZATION_RECEIVED_MESSAGE if ok else f"Login failed: {result[C.KEY_ERROR]}"
            self.wfile.write(msg.encode())
            threading.Thread(target=self.server.shutdown, daemon=True).start()

        def log_message(self, *args):
            """Silence the default per-request logging.

            Args:
                *args: Format string and values, ignored.
            """
            pass

    server = http.server.HTTPServer((config.LOOPBACK_HOST, port), Handler)
    timer = threading.Timer(timeout, server.shutdown)
    timer.start()
    try:
        if browser_url:
            webbrowser.open(browser_url)
        server.serve_forever()
    finally:
        timer.cancel()
        server.server_close()
    if C.KEY_CODE not in result:
        raise SystemExit(f"Login failed: {result.get(C.KEY_ERROR, C.BROWSER_TIMEOUT_MESSAGE)}")
    return result[C.KEY_CODE]


async def whoami(settings: Settings, access_token: str) -> str:
    """Look up which GitHub account a token belongs to.

    Args:
        settings: Supplies the API URL.
        access_token: Token to check.

    Returns:
        The account's login, or ``HTTP <status>`` if the lookup failed.
    """
    async with httpx.AsyncClient(timeout=config.TOKEN_TIMEOUT_SECONDS) as http:
        resp = await http.get(
            f"{settings.api_url}{C.USER_PATH}",
            headers={
                C.HEADER_AUTHORIZATION: f"{C.BEARER_PREFIX}{access_token}",
                C.HEADER_ACCEPT: C.GITHUB_MEDIA_TYPE,
            },
        )
    return (
        resp.json().get(C.KEY_LOGIN, "?")
        if resp.status_code == HTTPStatus.OK
        else f"HTTP {resp.status_code}"
    )


def main() -> None:
    """Run the browser login and cache the resulting token."""
    settings = config.load_settings()
    if not (settings.client_id and settings.client_secret):
        sys.exit(C.LOGIN_MISSING_CREDENTIALS)
    state = secrets.token_urlsafe(C.LOGIN_STATE_BYTES)
    verifier, challenge = pkce_pair()
    url = authorize_url(settings, state, challenge)
    print(f"Opening your browser to authorize. If it doesn't open, visit:\n\n  {url}\n")
    code = wait_for_code(settings.callback_port, state, browser_url=url)
    try:
        token = asyncio.run(
            exchange(
                settings,
                {
                    C.KEY_CODE: code,
                    C.KEY_CODE_VERIFIER: verifier,
                    C.KEY_REDIRECT_URI: settings.redirect_uri,
                },
            )
        )
    except (AuthRequired, AuthUnavailable, NotConfigured) as exc:
        sys.exit(f"Code exchange failed: {exc}")
    TokenStore(settings.token_file).save(token)
    login = asyncio.run(whoami(settings, token.access_token))
    print(f"Authorized as {login}. Token cached at {settings.token_file} (mode 0600).")


if __name__ == "__main__":
    main()
