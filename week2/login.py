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

import httpx

from oauth import AuthRequired, AuthUnavailable, Settings, TokenStore, exchange


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:96]
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def authorize_url(settings: Settings, state: str, challenge: str) -> str:
    query = urllib.parse.urlencode(
        {
            "client_id": settings.client_id,
            "redirect_uri": settings.redirect_uri,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{settings.oauth_url}/login/oauth/authorize?{query}"


def wait_for_code(port: int, expected_state: str, timeout: float = 300) -> str:
    """Serve one request on 127.0.0.1:<port>/callback and return the ``code`` it carries."""
    result: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            url = urllib.parse.urlparse(self.path)
            params = dict(urllib.parse.parse_qsl(url.query))
            if url.path != "/callback":
                self.send_error(404)
                return
            if params.get("state") != expected_state:
                result["error"] = "state mismatch (possible CSRF); start the login again"
            elif "error" in params:
                result["error"] = f"{params['error']}: {params.get('error_description', '')}"
            else:
                result["code"] = params.get("code", "")
            ok = "code" in result
            self.send_response(200 if ok else 400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            msg = "Logged in. You can close this tab." if ok else f"Login failed: {result['error']}"
            self.wfile.write(msg.encode())
            threading.Thread(target=self.server.shutdown, daemon=True).start()

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    timer = threading.Timer(timeout, server.shutdown)
    timer.start()
    try:
        server.serve_forever()
    finally:
        timer.cancel()
        server.server_close()
    if "code" not in result:
        raise SystemExit(f"Login failed: {result.get('error', 'timed out waiting for the browser')}")
    return result["code"]


async def whoami(settings: Settings, access_token: str) -> str:
    async with httpx.AsyncClient(timeout=15) as http:
        resp = await http.get(
            f"{settings.api_url}/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        )
    return resp.json().get("login", "?") if resp.status_code == 200 else f"HTTP {resp.status_code}"


def main() -> None:
    settings = Settings.from_env()
    if not (settings.client_id and settings.client_secret):
        sys.exit("Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET (env or week2/.env) first.")
    state = secrets.token_urlsafe(32)
    verifier, challenge = pkce_pair()
    url = authorize_url(settings, state, challenge)
    print(f"Opening your browser to authorize. If it doesn't open, visit:\n\n  {url}\n")
    webbrowser.open(url)
    code = wait_for_code(settings.callback_port, state)
    try:
        token = asyncio.run(
            exchange(
                settings,
                {"code": code, "code_verifier": verifier, "redirect_uri": settings.redirect_uri},
            )
        )
    except (AuthRequired, AuthUnavailable) as exc:
        sys.exit(f"Code exchange failed: {exc}")
    TokenStore(settings.token_file).save(token)
    login = asyncio.run(whoami(settings, token.access_token))
    print(f"Authorized as {login}. Token cached at {settings.token_file} (mode 0600).")


if __name__ == "__main__":
    main()
