"""Independent fixtures and expected contract values for the Assignment 2 tests.

Do not import production values here: a server/config change must not silently
change what the tests expect.
"""

from pathlib import Path

KEY_ACCESS_TOKEN = "access_token"
KEY_ASSIGNEES = "assignees"
KEY_AUTH = "auth"
KEY_BODY = "body"
KEY_BODY_TRUNCATED = "body_truncated"
KEY_CLIENT_ID = "client_id"
KEY_CLIENT_SECRET = "client_secret"
KEY_CODE = "code"
KEY_CODE_CHALLENGE = "code_challenge"
KEY_CODE_CHALLENGE_METHOD = "code_challenge_method"
KEY_CODE_VERIFIER = "code_verifier"
KEY_COLOR = "color"
KEY_COMMENTS = "comments"
KEY_COMMENTS_OMITTED = "comments_omitted"
KEY_CREATED = "created"
KEY_CREATED_AT = "created_at"
KEY_DEFAULT = "default"
KEY_DESCRIPTION = "description"
KEY_DETAILS = "details"
KEY_DRY_RUN = "dry_run"
KEY_ENUM = "enum"
KEY_ERROR = "error"
KEY_ERROR_DESCRIPTION = "error_description"
KEY_ERRORS = "errors"
KEY_EXPIRES_AT = "expires_at"
KEY_EXPIRES_IN = "expires_in"
KEY_FORM = "form"
KEY_FULL_NAME = "full_name"
KEY_HAS_ISSUES = "has_issues"
KEY_HINT = "hint"
KEY_HTML_URL = "html_url"
KEY_ID = "id"
KEY_INCOMPLETE_RESULTS = "incomplete_results"
KEY_INSTALLATIONS = "installations"
KEY_ISSUE = "issue"
KEY_ITEMS = "items"
KEY_JSON = "json"
KEY_LABELS = "labels"
KEY_LIMIT = "limit"
KEY_LOCATION = "location"
KEY_LOGIN = "login"
KEY_MAX_COMMENTS = "max_comments"
KEY_MESSAGE = "message"
KEY_METHOD = "method"
KEY_MILESTONE = "milestone"
KEY_NAME = "name"
KEY_NEXT_STEP = "next_step"
KEY_NODE_ID = "node_id"
KEY_NOTE = "note"
KEY_NUMBER = "number"
KEY_OPEN_ISSUES_AND_PRS = "open_issues_and_prs"
KEY_OPEN_ISSUES_COUNT = "open_issues_count"
KEY_PAGE = "page"
KEY_PATH = "path"
KEY_PATTERN = "pattern"
KEY_PER_PAGE = "per_page"
KEY_PERMISSIONS = "permissions"
KEY_PRIVATE = "private"
KEY_PROPERTIES = "properties"
KEY_PUSH = "push"
KEY_PUSHED_AT = "pushed_at"
KEY_Q = "q"
KEY_QUERY = "query"
KEY_REACTIONS = "reactions"
KEY_RECENT_COMMENTS = "recent_comments"
KEY_REDIRECT_URI = "redirect_uri"
KEY_REFRESH_EXPIRES_AT = "refresh_expires_at"
KEY_REFRESH_TOKEN = "refresh_token"
KEY_REFRESH_TOKEN_EXPIRES_IN = "refresh_token_expires_in"
KEY_REPO = "repo"
KEY_REPOS = "repos"
KEY_REPOSITORIES = "repositories"
KEY_REPOSITORY_URL = "repository_url"
KEY_RETRY_AFTER_SECONDS = "retry_after_seconds"
KEY_RETRYABLE = "retryable"
KEY_SCOPE = "scope"
KEY_STATE = "state"
KEY_STATE_REASON = "state_reason"
KEY_TITLE = "title"
KEY_TOKEN_TYPE = "token_type"
KEY_TOTAL_ACCESSIBLE = "total_accessible"
KEY_TOTAL_COUNT = "total_count"
KEY_UPDATED_AT = "updated_at"
KEY_URL = "url"
KEY_USER = "user"
KEY_WARNINGS = "warnings"
ERROR_AUTH_REQUIRED = "auth_required"
ERROR_FORBIDDEN = "forbidden"
ERROR_INVALID_ARGUMENTS = "invalid_arguments"
ERROR_ISSUES_DISABLED = "issues_disabled"
ERROR_NETWORK_ERROR = "network_error"
ERROR_NOT_CONFIGURED = "not_configured"
ERROR_NOT_FOUND = "not_found"
ERROR_RATE_LIMITED = "rate_limited"
ERROR_REDIRECT_REQUIRED = "redirect_required"
ERROR_UNKNOWN_LABELS = "unknown_labels"
ERROR_UPSTREAM_ERROR = "upstream_error"
ERROR_WRITE_OUTCOME_UNKNOWN = "write_outcome_unknown"
GITHUB_CLIENT_ID = "GITHUB_CLIENT_ID"
GITHUB_CLIENT_SECRET = "GITHUB_CLIENT_SECRET"
GITHUB_API_URL = "GITHUB_API_URL"
GITHUB_OAUTH_URL = "GITHUB_OAUTH_URL"
GH_MCP_CALLBACK_PORT = "GH_MCP_CALLBACK_PORT"
GH_MCP_TOKEN_FILE = "GH_MCP_TOKEN_FILE"
TOOL_LIST_REPOS = "list_repos"
TOOL_SEARCH_ISSUES = "search_issues"
TOOL_GET_ISSUE = "get_issue"
TOOL_CREATE_ISSUE = "create_issue"
HTTP_GET = "GET"
HTTP_POST = "POST"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_CONTENT_LENGTH = "Content-Length"
HEADER_REQUEST_LENGTH = "content-length"
HEADER_AUTHORIZATION = "authorization"
HEADER_RETRY_AFTER = "retry-after"
HEADER_RATE_REMAINING = "x-ratelimit-remaining"
HEADER_RATE_RESET = "x-ratelimit-reset"
JSON_MEDIA_TYPE = "application/json"
STATE_OPEN = "open"
STATE_CLOSED = "closed"
STATE_ALL = "all"
INVALID_STATE = "opened"
SERIALIZED_FALSE = "false"
PKCE_METHOD = "S256"
OWNER = "alice"
REPO_NAME = "alice/demo"
OLD_REPO_NAME = "alice/old"
NEWEST_REPO_NAME = "alice/newest"
MISSING_REPO_NAME = "alice/nope"
RENAMED_REPO_NAME = "alice/renamed"
REPO_DESCRIPTION = "Demo repo"
REPO_PUSHED_AT = "2026-09-30T10:00:00Z"
OLD_REPO_PUSHED_AT = "2024-01-01T00:00:00Z"
ARCHIVE_PUSHED_AT = "2020-01-01T00:00:00Z"
ISSUE_CREATED_AT = "2026-09-01T00:00:00Z"
ISSUE_UPDATED_AT = "2026-09-02T00:00:00Z"
TRANSFERRED_COMMENT_AT = "2026-10-04T12:00:00Z"
ISSUE_TITLE = "Crash on empty input"
SHORT_TITLE = "Crash"
NEW_ISSUE_TITLE = "New bug"
BUG_TITLE = "Bug"
REGRESSION_TITLE = "Regression test"
TRANSFERRED_TITLE = "Transferred issue"
TRANSFERRED_COMMENT = "Moved too"
ISSUE_BODY = "Steps to reproduce..."
NEW_ISSUE_BODY = "details"
BUG_LABEL = "bug"
DOCS_LABEL = "docs"
STARTER_LABEL = "good first issue"
UNKNOWN_LABEL = "bugg"
LAST_LABEL = "last-label"
LABEL_COLOR = "d73a4a"
PLACEHOLDER_URL = "..."
ISSUE_NODE_ID = "I_xyz"
REACTION_THUMBS_UP = "+1"
VALID_ACCESS_TOKEN = "ghu_valid"
VALID_REFRESH_TOKEN = "ghr_valid"
ROTATED_ACCESS_TOKEN = "ghu_new1"
ROTATED_REFRESH_TOKEN = "ghr_new1"
UNKNOWN_ACCESS_TOKEN = "some-token-the-server-does-not-have"
REVOKED_ACCESS_TOKEN = "revoked-elsewhere"
STORED_ACCESS_TOKEN = "test-access"
STORED_REFRESH_TOKEN = "test-refresh"
CLIENT_ID = "Iv1.test"
CLIENT_SECRET = "test-secret"
CREATED_CLIENT_ID = "test-client"
AUTH_CODE = "code-123"
FORGED_STATE = "forged"
TOKEN_FILENAME = "token.json"
STALE_TOKEN_FILENAME = "token.tmp"
ENV_FILENAME = ".env"
TOKEN_EXPIRED_MESSAGE = "expired"
OAUTH_BAD_REFRESH = "bad_refresh_token"
OAUTH_BAD_CODE = "bad_verification_code"
OAUTH_BAD_CREDENTIALS = "incorrect_client_credentials"
OAUTH_INVALID_CLIENT = "invalid_client"
TOKEN_TYPE = "bearer"
LOOPBACK_HOST = "127.0.0.1"
UNREACHABLE_API_URL = "http://127.0.0.1:9"
REPO_WEB_URL = "https://github.com/alice/demo"
REPO_API_URL = "https://api.github.com/repos/alice/demo"
RENAMED_ISSUE_URL = "https://github.com/alice/renamed/issues/9"
MANIFEST_CONVERSION_URL = "https://api.github.com/app-manifests/test-code/conversions"
APP_WEB_URL = "https://github.com/apps/test-app"
INSTALLATIONS_PATH = "/user/installations"
INSTALLATION_REPOS_PATH = "/user/installations/1/repositories"
REPO_PATH = "/repos/alice/demo"
LABELS_PATH = "/repos/alice/demo/labels"
ISSUE_PATH = "/repos/alice/demo/issues/7"
COMMENTS_PATH = "/repos/alice/demo/issues/7/comments"
ISSUES_PATH = "/repos/alice/demo/issues"
SEARCH_ISSUES_PATH = "/search/issues"
RENAMED_ISSUE_PATH = "/repos/alice/renamed/issues/9"
RENAMED_ISSUES_PATH = "/repos/alice/renamed/issues"
COMMENTS_SUFFIX = "/comments"
ISSUES_SUFFIX = "/issues"
OAUTH_PATH_PREFIX = "/login/"
TOKEN_PATH = "/login/oauth/access_token"
USER_PATH = "/user"
SEARCH_QUERY = "crash"
SCOPE_QUERY = "crash OR repo:bob/other"
QUOTED_SCOPE_QUERY = 'crash" OR repo:bob/other'
QUOTED_SCOPE_LABEL = 'bug" OR repo:bob/other'
EXPECTED_LABEL_QUERY = 'repo:alice/demo is:issue in:title,body label:"good first issue" "crash"'
EXPECTED_SCOPE_QUERY = 'repo:alice/demo is:issue in:title,body state:open "crash OR repo:bob/other"'
NO_REPOS_PREFIX = "0 repositories"
DISCOVERY_HINT = "call list_repos"
DUPLICATE_WARNING = "Possible duplicate: #7"
COMMIT_HINT = "dry_run=false"
LOGIN_HINT = "login.py"
RESTART_HINT = "restart"
INCOMPLETE_NOTE = "incomplete"
STATE_MISMATCH_MESSAGE = "state mismatch"
MISSING_CODE_MESSAGE = "missing authorization code"
EXISTING_CREDENTIALS_MESSAGE = "already has credentials"
BAD_CREDENTIALS_MESSAGE = "Bad credentials"
NOT_FOUND_MESSAGE = "Not Found"
VALIDATION_MESSAGE = "Validation Failed"
UNSEARCHABLE_REPO_MESSAGE = (
    "The listed users and repositories cannot be searched either because the resources do not exist"
)
RATE_LIMIT_MESSAGE = "API rate limit exceeded"
FORBIDDEN_MESSAGE = "Resource not accessible"
UPSTREAM_ERROR_MESSAGE = "boom"
RESPONSE_LOST_MESSAGE = "response lost"
TOO_MANY_REQUESTS_MESSAGE = "too many requests"
INVALID_TOKEN_RESPONSE = "invalid token response"
SECONDARY_LIMIT_MESSAGE = "secondary rate limit"
SECONDARY_LIMIT_FULL_MESSAGE = "You have exceeded a secondary rate limit."
THROTTLE_MESSAGE = "slow down"
LOOKUP_FAILED_MESSAGE = "lookup failed"
MOVED_PERMANENTLY_MESSAGE = "Moved Permanently"
MOVED_MESSAGE = "Moved"
INVALID_DATE = "invalid-date"
CORRUPT_EXPIRY = "bad"
STALE_CACHE_CONTENT = "stale"
WHITESPACE_TITLE = "  "
PLACEHOLDER_TEXT = "x"
TIMEOUT_FAILURE = "timeout"
SERVER_FAILURE = "server_error"
FORM_STATE_PATTERN = r"new\?state=([^\"]+)"
SECOND_COMMENT = "c2"
THIRD_COMMENT = "c3"

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_COMMAND = "uv"
SERVER_ARGS = ["run", "--directory", "week2", "python", "server.py"]
READ_TOOLS = (TOOL_LIST_REPOS, TOOL_SEARCH_ISSUES, TOOL_GET_ISSUE)
ALL_TOOLS = {*READ_TOOLS, TOOL_CREATE_ISSUE}
ISSUE_STATES = [STATE_OPEN, STATE_CLOSED, STATE_ALL]
BEARER_PREFIX = "Bearer "
AUTO_PORT = 0
ISSUE_NUMBER = 7
CREATED_ISSUE_NUMBER = 42
TRANSFERRED_ISSUE_NUMBER = 9
MISSING_ISSUE_NUMBER = 999
NONINTEGER_ISSUE_NUMBER = 7.5
REPO_LIMIT_OVERFLOW = 101.0
PAGE_SIZE = 100
LONG_REPO_COUNT = 500
TOTAL_REPO_COUNT = LONG_REPO_COUNT + 1
SMALL_REPO_LIMIT = 5
CONCURRENT_CALLS = 5
OPEN_ISSUE_COUNT = 3
COMMENT_COUNT = 3
RECENT_COMMENT_LIMIT = 2
LONG_BODY_LENGTH = 5000
CLIPPED_BODY_LENGTH = 4001
VALID_ACCESS_SECONDS = 3600
VALID_REFRESH_SECONDS = 10**6
ISSUED_ACCESS_SECONDS = 28800
ISSUED_REFRESH_SECONDS = 15897600
EXPIRED_SECONDS = -10
JUST_EXPIRED_SECONDS = -1
STORED_ACCESS_EXPIRY = 123
STORED_REFRESH_EXPIRY = 456
CORRUPT_REFRESH_TOKEN = 123
RATE_LIMIT_WAIT = 42
RATE_LIMIT_WAIT_MIN = 40
NUMERIC_RETRY_WAIT = 7
FALLBACK_RETRY_WAIT = 60
DATE_RETRY_WAIT = 120
TRANSIENT_RETRY_WAIT = 5
BROWSER_REDIRECT_DELAY = 0.2
HTTP_TIMEOUT = 5
CALLBACK_TIMEOUT = 3
LISTENER_TIMEOUT = 1
SERVER_DEADLINE = 5
PUBLIC_FILE_MODE = 0o644
PRIVATE_FILE_MODE = 0o600
FILE_MODE_MASK = 0o777
CONTROL_CHARACTERS = ["\x7f", "\x85", "\x9f"]
ENV_TEMPLATE = "GITHUB_CLIENT_ID=\nGITHUB_CLIENT_SECRET=\nGH_MCP_CALLBACK_PORT={port}\n"
EXISTING_ENV = "GITHUB_CLIENT_SECRET = 'existing-test-secret'\n"
MANIFEST_CALLBACK = "{url}created?state={state}&code=test-code"
REPO_PAGE_NAME = "alice/repo-{number}"
LABEL_PAGE_NAME = "label-{number}"
COMMENT_AUTHOR = "u{number}"
COMMENT_DATE = "2026-09-0{number}T00:00:00Z"
COMMENT_BODY = "c{number}"
ROTATED_ACCESS_FORMAT = "ghu_new{serial}"
ROTATED_REFRESH_FORMAT = "ghr_new{serial}"

