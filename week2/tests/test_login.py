"""The one-time browser login: state check, PKCE, code exchange, token cached with 0600."""

from __future__ import annotations

import json
import socket
import threading
import urllib.parse
import urllib.request

import login
import pytest

from . import constants as T


def free_port() -> int:
    """Find a localhost port that is free right now.

    Returns:
        The port number.
    """
    with socket.socket() as s:
        s.bind((T.LOOPBACK_HOST, T.AUTO_PORT))
        return s.getsockname()[1]


def fake_browser(fake, state_override=None):
    """Stand in for the user clicking Authorize: GitHub redirects back to our callback.

    Args:
        fake: The fake GitHub, which learns the PKCE challenge.
        state_override: State to send back instead of the real one, to fake a CSRF.

    Returns:
        A replacement for ``webbrowser.open``.
    """

    def open_url(url: str) -> None:
        """Read the authorize URL and hit the callback shortly after.

        Args:
            url: The authorize URL login.py tried to open.
        """
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))
        assert params[T.KEY_CODE_CHALLENGE_METHOD] == T.PKCE_METHOD
        fake.code_challenge = params[T.KEY_CODE_CHALLENGE]
        back = urllib.parse.urlencode(
            {T.KEY_CODE: fake.issued_code, T.KEY_STATE: state_override or params[T.KEY_STATE]}
        )
        target = f"{params[T.KEY_REDIRECT_URI]}?{back}"
        threading.Timer(T.BROWSER_REDIRECT_DELAY, lambda: _get(target)).start()

    return open_url


def _get(url: str) -> None:
    """Request a URL and ignore the result or any error.

    Args:
        url: URL to request.
    """
    try:
        urllib.request.urlopen(url, timeout=T.HTTP_TIMEOUT).read()
    except Exception:
        pass


def test_login_exchanges_code_and_caches_token(fake, server_env, tmp_path, monkeypatch):
    """A full login exchanges the code with the verifier and caches the token as 0600.

    Args:
        fake: The fake GitHub.
        server_env: Environment pointing at the fake.
        tmp_path: Directory holding the token file.
        monkeypatch: Used to replace the browser and set the callback port.
    """
    (tmp_path / T.TOKEN_FILENAME).unlink()
    monkeypatch.setenv(T.GH_MCP_CALLBACK_PORT, str(free_port()))
    fake.route(T.HTTP_GET, T.USER_PATH, {T.KEY_LOGIN: T.OWNER})
    fake.valid_tokens = {T.ROTATED_ACCESS_TOKEN}
    monkeypatch.setattr(login.webbrowser, "open", fake_browser(fake))
    login.main()
    cached = json.loads((tmp_path / T.TOKEN_FILENAME).read_text())
    assert (
        cached[T.KEY_ACCESS_TOKEN] == T.ROTATED_ACCESS_TOKEN
        and cached[T.KEY_REFRESH_TOKEN] == T.ROTATED_REFRESH_TOKEN
    )
    assert (tmp_path / T.TOKEN_FILENAME).stat().st_mode & T.FILE_MODE_MASK == T.PRIVATE_FILE_MODE
    exchange = fake.calls(T.HTTP_POST, T.TOKEN_PATH)[0][T.KEY_FORM]
    assert exchange[T.KEY_CLIENT_SECRET] == T.CLIENT_SECRET and exchange[T.KEY_CODE_VERIFIER]


def test_login_rejects_forged_state(fake, server_env, tmp_path, monkeypatch):
    """A callback with the wrong state aborts before any code exchange.

    Args:
        fake: The fake GitHub.
        server_env: Environment pointing at the fake.
        tmp_path: Directory holding the token file.
        monkeypatch: Used to replace the browser and set the callback port.
    """
    monkeypatch.setenv(T.GH_MCP_CALLBACK_PORT, str(free_port()))
    monkeypatch.setattr(login.webbrowser, "open", fake_browser(fake, state_override=T.FORGED_STATE))
    with pytest.raises(SystemExit, match=T.STATE_MISMATCH_MESSAGE):
        login.main()
    assert fake.calls(T.HTTP_POST, T.TOKEN_PATH) == []


def test_callback_is_listening_before_browser_opens(fake, server_env, monkeypatch):
    """Let an already-authorized browser redirect as soon as it opens.

    Args:
        fake: Local GitHub API and OAuth endpoint.
        server_env: Isolated credentials and endpoints.
        monkeypatch: Replaces the browser and callback port.
    """
    port = free_port()
    monkeypatch.setenv(T.GH_MCP_CALLBACK_PORT, str(port))
    fake.route(T.HTTP_GET, T.USER_PATH, {T.KEY_LOGIN: T.OWNER})
    browser = fake_browser(fake)

    def open_when_ready(url):
        """Check the listener before simulating the browser's redirect.

        Args:
            url: Authorization URL.
        """
        with socket.create_connection((T.LOOPBACK_HOST, port), timeout=T.LISTENER_TIMEOUT):
            pass
        browser(url)

    monkeypatch.setattr(login.webbrowser, "open", open_when_ready)
    login.main()
    assert len(fake.calls(T.HTTP_POST, T.TOKEN_PATH)) == 1


def test_login_rejects_callback_without_code(fake, server_env, monkeypatch):
    """Reject an empty callback before trying to exchange a code.

    Args:
        fake: Local GitHub API and OAuth endpoint.
        server_env: Isolated credentials and endpoints.
        monkeypatch: Replaces the browser and callback port.
    """
    fake.issued_code = ""
    monkeypatch.setenv(T.GH_MCP_CALLBACK_PORT, str(free_port()))
    monkeypatch.setattr(login.webbrowser, "open", fake_browser(fake))
    with pytest.raises(SystemExit, match=T.MISSING_CODE_MESSAGE):
        login.main()
    assert fake.calls(T.HTTP_POST, T.TOKEN_PATH) == []


def test_login_reports_rejected_app_credentials(fake, server_env, tmp_path, monkeypatch):
    """Explain invalid app credentials without a traceback or cache replacement.

    Args:
        fake: Local fake GitHub.
        server_env: Isolated credentials and endpoints.
        tmp_path: Token-cache directory.
        monkeypatch: Replaces the browser and callback port.
    """
    before = (tmp_path / T.TOKEN_FILENAME).read_bytes()
    fake.route(T.HTTP_POST, T.TOKEN_PATH, {T.KEY_ERROR: T.OAUTH_BAD_CREDENTIALS})
    monkeypatch.setenv(T.GH_MCP_CALLBACK_PORT, str(free_port()))
    monkeypatch.setattr(login.webbrowser, "open", fake_browser(fake))
    with pytest.raises(SystemExit, match=T.GITHUB_CLIENT_SECRET):
        login.main()
    assert (tmp_path / T.TOKEN_FILENAME).read_bytes() == before
