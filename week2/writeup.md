# Week 2 Write-up

## Part I: The Server

**API chosen**, and why:
> GitHub Issues, through a GitHub App's user OAuth flow. I triage issues every day, so I know which fields matter when I'm deciding what to work on and which are noise (`node_id`, `reactions`, the dozen `*_url` fields). GitHub Apps also let me pin the permission surface down to one resource and a chosen set of repos, which plain OAuth apps can't do.
>
> The demo repo is a private sandbox, `gilad12-coder/issues-mcp-sandbox`, which I seeded with four issues and two comments so the write tool could file a real issue without notifying anyone.

**How to run it** (one command):
```
uv run --directory week2 python server.py
```
That starts the server on stdio from the repo root, and it's the same command `.mcp.json.example` registers. First-time setup is three commands, all run once:
```
uv run --directory week2 python setup_app.py   # creates the GitHub App from a manifest, writes week2/.env
# install the app on the repos it may touch (the script prints the link)
uv run --directory week2 python login.py       # browser login, caches the token outside the repo
```
Tests: `uv run --directory week2 pytest` (29 tests, about 18 seconds, no network or GitHub account needed).

| Tool | What it does | Read/Write | Composes with |
|---|---|---|---|
| `list_repos` | Lists repositories the app is installed on, with `full_name`, `has_issues` and the open count | Read | Its `full_name` is the `repo` argument of all three other tools |
| `search_issues` | Searches one repo by text, state, kind, labels; returns summaries without bodies | Read | Takes `repo` from `list_repos`; its `number` feeds `get_issue` |
| `get_issue` | Reads one issue: body (clipped at 4000 chars), labels, assignees, newest comments | Read | Takes `repo` + `number` from `search_issues` |
| `create_issue` | Files an issue. Defaults to `dry_run=true`, which validates and previews without writing | Write | Takes `repo` from `list_repos`; the dry run calls search to flag possible duplicates |


## Part II: Agent Ergonomics

For each, point at the code (`file:line`) and say what it buys.

