"""Exercise app setup with a local callback and a stubbed manifest exchange."""

from __future__ import annotations

import re
import threading
import urllib.request

import httpx
import pytest
from dotenv import dotenv_values
from test_login import free_port

import setup_app


def test_setup_accepts_empty_template_and_preserves_settings(tmp_path, monkeypatch):
    """Fill an empty template privately without dropping callback settings.

    Args:
        tmp_path: Isolated environment file directory.
        monkeypatch: Replaces the browser, callback port and manifest exchange.
    """
    env_file = tmp_path / ".env"
    port = free_port()
    env_file.write_text(f"GITHUB_CLIENT_ID=\nGITHUB_CLIENT_SECRET=\nGH_MCP_CALLBACK_PORT={port}\n")
    env_file.chmod(0o644)
    monkeypatch.setattr(setup_app, "ENV_FILE", env_file)
    monkeypatch.setenv("GH_MCP_CALLBACK_PORT", str(port))
    errors = []
    threads = []

    def open_browser(url):
        """Complete only the local callback; never open GitHub.

        Args:
            url: Local app-manifest form URL.
        """
        def authorize():
            """Read the form's state and simulate GitHub's redirect."""
            try:
                with urllib.request.urlopen(url, timeout=3) as response:
                    form = response.read().decode()
                state = re.search(r"new\?state=([^\"]+)", form).group(1)
                with urllib.request.urlopen(f"{url}created?state={state}&code=test-code", timeout=3):
                    pass
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=authorize, daemon=True)
        threads.append(thread)
        thread.start()

    serve = setup_app.http.server.HTTPServer.serve_forever

    def serve_with_deadline(server):
        """Bound the test if the callback fails.

        Args:
            server: The local callback server.
        """
        timer = threading.Timer(5, server.shutdown)
        timer.start()
        try:
            serve(server)
        finally:
            timer.cancel()

    def convert_manifest(url, **kwargs):
        """Return fake credentials without making an external request.

        Args:
            url: Manifest-conversion URL.
            **kwargs: HTTP request options.

        Returns:
            A successful fake app-creation response.
        """
        assert url == "https://api.github.com/app-manifests/test-code/conversions"
        return httpx.Response(201, json={
            "client_id": "test-client", "client_secret": "test-secret",
            "html_url": "https://github.com/apps/test-app",
        }, request=httpx.Request("POST", url))

    monkeypatch.setattr(setup_app.webbrowser, "open", open_browser)
    monkeypatch.setattr(setup_app.http.server.HTTPServer, "serve_forever", serve_with_deadline)
    monkeypatch.setattr(setup_app.httpx, "post", convert_manifest)
    setup_app.main()
    for thread in threads:
        thread.join(timeout=3)
    assert not errors
    values = dotenv_values(env_file)
    assert values["GITHUB_CLIENT_SECRET"] == "test-secret"
    assert values["GH_MCP_CALLBACK_PORT"] == str(port)
    assert env_file.stat().st_mode & 0o777 == 0o600


def test_setup_preserves_existing_credentials(tmp_path, monkeypatch):
    """Stop before app creation when the environment file already has a secret.

    Args:
        tmp_path: Isolated environment file directory.
        monkeypatch: Replaces the environment file path.
    """
    env_file = tmp_path / ".env"
    original = "GITHUB_CLIENT_SECRET = 'existing-test-secret'\n"
    env_file.write_text(original)
    monkeypatch.setattr(setup_app, "ENV_FILE", env_file)
    monkeypatch.setattr(setup_app.webbrowser, "open", lambda url: pytest.fail("Setup must not open a browser"))
    with pytest.raises(SystemExit, match="already has credentials"):
        setup_app.main()
    assert env_file.read_text() == original
