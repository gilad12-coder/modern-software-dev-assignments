"""A fake GitHub (REST API + OAuth token endpoint) served over real HTTP on localhost."""

from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

REPO = {
    "full_name": "alice/demo",
    "description": "Demo repo",
    "private": False,
    "has_issues": True,
    "open_issues_count": 3,
    "pushed_at": "2026-09-30T10:00:00Z",
    "updated_at": "2026-09-30T10:00:00Z",
    "permissions": {"push": True},
}
OLD_REPO = {**REPO, "full_name": "alice/old", "pushed_at": "2024-01-01T00:00:00Z"}


def issue(number: int, title: str, **extra) -> dict:
    return {
        "number": number,
        "title": title,
        "state": "open",
        "state_reason": None,
        "user": {"login": "alice"},
        "labels": [{"name": "bug", "color": "d73a4a", "id": 1, "url": "..."}],
        "comments": 0,
        "created_at": "2026-09-01T00:00:00Z",
        "updated_at": "2026-09-02T00:00:00Z",
        "html_url": f"https://github.com/alice/demo/issues/{number}",
        "repository_url": "https://api.github.com/repos/alice/demo",
        "body": "Steps to reproduce...",
        "assignees": [],
        "milestone": None,
        "reactions": {"+1": 0},
        "node_id": "I_xyz",
        **extra,
    }


class FakeGitHub:
    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], object] = {}
        self.requests: list[dict] = []
        self.valid_tokens = {"ghu_valid"}
        self.refresh_tokens = {"ghr_valid"}
        self.refresh_calls = 0
        self.issued_code = "code-123"
        self.code_challenge: str | None = None
        self._serial = 0
        self._lock = threading.Lock()
        self._install_defaults()

    def route(self, method: str, path: str, body=None, status: int = 200, headers=None):
        self.routes[(method, path)] = (status, body, headers or {})

    def calls(self, method: str, path: str) -> list[dict]:
        return [r for r in self.requests if r["method"] == method and r["path"] == path]

    def _install_defaults(self) -> None:
        self.route("GET", "/user/installations", {"installations": [{"id": 1}]})
        self.route("GET", "/user/installations/1/repositories", {"repositories": [OLD_REPO, REPO]})
        self.route("GET", "/repos/alice/demo", REPO)
        self.route("GET", "/repos/alice/demo/labels", [{"name": "bug"}, {"name": "docs"}])
        self.route("GET", "/repos/alice/demo/issues/7", issue(7, "Crash on empty input"))
        self.route("GET", "/repos/alice/demo/issues/7/comments", [])
        self.route(
            "GET",
            "/search/issues",
            {"total_count": 1, "incomplete_results": False, "items": [issue(7, "Crash on empty input")]},
        )
        self.routes[("POST", "/repos/alice/demo/issues")] = lambda req: (
            201,
            issue(42, req["json"]["title"], labels=[{"name": n} for n in req["json"]["labels"]]),
            {},
        )
        self.routes[("POST", "/login/oauth/access_token")] = self._refresh

    def _refresh(self, req: dict):
        form = req["form"]
        with self._lock:
            if "code" in form:
                verifier_hash = hashlib.sha256(form.get("code_verifier", "").encode()).digest()
                challenge = base64.urlsafe_b64encode(verifier_hash).rstrip(b"=").decode()
                if form["code"] != self.issued_code or challenge != self.code_challenge:
                    return 200, {"error": "bad_verification_code"}, {}
            else:
                self.refresh_calls += 1
            if "code" not in form and form.get("refresh_token") not in self.refresh_tokens:
                return 200, {"error": "bad_refresh_token", "error_description": "expired"}, {}
            # Single use, like GitHub: the old refresh and access tokens both die.
            self.refresh_tokens.discard(form.get("refresh_token"))
            self._serial += 1
            access, refresh = f"ghu_new{self._serial}", f"ghr_new{self._serial}"
            self.valid_tokens = {access}
            self.refresh_tokens.add(refresh)
        return 200, {
            "access_token": access,
            "expires_in": 28800,
            "refresh_token": refresh,
            "refresh_token_expires_in": 15897600,
            "token_type": "bearer",
            "scope": "",
        }, {}

    def handle(self, handler: BaseHTTPRequestHandler) -> None:
        url = urllib.parse.urlparse(handler.path)
        length = int(handler.headers.get("content-length") or 0)
        raw = handler.rfile.read(length).decode() if length else ""
        req = {
            "method": handler.command,
            "path": url.path,
            "query": dict(urllib.parse.parse_qsl(url.query)),
            "auth": handler.headers.get("authorization"),
            "json": json.loads(raw) if raw and raw.startswith("{") else None,
            "form": dict(urllib.parse.parse_qsl(raw)) if raw and not raw.startswith("{") else {},
        }
        self.requests.append(req)
        if not url.path.startswith("/login/") and (req["auth"] or "")[7:] not in self.valid_tokens:
            status, body, headers = 401, {"message": "Bad credentials"}, {}
        else:
            spec = self.routes.get((req["method"], url.path), (404, {"message": "Not Found"}, {}))
            status, body, headers = spec(req) if callable(spec) else spec
        payload = json.dumps(body).encode()
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(payload)))
        for key, value in headers.items():
            handler.send_header(key, value)
        handler.end_headers()
        handler.wfile.write(payload)


@pytest.fixture
def fake():
    gh = FakeGitHub()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            gh.handle(self)

        do_POST = do_GET

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    gh.url = f"http://127.0.0.1:{server.server_port}"
    yield gh
    server.shutdown()
    server.server_close()


def write_token(path: Path, access="ghu_valid", refresh="ghr_valid", expires_in=3600, refresh_in=10**6):
    now = time.time()
    path.write_text(
        json.dumps(
            {
                "access_token": access,
                "expires_at": now + expires_in,
                "refresh_token": refresh,
                "refresh_expires_at": now + refresh_in,
            }
        )
    )


@pytest.fixture
def server_env(fake, tmp_path, monkeypatch) -> dict[str, str]:
    """Point the server at the fake GitHub with a valid cached token."""
    token_file = tmp_path / "token.json"
    write_token(token_file)
    env = {
        "GITHUB_CLIENT_ID": "Iv1.test",
        "GITHUB_CLIENT_SECRET": "test-secret",
        "GITHUB_API_URL": fake.url,
        "GITHUB_OAUTH_URL": fake.url,
        "GH_MCP_TOKEN_FILE": str(token_file),
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return env
