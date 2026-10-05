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
| `create_issue` | Previews by default; creates with `dry_run=false` | Write | Takes `repo`; searches for duplicates before creation |

## Part II: Agent Ergonomics

| Decision | Where | Why |
|---|---|---|
| Schema-level constraint | `server.py:96`, `server.py:389`, `server.py:531` | Repository pattern, state/sort enums, bounded lists, and nonblank titles reject invalid arguments before HTTP. Literal search phrases cannot inject extra repository qualifiers. |
| Output shaping (fields kept vs. dropped) | `server.py:197`, `server.py:266`, `server.py:120` | Keep `repo`, issue numbers, titles, state, labels, counts, and one URL; drop raw user objects and unused API fields. Clip bodies/comments with truncation flags; flag incomplete results to avoid false conclusions. |
| Structured errors (retry vs. don't-retry) | `server.py:41`, `server.py:136`, `github.py:131`, `github.py:184` | `isError=true` returns JSON with `error`, `retryable`, and a hint or wait time. Invalid arguments or credentials need correction; temporary read failures can be retried. `write_outcome_unknown` means creation may have succeeded, so the agent must search and ask before trying again. |
| Docstring that chains tools together | `server.py:20`, `server.py:464` | Instructions pass `list_repos.full_name` to `repo`, then the search result's `number` to `get_issue`, and prohibit guessing the repo from the checkout. |
| Brake on the write tool | `server.py:531` | `dry_run=true` validates and previews without a POST; `next_step` asks for confirmation before `false`. Readers have `readOnlyHint=true`; creation is non-idempotent. The server relies on the client to obtain confirmation. |

**One thing you changed after watching the agent misuse a tool:**
> I asked, “Which of my sandbox issues have the most discussion? Show the top one's comments.” In the [before run](transcripts/04a-guessed-repo-before-fix.txt), the agent assumed I meant `gilad12-coder/modern-software-dev-assignments`, the coursework repository. It first ran `gh-axi issue list` outside the MCP server, then called `search_issues` twice against that same repo: once with `query="sandbox"`, then with an empty query. Both searches included open and closed issues and returned zero matches. Without calling `list_repos`, it concluded that my repo had no issues and asked whether I meant another repository.
>
> I changed the `repo` parameter description to tell the agent to call `list_repos` and match an informal name against each repository's `full_name` and `description`, rather than guessing from the current directory. I also added an empty-search hint directing it back to repository discovery when the user had not supplied an exact name (`server.py:96`, `server.py:389`).
>
> With the same prompt in the [after run](transcripts/04b-guessed-repo-after-fix.txt), the agent started with `list_repos({})` and found `gilad12-coder/issues-mcp-sandbox`. It searched that repo with `state="all"` and `sort="comments"`, found five issues, then called `get_issue` for #1 with `max_comments=10`. It correctly identified the CSV export bug as the most discussed issue, showed its two comments, and noted that the other four issues had none.

## Part III: OAuth

**Flow**: how a token is obtained, cached, and refreshed:
> Requires Python 3.11+, `uv`, and Unix (tested on macOS). For one-time setup, run `uv run --directory week2 python setup_app.py`, install the app on the sandbox using its printed link, then run `uv run --directory week2 python login.py`.
>
> `login.py` obtains an authorization code through browser login with PKCE and state validation, then exchanges it for tokens. Tokens are cached atomically with mode 0600 at `~/.config/github-issues-mcp/token.json`. The server refreshes near expiry without prompting, allows only one refresh at a time, and saves the new token pair. A premature 401 triggers one refresh and retry (`login.py:144`, `oauth.py:164`, `oauth.py:270`, `github.py:214`).

**Scopes requested**, and why each is necessary:
> GitHub App permissions (`setup_app.py:27`): **Issues read/write** for searching, reading, and creating issues; mandatory **Metadata read** for repository discovery. No other permissions are requested. The demo token could access nine repositories, including the sandbox.

**Secrets**: what's in env, what's gitignored:
> `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` come from env or `week2/.env`. Gitignored: `.env`, real root/week2 `.mcp.json`, `token.json`, and `*.token.json`. Tokens are cached outside the repo. Committed examples contain no credentials; other private repo names in transcripts are redacted.

**Token dies mid-session**: what the agent sees:
> Missing or invalid refresh credentials or a second 401 returns `auth_required`, `retryable: false`, and a hint to run `uv run --directory week2 python login.py`. Rejected app credentials return `not_configured`, with instructions to correct them and restart. Tools never open a browser. Temporary token-endpoint failures return retryable `network_error` with a wait and preserve the cache.

## Part IV: Integration

**Registration config** (`.mcp.json.example`) and the client you used:
> Claude Code 2.1.287. Copy `week2/.mcp.json.example` to the repo root as `.mcp.json` and start the client there:

```json
{"mcpServers":{"github-issues":{"type":"stdio","command":"uv","args":["run","--directory","week2","python","server.py"]}}}
```

**End-to-end transcript**: the prompt, the tools that fired with their arguments, the result:

[Transcript 04b](transcripts/04b-guessed-repo-after-fix.txt) includes the full prompt, chained calls, and final answer. The excerpt below shows preview and approved creation from [transcript 01](transcripts/01-chain-and-file.txt); ellipses omit fields or body text. Saved demos predate the added output flags.

```text
USER: In my issues-mcp-sandbox repo there's an open bug about the CSV export. Find it,
read it including the comments, and tell me the likely root cause in two sentences. Then
draft a follow-up issue asking for a regression test for that bug, labeled bug. Show me
the preview; don't file it yet.

list_repos({})
  -> {"repos":[{"full_name":"gilad12-coder/issues-mcp-sandbox",...},...],"total_accessible":9}
search_issues({"repo":"gilad12-coder/issues-mcp-sandbox","query":"CSV"})
  -> {"total_count":2,"items":[{"number":1,"title":"CSV export crashes on rows with empty dates",...},...]}
get_issue({"repo":"gilad12-coder/issues-mcp-sandbox","number":1})
  -> {"body":"Exporting the weekly report to CSV throws `ValueError: time data '' does not match format` when any row has an empty `due_date`...",
      "recent_comments":[...,{"body":"Looks like `parse_date` in export.py calls strptime without checking for empty strings.",...}],...}
create_issue({"repo":"gilad12-coder/issues-mcp-sandbox",
  "title":"Add regression test for CSV export with empty optional date fields",
  "body":"Follow-up to #1. ...","labels":["bug"],"dry_run":true})
  -> {"created":false,"preview":{...},"next_step":"Nothing was created. Show this preview (and any warnings) to the user. If they confirm, call create_issue again with the same arguments and dry_run=false.",...}

USER: Looks good, file it.

create_issue({...same arguments...,"dry_run":false})
  -> {"created":true,"issue":{"number":5,"labels":["bug"],...},...}
ASSISTANT: I filed it as issue #5, labeled `bug`: https://github.com/gilad12-coder/issues-mcp-sandbox/issues/5
```

**A failure, handled**: what you provoked, what the agent saw, what it did next:

I temporarily replaced cached tokens with invalid values, then restored them; no real authorization was revoked. In [transcript 02](transcripts/02-revoked-token.txt):

```text
USER: What are the open bugs in my issues-mcp-sandbox repo?
list_repos({"limit":100})
  -> isError=true; error="auth_required"; retryable=false
  -> hint="Do not retry. Ask the user to run `uv run --directory week2 python login.py` in a terminal, then call the tool again."
```

The agent made one call, did not retry, and relayed the login command.

**Protocol-level test**: what it covers and how to run it:

```sh
uv run --directory week2 pytest tests/test_stdio.py
```

`tests/test_stdio.py` starts the real stdio server and checks initialization, schemas and annotations, chained read calls, preview without writing, explicit creation, and structured `not_found` errors. A fake GitHub API runs on localhost.
