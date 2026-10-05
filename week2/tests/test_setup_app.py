"""Exercise app setup with a local callback and a stubbed manifest exchange."""

from __future__ import annotations

import re
import threading
import urllib.request
from http import HTTPStatus

import httpx
import pytest
import setup_app
from dotenv import dotenv_values

from . import constants as T
from .test_login import free_port


def test_setup_accepts_empty_template_and_preserves_settings(tmp_path, monkeypatch):
    """Fill an empty template privately without dropping callback settings.

    Args:
        tmp_path: Isolated environment file directory.
        monkeypatch: Replaces the browser, callback port and manifest exchange.
    """
    env_file = tmp_path / T.ENV_FILENAME
    port = free_port()
    env_file.write_text(T.ENV_TEMPLATE.format(port=port))
    env_file.chmod(T.PUBLIC_FILE_MODE)
    monkeypatch.setattr(setup_app.config, "ENV_FILE", env_file)
    monkeypatch.setenv(T.GH_MCP_CALLBACK_PORT, str(port))
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
                with urllib.request.urlopen(url, timeout=T.CALLBACK_TIMEOUT) as response:
                    form = response.read().decode()
                state = re.search(T.FORM_STATE_PATTERN, form).group(1)
                with urllib.request.urlopen(
                    T.MANIFEST_CALLBACK.format(url=url, state=state), timeout=T.CALLBACK_TIMEOUT
                ):
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
        timer = threading.Timer(T.SERVER_DEADLINE, server.shutdown)
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
        assert url == T.MANIFEST_CONVERSION_URL
        return httpx.Response(
            HTTPStatus.CREATED,
            json={
                T.KEY_CLIENT_ID: T.CREATED_CLIENT_ID,
                T.KEY_CLIENT_SECRET: T.CLIENT_SECRET,
                T.KEY_HTML_URL: T.APP_WEB_URL,
            },
            request=httpx.Request(T.HTTP_POST, url),
        )

    monkeypatch.setattr(setup_app.webbrowser, "open", open_browser)
    monkeypatch.setattr(setup_app.http.server.HTTPServer, "serve_forever", serve_with_deadline)
    monkeypatch.setattr(setup_app.httpx, "post", convert_manifest)
    setup_app.main()
    for thread in threads:
        thread.join(timeout=T.CALLBACK_TIMEOUT)
    assert not errors
    values = dotenv_values(env_file)
    assert values[T.GITHUB_CLIENT_SECRET] == T.CLIENT_SECRET
    assert values[T.GH_MCP_CALLBACK_PORT] == str(port)
    assert env_file.stat().st_mode & T.FILE_MODE_MASK == T.PRIVATE_FILE_MODE


def test_setup_preserves_existing_credentials(tmp_path, monkeypatch):
    """Stop before app creation when the environment file already has a secret.

    Args:
        tmp_path: Isolated environment file directory.
        monkeypatch: Replaces the environment file path.
    """
    env_file = tmp_path / T.ENV_FILENAME
    original = T.EXISTING_ENV
    env_file.write_text(original)
    monkeypatch.setattr(setup_app.config, "ENV_FILE", env_file)
    monkeypatch.setattr(
        setup_app.webbrowser, "open", lambda url: pytest.fail("Setup must not open a browser")
    )
    with pytest.raises(SystemExit, match=T.EXISTING_CREDENTIALS_MESSAGE):
        setup_app.main()
    assert env_file.read_text() == original
