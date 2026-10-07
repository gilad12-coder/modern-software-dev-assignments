"""A fake GitHub (REST API + OAuth token endpoint) served over real HTTP on localhost."""

from __future__ import annotations

import base64
import hashlib
import json
import threading
import time
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from . import constants as T


def issue(number: int, title: str, **extra) -> dict:
    """Build a raw GitHub issue, including fields the server should drop.

    Args:
        number: Issue number.
        title: Issue title.
        **extra: Fields to add or override.

    Returns:
        The issue as GitHub's REST API returns it.
    """
    return {
        T.KEY_NUMBER: number,
        T.KEY_TITLE: title,
        T.KEY_STATE: T.STATE_OPEN,
        T.KEY_STATE_REASON: None,
        T.KEY_USER: {T.KEY_LOGIN: T.OWNER},
        T.KEY_LABELS: [
            {
                T.KEY_NAME: T.BUG_LABEL,
                T.KEY_COLOR: T.LABEL_COLOR,
                T.KEY_ID: 1,
                T.KEY_URL: T.PLACEHOLDER_URL,
            }
        ],
        T.KEY_COMMENTS: 0,
        T.KEY_CREATED_AT: T.ISSUE_CREATED_AT,
        T.KEY_UPDATED_AT: T.ISSUE_UPDATED_AT,
        T.KEY_HTML_URL: f"{T.REPO_WEB_URL}/issues/{number}",
        T.KEY_REPOSITORY_URL: T.REPO_API_URL,
        T.KEY_BODY: T.ISSUE_BODY,
        T.KEY_ASSIGNEES: [],
        T.KEY_MILESTONE: None,
        T.KEY_REACTIONS: {T.REACTION_THUMBS_UP: 0},
        T.KEY_NODE_ID: T.ISSUE_NODE_ID,
        **extra,
    }


