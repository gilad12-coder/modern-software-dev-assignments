# Week 5 write-up

## Repositories chosen

I compared three Python projects of different ages and sizes. Each also uses other languages.

| Repo | Languages | Size (Python lines) | Creation date |
|---|---|---|---|
| [Pydantic](https://github.com/pydantic/pydantic/tree/dd0c36a4be235522e34659ba372c59b43b55f33e) | Python and Rust | 181,487 | 05/03/2017 |
| [pandas](https://github.com/pandas-dev/pandas/tree/0988929a21cdcc933b380871a622138eb18cc207) | Python, Cython, C/C++ | 746,288 | 08/24/2010 |
| [FastRTC](https://github.com/gradio-app/fastrtc/tree/59ca4f77e1669a9599c0895fd0d7c39f356bf89f) | Python; JavaScript, Svelte, TypeScript in the browser | 10,712 | 09/25/2024 |

## Method and limits

I ran Factory's `/readiness-report` on all three repositories. The [course article](https://factory.com/news/agent-readiness) requires passing 80% of the checks at the target level and earlier levels. Droid 0.231.0 averages all scored checks, with levels starting at 20%, 40%, 60%, and 80%. I used the levels from the raw reports because the assignment asks for Droid's results. I [grouped](reports/pillar-mapping.json) the checks under the eight required pillars.

## Part I: Report results

### Summary

| Repo | Current level | Score | Next level | What to improve first |
|---|---|---|---|---|
| Pydantic | Level 3 | 47.1% | Level 4 at 60% | Agent instructions, build instructions, setup steps |
| pandas | Level 3 | 43.6% | Level 4 at 60% | Tests for the browser Python console, minimum test coverage |
| FastRTC | Level 2 | 25.4% | Level 3 at 40% | Agent instructions, fixed package versions, issue and pull request templates |

### Pillar scores

| Pillar | Pydantic | pandas | FastRTC |
|---|---|---|---|
| Style & Validation | 75.0% | 61.1% | 50.0% |
| Build System | 40.0% | 53.8% | 33.3% |
| Testing | 65.0% | 46.7% | 50.0% |
| Documentation | 71.4% | 71.4% | 42.9% |
| Dev Environment | 0.0% | 0.0% | 0.0% |
| Code Quality | 42.9% | 23.8% | 16.7% |
| Observability | 10.0% | 13.9% | 0.0% |
| Security & Governance | 54.5% | 54.5% | 0.0% |

### Failed or partly passed checks by pillar

| Category | What it covers |
|---|---|
| Style & Validation | Code layout, naming, and data type checks. |
| Build System | How to install, build, review, and release the project. |
| Testing | Whether tests exist, run reliably, and cover enough code. |
| Documentation | Instructions for understanding and contributing to the project. |
| Dev Environment | Tools and settings for working on the project locally. |
| Code Quality | Keeping code simple, organized, and free of duplication. |
| Observability | Finding and investigating problems while the software runs. |
| Security & Governance | Protecting sensitive data and managing contributions. |

1/2 means a check passed for one of two applications; 0/1 means it failed.

#### Style & Validation

- Pydantic: Strict data type checks (0/2); Naming rules (1/2).
- pandas: Code error and style checks (2/3); Data type checks (1/3); Automatic formatting (2/3); Strict data type checks (1/3); Naming rules (2/3).
- FastRTC: Checks before committing (0/1); Strict data type checks (0/1); Naming rules (0/1).

#### Build System

- Pydantic: Build instructions (0/1); Automated code review (0/1); Use of coding agents (0/1); Fast automated checks (0/1); Build time tracking (0/1); Release frequency (0/1); Setup steps (0/1); Feature on/off switches (0/1); Checks for unused packages (0/2).
- pandas: Build instructions (0/1); Build time tracking (0/1); Setup steps (0/1); Feature on/off switches (0/1); Checks for large dependencies (0/3); Checks for unused packages (0/3).
- FastRTC: Build instructions (0/1); Fixed package versions (0/1); Automated code review (0/1); Build time tracking (0/1); Release frequency (0/1); Feature on/off switches (0/1); Automatic release notes (0/1); Version mismatch checks (0/1); Checks for large dependencies (0/1); Checks for unused packages (0/1).

#### Testing

- Pydantic: Loading tests locally (1/2); Test run times (1/2); Finding tests that fail inconsistently (0/2); Minimum test coverage (1/2); Test naming rules (0/2).
- pandas: Unit tests (2/3); Integration tests (2/3); Loading tests locally (1/3); Test run times (2/3); Finding tests that fail inconsistently (0/3); Minimum test coverage (0/3); Test naming rules (1/3); Keeping tests independent (2/3); Instructions for trying the software (2/3); Working or documented usage steps (2/3).
- FastRTC: Loading tests locally (0/1); Test run times (0/1); Finding tests that fail inconsistently (0/1); Minimum test coverage (0/1); Test naming rules (0/1).

#### Documentation

- Pydantic: Agent instructions (0/1); Checking the agent instructions (0/1).
- pandas: Reusable task guides for agents (0/1); How parts connect and share data (0/1).
- FastRTC: Agent instructions (0/1); Reusable task guides for agents (0/1); Recent documentation updates (0/1); Checking the agent instructions (0/1).

#### Dev Environment

- Pydantic: Development container (0/1); Environment variable instructions (0/1).
- pandas: Development container (0/1); Environment variable instructions (0/1).
- FastRTC: Development container (0/1); Environment variable instructions (0/1).

#### Code Quality

- Pydantic: Tracking needed code cleanup (0/1); Checks for overly complex code (1/2); Checks for unused code (1/2); Checks for repeated code (0/2); Rules for how code modules connect (0/2).
- pandas: Checks for large files (0/1); Tracking needed code cleanup (0/1); Checks for overly complex code (0/3); Checks for unused code (2/3); Checks for repeated code (0/3); Rules for how code modules connect (2/3); Code quality measurements (1/3).
- FastRTC: Checks for large files (0/1); Tracking needed code cleanup (0/1); Checks for overly complex code (0/1); Checks for repeated code (0/1); Rules for how code modules connect (0/1).

#### Observability

- Pydantic: Instructions for handling failures (0/1); Logs with consistent fields (0/2); Following requests across components (0/2); Performance and error measurements (0/2); Error reports with useful details (0/2); Failure alerts (0/2); Tracking the effects of releases (0/2); Tracking how people use the software (0/2); Automatic issue reports from errors (0/2).
- pandas: Instructions for handling failures (0/1); Logs with consistent fields (0/3); Following requests across components (0/3); Performance and error measurements (0/3); Error reports with useful details (0/3); Failure alerts (2/3); Tracking the effects of releases (0/3); Checks that services are working (0/3); Protection when dependencies fail (1/3); Finding where time and memory are spent (0/3); Tracking how people use the software (0/3); Automatic issue reports from errors (2/3).
- FastRTC: Instructions for handling failures (0/1); Logs with consistent fields (0/1); Following requests across components (0/1); Performance and error measurements (0/1); Error reports with useful details (0/1); Failure alerts (0/1); Tracking the effects of releases (0/1); Finding where time and memory are spent (0/1); Tracking how people use the software (0/1); Automatic issue reports from errors (0/1).

#### Security & Governance

- Pydantic: Assigned code reviewers (0/1); Keeping unwanted files out of Git (0/1); Labels showing issue priority (0/1); Pull request templates (0/1); Protecting personal information (1/2); Removing private information from logs (1/2).
- pandas: Keeping unwanted files out of Git (0/1); Labels showing issue priority (0/1); Pull request templates (0/1); Security tests on the running software (0/3); Removing private information from logs (0/3).
- FastRTC: Assigned code reviewers (0/1); Automatic dependency updates (0/1); Keeping unwanted files out of Git (0/1); Secure storage for passwords and tokens (0/1); Waiting before adopting new package releases (0/1); Issue templates (0/1); Labels showing issue priority (0/1); Clear and up-to-date issues (0/1); Pull request templates (0/1); Protecting personal information (0/1); Removing private information from logs (0/1).

### The reports' suggested fixes

| Repo | Report suggestions |
|---|---|
| Pydantic | Expand AGENTS.md and automatically check its instructions. Add checks for unused packages and test names. Improve pull request templates, priority labels, and reviewer assignments. |
| pandas | Document how to try the browser Python console. Set a minimum test coverage requirement, ignore `.env` files, and document build settings. |
| FastRTC | Add AGENTS.md and use fixed Python package versions. Check that tests load after a fresh installation. Add contribution templates, priority labels, and automatic dependency updates. |

## Part II: Analysis

### Which pillars failed most?

The Dev Environment pillar scored 0% for all three repositories. Its scored checks covered only development containers and setup settings. Observability scores ranged from 0% to 13.9%, with gaps in logging, tracing, and usage tracking. Only FastRTC scored 0% on the Security & Governance checks Droid could assess. It lacked contribution templates, automatic dependency updates, a file that assigns code reviewers, and priority labels. Droid could not verify its branch protection or secret scanning.

### What explains the pattern?

FastRTC, the youngest and smallest project, has gaps in fixed package versions and contributor instructions. Pandas is older and larger than Pydantic but scores lower. Its website and browser console bring down the average; only two of its three applications have unit tests. Since all three projects mix Python with other languages, I cannot make a clear comparison by language.

Pydantic, pandas, and FastRTC had 22, 21, and 23 author names in their last 100 non-merge commits, including bots. Pydantic assigns [company engineers](https://pydantic.dev/jobs/evals-continuous-learning-engineer) to its libraries, and pandas has [NumFOCUS support](https://github.com/pandas-dev/pandas/blob/0988929a21cdcc933b380871a622138eb18cc207/README.md). These counts do not tell us how many people actively maintain each project. Without a confirmed example of a project maintained by one person, this sample cannot show how company support affects readiness.

### Cheapest useful fix for each repository

| Repo | Proposed fix | Why this fix |
|---|---|---|
| Pydantic | Add setup and test commands to [AGENTS.md](https://github.com/pydantic/pydantic/blob/dd0c36a4be235522e34659ba372c59b43b55f33e/AGENTS.md). | Pydantic's main tests could not load because the installed pydantic-core version was incompatible. I agree with the report's recommendation because the [guide](https://github.com/pydantic/pydantic/blob/dd0c36a4be235522e34659ba372c59b43b55f33e/CONTRIBUTING.md) already provides `make install` and test commands to add to AGENTS.md. Copying those steps takes only a short documentation edit. Agents would have setup steps to follow from the start, which could reduce version mistakes and help them check their changes sooner. |
| pandas | Add a basic test: build and open the [browser Python console](https://github.com/pandas-dev/pandas/blob/0988929a21cdcc933b380871a622138eb18cc207/web/interactive_terminal/README.md), import pandas, and check one DataFrame result. | The browser console is the only pandas application in the report without unit tests. I would reuse its existing build for a basic test to keep the setup work small. The report recommends usage instructions. A test takes more effort to write, but it checks whether the console still works after updates. Agents could rerun it to catch broken imports or incorrect results. |
| FastRTC | Document one command to install [test packages](https://github.com/gradio-app/fastrtc/blob/59ca4f77e1669a9599c0895fd0d7c39f356bf89f/.github/workflows/tests.yml) and load the tests. | During the audit, Droid could not load FastRTC's tests because the package was not installed. I would document a setup command using the packages already listed in the test workflow. That keeps the edit small and helps agents install the required packages before they load the tests. The report recommends AGENTS.md and installation improvements; I would add this command first, then reference it from AGENTS.md. |

### Where the framework falls short

Some Observability checks lower a library's score for features that belong in the applications using it. An application can monitor whether its service is running, so the library may not need its own health checks. Droid skips health checks for FastRTC but gives pandas 0/3 across its library and web applications. That makes the scores harder to compare: they partly depend on which checks Droid decides to apply. Droid should skip checks that do not fit an application's purpose. I would give more weight to whether agents can set up the project, change code, and run useful tests.

## Raw reports

Calculations: [derived-scores.json](reports/derived-scores.json).

| Repo | Full results (JSON) | Report text | Save confirmation |
|---|---|---|---|
| Pydantic | [pydantic.native.json](reports/pydantic.native.json) | [pydantic.summary.md](reports/pydantic.summary.md) | [Receipt](reports/pydantic.receipt.json) |
| pandas | [pandas.native.json](reports/pandas.native.json) | [pandas.summary.md](reports/pandas.summary.md) | [Receipt](reports/pandas.receipt.json) |
| FastRTC | [fastrtc.native.json](reports/fastrtc.native.json) | [fastrtc.summary.md](reports/fastrtc.summary.md) | [Receipt](reports/fastrtc.receipt.json) |

### Pydantic

````text
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
````

### pandas

````text
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
````

### FastRTC

````text
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
````
