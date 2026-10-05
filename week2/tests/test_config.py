"""Verify defaults and environment overrides after separating configuration."""

from pathlib import Path

import config

from . import constants as T


def test_settings_defaults_without_credentials(monkeypatch):
    """Keep defaults outside the repository and leave absent credentials unset.

    Args:
        monkeypatch: Clears process settings without reading or changing real secrets.
    """
    for key in T.CONFIG_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    settings = config.load_settings()

    assert settings.client_id is None
    assert settings.client_secret is None
    assert settings.api_url == T.DEFAULT_API_URL
    assert settings.oauth_url == T.DEFAULT_OAUTH_URL
    assert settings.callback_port == T.DEFAULT_CALLBACK_PORT
    assert settings.token_file == Path.home() / T.DEFAULT_TOKEN_PATH
    assert settings.redirect_uri == (
        f"http://{T.LOOPBACK_HOST}:{T.DEFAULT_CALLBACK_PORT}{T.CALLBACK_PATH}"
    )


def test_settings_environment_overrides(fake, server_env, monkeypatch):
    """Apply overrides, normalize base URLs, and expand the token-cache path.

    Args:
        fake: Local endpoint base URL.
        server_env: Isolated client credentials and endpoints.
        monkeypatch: Overrides callback, token path, and trailing URL slashes.
    """
    monkeypatch.setenv(T.GH_MCP_TOKEN_FILE, T.CUSTOM_TOKEN_PATH)
    monkeypatch.setenv(T.GH_MCP_CALLBACK_PORT, str(T.CUSTOM_CALLBACK_PORT))
    monkeypatch.setenv(T.GITHUB_API_URL, fake.url + "/")
    monkeypatch.setenv(T.GITHUB_OAUTH_URL, fake.url + "/")

    settings = config.load_settings()

    assert settings.client_id == T.CLIENT_ID
    assert settings.client_secret == T.CLIENT_SECRET
    assert settings.api_url == fake.url
    assert settings.oauth_url == fake.url
    assert settings.token_file == Path(T.CUSTOM_TOKEN_PATH).expanduser()
    assert settings.callback_port == T.CUSTOM_CALLBACK_PORT
    assert settings.redirect_uri == (
        f"http://{T.LOOPBACK_HOST}:{T.CUSTOM_CALLBACK_PORT}{T.CALLBACK_PATH}"
    )