| Decision | Where | Why |
|---|---|---|
| Schema-level constraint | `server.py:40-56` (`Repo` has a regex `pattern`, `IssueNumber` has `ge=1`), `server.py:332-338` (`state`, `kind`, `sort` are `Literal`s), `server.py:456-461` (title 1-256 chars, at most 10 labels) | Bad arguments are rejected by schema validation before any HTTP request goes out (`test_schema_rejects_bad_arguments_before_any_request` checks the fake GitHub saw zero calls). The enums show up as `enum` in the JSON schema, so the model sees the valid values instead of reading them from prose. Every constraint lives in the schema; the docstrings only say where values come from, so the two can't disagree. |
| Output shaping (fields kept vs. dropped) | `server.py:141-206` (output models), `server.py:209-261` (raw-to-model mapping), `server.py:64` (`_clip`) | Kept: number, title, state, `state_reason`, author login, label names, comment count, timestamps, one URL. Dropped: `node_id`, `reactions`, `user` objects, every `*_url` except `html_url`, `performed_via_github_app` and so on. Measured on the sandbox: `get_issue` #1 returns 1,033 bytes where the raw issue plus comments is 6,510; `search_issues` returns 1,757 where raw search is 16,102. Bodies and comments are clipped with a `body_truncated` flag, so the agent knows when it's missing text. Search returns no bodies at all, which pushes the agent to `get_issue` for the one it wants. |
| Structured errors (retry vs. don't-retry) | `github.py:122-172` (`failure_from_response`), `github.py:61` (`auth_failure`), `server.py:80-119` (`agent_errors`) | Every failure comes back as `isError=true` with JSON: `error` code, `message`, `retryable`, and where it helps `retry_after_seconds` and a `hint`. 404, 403, 422 and `auth_required` set `retryable: false`; rate limits (403/429 with the rate-limit headers or `Retry-After`), 5xx and network errors set `retryable: true` with a wait. Unexpected exceptions become `internal_error` with no traceback (`mask_error_details=True` at `server.py:38`). A 422 from search on an inaccessible repo is turned into `not_found` with a hint to call `list_repos` (`server.py:368-374`), because GitHub's own message ("cannot be searched") doesn't tell the agent what to do. |
| Docstring that chains tools together | `server.py:19-36` (`FastMCP(instructions=...)`), `server.py:275` ("Start here"), `server.py:398` ("Get `number` from search_issues; do not guess it"), `server.py:44-48` (`repo` field description) | The instructions give the four-step workflow once. Each tool docstring then names the tool its inputs come from, and the `repo` description says it must be copied from a `list_repos` `full_name`. In every Claude Code run I recorded after the fix in the next answer, the agent called the tools in the documented order. |
| Brake on the write tool | `server.py:462-465` (`dry_run` defaults to `True`), `server.py:467-472` (docstring), `server.py:444-452` (annotations), `server.py:547-550` (`next_step`) | `create_issue` previews unless `dry_run=false` is passed explicitly. The dry run checks the repo accepts issues and that every label exists, warns that GitHub drops labels silently without push access, and searches for open issues with a similar title. Its `next_step` field tells the agent to show the preview and only re-call after the user agrees. The three readers carry `readOnlyHint: true`; `create_issue` carries `readOnlyHint: false, idempotentHint: false`, so a client can require confirmation for it. In transcript 01, Sonnet stopped at the preview and filed only after "Looks good, file it." |

**One thing you changed after watching the agent misuse a tool:**
> I ran Claude Code with Haiku on a loose prompt: "Which of my sandbox issues have the most discussion? Show the top one's comments." In 3 of 4 runs it never called `list_repos`. It assumed "my repo" meant the git checkout it was running in (`gilad12-coder/modern-software-dev-assignments`) and passed that straight to `search_issues`. That repo has issues turned off, so search came back `{"total_count":0,"items":[]}` and the agent told me I had no issues (`transcripts/04a-guessed-repo-before-fix.txt`). Nothing in the response hinted that the repo itself might be wrong.
>
> I changed two things. The `repo` field description now says not to guess it from the current directory or an informal name, and to match the user's words against `list_repos` (`server.py:44-48`, plus a sentence in the instructions at `server.py:25-27`). And an empty search result now carries a `note` saying that if the user didn't give this exact name, it should call `list_repos` (`server.py:376-383`, tested by `test_empty_search_points_at_list_repos`). With the same prompt and model, 4 of 4 runs then went `list_repos`, `search_issues` on the sandbox sorted by comments, then `get_issue` #1 (`transcripts/04b-guessed-repo-after-fix.txt`). Four runs per side is a small sample, but the before-fix failures all broke the same way.


## Part III: OAuth

**Flow**: how a token is obtained, cached, and refreshed:
> I use a GitHub App with "expire user authorization tokens" on, so access tokens last 8 hours and come with a 6-month refresh token.
>
> Getting the first token happens once, outside the server, in `login.py`. It generates a PKCE verifier and S256 challenge (`login.py:23`) and a random `state`. It opens the browser to `/login/oauth/authorize` and listens on `127.0.0.1:8765/callback` for one request, rejecting it if `state` doesn't match (`login.py:85`). Then it exchanges the code with the client secret and PKCE verifier (`login.py:152`, `oauth.py:161`).
>
> The token is cached in `~/.config/github-issues-mcp/token.json`, outside the repo, written atomically with mode 0600 (`oauth.py:147-158`).
>
> Refresh happens inside the server. `TokenManager.access_token` (`oauth.py:214`) returns the cached token if it has more than 120 seconds left (`oauth.py:24`, `oauth.py:272`). Otherwise it trades the refresh token for a new pair and saves both. GitHub refresh tokens are single-use, so refresh is serialized with an asyncio lock and an `flock` on a sidecar file (`oauth.py:243-254`). Without that, two concurrent tool calls, or two Claude sessions sharing the cache, could each spend the same refresh token, leaving one with a dead token (`test_concurrent_calls_refresh_only_once`). If GitHub answers 401 to a token that hasn't expired yet, which happens when it's been revoked or rotated elsewhere, the client refreshes once and retries the request once (`github.py:217-222`).
>
> I checked silent refresh against real GitHub, not only the fake. I set `expires_at` in the cache to a minute ago and called `search_issues` over stdio. The call succeeded, and the cache then held a new access token and a new refresh token (different SHA-256 prefixes than before), expiring in 28,799 seconds, still mode 0600.

**Scopes requested**, and why each is necessary:
> GitHub Apps don't use OAuth scopes. A user token can do the intersection of what the user can do and the app's fine-grained permissions, limited to the repos the app is installed on. The app manifest (`setup_app.py:44`) asks for exactly two permissions:
>
> - Issues, read and write. Read covers `search_issues` and `get_issue`; write is needed only for `create_issue`. GitHub has no create-only level, and there's no way to drop write without losing the write tool.
> - Metadata, read. GitHub makes this mandatory for every app. It's what `list_repos` (`/user/installations/{id}/repositories`) and the `has_issues` check in `create_issue` read.
>
> Nothing else: no Contents, Pull requests, Administration or account permissions, and no webhook (`"active": False`). The token can't read code or touch PRs even where the user could. The installation step narrows it further to chosen repositories.

**Secrets**: what's in env, what's gitignored:
> `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` come from the environment, loaded from `week2/.env` by `python-dotenv` (`oauth.py:21`). They can also go in the `env` block of a real `.mcp.json`. `setup_app.py` writes `.env` with mode 0600, and the app's private key, which the manifest flow also returns, is discarded because the user-token flow never needs it.
>
> Gitignored: `week2/.env`, `week2/.mcp.json`, `/.mcp.json` at the repo root, `token.json` and `*.token.json`. The token cache lives in `~/.config` anyway. Committed instead: `.env.example` with empty values, and `.mcp.json.example` with no secrets in it.
>
> I checked the committed tree for `ghu_`, `ghr_`, the client secret's value and the token file path before pushing. The transcripts in `week2/transcripts/` were also scanned for tokens and local paths, and the names of my other (private) repositories were replaced with a "redacted" marker.

**Token dies mid-session**: what the agent sees:
> The server never opens a browser. `TokenManager` only refreshes (`oauth.py:215`), and `webbrowser` is imported only by `login.py`. When there's no cache, the refresh token has expired, GitHub rejects the refresh, or a refreshed token still gets a 401, the tool returns:
>
> ```json
> {"error": "auth_required", "message": "GitHub authorization is missing or no longer valid (bad_refresh_token: The refresh token passed is incorrect or expired.).", "retryable": false, "hint": "Do not retry. Ask the user to run `uv run --directory week2 python login.py` in a terminal, then call the tool again."}
> ```
>
> That's real output from the provoked failure below. A network failure while reaching the token endpoint is different. It returns `network_error` with `retryable: true`, because the token may be fine.


## Part IV: Integration

**Registration config** (`.mcp.json.example`) and the client you used:
> Client: Claude Code 2.1.287. `week2/.mcp.json.example`:
>
> ```json
> {"mcpServers": {"github-issues": {"type": "stdio", "command": "uv",
>   "args": ["run", "--directory", "week2", "python", "server.py"]}}}
> ```
>
> To use it, copy it to `.mcp.json` at the repo root (gitignored) and start Claude Code there. The recorded runs used `claude -p ... --mcp-config .mcp.json --strict-mcp-config --allowedTools "mcp__github-issues__*"`, so only this server was loaded. Credentials come from `week2/.env`, so the config file holds no secrets.

**End-to-end transcript**: the prompt, the tools that fired with their arguments, the result:
```
USER: In my issues-mcp-sandbox repo there's an open bug about the CSV export. Find it,
read it including the comments, and tell me the likely root cause in two sentences. Then
draft a follow-up issue asking for a regression test for that bug, labeled bug. Show me
the preview; don't file it yet.

TOOL CALL  list_repos({})
  -> {"repos":[{"full_name":"gilad12-coder/issues-mcp-sandbox","private":true,
     "has_issues":true,"open_issues_and_prs":4,...}, ...],"total_accessible":9}
TOOL CALL  search_issues({"repo": "gilad12-coder/issues-mcp-sandbox", "query": "CSV"})
  -> {"total_count":2,"items":[{"number":1,"title":"CSV export crashes on rows with
     empty dates","labels":["bug"],"comments":2,...}, {"number":3,...}]}
TOOL CALL  get_issue({"repo": "gilad12-coder/issues-mcp-sandbox", "number": 1})
  -> {"number":1,"body":"Exporting the weekly report to CSV throws `ValueError: time
     data '' does not match format` when any row has an empty `due_date`...",
     "recent_comments":[{"body":"Same here. Also happens when `completed_at` is
     empty..."},{"body":"Looks like `parse_date` in export.py calls strptime without
     checking for empty strings."}],"comments_omitted":0,...}
TOOL CALL  create_issue({"repo": "gilad12-coder/issues-mcp-sandbox", "title": "Add
  regression test for CSV export with empty optional date fields", "body": "Follow-up
  to #1. ...", "labels": ["bug"], "dry_run": true})
  -> {"dry_run":true,"created":false,"preview":{...},"warnings":[],"next_step":"Nothing
     was created. Show this preview (and any warnings) to the user. If they confirm,
     call create_issue again with the same arguments and dry_run=false."}

ASSISTANT: The bug is issue #1 ... Likely root cause: `parse_date` in `export.py` passes
empty strings straight to `strptime` ... [shows the draft] The dry run came back with
no warnings, and the `bug` label exists in the repo.

USER: Looks good, file it.

TOOL CALL  create_issue({... same arguments ..., "dry_run": false})
  -> {"dry_run":false,"created":true,"issue":{"number":5,"labels":["bug"],"url":
     "https://github.com/gilad12-coder/issues-mcp-sandbox/issues/5",...},
     "next_step":"Created .../issues/5. Do not call create_issue again for this issue."}

ASSISTANT: I filed it as issue #5, labeled `bug`:
https://github.com/gilad12-coder/issues-mcp-sandbox/issues/5
```
That's four tools chained, with each output feeding the next call's arguments and the write held at the preview until I confirmed. The full, unabridged transcript is `week2/transcripts/01-chain-and-file.txt`. Sonnet ran it; the only edits are the redacted names of my other repositories in the `list_repos` result.

**A failure, handled**: what you provoked, what the agent saw, what it did next:
```
Provoked: a revoked token mid-session. I backed up the token cache, replaced the access
and refresh tokens with invalid ones, ran Claude Code, then restored the backup.

USER: What are the open bugs in my issues-mcp-sandbox repo?

TOOL CALL  list_repos({"limit": 100})
  [server: GitHub 401 on the access token -> one refresh attempt -> GitHub answers
   bad_refresh_token -> AuthRequired; no browser opened]
TOOL RESULT (isError=True)  {"error": "auth_required", "message": "GitHub authorization
  is missing or no longer valid (bad_refresh_token: The refresh token passed is incorrect
  or expired.).", "retryable": false, "hint": "Do not retry. Ask the user to run `uv run
  --directory week2 python login.py` in a terminal, then call the tool again."}

ASSISTANT: I can't list your issues yet because the GitHub authorization for the
`github-issues` MCP server has expired (`bad_refresh_token`). This needs you to act.
In a terminal, run:
    uv run --directory week2 python login.py
Tell me when it's done and I'll look up the open bugs in `issues-mcp-sandbox`.
```
The agent made exactly one tool call, didn't retry, and passed the fix to me word for word (`transcripts/02-revoked-token.txt`).

I recorded a second, agent-recoverable failure in `transcripts/03-unknown-label.txt`. Haiku was asked for an issue "labeled performance", but the sandbox's label is `perf`. The dry run returned `unknown_labels` with `retryable: false` and the hint "Use only existing labels: bug, documentation, perf". The very next call used `["perf"]` and the preview succeeded. So the agent fixed its arguments instead of repeating the same call, which is what the `retryable` flag is for.

**Protocol-level test**: what it covers and how to run it:
> `week2/tests/test_stdio.py` spawns the server as a subprocess with the documented command (`uv run --directory week2 python server.py`) and talks to it over the real stdio transport with FastMCP's `Client`:
>
> - `test_stdio_handshake_exposes_contract` checks the `initialize` handshake carries the instructions, `tools/list` returns exactly the four tools, the readers have `readOnlyHint: true`, `create_issue` has `readOnlyHint: false`, `dry_run` defaults to `true`, `state` is an enum, `repo` has a pattern, and an output schema is published.
> - `test_stdio_chain_and_error` runs `list_repos`, `search_issues` and `get_issue` as a chain, feeding each result into the next call. It then asks for issue 999 and checks the result is `isError` with `"error": "not_found"`.
>
> GitHub is replaced by a local fake HTTP server (`tests/conftest.py`), pointed to through `GITHUB_API_URL` and `GITHUB_OAUTH_URL`, so nothing touches the network. The other 25 tests in `test_tools.py` also go through MCP `tools/call` messages, using an in-process client rather than a subprocess. They cover every error class, refresh, rotation, the 401-retry path, concurrent refresh, and the dry run. `test_login.py` drives the login callback, including a forged `state`.
>
> Run: `uv run --directory week2 pytest` (or `pytest tests/test_stdio.py` for just the protocol tests).


## Submission
1. `Command (⌘) + F` for `TODO`. No results means you're done.
2. Confirm no tokens, client secrets, cached token file, or real `.mcp.json` are committed.
3. Push all changes to your remote repository and submit via Gradescope.
4. Clean up (optional): remove the server from your agent config, delete your cached token, and revoke the OAuth app's access.
