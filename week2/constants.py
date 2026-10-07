"""Fixed MCP/GitHub protocol names, paths, validation rules, and safety invariants.

Adjust deployment settings, timeouts, and response limits in ``config.py``.
"""

from typing import Literal

KEY_ACCESS_TOKEN = "access_token"
KEY_ASSIGNEES = "assignees"
KEY_BODY = "body"
KEY_CALLBACK_URLS = "callback_urls"
KEY_CLIENT_ID = "client_id"
KEY_CLIENT_SECRET = "client_secret"
KEY_CODE = "code"
KEY_CODE_CHALLENGE = "code_challenge"
KEY_CODE_CHALLENGE_METHOD = "code_challenge_method"
KEY_CODE_VERIFIER = "code_verifier"
KEY_COMMENTS = "comments"
KEY_CREATED_AT = "created_at"
KEY_DEFAULT_EVENTS = "default_events"
KEY_DEFAULT_PERMISSIONS = "default_permissions"
KEY_DESCRIPTION = "description"
KEY_DETAILS = "details"
KEY_ERROR = "error"
KEY_ERROR_DESCRIPTION = "error_description"
KEY_ERRORS = "errors"
KEY_EXPIRES_IN = "expires_in"
KEY_FIELD = "field"
KEY_FULL_NAME = "full_name"
KEY_GRANT_TYPE = "grant_type"
KEY_HAS_ISSUES = "has_issues"
KEY_HINT = "hint"
KEY_HOOK_ATTRIBUTES = "hook_attributes"
KEY_HTML_URL = "html_url"
KEY_ID = "id"
KEY_INCOMPLETE_RESULTS = "incomplete_results"
KEY_INSTALLATIONS = "installations"
KEY_ITEMS = "items"
KEY_LABELS = "labels"
KEY_LOC = "loc"
KEY_LOGIN = "login"
KEY_MESSAGE = "message"
KEY_MILESTONE = "milestone"
KEY_MSG = "msg"
KEY_NAME = "name"
KEY_NUMBER = "number"
KEY_OPEN_ISSUES_COUNT = "open_issues_count"
KEY_PER_PAGE = "per_page"
KEY_PERMISSIONS = "permissions"
KEY_PRIVATE = "private"
KEY_PUBLIC = "public"
KEY_PULL_REQUEST = "pull_request"
KEY_PUSH = "push"
KEY_PUSHED_AT = "pushed_at"
KEY_Q = "q"
KEY_REDIRECT_URI = "redirect_uri"
KEY_REDIRECT_URL = "redirect_url"
KEY_REFRESH_TOKEN = "refresh_token"
KEY_REFRESH_TOKEN_EXPIRES_IN = "refresh_token_expires_in"
KEY_REPOSITORIES = "repositories"
KEY_REPOSITORY_URL = "repository_url"
KEY_RETRY_AFTER_SECONDS = "retry_after_seconds"
KEY_RETRYABLE = "retryable"
KEY_STATE = "state"
KEY_STATE_REASON = "state_reason"
KEY_TITLE = "title"
KEY_TOTAL_COUNT = "total_count"
KEY_UPDATED_AT = "updated_at"
KEY_URL = "url"
KEY_USER = "user"

ERROR_AUTH_REQUIRED = "auth_required"
ERROR_FORBIDDEN = "forbidden"
ERROR_GONE = "gone"
ERROR_HTTP_ERROR = "http_error"
ERROR_INTERNAL_ERROR = "internal_error"
ERROR_INVALID_ARGUMENTS = "invalid_arguments"
ERROR_INVALID_REQUEST = "invalid_request"
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
GH_MCP_TOKEN_FILE = "GH_MCP_TOKEN_FILE"
GH_MCP_CALLBACK_PORT = "GH_MCP_CALLBACK_PORT"

