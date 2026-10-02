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
from pathlib import Path

import httpx

from oauth import Settings

ENV_FILE = Path(__file__).with_name(".env")


def manifest(settings: Settings, name: str) -> dict:
    """Describe the GitHub App to create, including its full permission set.

    Args:
        settings: Supplies the callback port and redirect URI.
        name: App name; must be unique on GitHub.

    Returns:
        The manifest GitHub's app-creation form expects.
    """
    return {
        "name": name,
        "url": "https://github.com/mihail911/modern-software-dev-assignments",
        "redirect_url": f"http://127.0.0.1:{settings.callback_port}/created",
        "callback_urls": [settings.redirect_uri],
        "public": False,
        "hook_attributes": {"url": "https://example.invalid/unused", "active": False},
        # The whole permission surface of this server. Nothing else is requestable.
        "default_permissions": {"issues": "write", "metadata": "read"},
        "default_events": [],
    }


def main() -> None:
    """Create the app through the browser and save its client credentials to ``.env``."""
    if ENV_FILE.exists() and "GITHUB_CLIENT_SECRET=" in ENV_FILE.read_text():
        sys.exit(f"{ENV_FILE} already has credentials; delete it to create a new app.")
    settings = Settings.from_env()
    name = f"issues-mcp-{secrets.token_hex(3)}"
    state = secrets.token_urlsafe(16)
    form = (
        '<form id="f" method="post" action="https://github.com/settings/apps/new?state='
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
            elif url.path == "/created" and params.get("state") == state:
                result["code"] = params["code"]
                body = "App created. Return to the terminal."
                threading.Thread(target=self.server.shutdown, daemon=True).start()
            else:
                self.send_error(400)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *args):
            """Silence the default per-request logging.

            Args:
                *args: Format string and values, ignored.
            """
            pass

    server = http.server.HTTPServer(("127.0.0.1", settings.callback_port), Handler)
    start = f"http://127.0.0.1:{settings.callback_port}/"
    print(f"Opening {start} -> GitHub. Click 'Create GitHub App' there.")
    webbrowser.open(start)
    server.serve_forever()
    server.server_close()

    resp = httpx.post(
        f"https://api.github.com/app-manifests/{result['code']}/conversions",
        headers={"Accept": "application/vnd.github+json"},
        timeout=20,
    )
    resp.raise_for_status()
    app = resp.json()
    # The response also carries the app's private key and webhook secret. This server
    # never acts as the app itself, so they are deliberately dropped, not stored.
    env_text = f"GITHUB_CLIENT_ID={app['client_id']}\nGITHUB_CLIENT_SECRET={app['client_secret']}\n"
    ENV_FILE.write_text(env_text)
    ENV_FILE.chmod(0o600)
    print(f"Saved client ID and secret to {ENV_FILE} (gitignored, mode 0600).")
    print(f"Next: install the app on the repos it may touch: {app['html_url']}/installations/new")
    print("Then: uv run --directory week2 python login.py")


if __name__ == "__main__":
    main()
