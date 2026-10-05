"""MCP server exposing GitHub issues to a coding agent.

Run from the repo root:  uv run --directory week2 python server.py   (stdio transport)
"""

from __future__ import annotations

import functools
import json
import math
from typing import Annotated, Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError, ValidationError
from fastmcp.server.middleware import Middleware
from pydantic import BaseModel, BeforeValidator, Field, ValidationError as PydanticValidationError

from github import GitHub, ToolFailure

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


class ArgumentErrors(Middleware):
    """Apply the JSON error contract to validation that runs before tool functions."""

    async def on_call_tool(self, context, call_next):
        """Convert schema failures into actionable errors without echoing input values.

        Args:
            context: The MCP tool-call request.
            call_next: The rest of the middleware and tool dispatch chain.

        Returns:
            The tool result on success.

        Raises:
            ToolError: JSON describing invalid arguments.
        """
        try:
            return await call_next(context)
        except ValidationError as exc:
            cause = exc.__cause__
            details = []
            if isinstance(cause, PydanticValidationError):
                details = [
                    f"{'.'.join(map(str, item['loc']))}: {item['msg']}"
                    for item in cause.errors(include_input=False, include_url=False)
                ]
            failure = ToolFailure(
                "invalid_arguments", "Arguments do not match this tool's schema.",
                retryable=False,
                hint="Correct the indicated fields using the published schema, then call again.",
                details=details,
            )
            raise ToolError(json.dumps(failure.payload())) from exc


mcp = FastMCP(
    "github-issues", instructions=INSTRUCTIONS, mask_error_details=True,
    middleware=[ArgumentErrors()], strict_input_validation=True,
)


def _json_integer(value: object) -> object:
    """Accept integral JSON numbers without coercing strings or booleans.

    Args:
        value: The input before strict integer validation.

    Returns:
        An integer for an integral float; otherwise the original value.
    """
    return int(value) if isinstance(value, float) and value.is_integer() else value


JsonInteger = Annotated[int, BeforeValidator(_json_integer)]

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
    JsonInteger,
    Field(ge=1, description="Issue number (the `number` field from search_issues), not its URL."),
]
LabelName = Annotated[str, Field(min_length=1, max_length=50)]

READ_ONLY = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True}

BODY_LIMIT = 4000
COMMENT_LIMIT = 1500


def _clip(text: str | None, limit: int) -> tuple[str, bool]:
    """Cut text to a length limit, marking the cut with an ellipsis.

    Args:
        text: Text to clip; None counts as empty.
        limit: Maximum characters to keep.

    Returns:
        The possibly clipped text and whether it was clipped.
    """
    text = text or ""
    if len(text) <= limit:
        return text, False
    return text[:limit] + "…", True


def agent_errors(fn):
    """Report every failure as a JSON tool error (isError=true) instead of a traceback.

    Args:
        fn: The async tool function to wrap.

    Returns:
        A wrapper with the same signature that turns exceptions into ToolErrors.
    """

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        """Run the tool and convert any failure into a JSON ToolError.

        Args:
            *args: Positional tool arguments.
            **kwargs: Keyword tool arguments.

        Returns:
            Whatever the tool returns.

        Raises:
            ToolError: Carries the failure payload as JSON.
        """
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
    """Replace a failure's hint when its error code is one of ``codes``.

    Args:
        failure: The failure to adjust.
        codes: Error codes the new hint applies to.
        hint: Tool-specific next step for the agent.

    Returns:
        The same failure object, possibly with a new hint.
    """
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
    incomplete_results: bool = Field(default=False, description="GitHub returned only partial search results.")
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
    """Shape a raw GitHub issue into the fields an agent needs.

    Args:
        repo: The issue's repository as "owner/name".
        raw: The issue as GitHub's REST API returns it.

    Returns:
        The issue summary.
    """
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
    """Shape a raw GitHub comment, clipping its body.

    Args:
        raw: The comment as GitHub's REST API returns it.

    Returns:
        The shaped comment.
    """
    body, truncated = _clip(raw.get("body"), COMMENT_LIMIT)
    return Comment(
        author=(raw.get("user") or {}).get("login"),
        created_at=raw["created_at"],
        body=body,
        body_truncated=truncated,
    )


def _repo_from_url(repository_url: str) -> str:
    """Get "owner/name" from an API repository URL.

    Args:
        repository_url: URL such as ``https://api.github.com/repos/owner/name``.

    Returns:
        The repository as "owner/name".
    """
    return "/".join(repository_url.rstrip("/").split("/")[-2:])


# ---------- tools ----------


@mcp.tool(title="List accessible repositories", annotations=READ_ONLY)
@agent_errors
async def list_repos(
    sort: Literal["pushed", "updated", "full_name"] = "pushed",
    limit: Annotated[JsonInteger, Field(ge=1, le=100)] = 30,
) -> RepoList:
    """List the repositories this server can read and file issues in.

    Start here: the `full_name` of each result is the `repo` argument every other tool
    expects. This lists repositories available through the app's installations. If
    `total_accessible` exceeds `limit`, more exist than are shown in this response.

    Args:
        sort: Order of results: most recently pushed, most recently updated, or by name.
        limit: Maximum number of repositories to return.

    Returns:
        The repositories, their total count, and a note when empty or truncated.
    """
    gh = GitHub()
    installations = []
    page = 1
    while True:
        batch = (await gh.get("/user/installations", per_page=100, page=page))["installations"]
        installations.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    raw: list[dict] = []
    for inst in installations:
        page = 1
        while True:
            data = await gh.get(
                f"/user/installations/{inst['id']}/repositories", per_page=100, page=page
            )
            raw.extend(data["repositories"])
            if len(data["repositories"]) < 100:
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
    elif len(raw) > limit:
        note = f"Showing {len(repos)} of {len(raw)} repositories; increase limit (maximum 100) or change sort."
    return RepoList(repos=repos, total_accessible=len(raw), note=note)


