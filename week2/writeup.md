# Week 2 Write-up

## Part I: The Server

**API chosen**, and why:
> I chose GitHub Issues through GitHub App OAuth for issue triage across my projects, with app permissions to limit access. The demo uses `gilad12-coder/issues-mcp-sandbox`.
>
**How to run it** (one command):
```sh
uv run --directory week2 python server.py
```
Run from the repo root.

| Tool | What it does | Read/Write | Composes with |
|---|---|---|---|
| `list_repos` | Lists accessible repositories | Read | `full_name` feeds every other tool's `repo` |
| `search_issues` | Searches a repository; returns issue summaries | Read | Takes `repo`; returns `number` for `get_issue` |
| `get_issue` | Reads an issue and recent comments | Read | Takes `repo` and `number` from search |
| `create_issue` | Previews by default; creates with `dry_run=false` | Write | Takes `repo` from `list_repos`; preview checks for duplicates |

## Part II: Agent Ergonomics

| Decision | Where | Why |
|---|---|---|
| Schema-level constraint | `server.py:96`, `server.py:389`, `server.py:531` | Repository pattern, state/sort enums, bounded lists, and nonblank titles reject invalid arguments before HTTP. Literal search phrases cannot inject extra repository qualifiers. |
| Output shaping (fields kept vs. dropped) | `server.py:197`, `server.py:266`, `server.py:120` | Keep `repo`, issue numbers, titles, state, labels, counts, and one URL; drop raw user objects and unused API fields to reduce token use. Clip bodies/comments with truncation flags; flag incomplete results so the agent knows when content is missing and avoids false conclusions. |
| Structured errors (retry vs. don't-retry) | `server.py:41`, `server.py:136`, `github.py:131`, `github.py:184` | `isError=true` returns JSON with `error`, `retryable`, and a hint or wait time. Invalid arguments or credentials need correction; temporary read failures can be retried. `write_outcome_unknown` means creation may have succeeded, so the agent must search and ask before trying again. |
| Docstring that chains tools together | `server.py:20`, `server.py:464` | Instructions pass `list_repos.full_name` to `repo`, then the search result's `number` to `get_issue`. Using returned identifiers prevents guesses about which repository or issue the user means. |
| Brake on the write tool | `server.py:531` | `dry_run=true` validates and previews without a POST; `next_step` asks for confirmation before `false`. Readers have `readOnlyHint=true`; creation is non-idempotent. The server relies on the client to obtain confirmation. |

**One thing you changed after watching the agent misuse a tool:**
> I asked, “Which of my sandbox issues have the most discussion? Show the top one's comments.” In the [before run](transcripts/04a-guessed-repo-before-fix.txt), the agent assumed I meant `gilad12-coder/modern-software-dev-assignments`, the coursework repository. It first ran `gh-axi issue list` outside the MCP server, then called `search_issues` twice against that same repo: once with `query="sandbox"`, then with an empty query. Both searches included open and closed issues and returned zero matches. Without calling `list_repos`, it concluded that my repo had no issues and asked whether I meant another repository.
>
> I changed the `repo` parameter description to tell the agent to call `list_repos` and match an informal name against each repository's `full_name` and `description`, rather than guessing from the current directory. I also added an empty-search hint directing it back to repository discovery when the user had not supplied an exact name (`server.py:96`, `server.py:389`).
>
> With the same prompt in the [after run](transcripts/04b-guessed-repo-after-fix.txt), the agent started with `list_repos({})` and found `gilad12-coder/issues-mcp-sandbox`. It searched that repo with `state="all"` and `sort="comments"`, found five issues, then called `get_issue` for #1 with `max_comments=10`. It correctly identified the CSV export bug as the most discussed issue, showed its two comments, and noted that the other four issues had none.

## Part III: OAuth

**Flow**: how a token is obtained, cached, and refreshed:
> `login.py` obtains an authorization code through browser login with PKCE and state validation, then exchanges it for tokens. Tokens are cached atomically with mode 0600 at `~/.config/github-issues-mcp/token.json`. The server refreshes near expiry without prompting, allows only one refresh at a time, and saves the new token pair. A premature 401 triggers one refresh and retry (`login.py:144`, `oauth.py:164`, `oauth.py:270`, `github.py:214`).

**Scopes requested**, and why each is necessary:
> GitHub App permissions (`setup_app.py:27`): **Issues read/write** for searching, reading, and creating issues; mandatory **Metadata read** for repository discovery. No other permissions are requested. The demo token could access nine repositories, including the sandbox.

**Secrets**: what's in env, what's gitignored:
> `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` come from env or `week2/.env`. Gitignored: `.env`, real root/week2 `.mcp.json`, `token.json`, and `*.token.json`. Tokens are cached outside the repo. Committed examples contain no credentials; other private repo names in transcripts are redacted.

**Token dies mid-session**: what the agent sees:
> A missing token cache, expired or invalid refresh credentials, or another 401 after refreshing returns `auth_required` with `retryable: false`. The agent should stop retrying and ask the user to run `uv run --directory week2 python login.py` in a terminal from the repo root. The user completes GitHub authorization in the browser; once the command saves the new tokens, the agent can repeat the original tool call. The tool itself never opens a browser.
>
> Missing or rejected app credentials return `not_configured`, also with `retryable: false`. The hint asks the user to correct `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` in `week2/.env` or the `env` block of `.mcp.json`. These must be matching credentials for the same GitHub App. The user then restarts the MCP server so it loads the corrected values, and the agent retries the tool. If the next error is `auth_required`, the user also completes the login step above; repeatedly calling the tool cannot repair either problem.
>
> Temporary token-endpoint failures return `network_error` with `retryable: true`, `retry_after_seconds`, and a hint to wait that long before retrying. The cached tokens are preserved, so the user does not need to delete the cache or log in again for this error.

## Part IV: Integration

**Registration config** (`.mcp.json.example`) and the client you used:
> Claude Code 2.1.287. Copy `week2/.mcp.json.example` to the repo root as `.mcp.json` and start the client there:

```json
{"mcpServers":{"github-issues":{"type":"stdio","command":"uv","args":["run","--directory","week2","python","server.py"]}}}
```

**End-to-end transcript**: the prompt, the tools that fired with their arguments, the result:

[Transcript 04b](transcripts/04b-guessed-repo-after-fix.txt) records this three-tool chain. The prompt and arguments below are copied from the recording; tool results are summarized.

```text
USER: Which of my sandbox issues have the most discussion? Show the top one's comments.

list_repos({})
  -> Found gilad12-coder/issues-mcp-sandbox among 9 accessible repositories.
search_issues({"repo": "gilad12-coder/issues-mcp-sandbox", "state": "all", "sort": "comments", "limit": 10})
  -> 5 issues; #1 had 2 comments, and the other four had none.
get_issue({"repo": "gilad12-coder/issues-mcp-sandbox", "number": 1, "max_comments": 10})
  -> Returned issue #1's body and both comments, with no comments omitted.
```

**Result:** The agent answered with the most discussed issue and its comments:

> Your sandbox repo has **5 issues total**. The most discussed is **#1 "CSV export crashes on rows with empty dates"** with 2 comments:
>
> **Issue #1** (open, labeled `bug`)
> > Exporting the weekly report to CSV throws `ValueError: time data '' does not match format` when any row has an empty `due_date`. Reproduce: create a task without a due date, then run `export --csv`.
>
> **Comments:**
>
> 1. **gilad12-coder** (2026-10-02 19:46:32)
>    > Same here. Also happens when `completed_at` is empty, so it's any optional date column.
>
> 2. **gilad12-coder** (2026-10-02 19:46:33)
>    > Looks like `parse_date` in export.py calls strptime without checking for empty strings.
>
> The other 4 issues have no comments yet.

[Transcript 01](transcripts/01-chain-and-file.txt) also records a write: the agent previewed a regression-test issue, then created issue #5 only after I said, “Looks good, file it.”

**A failure, handled**: what you provoked, what the agent saw, what it did next:

I backed up the token cache and replaced the cached access and refresh tokens with invalid values to simulate unusable authorization; I did not revoke the actual GitHub authorization. In [transcript 02](transcripts/02-revoked-token.txt), I then asked for the sandbox's open bugs. The agent started with `list_repos`, but GitHub rejected the invalid refresh token, so the server could not obtain a usable access token. It returned this structured error:

```text
USER: What are the open bugs in my issues-mcp-sandbox repo?
TOOL CALL: list_repos({"limit":100})
TOOL RESULT (isError=true):
{
  "error": "auth_required",
  "message": "GitHub authorization is missing or no longer valid (bad_refresh_token: The refresh token passed is incorrect or expired.).",
  "retryable": false,
  "hint": "Do not retry. Ask the user to run `uv run --directory week2 python login.py` in a terminal, then call the tool again."
}
```

`retryable: false` told the agent that repeating the call with the same credentials would not fix the problem. The `hint` gave it a specific recovery step to pass to me. It responded:

```text
I can't list your issues yet because the GitHub authorization for the
`github-issues` MCP server has expired (`bad_refresh_token`). This needs you to
act. In a terminal, run:

uv run --directory week2 python login.py

Tell me when it's done and I'll look up the open bugs in `issues-mcp-sandbox`.
```

The agent made only that one MCP call and waited for me to log in. It also identified that the startup `gh-axi` output showing zero issues belonged to the coursework repository, so it could not answer the sandbox question. The recording ends at this request for reauthorization; it does not show a completed login or resumed search. I restored the backed-up tokens afterward.

**Protocol-level test**: what it covers and how to run it:

**Coverage:** `tests/test_stdio.py` launches `server.py` as a subprocess and communicates over MCP stdio. Its three tests check:

- **Initialization and tool contracts:** workflow instructions, discovery of all four tools, read/write annotations, the default `dry_run=true`, and input/output schema fields.
- **Chained reads and errors:** `list_repos → search_issues → get_issue`, passing the returned `full_name` and issue `number` between calls; a missing issue returns `isError=true` with `error="not_found"`.
- **Write safety:** preview makes no issue-creation POST; repeating the call with `dry_run=false` creates an issue with exactly one POST containing the expected title, body, and labels.

The tests use fake GitHub/OAuth endpoints on localhost, so they need no real GitHub credentials or API calls.

**Run from the repo root:**

```sh
uv run --directory week2 pytest tests/test_stdio.py
```
