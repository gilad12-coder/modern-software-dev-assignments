# Level
**Level 3, 47.1%** (32 of 68 evaluated signals passed; 16 were skipped). The report was stored. The repository remained unchanged.

# Applications
1. `.` - Pydantic Python data-validation library.
2. `pydantic-core` - Separately built Rust/Python validation and serialization package.

# Criteria

Scores use the two applications as the denominator for application checks. `N/A` means the criterion was skipped.

**Style & Validation**
- Linter configured: 2/2 - Both packages configure Ruff.
- Type checker: 2/2 - Both configure Pyright; core also compiles Rust.
- Formatter: 2/2 - Both use Ruff format; core also uses `cargo fmt`.
- Pre-commit hooks: 2/2 - Both packages configure quality hooks.
- Strict typing: 0/2 - Strict checking is limited to one root test file.
- Naming consistency: 1/2 - Core enforces Rust naming warnings; root lacks naming rules.
- Cyclomatic complexity: 1/2 - Core enables Ruff complexity checks; root sets a limit without enabling the rule.
- Large-file detection: 1/1 - Core enables `check-added-large-files`.
- Dead-code detection: 1/2 - Core treats Rust dead-code warnings as errors.
- Duplicate-code detection: 0/2 - No duplicate-code checker was found.
- Code modularization: 0/2 - No module-boundary enforcement was found.
- Tech-debt tracking: 0/1 - No enforced TODO or FIXME tracking was found.
- N+1 query detection: N/A/2 - Neither library owns database queries.
- Heavy-dependency detection: N/A/2 - Neither package is a bundled application.
- Unused-dependency detection: 0/2 - No unused-dependency check was found.

**Build System**
- Build command documented: 0/1 - Commands appear in the contributing guide, not the root README or AGENTS.md.
- Dependencies pinned: 1/1 - The repository commits uv and Cargo lockfiles.
- VCS CLI tools: 1/1 - GitHub CLI access worked.
- Automated PR review: 0/1 - Recent PRs showed no generated code reviews.
- Agentic development: 0/1 - No active coding-agent workflow or recent agent co-authorship was found.
- Fast CI feedback: 0/1 - Most sampled PR check spans exceeded 10 minutes.
- Build performance tracking: 0/1 - Build caching exists, but build-duration monitoring was not found.
- Deployment frequency: 0/1 - Automated releases did not occur multiple times per week.
- Single-command setup: 0/1 - Root README and AGENTS.md lack a fresh-clone development path.
- Feature-flag infrastructure: 0/1 - No feature-flag system was found.
- Release-notes automation: 1/1 - Release scripts and GitHub release categories prepare notes.
- Progressive rollout: N/A/1 - This is not an infrastructure repository.
- Rollback automation: N/A/1 - The packages are published libraries, not managed deployments.
- Monorepo tooling: 1/1 - A uv workspace includes pydantic-core.
- Version-drift detection: 1/1 - A CI test checks the pinned companion core version.
- Release automation: 1/1 - Tag-triggered CI builds and publishes both packages.
- Dead-feature-flag detection: N/A/1 - There is no feature-flag system.

**Testing**
- Unit tests present: 2/2 - Both packages have unit-test suites.
- Integration tests present: 2/2 - Plugin, third-party, and cross-package tests exist.
- Unit tests runnable: 1/2 - Core collected three tests. Root collection failed because installed core 2.41.5 differs from required 2.50.0.
- Test performance tracking: 1/2 - Root CI reports test durations; core lacks retained timing reports.
- Flaky-test detection: 0/2 - No retry, quarantine, or stability-tracking system was found.
- Coverage thresholds: 1/2 - Root CI sets a 91% threshold; core does not enforce one.
- Test naming conventions: 0/2 - Neither pytest configuration explicitly sets a test-file pattern.
- Test isolation: 2/2 - Root supports parallel test execution; core uses isolated test fixtures.
- Interactive QA documented: 2/2 - Both READMEs provide installation and validation examples.
- Interactive QA runnable: 2/2 - Both have complete documented fallback paths. This audit did not install packages or run those paths.

