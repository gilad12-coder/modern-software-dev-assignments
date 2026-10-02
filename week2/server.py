"""MCP server exposing GitHub issues to a coding agent.

Run from the repo root:  uv run --directory week2 python server.py   (stdio transport)
"""

from __future__ import annotations

import functools
import json
import math
from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field

from github import GitHub, ToolFailure

INSTRUCTIONS = """\
Tools for reading and filing GitHub issues in repositories the user has installed this
server's GitHub App on.

Workflow:
1. list_repos gives the `full_name` ("owner/name") of every repository you can use.
   Every other tool takes that exact string as `repo`. When the user names a repository
   loosely ("my sandbox repo"), call list_repos first instead of assuming the current
   directory's repository; these tools only see repos the GitHub App is installed on.
2. search_issues(repo=...) finds issues and returns their `number`s.
3. get_issue(repo, number) reads one issue in full, including recent comments.
4. create_issue files a new issue. It defaults to dry_run=true and only previews.
   Show the preview to the user and call again with dry_run=false only after they agree.

Errors come back as JSON with an `error` code and a `retryable` flag. If retryable is
false, do not repeat the same call: follow the `hint`. auth_required always needs the
user to act; tell them the command in the hint instead of retrying.
"""

mcp = FastMCP("github-issues", instructions=INSTRUCTIONS, mask_error_details=True)

Repo = Annotated[
    str,
    Field(
        pattern=r"^[A-Za-z0-9-]{1,39}/[A-Za-z0-9._-]{1,100}$",
        description=(
            'Repository as "owner/name", copied from a list_repos `full_name`. Do not guess '
            "it from the current directory or an informal name like \"my sandbox repo\": call "
            "list_repos and match the user's words against `full_name` and `description`."
        ),
        examples=["octocat/hello-world"],
    ),
]
IssueNumber = Annotated[
    int,
    Field(ge=1, description="Issue number (the `number` field from search_issues), not its URL."),
]
LabelName = Annotated[str, Field(min_length=1, max_length=50)]

READ_ONLY = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True}

BODY_LIMIT = 4000
COMMENT_LIMIT = 1500


def _clip(text: str | None, limit: int) -> tuple[str, bool]:
    text = text or ""
    if len(text) <= limit:
        return text, False
    return text[:limit] + "…", True


def agent_errors(fn):
    """Report every failure as a JSON tool error (isError=true) instead of a traceback."""

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except ToolFailure as failure:
            raise ToolError(json.dumps(failure.payload())) from failure
        except ToolError:
            raise
        except Exception as exc:
            failure = ToolFailure(
                "internal_error",
                f"Unexpected server error ({type(exc).__name__}).",
                retryable=False,
                hint="This is a bug in the server, not in your arguments. Tell the user.",
            )
            raise ToolError(json.dumps(failure.payload())) from exc

    return wrapper


def _with_hint(failure: ToolFailure, codes: set[str], hint: str) -> ToolFailure:
    if failure.error in codes:
        failure.hint = hint
    return failure


# ---------- output models ----------


class Repository(BaseModel):
    full_name: str = Field(description='Pass this as `repo` to the other tools.')
    description: str
    private: bool
    has_issues: bool = Field(description="False means create_issue will fail for this repo.")
    open_issues_and_prs: int = Field(description="GitHub counts open pull requests here too.")
    pushed_at: str | None


class RepoList(BaseModel):
    repos: list[Repository]
    total_accessible: int
    note: str | None = None


class IssueSummary(BaseModel):
    repo: str
    number: int
    title: str
    state: Literal["open", "closed"]
    state_reason: str | None = Field(description="completed, not_planned, reopened, or null.")
    author: str | None
    labels: list[str]
    comments: int
    created_at: str
    updated_at: str
    url: str


class SearchResult(BaseModel):
    total_count: int = Field(description="Matches on GitHub; `items` holds at most `limit`.")
    items: list[IssueSummary]
    note: str | None = None


class Comment(BaseModel):
    author: str | None
    created_at: str
    body: str
    body_truncated: bool


class IssueDetail(IssueSummary):
    is_pull_request: bool
    body: str
    body_truncated: bool
    assignees: list[str]
    milestone: str | None
    recent_comments: list[Comment] = Field(description="The newest comments, oldest first.")
    comments_omitted: int = Field(description="Older comments not included.")


class IssuePreview(BaseModel):
    repo: str
    title: str
    body: str
    labels: list[str]


class CreateIssueResult(BaseModel):
    dry_run: bool
    created: bool
    preview: IssuePreview
    warnings: list[str]
    issue: IssueSummary | None = None
    next_step: str


def _summary(repo: str, raw: dict) -> IssueSummary:
    return IssueSummary(
        repo=repo,
        number=raw["number"],
        title=raw["title"],
        state=raw["state"],
        state_reason=raw.get("state_reason"),
        author=(raw.get("user") or {}).get("login"),
        labels=[label["name"] for label in raw.get("labels", [])],
        comments=raw.get("comments", 0),
        created_at=raw["created_at"],
        updated_at=raw["updated_at"],
        url=raw["html_url"],
    )


