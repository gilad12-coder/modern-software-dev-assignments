"""Create the GitHub App from a manifest, so its permissions are declared in code.

Run once from the repo root:  uv run --directory week2 python setup_app.py
Opens a browser, you click "Create GitHub App", and the client ID/secret land in week2/.env.
"""

from __future__ import annotations

import html
import http.server
import json
import secrets
import sys
import threading
import urllib.parse
import webbrowser
from http import HTTPStatus

import config
import constants as C
import httpx
from dotenv import dotenv_values, set_key
from models import Settings


def manifest(settings: Settings, name: str) -> dict:
    """Describe the GitHub App to create, including its full permission set.

    Args:
        settings: Supplies the callback port and redirect URI.
        name: App name; must be unique on GitHub.

    Returns:
        The manifest GitHub's app-creation form expects.
    """
    return {
        C.KEY_NAME: name,
        C.KEY_URL: config.APP_HOMEPAGE,
        C.KEY_REDIRECT_URL: f"http://{config.LOOPBACK_HOST}:{settings.callback_port}{C.APP_CALLBACK_PATH}",
        C.KEY_CALLBACK_URLS: [settings.redirect_uri],
        C.KEY_PUBLIC: False,
        C.KEY_HOOK_ATTRIBUTES: C.DISABLED_WEBHOOK.copy(),
        # The whole permission surface of this server. Nothing else is requestable.
        C.KEY_DEFAULT_PERMISSIONS: C.APP_PERMISSIONS.copy(),
        C.KEY_DEFAULT_EVENTS: [],
    }


def main() -> None:
    """Create the app through the browser and save its client credentials to ``.env``."""
    if config.ENV_FILE.exists() and dotenv_values(config.ENV_FILE).get(C.GITHUB_CLIENT_SECRET):
        sys.exit(f"{config.ENV_FILE} already has credentials; delete it to create a new app.")
    settings = config.load_settings()
    name = f"{config.APP_NAME_PREFIX}{secrets.token_hex(C.APP_NAME_RANDOM_BYTES)}"
    state = secrets.token_urlsafe(C.APP_STATE_BYTES)
    form = (
        f'<form id="f" method="post" action="{settings.oauth_url}{C.APP_CREATE_PATH}?state='
        f'{state}"><input type="hidden" name="manifest" value="'
        f'{html.escape(json.dumps(manifest(settings, name)))}"></form>'
        "<script>document.getElementById('f').submit()</script>"
    )
    result: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        """Serves the auto-submitting manifest form and catches GitHub's redirect."""

        def do_GET(self):
            """Serve the form at ``/`` or record the code GitHub sends to ``/created``."""
            url = urllib.parse.urlparse(self.path)
            params = dict(urllib.parse.parse_qsl(url.query))
            if url.path == "/":
                body = form
            elif url.path == C.APP_CALLBACK_PATH and params.get(C.KEY_STATE) == state:
                result[C.KEY_CODE] = params[C.KEY_CODE]
                body = C.APP_CREATED_MESSAGE
                threading.Thread(target=self.server.shutdown, daemon=True).start()
            else:
                self.send_error(HTTPStatus.BAD_REQUEST)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header(C.HEADER_CONTENT_TYPE, C.HTML_MEDIA_TYPE)
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *args):
            """Silence the default per-request logging.

            Args:
                *args: Format string and values, ignored.
            """
            pass

    server = http.server.HTTPServer((config.LOOPBACK_HOST, settings.callback_port), Handler)
    start = f"http://{config.LOOPBACK_HOST}:{settings.callback_port}/"
    print(f"Opening {start} -> GitHub. Click 'Create GitHub App' there.")
    webbrowser.open(start)
    server.serve_forever()
    server.server_close()

    resp = httpx.post(
        settings.api_url + C.MANIFEST_CONVERSION_PATH.format(code=result[C.KEY_CODE]),
        headers={C.HEADER_ACCEPT: C.GITHUB_MEDIA_TYPE},
        timeout=config.API_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    app = resp.json()
    # The response also carries the app's private key and webhook secret. This server
    # never acts as the app itself, so they are deliberately dropped, not stored.
    # Restrict access before writing secrets; keep optional settings in copied templates.
    config.ENV_FILE.touch(mode=C.PRIVATE_FILE_MODE, exist_ok=True)
    config.ENV_FILE.chmod(C.PRIVATE_FILE_MODE)
    set_key(config.ENV_FILE, C.GITHUB_CLIENT_ID, app[C.KEY_CLIENT_ID])
    set_key(config.ENV_FILE, C.GITHUB_CLIENT_SECRET, app[C.KEY_CLIENT_SECRET])
    print(f"Saved client ID and secret to {config.ENV_FILE} (gitignored, mode 0600).")
    print(
        f"Next: install the app on the repos it may touch: {app[C.KEY_HTML_URL]}{C.APP_INSTALL_PATH}"
    )
    print(f"Then: {C.LOGIN_COMMAND}")


if __name__ == "__main__":
    main()
