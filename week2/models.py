"""Data models shared by configuration, OAuth, GitHub, and MCP tools."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import constants as C
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class Settings:
    """Configuration read from the environment (and ``week2/.env``).

    Attributes:
        client_id: GitHub App client ID, or None if unset.
        client_secret: GitHub App client secret, or None if unset.
        token_file: Where the token cache lives, outside the repo.
        api_url: Base URL of the GitHub REST API.
        oauth_url: Base URL of GitHub's OAuth endpoints.
        callback_port: Local port the login flow listens on.
        callback_host: Local address used for the OAuth redirect.
    """

    client_id: str | None
    client_secret: str | None
    token_file: Path
    api_url: str
    oauth_url: str
    callback_port: int
    callback_host: str

    @property
    def redirect_uri(self) -> str:
        """The OAuth callback URL registered on the GitHub App.

        Returns:
            ``http://127.0.0.1:<callback_port>/callback``.
        """
        return f"http://{self.callback_host}:{self.callback_port}{C.OAUTH_CALLBACK_PATH}"


@dataclass(frozen=True)
class Token:
    """A cached user token pair with absolute expiry times.

    Attributes:
        access_token: Token sent to the API; lasts 8 hours.
        expires_at: Unix time when the access token expires.
        refresh_token: Single-use token that buys a new pair.
        refresh_expires_at: Unix time when the refresh token expires.
    """

    access_token: str
    expires_at: float
    refresh_token: str
    refresh_expires_at: float

    @classmethod
    def from_response(cls, data: dict, now: float | None = None) -> Token:
        """Build a token from GitHub's token endpoint response.

        Args:
            data: Decoded JSON from ``/login/oauth/access_token``.
            now: Current Unix time; defaults to ``time.time()``.

        Returns:
            The token with relative lifetimes turned into absolute times.
        """
        now = time.time() if now is None else now
        return cls(
            access_token=data[C.KEY_ACCESS_TOKEN],
            expires_at=now + int(data[C.KEY_EXPIRES_IN]),
            refresh_token=data[C.KEY_REFRESH_TOKEN],
            refresh_expires_at=now + int(data[C.KEY_REFRESH_TOKEN_EXPIRES_IN]),
        )


@dataclass
class ToolFailure(Exception):
    """A failure reported to the agent as data. ``retryable`` is the key field.

    Attributes:
        error: Short machine-readable code such as ``not_found`` or ``auth_required``.
        message: Human-readable description of what went wrong.
        retryable: Whether repeating the same call unchanged can succeed.
        retry_after_seconds: How long to wait before retrying, when known.
        hint: The next step the agent should take instead of retrying blindly.
        details: Per-field messages GitHub attached to a 422 response.
    """

    error: str
    message: str
    retryable: bool
    retry_after_seconds: int | None = None
    hint: str | None = None
    details: list[str] = field(default_factory=list)

    def payload(self) -> dict[str, Any]:
        """Build the JSON body sent to the agent as the tool error.

        Returns:
            The failure as a dict, leaving out optional fields that are unset.
        """
        out: dict[str, Any] = {
            C.KEY_ERROR: self.error,
            C.KEY_MESSAGE: self.message,
            C.KEY_RETRYABLE: self.retryable,
        }
        if self.retry_after_seconds is not None:
            out[C.KEY_RETRY_AFTER_SECONDS] = self.retry_after_seconds
        if self.details:
            out[C.KEY_DETAILS] = self.details
        if self.hint:
            out[C.KEY_HINT] = self.hint
        return out


class Repository(BaseModel):
    full_name: str = Field(description=C.FULL_NAME_DESCRIPTION)
    description: str
    private: bool
    has_issues: bool = Field(description=C.HAS_ISSUES_DESCRIPTION)
    open_issues_and_prs: int = Field(description=C.OPEN_ISSUES_DESCRIPTION)
    pushed_at: str | None


class RepoList(BaseModel):
    repos: list[Repository]
    total_accessible: int
    note: str | None = None


class IssueSummary(BaseModel):
    repo: str
    number: int
    title: str
    state: C.IssueStatus
    state_reason: str | None = Field(description=C.STATE_REASON_DESCRIPTION)
    author: str | None
    labels: list[str]
    comments: int
    created_at: str
    updated_at: str
    url: str


class SearchResult(BaseModel):
    total_count: int = Field(description=C.TOTAL_COUNT_DESCRIPTION)
    items: list[IssueSummary]
    incomplete_results: bool = Field(default=False, description=C.INCOMPLETE_DESCRIPTION)
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
    recent_comments: list[Comment] = Field(description=C.RECENT_COMMENTS_DESCRIPTION)
    comments_omitted: int = Field(description=C.COMMENTS_OMITTED_DESCRIPTION)


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
