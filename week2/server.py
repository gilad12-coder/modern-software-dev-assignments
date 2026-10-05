"""MCP server exposing GitHub issues to a coding agent.

Run from the repo root:  uv run --directory week2 python server.py   (stdio transport)
"""

from __future__ import annotations

import functools
import json
import math
from typing import Annotated

import config
import constants as C
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError, ValidationError
from fastmcp.server.middleware import Middleware
from github import GitHub
from models import (
    Comment,
    CreateIssueResult,
    IssueDetail,
    IssuePreview,
    IssueSummary,
    RepoList,
    Repository,
    SearchResult,
    ToolFailure,
)
from pydantic import BeforeValidator, Field
from pydantic import ValidationError as PydanticValidationError


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
                    f"{'.'.join(map(str, item[C.KEY_LOC]))}: {item[C.KEY_MSG]}"
                    for item in cause.errors(include_input=False, include_url=False)
                ]
            failure = ToolFailure(
                C.ERROR_INVALID_ARGUMENTS,
                C.INVALID_ARGUMENTS_MESSAGE,
                retryable=False,
                hint=C.INVALID_ARGUMENTS_HINT,
                details=details,
            )
            raise ToolError(json.dumps(failure.payload())) from exc


mcp = FastMCP(
    C.SERVER_NAME,
    instructions=C.INSTRUCTIONS,
    mask_error_details=True,
    middleware=[ArgumentErrors()],
    strict_input_validation=True,
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
        pattern=C.REPO_PATTERN,
        description=(C.REPO_DESCRIPTION),
        examples=[C.REPO_EXAMPLE],
    ),
]
IssueNumber = Annotated[
    JsonInteger,
    Field(ge=C.MIN_ISSUE_NUMBER, description=C.ISSUE_NUMBER_DESCRIPTION),
]
LabelName = Annotated[str, Field(min_length=C.MIN_TEXT_LENGTH, max_length=config.LABEL_NAME_LIMIT)]


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
    return text[:limit] + C.TRUNCATION_MARKER, True


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
                C.ERROR_INTERNAL_ERROR,
                f"Unexpected server error ({type(exc).__name__}).",
                retryable=False,
                hint=C.INTERNAL_ERROR_HINT,
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
        number=raw[C.KEY_NUMBER],
        title=raw[C.KEY_TITLE],
        state=raw[C.KEY_STATE],
        state_reason=raw.get(C.KEY_STATE_REASON),
        author=(raw.get(C.KEY_USER) or {}).get(C.KEY_LOGIN),
        labels=[label[C.KEY_NAME] for label in raw.get(C.KEY_LABELS, [])],
        comments=raw.get(C.KEY_COMMENTS, 0),
        created_at=raw[C.KEY_CREATED_AT],
        updated_at=raw[C.KEY_UPDATED_AT],
        url=raw[C.KEY_HTML_URL],
    )