class FakeGitHub:
    """In-memory GitHub: canned routes, token checks and single-use refresh tokens.

    Attributes:
        routes: Response per (method, path): a (status, body, headers) tuple or a callable.
        requests: Every request received, in order.
        valid_tokens: Access tokens the API currently accepts.
        refresh_tokens: Refresh tokens that have not been used yet.
        refresh_calls: How many refresh grants were attempted.
        issued_code: Authorization code the login flow should exchange.
        code_challenge: PKCE challenge from the last authorize URL.
        url: Base URL, set once the HTTP server is running.
    """

    def __init__(self) -> None:
        """Start with a valid token pair and the default routes."""
        self.routes: dict[tuple[str, str], object] = {}
        self.requests: list[dict] = []
        self.valid_tokens = {T.VALID_ACCESS_TOKEN}
        self.refresh_tokens = {T.VALID_REFRESH_TOKEN}
        self.refresh_calls = 0
        self.issued_code = T.AUTH_CODE
        self.code_challenge: str | None = None
        self._serial = 0
        self._lock = threading.Lock()
        self._install_defaults()

    def route(self, method: str, path: str, body=None, status: int = HTTPStatus.OK, headers=None):
        """Set a canned response for one endpoint.

        Args:
            method: HTTP method.
            path: Request path without the query string.
            body: JSON body to return.
            status: HTTP status to return.
            headers: Extra response headers.
        """
        self.routes[(method, path)] = (status, body, headers or {})

    def calls(self, method: str, path: str) -> list[dict]:
        """List the recorded requests to one endpoint.

        Args:
            method: HTTP method.
            path: Request path without the query string.

        Returns:
            The matching requests, oldest first.
        """
        return [r for r in self.requests if r[T.KEY_METHOD] == method and r[T.KEY_PATH] == path]

    def _install_defaults(self) -> None:
        """Register one installation, two repos, issue #7 and the token endpoint."""
        self.route(T.HTTP_GET, T.INSTALLATIONS_PATH, {T.KEY_INSTALLATIONS: [{T.KEY_ID: 1}]})
        self.route(
            T.HTTP_GET, T.INSTALLATION_REPOS_PATH, {T.KEY_REPOSITORIES: [T.OLD_REPO, T.REPO]}
        )
        self.route(T.HTTP_GET, T.REPO_PATH, T.REPO)
        self.route(
            T.HTTP_GET, T.LABELS_PATH, [{T.KEY_NAME: T.BUG_LABEL}, {T.KEY_NAME: T.DOCS_LABEL}]
        )
        self.route(T.HTTP_GET, T.ISSUE_PATH, issue(T.ISSUE_NUMBER, T.ISSUE_TITLE))
        self.route(T.HTTP_GET, T.COMMENTS_PATH, [])
        self.route(
            T.HTTP_GET,
            T.SEARCH_ISSUES_PATH,
            {
                T.KEY_TOTAL_COUNT: 1,
                T.KEY_INCOMPLETE_RESULTS: False,
                T.KEY_ITEMS: [issue(T.ISSUE_NUMBER, T.ISSUE_TITLE)],
            },
        )
        self.routes[(T.HTTP_POST, T.ISSUES_PATH)] = lambda req: (
            HTTPStatus.CREATED,
            issue(
                T.CREATED_ISSUE_NUMBER,
                req[T.KEY_JSON][T.KEY_TITLE],
                labels=[{T.KEY_NAME: n} for n in req[T.KEY_JSON][T.KEY_LABELS]],
            ),
            {},
        )
        self.routes[(T.HTTP_POST, T.TOKEN_PATH)] = self._refresh

    def _refresh(self, req: dict):
        """Act as GitHub's token endpoint for code exchange and refresh grants.

        Args:
            req: The recorded request, with its form fields.

        Returns:
            A (status, body, headers) tuple; errors come back as HTTP 200, as on GitHub.
        """
        form = req[T.KEY_FORM]
        with self._lock:
            if T.KEY_CODE in form:
                verifier_hash = hashlib.sha256(form.get(T.KEY_CODE_VERIFIER, "").encode()).digest()
                challenge = base64.urlsafe_b64encode(verifier_hash).rstrip(b"=").decode()
                if form[T.KEY_CODE] != self.issued_code or challenge != self.code_challenge:
                    return HTTPStatus.OK, {T.KEY_ERROR: T.OAUTH_BAD_CODE}, {}
            else:
                self.refresh_calls += 1
            if T.KEY_CODE not in form and form.get(T.KEY_REFRESH_TOKEN) not in self.refresh_tokens:
                return (
                    HTTPStatus.OK,
                    {
                        T.KEY_ERROR: T.OAUTH_BAD_REFRESH,
                        T.KEY_ERROR_DESCRIPTION: T.TOKEN_EXPIRED_MESSAGE,
                    },
                    {},
                )
            # Single use, like GitHub: the old refresh and access tokens both die.
            self.refresh_tokens.discard(form.get(T.KEY_REFRESH_TOKEN))
            self._serial += 1
            access, refresh = (
                T.ROTATED_ACCESS_FORMAT.format(serial=self._serial),
                T.ROTATED_REFRESH_FORMAT.format(serial=self._serial),
            )
            self.valid_tokens = {access}
            self.refresh_tokens.add(refresh)
        return (
            HTTPStatus.OK,
            {
                T.KEY_ACCESS_TOKEN: access,
                T.KEY_EXPIRES_IN: T.ISSUED_ACCESS_SECONDS,
                T.KEY_REFRESH_TOKEN: refresh,
                T.KEY_REFRESH_TOKEN_EXPIRES_IN: T.ISSUED_REFRESH_SECONDS,
                T.KEY_TOKEN_TYPE: T.TOKEN_TYPE,
                T.KEY_SCOPE: "",
            },
            {},
        )

    def handle(self, handler: BaseHTTPRequestHandler) -> None:
        """Record a request, check its token and write the routed response.

        Args:
            handler: The HTTP handler for the incoming request.
        """
        url = urllib.parse.urlparse(handler.path)
        length = int(handler.headers.get(T.HEADER_REQUEST_LENGTH) or 0)
        raw = handler.rfile.read(length).decode() if length else ""
        req = {
            T.KEY_METHOD: handler.command,
            T.KEY_PATH: url.path,
            T.KEY_QUERY: dict(urllib.parse.parse_qsl(url.query)),
            T.KEY_AUTH: handler.headers.get(T.HEADER_AUTHORIZATION),
            T.KEY_JSON: json.loads(raw) if raw and raw.startswith("{") else None,
            T.KEY_FORM: dict(urllib.parse.parse_qsl(raw))
            if raw and not raw.startswith("{")
            else {},
        }
        self.requests.append(req)
        if (
            not url.path.startswith(T.OAUTH_PATH_PREFIX)
            and (req[T.KEY_AUTH] or "")[len(T.BEARER_PREFIX) :] not in self.valid_tokens
        ):
            status, body, headers = (
                HTTPStatus.UNAUTHORIZED,
                {T.KEY_MESSAGE: T.BAD_CREDENTIALS_MESSAGE},
                {},
            )
        else:
            spec = self.routes.get(
                (req[T.KEY_METHOD], url.path),
                (HTTPStatus.NOT_FOUND, {T.KEY_MESSAGE: T.NOT_FOUND_MESSAGE}, {}),
            )
            status, body, headers = spec(req) if callable(spec) else spec
        payload = json.dumps(body).encode()
        handler.send_response(status)
        handler.send_header(T.HEADER_CONTENT_TYPE, T.JSON_MEDIA_TYPE)
        handler.send_header(T.HEADER_CONTENT_LENGTH, str(len(payload)))
        for key, value in headers.items():
            handler.send_header(key, value)
        handler.end_headers()
        handler.wfile.write(payload)