def _comment(raw: dict) -> Comment:
    body, truncated = _clip(raw.get("body"), COMMENT_LIMIT)
    return Comment(
        author=(raw.get("user") or {}).get("login"),
        created_at=raw["created_at"],
        body=body,
        body_truncated=truncated,
    )


def _repo_from_url(repository_url: str) -> str:
    return "/".join(repository_url.rstrip("/").split("/")[-2:])


# ---------- tools ----------


@mcp.tool(title="List accessible repositories", annotations=READ_ONLY)
@agent_errors
async def list_repos(
    sort: Literal["pushed", "updated", "full_name"] = "pushed",
    limit: Annotated[int, Field(ge=1, le=100)] = 30,
) -> RepoList:
    """List the repositories this server can read and file issues in.

    Start here: the `full_name` of each result is the `repo` argument every other tool
    expects. Only repositories the user installed the GitHub App on are visible, so a
    repository missing from this list will fail in the other tools too.
    """
    gh = GitHub()
    installations = (await gh.get("/user/installations", per_page=100))["installations"]
    raw: list[dict] = []
    for inst in installations:
        page = 1
        while True:
            data = await gh.get(
                f"/user/installations/{inst['id']}/repositories", per_page=100, page=page
            )
            raw.extend(data["repositories"])
            if len(data["repositories"]) < 100 or page >= 5:
                break
            page += 1
    key = {"pushed": "pushed_at", "updated": "updated_at", "full_name": "full_name"}[sort]
    raw.sort(key=lambda r: r.get(key) or "", reverse=sort != "full_name")
    repos = [
        Repository(
            full_name=r["full_name"],
            description=_clip(r.get("description"), 120)[0],
            private=r["private"],
            has_issues=r.get("has_issues", True),
            open_issues_and_prs=r.get("open_issues_count", 0),
            pushed_at=r.get("pushed_at"),
        )
        for r in raw[:limit]
    ]
    note = None
    if not raw:
        note = (
            "0 repositories. The user has not installed the GitHub App on any repository; "
            "ask them to install it from the app's GitHub page."
        )
    return RepoList(repos=repos, total_accessible=len(raw), note=note)


@mcp.tool(title="Search issues in a repository", annotations=READ_ONLY)
@agent_errors
async def search_issues(
    repo: Repo,
    query: Annotated[
        str,
        Field(
            max_length=200,
            description="Free text matched against titles and bodies. Empty matches everything.",
        ),
    ] = "",
    state: Literal["open", "closed", "all"] = "open",
    kind: Literal["issue", "pull_request"] = "issue",
    labels: Annotated[
        list[LabelName], Field(max_length=5, description="Every label must match (AND).")
    ] = [],
    sort: Literal["updated", "created", "comments", "best_match"] = "updated",
    limit: Annotated[int, Field(ge=1, le=50)] = 10,
) -> SearchResult:
    """Search issues (or pull requests) in one repository, newest activity first by default.

    `repo` comes from list_repos. Results are summaries without bodies: pass a result's
    `repo` and `number` to get_issue to read the full text and comments.
    """
    parts = [f"repo:{repo}", "is:issue" if kind == "issue" else "is:pr"]
    if state != "all":
        parts.append(f"state:{state}")
    parts += [f'label:"{label}"' for label in labels]
    if query.strip():
        parts.append(query.strip())
    params = {"q": " ".join(parts), "per_page": limit}
    if sort != "best_match":
        params.update(sort=sort, order="desc")
    try:
        data = await GitHub().get("/search/issues", **params)
    except ToolFailure as failure:
        if failure.error == "invalid_request" and any(
            "cannot be searched" in d for d in failure.details
        ):
            failure.error = "not_found"
            failure.hint = f"{repo} does not exist or is not accessible. Call list_repos."
        raise
    items = [_summary(_repo_from_url(i["repository_url"]), i) for i in data["items"]]
    note = None
    if not items:
        # Agents that guessed `repo` read an empty result as "no such issues" and stop.
        note = (
            f"0 matches in {repo}. If the user did not give this exact repository name, "
            "call list_repos and pick the repo whose name or description matches; "
            "otherwise try state='all' or a shorter query."
        )
    return SearchResult(total_count=data["total_count"], items=items, note=note)