**Documentation**
- AGENTS.md: 0/1 - The root file only points to the contributing guide.
- README: 1/1 - Root README includes installation and usage.
- Automated documentation generation: 1/1 - MkDocs generates API documentation in CI.
- Skills: 1/1 - A valid Pydantic skill exists.
- Documentation freshness: 1/1 - Key documents changed within 180 days.
- API schema docs: N/A/2 - Neither package hosts a service API.
- Service flow documented: 1/1 - Architecture docs describe the two-package validation flow.
- AGENTS.md validation: 0/1 - No check validates its guidance.

**Dev Environment**
- Dev container: 0/1 - No devcontainer configuration was found.
- Environment template: 0/1 - No `.env.example` or root environment-variable guidance was found.
- Local services setup: N/A/1 - Library development needs no external local service.
- Database schema: N/A/2 - Neither library owns a database.
- Devcontainer runnable: N/A/1 - The devcontainer CLI is unavailable.

**Debugging & Observability**
- Structured logging: 0/2 - Neither package configures a structured logger.
- Distributed tracing: 0/2 - Neither package propagates its own trace IDs.
- Metrics collection: 0/2 - Logfire examples target consumer applications, not package telemetry.
- Code-quality metrics: 2/2 - Coverage reporting and benchmark dashboards exist.
- Contextual error tracking: 0/2 - No configured production error tracker was found.
- Alerting: 0/2 - No package alert rules were found.
- Runbooks: 0/1 - No incident runbook was found.
- Deployment observability: 0/2 - Release-impact dashboards are not documented.
- Health checks: N/A/2 - Neither package runs as a service.
- Circuit breakers: N/A/2 - Neither package owns external service calls.
- Profiling: 2/2 - CodSpeed profiles both packages; core also documents flamegraphs.
- Product analytics: 0/2 - No product-usage analytics are instrumented.
- Error-to-insight pipeline: 0/2 - No error tracker files issues automatically.

**Security**
- Branch protection: N/A/1 - The authenticated account lacks admin access to verify rules.
- Secret scanning: N/A/1 - No local scanner was found; native scanning could not be verified without admin access.
- CODEOWNERS: 0/1 - No CODEOWNERS file was found.
- Automated security review: N/A/1 - No readable assessment was found; native scanning could not be verified.
- Dependency updates: 1/1 - Dependabot is active for Actions and Cargo.
- Gitignore comprehensive: 0/1 - Root `.gitignore` does not exclude `.env` files.
- DAST scanning: N/A/2 - Neither package is a deployed web service.
- PII handling: 1/2 - Root docs explain sensitive-value handling; core lacks separate guidance.
- Privacy compliance: N/A/1 - The libraries do not directly collect or retain end-user data.
- Secrets management: 1/1 - Workflows use GitHub Actions secrets.
- Log scrubbing: 1/2 - Root docs show Logfire redaction; core lacks equivalent guidance.
- Minimum release age: 1/1 - Dependabot applies a seven-day cooldown.
- Issue templates: 1/1 - Structured bug and feature forms exist.
- Issue labeling system: 0/1 - Type and topic labels exist, but priority tiers do not.
- Backlog health: 1/1 - 44 of 50 sampled open issues had descriptive titles and labels.
- PR templates: 0/1 - The template lacks testing and context sections.

# Action Items
- Expand root `AGENTS.md` with setup, build, test, and validation commands. Check those commands in CI.
- Add a local unused-dependency check and explicit test naming rules for both packages.
- Add testing and context sections to the PR template. Add priority labels and CODEOWNERS.

---
View the full report: https://app.factory.ai/analytics/readiness/https%253A%252F%252Fgithub.com%252Fpydantic%252Fpydantic