@pytest.fixture
def fake():
    """Serve a FakeGitHub over real HTTP on a free localhost port.

    Yields:
        The running fake, with ``url`` set.
    """
    gh = FakeGitHub()

    class Handler(BaseHTTPRequestHandler):
        """Forwards every request to the fake."""

        def do_GET(self):
            """Handle GET (and POST, aliased below) through the fake."""
            gh.handle(self)

        do_POST = do_GET

        def log_message(self, *args):
            """Silence the default per-request logging.

            Args:
                *args: Format string and values, ignored.
            """
            pass

    server = ThreadingHTTPServer((T.LOOPBACK_HOST, T.AUTO_PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    gh.url = f"http://{T.LOOPBACK_HOST}:{server.server_port}"
    yield gh
    server.shutdown()
    server.server_close()


def write_token(
    path: Path,
    access=T.VALID_ACCESS_TOKEN,
    refresh=T.VALID_REFRESH_TOKEN,
    expires_in=T.VALID_ACCESS_SECONDS,
    refresh_in=T.VALID_REFRESH_SECONDS,
):
    """Write a token cache file in the format TokenStore reads.

    Args:
        path: Where to write the file.
        access: Access token.
        refresh: Refresh token.
        expires_in: Seconds until the access token expires (negative for expired).
        refresh_in: Seconds until the refresh token expires.
    """
    now = time.time()
    path.write_text(
        json.dumps(
            {
                T.KEY_ACCESS_TOKEN: access,
                T.KEY_EXPIRES_AT: now + expires_in,
                T.KEY_REFRESH_TOKEN: refresh,
                T.KEY_REFRESH_EXPIRES_AT: now + refresh_in,
            }
        )
    )


@pytest.fixture
def server_env(fake, tmp_path, monkeypatch) -> dict[str, str]:
    """Point the server at the fake GitHub with a valid cached token.

    Args:
        fake: The running fake GitHub.
        tmp_path: Per-test directory for the token file.
        monkeypatch: Used to set the environment variables.

    Returns:
        The environment variables that were set, for passing to subprocesses.
    """
    token_file = tmp_path / T.TOKEN_FILENAME
    write_token(token_file)
    env = {
        T.GITHUB_CLIENT_ID: T.CLIENT_ID,
        T.GITHUB_CLIENT_SECRET: T.CLIENT_SECRET,
        T.GITHUB_API_URL: fake.url,
        T.GITHUB_OAUTH_URL: fake.url,
        T.GH_MCP_TOKEN_FILE: str(token_file),
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return env