@mcp.tool(title="Read one issue with comments", annotations=READ_ONLY)
@agent_errors
async def get_issue(
    repo: Repo,
    number: IssueNumber,
    max_comments: Annotated[
        int, Field(ge=0, le=30, description="How many of the newest comments to include.")
    ] = 10,
) -> IssueDetail:
    """Read one issue: full body (clipped at 4000 chars), labels, assignees, newest comments.

    Get `number` from search_issues; do not guess it. Works for pull requests too
    (`is_pull_request` is then true), since GitHub numbers both in one sequence.
    """
    gh = GitHub()
    try:
        raw = await gh.get(f"/repos/{repo}/issues/{number}")
    except ToolFailure as failure:
        raise _with_hint(
            failure,
            {"not_found", "gone"},
            f"No issue #{number} in {repo}, or the repo is not accessible. "
            f"Find valid numbers with search_issues(repo='{repo}').",
        ) from None
    comments: list[dict] = []
    total = raw.get("comments", 0)
    if max_comments and total:
        # Comments are returned oldest first, so walk backwards from the last page.
        page = math.ceil(total / 100)
        while page >= 1 and len(comments) < max_comments:
            batch = await gh.get(f"/repos/{repo}/issues/{number}/comments", per_page=100, page=page)
            comments = batch + comments
            page -= 1
    recent = comments[-max_comments:] if max_comments else []
    body, body_truncated = _clip(raw.get("body"), BODY_LIMIT)
    return IssueDetail(
        **_summary(repo, raw).model_dump(),
        is_pull_request="pull_request" in raw,
        body=body,
        body_truncated=body_truncated,
        assignees=[a["login"] for a in raw.get("assignees") or []],
        milestone=(raw.get("milestone") or {}).get("title"),
        recent_comments=[
            _comment(c) for c in recent
        ],
        comments_omitted=max(0, total - len(recent)),
    )


@mcp.tool(
    title="File a new issue (dry run by default)",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
@agent_errors
async def create_issue(
    repo: Repo,
    title: Annotated[str, Field(min_length=1, max_length=256)],
    body: Annotated[str, Field(max_length=20000, description="Markdown.")] = "",
    labels: Annotated[
        list[LabelName],
        Field(max_length=10, description="Must already exist in the repo; unknown labels fail."),
    ] = [],
    dry_run: Annotated[
        bool,
        Field(description="true (default) only previews. false creates the issue for real."),
    ] = True,
) -> CreateIssueResult:
    """File a new issue. Defaults to a dry run that validates and previews without writing.

    `repo` comes from list_repos. The dry run checks the repo accepts issues, that every
    label exists, and lists open issues with a similar title so you can avoid duplicates.
    Issues cannot be deleted through the API and filing one notifies watchers, so show the
    preview to the user and only call again with dry_run=false once they confirm.
    """
    gh = GitHub()
    preview = IssuePreview(repo=repo, title=title, body=body, labels=labels)
    try:
        repo_info = await gh.get(f"/repos/{repo}")
    except ToolFailure as failure:
        raise _with_hint(
            failure,
            {"not_found"},
            f"{repo} does not exist or the GitHub App is not installed on it. Call list_repos.",
        ) from None
    if not repo_info.get("has_issues", True):
        raise ToolFailure(
            "issues_disabled",
            f"Issues are turned off for {repo}.",
            retryable=False,
            hint="Pick another repository from list_repos, or ask the user to enable issues.",
        )
    if labels:
        existing = {lbl["name"] for lbl in await gh.get(f"/repos/{repo}/labels", per_page=100)}
        unknown = [lbl for lbl in labels if lbl not in existing]
        if unknown:
            raise ToolFailure(
                "unknown_labels",
                f"These labels do not exist in {repo}: {', '.join(unknown)}.",
                retryable=False,
                hint="Use only existing labels: " + ", ".join(sorted(existing)[:40]),
            )

    warnings: list[str] = []
    if not dry_run:
        created = await gh.request("POST", f"/repos/{repo}/issues", json=preview.model_dump(
            include={"title", "body", "labels"}
        ))
        issue = _summary(repo, created.json())
        if labels and not issue.labels:
            warnings.append("GitHub dropped the labels: the user lacks push access to this repo.")
        return CreateIssueResult(
            dry_run=False,
            created=True,
            preview=preview,
            warnings=warnings,
            issue=issue,
            next_step=f"Created {issue.url}. Do not call create_issue again for this issue.",
        )

    if labels and not (repo_info.get("permissions") or {}).get("push"):
        warnings.append("You lack push access here, so GitHub will silently drop the labels.")
    phrase = title.replace('"', " ").strip()
    try:
        similar = await gh.get(
            "/search/issues", q=f'repo:{repo} is:issue state:open in:title "{phrase}"', per_page=3
        )
        warnings += [
            f"Possible duplicate: #{i['number']} {i['title']!r} ({i['html_url']})"
            for i in similar["items"]
        ]
    except ToolFailure as failure:
        warnings.append(f"Duplicate check skipped ({failure.error}).")
    return CreateIssueResult(
        dry_run=True,
        created=False,
        preview=preview,
        warnings=warnings,
        next_step=(
            "Nothing was created. Show this preview (and any warnings) to the user. If they "
            "confirm, call create_issue again with the same arguments and dry_run=false."
        ),
    )


if __name__ == "__main__":
    mcp.run(show_banner=False)
