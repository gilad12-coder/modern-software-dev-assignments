# Level
**Level 2, 25.4%** (17 passes, 50 failures, 17 skips). The report was stored for commit `59ca4f7`.

# Applications
1. `.` - FastRTC Python library, with a bundled Gradio UI and example demos.

# Criteria

**Style & Validation**
- Linter configured: 1/1 - Ruff runs in CI.
- Type checker: 1/1 - Pyright runs in CI.
- Formatter: 1/1 - Ruff format and Prettier run in CI.
- Pre-commit hooks: 0/1 - No hooks are configured.
- Strict typing: 0/1 - Pyright strict mode is not enabled.
- Naming consistency: 0/1 - No naming rules are enforced.
- Cyclomatic complexity: 0/1 - No complexity check exists.
- Large file detection: 0/1 - No file-size or line-count check exists.
- Dead code detection: 1/1 - Ruff flags unused imports and variables.
- Duplicate code detection: 0/1 - No duplication check exists.
- Code modularization: 0/1 - No module-boundary check exists.
- Tech debt tracking: 0/1 - TODO markers have no tracking check.
- N+1 query detection: null/1 - The library has no database query layer.

**Build System**
- Build command documented: 0/1 - The README omits the package build command.
- Dependencies pinned: 0/1 - The main Python package has no lockfile.
- VCS CLI tools: 1/1 - GitHub CLI is authenticated.
- Automated PR review: 0/1 - Recent PRs show no generated code reviews.
- Agentic development: 1/1 - Git history includes an AI-agent co-author.
- Fast CI feedback: 1/1 - Nine sampled PRs averaged 117 seconds of CI checks.
- Build performance tracking: 0/1 - No build-duration monitoring exists.
- Deployment frequency: 0/1 - Releases and deployments are not frequent.
- Single-command setup: 1/1 - Installation and `just` launch targets provide a short path.
- Feature-flag infrastructure: 0/1 - No flag system is configured.
- Release notes automation: 0/1 - No automated release notes exist.
- Progressive rollout: null/1 - This is not an infrastructure repository.
- Rollback automation: null/1 - This is not an infrastructure repository.
- Monorepo tooling: null/1 - This is one library application.
- Heavy dependency detection: 0/1 - No frontend size budget or analyzer exists.
- Unused dependencies detection: 0/1 - No dependency-use check exists.
- Version drift detection: 0/1 - No cross-package version check exists.
- Release automation: 1/1 - CI publishes documentation on main pushes.
- Dead feature-flag detection: null/1 - No feature-flag system exists.

**Testing**
- Unit tests exist: 1/1 - Python unit tests are present.
- Integration tests exist: 1/1 - API and WebRTC connection tests are present.
- Unit tests runnable: 0/1 - Bounded collection failed because `fastrtc` was not importable.
- Test performance tracking: 0/1 - CI does not retain test timing metrics.
- Flaky test detection: 0/1 - No retry or stability tracking exists.
- Test coverage thresholds: 0/1 - No coverage minimum is enforced.
- Test naming conventions: 0/1 - No explicit naming rule is configured.
- Test isolation: 1/1 - Async fixture loops use function scope.
- Interactive QA documented: 1/1 - The echo UI has a setup, launch, and microphone path.
- Interactive QA runnable: 1/1 - The complete documented path qualified as fallback; it was not launched.

**Documentation**
- AGENTS.md: 0/1 - No root AGENTS.md exists.
- README: 1/1 - The root README covers installation and usage.
- Automated doc generation: 1/1 - MkDocs builds and publishes documentation.
- Skills: 0/1 - No repository skill is configured.
- Documentation freshness: 0/1 - Key documentation changed more than 180 days ago.
- API schema docs: null/1 - The root application is a library, not a deployed API.
- Service flow documented: 1/1 - Guides explain TURN providers and API flows.
- AGENTS.md validation: 0/1 - There is no AGENTS.md to validate.

**Dev Environment**
- Devcontainer: 0/1 - No devcontainer is configured.
- Environment template: 0/1 - No `.env.example` exists; the root README omits environment variables.
- Local services setup: null/1 - The local echo path needs no mandatory service.
- Database schema: null/1 - The library has no database.
- Devcontainer runnable: null/1 - The devcontainer CLI is unavailable.

**Debugging & Observability**
- Structured logging: 0/1 - Logging is not structured.
- Distributed tracing: 0/1 - No trace-ID propagation exists.
- Metrics collection: 0/1 - No performance telemetry is configured.
- Code quality metrics: null/1 - No local metrics exist; the native check needs admin access.
- Contextual error tracking: 0/1 - No contextual error tracker exists.
- Alerting: 0/1 - No alert rules exist.
- Runbooks: 0/1 - No incident runbook is linked.
- Deployment observability: 0/1 - No deploy-impact dashboard or notification is documented.
- Health checks: null/1 - The library is not itself a deployed service.
- Circuit breakers: null/1 - External TURN calls are optional library integrations.
- Profiling: 0/1 - No profiling setup exists.
- Product analytics: 0/1 - No usage analytics are instrumented.
- Error-to-insight pipeline: 0/1 - Errors do not create linked issues automatically.

**Security**
- Branch protection: null/1 - GitHub admin access is unavailable.
- Secret scanning: null/1 - No local scan exists; the native check needs admin access.
- CODEOWNERS: 0/1 - No CODEOWNERS file exists.
- Automated security review: null/1 - No local report exists; the native check needs admin access.
- Dependency update automation: 0/1 - No Dependabot or Renovate setup exists.
- Gitignore coverage: 0/1 - It omits `.idea` and some build artifacts.
- DAST scanning: null/1 - The root library is not a deployed web service.
- PII handling: 0/1 - No handling procedure exists for user audio or video.
- Privacy compliance: null/1 - The library does not itself retain end-user data.
- Secrets management: 0/1 - No managed-secrets pattern is configured.
- Log scrubbing: 0/1 - No log-redaction mechanism exists.
- Minimum release age: 0/1 - No dependency waiting period is defined.

**Project Workflow**
- Issue templates: 0/1 - No issue templates exist.
- Issue labeling system: 0/1 - Priority labels are missing.
- Backlog health: 0/1 - Most sampled open issues have no label.
- PR templates: 0/1 - No PR template exists.

# Action Items
- Add `AGENTS.md` with build, test, and local QA commands.
- Pin Python dependencies and make the bounded test collection work from a fresh checkout.
- Add issue and PR templates, priority labels, and a dependency update policy.

---
View the full report: https://app.factory.ai/analytics/readiness/https%253A%252F%252Fgithub.com%252Fgradio-app%252Ffastrtc