@mcp.tool(title="Search issues in a repository", annotations=READ_ONLY)
@agent_errors
async def search_issues(
    repo: Repo,
    query: Annotated[
        str,
        Field(
            max_length=200,
            pattern=r'^[^"\\\x00-\x1f\x7f-\x9f]*$',
            description=(
                "Literal phrase in titles and bodies, not GitHub search syntax. "
                "No double quotes, backslashes or control characters. Empty matches everything."
            ),
        ),
    ] = "",
    state: Literal["open", "closed", "all"] = "open",
    kind: Literal["issue", "pull_request"] = "issue",
    labels: Annotated[
        list[Annotated[LabelName, Field(pattern=r'^[^"\\\x00-\x1f\x7f-\x9f]*$')]],
        Field(max_length=5, description="Every label must match (AND). No double quotes, backslashes or control characters."),
    ] = [],
    sort: Literal["updated", "created", "comments", "best_match"] = "updated",
    limit: Annotated[JsonInteger, Field(ge=1, le=50)] = 10,
) -> SearchResult:
    """Search issues (or pull requests) in one repository, newest activity first by default.

    `repo` comes from list_repos. Results are summaries without bodies: pass a result's
    `repo` and `number` to get_issue to read the full text and comments.

    Args:
        repo: Repository as "owner/name", copied from a list_repos `full_name`.
        query: Literal phrase in titles and bodies; empty matches everything. No search
            syntax, double quotes, backslashes or control characters.
        state: Which issues to include by state.
        kind: Search issues or pull requests.
        labels: Every label must match (AND). No double quotes, backslashes or control characters.
        sort: Order of results; best_match uses GitHub's relevance ranking.
        limit: Maximum number of results to return.

    Returns:
        The total match count, issue summaries, and explicit empty or incomplete results.
    """
    parts = [f"repo:{repo}", "is:issue" if kind == "issue" else "is:pr", "in:title,body"]
    if state != "all":
        parts.append(f"state:{state}")
    parts += [f'label:"{label}"' for label in labels]
    if query.strip():
        parts.append(f'"{query.strip()}"')
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
    incomplete = data.get("incomplete_results", False)
    if incomplete:
        note = "GitHub returned incomplete search results. Narrow the query and try again before drawing conclusions."
    return SearchResult(total_count=data["total_count"], items=items, incomplete_results=incomplete, note=note)


@mcp.tool(title="Read one issue with comments", annotations=READ_ONLY)
@agent_errors
async def get_issue(
    repo: Repo,
    number: IssueNumber,
    max_comments: Annotated[
        JsonInteger, Field(ge=0, le=30, description="How many of the newest comments to include.")
    ] = 10,
) -> IssueDetail:
    """Read one issue: full body (clipped at 4000 chars), labels, assignees, newest comments.

    Get `number` from search_issues; do not guess it. Works for pull requests too
    (`is_pull_request` is then true), since GitHub numbers both in one sequence.

    Args:
        repo: Repository as "owner/name", copied from a list_repos `full_name`.
        number: Issue number (the `number` field from search_issues), not its URL.
        max_comments: How many of the newest comments to include.

    Returns:
        The issue's summary fields plus body, assignees, milestone and recent comments.
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
    repo = _repo_from_url(raw["repository_url"]) if raw.get("repository_url") else repo
    number = raw["number"]
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
    title: Annotated[str, Field(min_length=1, max_length=256, pattern=r"\S")],
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
    Filing an issue creates visible state and can notify watchers, so show the preview
    to the user and only call again with dry_run=false once they confirm.

    Args:
        repo: Repository as "owner/name", copied from a list_repos `full_name`.
        title: Issue title.
        body: Markdown.
        labels: Must already exist in the repo; unknown labels fail.
        dry_run: true (default) only previews. false creates the issue for real.

    Returns:
        The preview and warnings; after a real write, also the created issue.
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
        existing = set()
        page = 1
        while True:
            batch = await gh.get(f"/repos/{repo}/labels", per_page=100, page=page)
            existing.update(lbl["name"] for lbl in batch)
            if len(batch) < 100:
                break
            page += 1
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
    phrase = " ".join(title.replace('"', " ").replace("\\", " ").split())
    similar = await gh.get(
        "/search/issues", q=f'repo:{repo} is:issue state:open in:title "{phrase}"', per_page=3
    )
    if similar.get("incomplete_results"):
        warnings.append("Duplicate search was incomplete; check for existing issues before filing.")
    warnings += [
        f"Possible duplicate: #{i['number']} {i['title']!r} ({i['html_url']})"
        for i in similar["items"]
    ]
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