def _comment(raw: dict) -> Comment:
    """Shape a raw GitHub comment, clipping its body.

    Args:
        raw: The comment as GitHub's REST API returns it.

    Returns:
        The shaped comment.
    """
    body, truncated = _clip(raw.get(C.KEY_BODY), config.COMMENT_LIMIT)
    return Comment(
        author=(raw.get(C.KEY_USER) or {}).get(C.KEY_LOGIN),
        created_at=raw[C.KEY_CREATED_AT],
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
    return "/".join(repository_url.rstrip("/").split("/")[-C.REPOSITORY_URL_SEGMENTS :])


# ---------- tools ----------


@mcp.tool(title=C.LIST_REPOS_TITLE, annotations=C.READ_ONLY_ANNOTATIONS)
@agent_errors
async def list_repos(
    sort: C.RepoSort = config.DEFAULT_REPO_SORT,
    limit: Annotated[
        JsonInteger, Field(ge=C.MIN_RESULT_LIMIT, le=config.MAX_REPO_LIMIT)
    ] = config.DEFAULT_REPO_LIMIT,
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
    page = C.FIRST_PAGE
    while True:
        batch = (await gh.get(C.INSTALLATIONS_PATH, per_page=config.API_PAGE_SIZE, page=page))[
            C.KEY_INSTALLATIONS
        ]
        installations.extend(batch)
        if len(batch) < config.API_PAGE_SIZE:
            break
        page += 1
    raw: list[dict] = []
    for inst in installations:
        page = C.FIRST_PAGE
        while True:
            data = await gh.get(
                C.INSTALLATION_REPOS_PATH.format(installation_id=inst[C.KEY_ID]),
                per_page=config.API_PAGE_SIZE,
                page=page,
            )
            raw.extend(data[C.KEY_REPOSITORIES])
            if len(data[C.KEY_REPOSITORIES]) < config.API_PAGE_SIZE:
                break
            page += 1
    key = C.REPO_SORT_FIELDS[sort]
    raw.sort(key=lambda r: r.get(key) or "", reverse=sort != C.KEY_FULL_NAME)
    repos = [
        Repository(
            full_name=r[C.KEY_FULL_NAME],
            description=_clip(r.get(C.KEY_DESCRIPTION), config.REPO_DESCRIPTION_LIMIT)[0],
            private=r[C.KEY_PRIVATE],
            has_issues=r.get(C.KEY_HAS_ISSUES, True),
            open_issues_and_prs=r.get(C.KEY_OPEN_ISSUES_COUNT, 0),
            pushed_at=r.get(C.KEY_PUSHED_AT),
        )
        for r in raw[:limit]
    ]
    note = None
    if not raw:
        note = C.NO_REPOS_NOTE
    elif len(raw) > limit:
        note = f"Showing {len(repos)} of {len(raw)} repositories; increase limit (maximum {config.MAX_REPO_LIMIT}) or change sort."
    return RepoList(repos=repos, total_accessible=len(raw), note=note)


@mcp.tool(title=C.SEARCH_ISSUES_TITLE, annotations=C.READ_ONLY_ANNOTATIONS)
@agent_errors
async def search_issues(
    repo: Repo,
    query: Annotated[
        str,
        Field(
            max_length=config.QUERY_LIMIT,
            pattern=C.SEARCH_TEXT_PATTERN,
            description=(C.SEARCH_QUERY_DESCRIPTION),
        ),
    ] = "",
    state: C.IssueState = config.DEFAULT_SEARCH_STATE,
    kind: C.IssueKind = config.DEFAULT_SEARCH_KIND,
    labels: Annotated[
        list[Annotated[LabelName, Field(pattern=C.SEARCH_TEXT_PATTERN)]],
        Field(max_length=config.SEARCH_LABEL_LIMIT, description=C.SEARCH_LABELS_DESCRIPTION),
    ] = [],
    sort: C.IssueSort = config.DEFAULT_SEARCH_SORT,
    limit: Annotated[
        JsonInteger, Field(ge=C.MIN_RESULT_LIMIT, le=config.MAX_SEARCH_LIMIT)
    ] = config.DEFAULT_SEARCH_LIMIT,
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
    parts = [
        C.SEARCH_REPO_TEMPLATE.format(repo=repo),
        C.SEARCH_ISSUES_QUALIFIER if kind == C.KIND_ISSUE else C.SEARCH_PRS_QUALIFIER,
        C.SEARCH_TEXT_QUALIFIER,
    ]
    if state != C.STATE_ALL:
        parts.append(C.SEARCH_STATE_TEMPLATE.format(state=state))
    parts += [C.SEARCH_LABEL_TEMPLATE.format(label=label) for label in labels]
    if query.strip():
        parts.append(C.SEARCH_PHRASE_TEMPLATE.format(phrase=query.strip()))
    params = {C.KEY_Q: " ".join(parts), C.KEY_PER_PAGE: limit}
    if sort != C.SORT_BEST_MATCH:
        params.update(sort=sort, order=C.SORT_DESCENDING)
    try:
        data = await GitHub().get(C.SEARCH_ISSUES_PATH, **params)
    except ToolFailure as failure:
        if failure.error == C.ERROR_INVALID_REQUEST and any(
            C.UNSEARCHABLE_REPO_MARKER in d for d in failure.details
        ):
            failure.error = C.ERROR_NOT_FOUND
            failure.hint = f"{repo} does not exist or is not accessible. Call list_repos."
        raise
    items = [_summary(_repo_from_url(i[C.KEY_REPOSITORY_URL]), i) for i in data[C.KEY_ITEMS]]
    note = None
    if not items:
        # Agents that guessed `repo` read an empty result as "no such issues" and stop.
        note = (
            f"0 matches in {repo}. If the user did not give this exact repository name, "
            "call list_repos and pick the repo whose name or description matches; "
            "otherwise try state='all' or a shorter query."
        )
    incomplete = data.get(C.KEY_INCOMPLETE_RESULTS, False)
    if incomplete:
        note = C.INCOMPLETE_SEARCH_NOTE
    return SearchResult(
        total_count=data[C.KEY_TOTAL_COUNT], items=items, incomplete_results=incomplete, note=note
    )


@mcp.tool(title=C.GET_ISSUE_TITLE, annotations=C.READ_ONLY_ANNOTATIONS)
@agent_errors
async def get_issue(
    repo: Repo,
    number: IssueNumber,
    max_comments: Annotated[
        JsonInteger,
        Field(ge=C.MIN_COMMENTS, le=config.MAX_COMMENTS, description=C.MAX_COMMENTS_DESCRIPTION),
    ] = config.DEFAULT_COMMENTS,
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
        raw = await gh.get(C.ISSUE_PATH.format(repo=repo, number=number))
    except ToolFailure as failure:
        raise _with_hint(
            failure,
            {C.ERROR_NOT_FOUND, C.ERROR_GONE},
            f"No issue #{number} in {repo}, or the repo is not accessible. "
            f"Find valid numbers with search_issues(repo='{repo}').",
        ) from None
    repo = _repo_from_url(raw[C.KEY_REPOSITORY_URL]) if raw.get(C.KEY_REPOSITORY_URL) else repo
    number = raw[C.KEY_NUMBER]
    comments: list[dict] = []
    total = raw.get(C.KEY_COMMENTS, 0)
    if max_comments and total:
        # Comments are returned oldest first, so walk backwards from the last page.
        page = math.ceil(total / config.API_PAGE_SIZE)
        while page >= C.FIRST_PAGE and len(comments) < max_comments:
            batch = await gh.get(
                C.COMMENTS_PATH.format(repo=repo, number=number),
                per_page=config.API_PAGE_SIZE,
                page=page,
            )
            comments = batch + comments
            page -= 1
    recent = comments[-max_comments:] if max_comments else []
    body, body_truncated = _clip(raw.get(C.KEY_BODY), config.BODY_LIMIT)
    return IssueDetail(
        **_summary(repo, raw).model_dump(),
        is_pull_request=C.KEY_PULL_REQUEST in raw,
        body=body,
        body_truncated=body_truncated,
        assignees=[a[C.KEY_LOGIN] for a in raw.get(C.KEY_ASSIGNEES) or []],
        milestone=(raw.get(C.KEY_MILESTONE) or {}).get(C.KEY_TITLE),
        recent_comments=[_comment(c) for c in recent],
        comments_omitted=max(0, total - len(recent)),
    )


@mcp.tool(
    title=C.CREATE_ISSUE_TITLE,
    annotations=C.CREATE_ANNOTATIONS,
)
@agent_errors
async def create_issue(
    repo: Repo,
    title: Annotated[
        str,
        Field(
            min_length=C.MIN_TEXT_LENGTH,
            max_length=config.ISSUE_TITLE_LIMIT,
            pattern=C.NONBLANK_PATTERN,
        ),
    ],
    body: Annotated[
        str, Field(max_length=config.ISSUE_BODY_LIMIT, description=C.BODY_DESCRIPTION)
    ] = "",
    labels: Annotated[
        list[LabelName],
        Field(max_length=config.CREATE_LABEL_LIMIT, description=C.CREATE_LABELS_DESCRIPTION),
    ] = [],
    dry_run: Annotated[
        bool,
        Field(description=C.DRY_RUN_DESCRIPTION),
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
        repo_info = await gh.get(C.REPO_PATH.format(repo=repo))
    except ToolFailure as failure:
        raise _with_hint(
            failure,
            {C.ERROR_NOT_FOUND},
            f"{repo} does not exist or the GitHub App is not installed on it. Call list_repos.",
        ) from None
    if not repo_info.get(C.KEY_HAS_ISSUES, True):
        raise ToolFailure(
            C.ERROR_ISSUES_DISABLED,
            f"Issues are turned off for {repo}.",
            retryable=False,
            hint=C.ISSUES_DISABLED_HINT,
        )
    if labels:
        existing = set()
        page = C.FIRST_PAGE
        while True:
            batch = await gh.get(
                C.LABELS_PATH.format(repo=repo), per_page=config.API_PAGE_SIZE, page=page
            )
            existing.update(lbl[C.KEY_NAME] for lbl in batch)
            if len(batch) < config.API_PAGE_SIZE:
                break
            page += 1
        unknown = [lbl for lbl in labels if lbl not in existing]
        if unknown:
            raise ToolFailure(
                C.ERROR_UNKNOWN_LABELS,
                f"These labels do not exist in {repo}: {', '.join(unknown)}.",
                retryable=False,
                hint=C.LABEL_HINT_PREFIX + ", ".join(sorted(existing)[: config.LABEL_HINT_LIMIT]),
            )

    warnings: list[str] = []
    if not dry_run:
        created = await gh.request(
            C.HTTP_POST,
            C.ISSUES_PATH.format(repo=repo),
            json=preview.model_dump(include={C.KEY_TITLE, C.KEY_BODY, C.KEY_LABELS}),
        )
        issue = _summary(repo, created.json())
        if labels and not issue.labels:
            warnings.append(C.LABELS_DROPPED_WARNING)
        return CreateIssueResult(
            dry_run=False,
            created=True,
            preview=preview,
            warnings=warnings,
            issue=issue,
            next_step=f"Created {issue.url}. Do not call create_issue again for this issue.",
        )

    if labels and not (repo_info.get(C.KEY_PERMISSIONS) or {}).get(C.KEY_PUSH):
        warnings.append(C.LABELS_WILL_DROP_WARNING)
    phrase = " ".join(title.replace('"', " ").replace("\\", " ").split())
    similar = await gh.get(
        C.SEARCH_ISSUES_PATH,
        q=C.DUPLICATE_QUERY_TEMPLATE.format(repo=repo, phrase=phrase),
        per_page=config.DUPLICATE_CHECK_LIMIT,
    )
    if similar.get(C.KEY_INCOMPLETE_RESULTS):
        warnings.append(C.INCOMPLETE_DUPLICATES_WARNING)
    warnings += [
        f"Possible duplicate: #{i[C.KEY_NUMBER]} {i[C.KEY_TITLE]!r} ({i[C.KEY_HTML_URL]})"
        for i in similar[C.KEY_ITEMS]
    ]
    return CreateIssueResult(
        dry_run=True,
        created=False,
        preview=preview,
        warnings=warnings,
        next_step=(C.PREVIEW_NEXT_STEP),
    )


if __name__ == "__main__":
    mcp.run(show_banner=False)
