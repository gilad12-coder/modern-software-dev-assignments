"""Runtime configuration and tuning defaults; credentials come from env or .env.

Environment variables override the local ``.env`` file. Protocol identifiers and
fixed safety requirements live in ``constants.py``.
"""

from __future__ import annotations

import os
from pathlib import Path

import constants as C
from dotenv import load_dotenv
from models import Settings

ENV_FILE = Path(__file__).with_name(".env")
load_dotenv(ENV_FILE)

DEFAULT_API_URL = "https://api.github.com"
DEFAULT_OAUTH_URL = "https://github.com"
DEFAULT_CALLBACK_PORT = 8765
DEFAULT_TOKEN_PATH = Path(".config") / "github-issues-mcp" / "token.json"
LOOPBACK_HOST = "127.0.0.1"
APP_HOMEPAGE = "https://github.com/mihail911/modern-software-dev-assignments"
APP_NAME_PREFIX = "issues-mcp-"

API_TIMEOUT_SECONDS = 20
TOKEN_TIMEOUT_SECONDS = 15
LOGIN_TIMEOUT_SECONDS = 300
# Refresh before expiry so a token stays valid while a request is in flight.
EXPIRY_SKEW_SECONDS = 120
TRANSIENT_RETRY_SECONDS = 5
RATE_LIMIT_RETRY_SECONDS = 60
MIN_RETRY_SECONDS = 1

API_PAGE_SIZE = 100
DEFAULT_REPO_SORT = C.SORT_PUSHED
DEFAULT_REPO_LIMIT = 30
MAX_REPO_LIMIT = 100
DEFAULT_SEARCH_STATE = C.STATE_OPEN
DEFAULT_SEARCH_KIND = C.KIND_ISSUE
DEFAULT_SEARCH_SORT = C.SORT_UPDATED
DEFAULT_SEARCH_LIMIT = 10
MAX_SEARCH_LIMIT = 50
DEFAULT_COMMENTS = 10
MAX_COMMENTS = 30
BODY_LIMIT = 4000
COMMENT_LIMIT = 1500
REPO_DESCRIPTION_LIMIT = 120
ERROR_BODY_LIMIT = 200
QUERY_LIMIT = 200
LABEL_NAME_LIMIT = 50
SEARCH_LABEL_LIMIT = 5
CREATE_LABEL_LIMIT = 10
ISSUE_TITLE_LIMIT = 256
ISSUE_BODY_LIMIT = 20000
LABEL_HINT_LIMIT = 40
DUPLICATE_CHECK_LIMIT = 3


def load_settings() -> Settings:
    """Read process settings from environment variables, with configuration defaults.

    Returns:
        Credentials, endpoint URLs, token-cache path, and callback settings.
    """
    default_token = Path.home() / DEFAULT_TOKEN_PATH
    return Settings(
        client_id=os.environ.get(C.GITHUB_CLIENT_ID) or None,
        client_secret=os.environ.get(C.GITHUB_CLIENT_SECRET) or None,
        token_file=Path(os.environ.get(C.GH_MCP_TOKEN_FILE) or default_token).expanduser(),
        api_url=os.environ.get(C.GITHUB_API_URL, DEFAULT_API_URL).rstrip("/"),
        oauth_url=os.environ.get(C.GITHUB_OAUTH_URL, DEFAULT_OAUTH_URL).rstrip("/"),
        callback_port=int(os.environ.get(C.GH_MCP_CALLBACK_PORT, str(DEFAULT_CALLBACK_PORT))),
        callback_host=LOOPBACK_HOST,
    )
