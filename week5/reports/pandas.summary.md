# Level
**Level 3**, 43.6% across 68 evaluated criteria. Sixteen criteria were skipped. The report was stored for commit `0988929a21cdcc933b380871a622138eb18cc207`.

# Applications
1. `.` - pandas data analysis library.
2. `web` - Static pandas project website.
3. `web/interactive_terminal` - Browser-based pandas REPL.

# Criteria
`null` means skipped. Application scores use a denominator of 3. Repository scores use a denominator of 1.

**Style & Validation**
- Linter configured: 2/3 - Ruff covers library and website Python code.
- Type checker: 1/3 - Mypy and Pyright target pandas.
- Formatter: 2/3 - Source formatters cover pandas and the website.
- Pre-commit hooks: 3/3 - Repository hooks also check REPL configuration text.
- Strict typing: 1/3 - Pandas enables several strict Mypy options.
- Naming consistency: 2/3 - Python import and test-name checks apply.
- Cyclomatic complexity: 0/3 - No enforced complexity threshold.
- Large file detection: 0/1 - No file-size gate.
- Dead code detection: 2/3 - Vulture checks Python source.
- Duplicate code detection: 0/3 - No duplication gate.
- Code modularization: 2/3 - Hooks reject cross-module private access.
- Tech debt tracking: 0/1 - No debt-marker tracking check.
- N+1 detection: null/3 - No database-backed service requires it.

**Build System**
- Build command documented: 0/1 - Commands are in the contributor guide, not README or AGENTS.md.
- Dependencies pinned: 1/1 - `pixi.lock` is committed.
- VCS CLI tools: 1/1 - `gh` is installed and authenticated.
- Automated PR review: null/1 - Repository instructions prevented PR inspection.
- Agentic development: 1/1 - Recent commits include AI co-author trailers.
- Fast CI feedback: null/1 - PR check durations were not accessible under repository instructions.
- Build performance tracking: 0/1 - No build-duration trend tracking.
- Deployment frequency: 1/1 - Website publishing runs on main; recent push runs succeeded.
- Single-command setup: 0/1 - Setup needs separate environment and build steps.
- Feature flag infrastructure: 0/1 - No rollout flag system.
- Release notes automation: 1/1 - Release workflow generates draft notes.
- Progressive rollout: null/1 - No applicable service rollout infrastructure.
- Rollback automation: null/1 - No applicable service rollback infrastructure.
- Monorepo tooling: 1/1 - Pixi coordinates the three builds.
- Heavy dependency detection: 0/3 - No size budget or analyzer.
- Unused dependencies detection: 0/3 - No unused-dependency check.
- Version drift detection: null/1 - One shared dependency package.
- Release automation: 1/1 - Workflows publish packages and the website.
- Dead feature flag detection: null/1 - No feature flag system.
- Issue templates: 1/1 - Structured templates cover common issue types.
- Issue labeling system: 0/1 - No complete priority, type, and area scheme.
- Backlog health: null/1 - Repository instructions prevented issue inspection.
- PR templates: 0/1 - The checklist lacks description and context sections.

**Testing**
- Unit tests exist: 2/3 - Library and website have pytest tests.
- Integration tests exist: 2/3 - Library integrations and website generation have tests.
- Unit tests runnable: 1/3 - Website collection succeeded. Library collection failed on missing extensions and a NumPy/PyArrow conflict.
- Test performance tracking: 2/3 - Pytest reports the 30 slowest tests.
- Flaky test detection: 0/3 - No retry or stability tracking found.
- Coverage thresholds: 0/3 - Codecov coverage gates are disabled.
- Test naming conventions: 1/3 - A hook checks pandas test names.
- Test isolation: 2/3 - Pandas uses parallel workers; website tests use temporary paths.
- Interactive QA documented: 2/3 - The REPL guide omits serving and an interaction.
- Interactive QA runnable: 2/3 - Library and website have complete documented paths. This was a documentation fallback, not a live run.

**Documentation**
- AGENTS.md: 1/1 - Root guidance covers tooling and workflow.
- README: 1/1 - Root README covers purpose and installation.
- Automated documentation generation: 1/1 - CI builds and publishes documentation.
- Skills: 0/1 - No repository `SKILL.md` found.
- Documentation freshness: 1/1 - Key documents changed within 180 days.
- API schema docs: null/3 - No HTTP API application.
- Service flow documented: 0/1 - No architecture diagram or service flow document.
- AGENTS.md validation: 1/1 - Repository-wide link checks include its references.

**Dev Environment**
- Devcontainer: 0/1 - No devcontainer configuration.
- Environment template: 0/1 - No environment-variable template or root inventory.
- Local services setup: null/1 - No required local service.
- Database schema: null/3 - None of the applications owns a database.
- Devcontainer runnable: null/1 - No devcontainer or CLI.

**Debugging & Observability**
- Structured logging: 0/3 - No structured logger configured.
- Distributed tracing: 0/3 - No trace propagation configured.
- Metrics collection: 0/3 - No application telemetry configured.
- Code quality metrics: 1/3 - Pandas uploads coverage to Codecov.
- Contextual error tracking: 0/3 - No configured error tracker.
- Alerting: 2/3 - Automation reports nightly-build and broken-link failures.
- Runbooks: 0/1 - No incident-response runbook found.
- Deployment observability: 0/3 - No deployment-impact dashboard reference.
- Health checks: 0/3 - Static sites have no configured probe.
- Circuit breakers: 1/3 - Website generation falls back when GitHub returns 403.
- Profiling: 0/3 - Benchmarks exist, but no profiler is configured.
- Product analytics: 0/3 - No usage analytics found.
- Error-to-insight pipeline: 2/3 - Build and link failures create or update issues.

**Security**
- Branch protection: null/1 - GitHub CLI lacks repository admin access.
- Secret scanning: null/1 - No local scanner; native status needs admin access.
- CODEOWNERS: 1/1 - Maintainers own key paths.
- Automated security review: 1/1 - CodeQL and Scorecard generate assessments.
- Dependency update automation: 1/1 - Dependabot and scheduled lockfile updates run.
- Gitignore comprehensive: 0/1 - `.env` files are not excluded.
- DAST scanning: 0/3 - No running-site security scan.
- PII handling: null/3 - No owned end-user data service.
- Privacy compliance: null/1 - No end-user data collection infrastructure.
- Secrets management: 1/1 - CI injects secrets through GitHub Actions.
- Log scrubbing: 0/3 - No redaction mechanism found.
- Minimum release age: 1/1 - Dependabot waits seven days before updates.

# Action Items
- Add a documented serve-and-drive check for the JupyterLite REPL.
- Enable a minimum coverage gate for pandas.
- Exclude `.env` files and document the environment variables used during builds.

---
View the full report: https://app.factory.ai/analytics/readiness/https%253A%252F%252Fgithub.com%252Fpandas-dev%252Fpandas