SERVER_NAME = "github-issues"
LOGIN_COMMAND = "uv run --directory week2 python login.py"
HTTP_GET = "GET"
HTTP_POST = "POST"
HTTP_HEAD = "HEAD"
HEADER_ACCEPT = "Accept"
HEADER_AUTHORIZATION = "Authorization"
HEADER_CONTENT_TYPE = "Content-Type"
HEADER_API_VERSION = "X-GitHub-Api-Version"
HEADER_RETRY_AFTER = "retry-after"
HEADER_RATE_REMAINING = "x-ratelimit-remaining"
HEADER_RATE_RESET = "x-ratelimit-reset"
JSON_MEDIA_TYPE = "application/json"
GITHUB_MEDIA_TYPE = "application/vnd.github+json"
TEXT_MEDIA_TYPE = "text/plain; charset=utf-8"
HTML_MEDIA_TYPE = "text/html; charset=utf-8"
GITHUB_API_VERSION = "2022-11-28"
BEARER_PREFIX = "Bearer "
STATE_OPEN = "open"
STATE_ALL = "all"
KIND_ISSUE = "issue"
SORT_PUSHED = "pushed"
SORT_UPDATED = "updated"
SORT_BEST_MATCH = "best_match"
SORT_DESCENDING = "desc"
REPO_PATTERN = r"^[A-Za-z0-9-]{1,39}/[A-Za-z0-9._-]{1,100}$"
SEARCH_TEXT_PATTERN = r'^[^"\\\x00-\x1f\x7f-\x9f]*$'
NONBLANK_PATTERN = r"\S"
REPO_EXAMPLE = "octocat/hello-world"
TRUNCATION_MARKER = "…"
PKCE_METHOD = "S256"
TOKEN_LOCK_SUFFIX = ".lock"
RATE_LIMIT_EXHAUSTED = "0"
SECONDARY_RATE_LIMIT_MARKER = "secondary rate limit"
UNSEARCHABLE_REPO_MARKER = "cannot be searched"
OAUTH_TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
OAUTH_SERVER_ERROR = "server_error"
OAUTH_BAD_CREDENTIALS = "incorrect_client_credentials"
OAUTH_INVALID_CLIENT = "invalid_client"
SEARCH_ISSUES_QUALIFIER = "is:issue"
SEARCH_PRS_QUALIFIER = "is:pr"
SEARCH_TEXT_QUALIFIER = "in:title,body"
INSTALLATIONS_PATH = "/user/installations"
SEARCH_ISSUES_PATH = "/search/issues"
USER_PATH = "/user"
OAUTH_TOKEN_PATH = "/login/oauth/access_token"
OAUTH_AUTHORIZE_PATH = "/login/oauth/authorize"
OAUTH_CALLBACK_PATH = "/callback"
APP_CALLBACK_PATH = "/created"
APP_CREATE_PATH = "/settings/apps/new"
INSTALLATION_REPOS_PATH = "/user/installations/{installation_id}/repositories"
REPO_PATH = "/repos/{repo}"
LABELS_PATH = "/repos/{repo}/labels"
ISSUES_PATH = "/repos/{repo}/issues"
ISSUE_PATH = "/repos/{repo}/issues/{number}"
COMMENTS_PATH = "/repos/{repo}/issues/{number}/comments"
MANIFEST_CONVERSION_PATH = "/app-manifests/{code}/conversions"
APP_INSTALL_PATH = "/installations/new"

PRIVATE_DIRECTORY_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
PKCE_ENTROPY_BYTES = 64
PKCE_VERIFIER_LENGTH = 96
LOGIN_STATE_BYTES = 32
APP_STATE_BYTES = 16
APP_NAME_RANDOM_BYTES = 3
FIRST_PAGE = 1
MIN_ISSUE_NUMBER = 1
MIN_TEXT_LENGTH = 1
MIN_RESULT_LIMIT = 1
MIN_COMMENTS = 0
REPOSITORY_URL_SEGMENTS = 2

IssueStatus = Literal["open", "closed"]
IssueState = Literal["open", "closed", "all"]
IssueKind = Literal["issue", "pull_request"]
RepoSort = Literal["pushed", "updated", "full_name"]
IssueSort = Literal["updated", "created", "comments", "best_match"]

