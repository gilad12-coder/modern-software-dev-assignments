"""The one-time browser login: state check, PKCE, code exchange, token cached with 0600."""

from __future__ import annotations

import json
import socket
import threading
import urllib.parse
import urllib.request

import pytest

import login


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def fake_browser(fake, state_override=None):
    """Stand in for the user clicking Authorize: GitHub redirects back to our callback."""

    def open_url(url: str) -> None:
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(url).query))
        assert params["code_challenge_method"] == "S256"
        fake.code_challenge = params["code_challenge"]
        back = urllib.parse.urlencode(
            {"code": fake.issued_code, "state": state_override or params["state"]}
        )
        target = f"{params['redirect_uri']}?{back}"
        threading.Timer(0.2, lambda: _get(target)).start()

    return open_url


def _get(url: str) -> None:
    try:
        urllib.request.urlopen(url, timeout=5).read()
    except Exception:
        pass


def test_login_exchanges_code_and_caches_token(fake, server_env, tmp_path, monkeypatch):
    (tmp_path / "token.json").unlink()
    monkeypatch.setenv("GH_MCP_CALLBACK_PORT", str(free_port()))
    fake.route("GET", "/user", {"login": "alice"})
    fake.valid_tokens = {"ghu_new1"}
    monkeypatch.setattr(login.webbrowser, "open", fake_browser(fake))
    login.main()
    cached = json.loads((tmp_path / "token.json").read_text())
    assert cached["access_token"] == "ghu_new1" and cached["refresh_token"] == "ghr_new1"
    assert oct((tmp_path / "token.json").stat().st_mode)[-3:] == "600"
    exchange = fake.calls("POST", "/login/oauth/access_token")[0]["form"]
    assert exchange["client_secret"] == "test-secret" and exchange["code_verifier"]


def test_login_rejects_forged_state(fake, server_env, tmp_path, monkeypatch):
    monkeypatch.setenv("GH_MCP_CALLBACK_PORT", str(free_port()))
    monkeypatch.setattr(login.webbrowser, "open", fake_browser(fake, state_override="forged"))
    with pytest.raises(SystemExit, match="state mismatch"):
        login.main()
    assert fake.calls("POST", "/login/oauth/access_token") == []