REPO = {
    KEY_FULL_NAME: REPO_NAME,
    KEY_DESCRIPTION: REPO_DESCRIPTION,
    KEY_PRIVATE: False,
    KEY_HAS_ISSUES: True,
    KEY_OPEN_ISSUES_COUNT: OPEN_ISSUE_COUNT,
    KEY_PUSHED_AT: REPO_PUSHED_AT,
    KEY_UPDATED_AT: REPO_PUSHED_AT,
    KEY_PERMISSIONS: {KEY_PUSH: True},
}
OLD_REPO = {**REPO, KEY_FULL_NAME: OLD_REPO_NAME, KEY_PUSHED_AT: OLD_REPO_PUSHED_AT}

EXPECTED_CHAIN_PATHS = [INSTALLATIONS_PATH, INSTALLATION_REPOS_PATH, SEARCH_ISSUES_PATH]
RENAMED_REPO_PATH = "/repos/alice/renamed"

DEFAULT_API_URL = "https://api.github.com"
DEFAULT_OAUTH_URL = "https://github.com"
DEFAULT_CALLBACK_PORT = 8765
DEFAULT_TOKEN_PATH = Path(".config") / "github-issues-mcp" / "token.json"
CUSTOM_CALLBACK_PORT = 9876
CUSTOM_TOKEN_PATH = "~/test-github-mcp/token.json"
CALLBACK_PATH = "/callback"
CONFIG_ENV_KEYS = (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    GITHUB_API_URL,
    GITHUB_OAUTH_URL,
    GH_MCP_TOKEN_FILE,
    GH_MCP_CALLBACK_PORT,
)