READ_ONLY_ANNOTATIONS = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True}
CREATE_ANNOTATIONS = {
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": True,
}
APP_PERMISSIONS = {"issues": "write", "metadata": "read"}
DISABLED_WEBHOOK = {"url": "https://example.invalid/unused", "active": False}
REPO_SORT_FIELDS = {
    SORT_PUSHED: KEY_PUSHED_AT,
    SORT_UPDATED: KEY_UPDATED_AT,
    KEY_FULL_NAME: KEY_FULL_NAME,
}

INSTRUCTIONS = """\
Tools for reading and filing GitHub issues in repositories the user has installed this
server's GitHub App on.

Workflow:
1. list_repos gives `full_name` ("owner/name") values for installed repositories,
   up to its `limit`. Check `total_accessible` and `note` for omitted repositories.
   Every other tool takes that exact string as `repo`. When the user names a repository
   loosely ("my sandbox repo"), call list_repos first instead of assuming the current
   directory's repository.
2. search_issues(repo=...) finds issues and returns their `number`s.
3. get_issue(repo, number) reads its body and recent comments, with explicit truncation flags.
4. create_issue files a new issue. It defaults to dry_run=true and only previews.
   Show the preview to the user and call again with dry_run=false only after they agree.

Errors come back as JSON with an `error` code and a `retryable` flag. If retryable is
false, do not repeat the same call: follow the `hint`. auth_required always needs the
user to act; tell them the command in the hint instead of retrying.
"""

INVALID_ARGUMENTS_MESSAGE = "Arguments do not match this tool's schema."
INVALID_ARGUMENTS_HINT = "Correct the indicated fields using the published schema, then call again."
REPO_DESCRIPTION = 'Repository as "owner/name", copied from a list_repos `full_name`. Do not guess it from the current directory or an informal name like "my sandbox repo": call list_repos and match the user\'s words against `full_name` and `description`.'
ISSUE_NUMBER_DESCRIPTION = "Issue number (the `number` field from search_issues), not its URL."
INTERNAL_ERROR_HINT = "This is a bug in the server, not in your arguments. Tell the user."
FULL_NAME_DESCRIPTION = "Pass this as `repo` to the other tools."
HAS_ISSUES_DESCRIPTION = "False means create_issue will fail for this repo."
OPEN_ISSUES_DESCRIPTION = "GitHub counts open pull requests here too."
STATE_REASON_DESCRIPTION = "completed, not_planned, reopened, or null."
TOTAL_COUNT_DESCRIPTION = "Matches on GitHub; `items` holds at most `limit`."
INCOMPLETE_DESCRIPTION = "GitHub returned only partial search results."
RECENT_COMMENTS_DESCRIPTION = "The newest comments, oldest first."
COMMENTS_OMITTED_DESCRIPTION = "Older comments not included."
LIST_REPOS_TITLE = "List accessible repositories"
SEARCH_ISSUES_TITLE = "Search issues in a repository"
GET_ISSUE_TITLE = "Read one issue with comments"
CREATE_ISSUE_TITLE = "File a new issue (dry run by default)"
NO_REPOS_NOTE = "0 repositories. The user has not installed the GitHub App on any repository; ask them to install it from the app's GitHub page."
SEARCH_QUERY_DESCRIPTION = "Literal phrase in titles and bodies, not GitHub search syntax. No double quotes, backslashes or control characters. Empty matches everything."
SEARCH_LABELS_DESCRIPTION = (
    "Every label must match (AND). No double quotes, backslashes or control characters."
)
INCOMPLETE_SEARCH_NOTE = "GitHub returned incomplete search results. Narrow the query and try again before drawing conclusions."
MAX_COMMENTS_DESCRIPTION = "How many of the newest comments to include."
BODY_DESCRIPTION = "Markdown."
CREATE_LABELS_DESCRIPTION = "Must already exist in the repo; unknown labels fail."
DRY_RUN_DESCRIPTION = "true (default) only previews. false creates the issue for real."
ISSUES_DISABLED_HINT = "Pick another repository from list_repos, or ask the user to enable issues."
LABEL_HINT_PREFIX = "Use only existing labels: "
LABELS_DROPPED_WARNING = "GitHub dropped the labels: the user lacks push access to this repo."
LABELS_WILL_DROP_WARNING = "You lack push access here, so GitHub will silently drop the labels."
INCOMPLETE_DUPLICATES_WARNING = (
    "Duplicate search was incomplete; check for existing issues before filing."
)
PREVIEW_NEXT_STEP = "Nothing was created. Show this preview (and any warnings) to the user. If they confirm, call create_issue again with the same arguments and dry_run=false."
FORBIDDEN_HINT = "The GitHub App is probably not installed on this repository, or lacks the permission. Call list_repos to see which repositories this server can use."
INVALID_REQUEST_HINT = (
    "Fix the arguments using the details above; retrying unchanged will fail again."
)
UPSTREAM_ERROR_HINT = "Transient GitHub failure. Retry once after a short wait."
UNKNOWN_WRITE_MESSAGE = "GitHub may have created the issue, but its confirmation was lost."
UNKNOWN_WRITE_HINT = "Do not repeat create_issue. Use search_issues with the same repo and a short phrase from the title to check for an existing issue; ask the user before any retry."
REJECTED_REFRESH_MESSAGE = "GitHub rejected the refreshed token"
NOT_CONFIGURED_HINT = "Do not retry. Ask the user to correct GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in week2/.env or the env block of .mcp.json, then restart the MCP server."
REDIRECT_HINT = "Call list_repos to find the current repository name. For a write, confirm the destination with the user before trying again."
NETWORK_TIMEOUT_MESSAGE = "GitHub did not respond in time."
OAUTH_RATE_LIMIT_MESSAGE = "GitHub's token endpoint is rate limited; the cached token was kept."
OAUTH_INVALID_JSON_MESSAGE = "GitHub's token endpoint returned invalid JSON."
OAUTH_UNEXPECTED_RESPONSE_MESSAGE = "GitHub's token endpoint returned an unexpected response."
OAUTH_UNAVAILABLE_MESSAGE = "GitHub's token endpoint is temporarily unavailable."
OAUTH_REJECTED_CREDENTIALS_MESSAGE = "GitHub rejected GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET; correct them in week2/.env or the env block of .mcp.json."
OAUTH_NO_ACCESS_MESSAGE = "GitHub's token endpoint returned no access token."
OAUTH_NO_REFRESH_MESSAGE = "GitHub returned a token without a refresh token. Enable 'Expire user authorization tokens' in the GitHub App settings."
OAUTH_INCOMPLETE_TOKEN_MESSAGE = "GitHub's token endpoint returned incomplete token data."
MISSING_CREDENTIALS_MESSAGE = "GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET are not set"
NO_TOKEN_MESSAGE = "no cached token"
REFRESH_EXPIRED_MESSAGE = "the refresh token expired (they last 6 months)"
LOGIN_MISSING_CREDENTIALS = (
    "Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET (env or week2/.env) first."
)
STATE_MISMATCH_MESSAGE = "state mismatch (possible CSRF); start the login again"
MISSING_CODE_MESSAGE = "missing authorization code; start the login again"
AUTHORIZATION_RECEIVED_MESSAGE = "Authorization received. Return to the terminal to finish login."
BROWSER_TIMEOUT_MESSAGE = "timed out waiting for the browser"
APP_CREATED_MESSAGE = "App created. Return to the terminal."
SEARCH_REPO_TEMPLATE = "repo:{repo}"
SEARCH_STATE_TEMPLATE = "state:{state}"
SEARCH_LABEL_TEMPLATE = 'label:"{label}"'
SEARCH_PHRASE_TEMPLATE = '"{phrase}"'
DUPLICATE_QUERY_TEMPLATE = 'repo:{repo} is:issue state:open in:title "{phrase}"'
