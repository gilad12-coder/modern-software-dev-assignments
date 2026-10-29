# Week 5 Write-up

## Repositories chosen

I compared Pydantic, pandas, and FastRTC. All three expose Python APIs, but their implementation languages and project sizes differ.

| Repo | Languages | Size | Created / current activity |
|---|---|---|---|
| [Pydantic](https://github.com/pydantic/pydantic/tree/dd0c36a4be235522e34659ba372c59b43b55f33e) | Python and Rust | 872 tracked files; 181,487 Python lines | Created 2017-05-03; checked-out commit 2026-10-29; 29,232 stars at capture |
| [pandas](https://github.com/pandas-dev/pandas/tree/0988929a21cdcc933b380871a622138eb18cc207) | Python, Cython, C/C++ | 2,688 tracked files; 746,288 Python lines | Created 2010-08-24; checked-out commit 2026-10-29; 50,252 stars at capture |
| [FastRTC](https://github.com/gradio-app/fastrtc/tree/59ca4f77e1669a9599c0895fd0d7c39f356bf89f) | Python API; JavaScript, Svelte, TypeScript frontend | 264 tracked files; 10,712 Python lines | Created 2024-09-25; checked-out commit 2026-10-21; 4,636 stars at capture |

Size counts come from the checked-out commits. Python line counts include tests, comments, and blank lines, and exclude other languages. Dates describe GitHub repository creation, not the first release of each project. GitHub reports JavaScript as FastRTC's largest language by bytes; its Python library includes a browser frontend. This is a comparison within the Python ecosystem, with limited language diversity. [Repository metadata](reports/repository-metadata.json)

## Method and limits

I ran Factory's native `/readiness-report` command on October 29, 2026, using Droid 0.231.0 and its default GPT-6 Sol model at medium effort. Each repository had a clean working tree at the recorded commit. Reports used local source and available GitHub evidence. The runs did not install dependencies or change repository files.

Droid assessed two Pydantic packages, three pandas applications, and one FastRTC application:

- Pydantic: the main Python package and `pydantic-core`.
- pandas: the library, the static website, and the JupyterLite browser REPL.
- FastRTC: one library application, including its bundled UI and demos.

The current command evaluates 84 criteria. A repository criterion has denominator 1. An application criterion can receive partial credit, such as 2/3. A null numerator means skipped and contributes nothing to either side of the average.

There is a scoring-version mismatch. The [course's linked article](https://factory.com/news/agent-readiness) describes progression through 80% completion of successive levels. The installed command instead averages all non-skipped criterion fractions, with level boundaries at 20%, 40%, 60%, and 80%. I report the levels that this command actually produced. I do not apply the article's different progression rule to these results. [Run metadata](reports/run-metadata.json)

The pillar table below uses the assignment's eight headings. I separated Code Quality from the current Style & Validation group. Task Discovery belongs under Security & Governance here; product analytics belongs under Observability. The [mapping](reports/pillar-mapping.json) assigns every criterion exactly once. These pillar scores are my calculations from the native results, not extra scores returned by Factory.

Test evidence is limited to collection, not test execution. The Pydantic core sample collected three tests; the pandas website sample collected five. Pydantic's main sample failed because the installed core version was 2.41.5, while the checkout required 2.50.0. The pandas library sample failed on missing compiled extensions and a local PyArrow/NumPy incompatibility. FastRTC's sample failed because the package was not installed. These failures describe the assessment environment; they do not establish broken tests in the projects. Successful collection also does not verify compiled extensions from these commits.

Pydantic's first run stopped at a test-collection permission check. I resumed the same session with permission for those bounded commands. Storage succeeded and the complete report appeared, but the resumed CLI exited 1 and repeated its summary in an error event. Its cause remains unconfirmed. The other two CLIs exited 0. All three successful storage receipts are included. Pandas also restricted issue and PR interactions in its repository instructions, which caused Droid to skip several remote checks. The available evidence therefore differs between repositories.

## Part I: Report results

### Summary

| Repo | Native maturity level | Weighted score | Complete / partial / zero / skipped criteria | Next level |
|---|---|---|---|---|
| Pydantic | Level 3 | 47.1% (32/68) | 28 / 8 / 32 / 16 | 60% |
| pandas | Level 3 | 43.6% (29.667/68) | 19 / 19 / 30 / 16 | 60% |
| FastRTC | Level 2 | 25.4% (17/67) | 17 / 0 / 50 / 17 | 40% |

“Points” means the sum of criterion fractions. Pydantic has 28 complete passes and eight half-passes, totaling 32 points. Its native summary's phrase “32 ... signals passed” is shorthand, not a count of complete passes. Pandas has 19 complete passes and 19 partial passes. FastRTC has 17 complete passes and no partial passes.

The current scoring rule has no mandatory, level-specific blocking criterion. With the same denominators and skip decisions, Pydantic needs at least nine complete criterion improvements to reach 60%; pandas needs twelve. FastRTC needs ten to reach 40%. Partial improvements can require more changes. One implementation change can also improve several criteria.

The main candidates are setup and build guidance, missing coverage or validation checks, and incomplete application coverage. Pydantic's unresolved criteria include `agents_md`, `build_cmd_doc`, and `single_command_setup`. Pandas loses credit on its browser REPL and has no enforced coverage threshold. FastRTC lacks contributor guidance, Python dependency pinning, pre-commit hooks, and several contribution-process checks. The full inventory follows below.

### Pillar scores

Each cell shows percent and weighted points divided by evaluated criteria. A 1/2 criterion contributes 0.5 points. Skips are excluded. Pillars have different numbers of criteria, so averaging the eight percentages would give the wrong overall score. Displayed values are rounded.

| Pillar | Pydantic | pandas | FastRTC |
|---|---|---|---|
| Style & Validation | 75.0% (4.5/6) | 61.1% (3.667/6) | 50.0% (3/6) |
| Build System | 40.0% (6/15) | 53.8% (7/13) | 33.3% (5/15) |
| Testing | 65.0% (6.5/10) | 46.7% (4.667/10) | 50.0% (5/10) |
| Documentation | 71.4% (5/7) | 71.4% (5/7) | 42.9% (3/7) |
| Dev Environment | 0.0% (0/2) | 0.0% (0/2) | 0.0% (0/2) |
| Code Quality | 42.9% (3/7) | 23.8% (1.667/7) | 16.7% (1/6) |
| Observability | 10.0% (1/10) | 13.9% (1.667/12) | 0.0% (0/10) |
| Security & Governance | 54.5% (6/11) | 54.5% (6/11) | 0.0% (0/11) |

### Failed criteria by pillar

The inventory includes both zero scores and partial scores. A partial score identifies uneven coverage between applications. Skipped criteria remain in the raw reports and are not presented as failures.

<details>
<summary>Complete failed and partial criterion inventory</summary>

#### Style & Validation

- Pydantic: `strict_typing` (0/2); `naming_consistency` (1/2).
- pandas: `lint_config` (2/3); `type_check` (1/3); `formatter` (2/3); `strict_typing` (1/3); `naming_consistency` (2/3).
- FastRTC: `pre_commit_hooks` (0/1); `strict_typing` (0/1); `naming_consistency` (0/1).

#### Build System

- Pydantic: `build_cmd_doc` (0/1); `automated_pr_review` (0/1); `agentic_development` (0/1); `fast_ci_feedback` (0/1); `build_performance_tracking` (0/1); `deployment_frequency` (0/1); `single_command_setup` (0/1); `feature_flag_infrastructure` (0/1); `unused_dependencies_detection` (0/2).
- pandas: `build_cmd_doc` (0/1); `build_performance_tracking` (0/1); `single_command_setup` (0/1); `feature_flag_infrastructure` (0/1); `heavy_dependency_detection` (0/3); `unused_dependencies_detection` (0/3).
- FastRTC: `build_cmd_doc` (0/1); `deps_pinned` (0/1); `automated_pr_review` (0/1); `build_performance_tracking` (0/1); `deployment_frequency` (0/1); `feature_flag_infrastructure` (0/1); `release_notes_automation` (0/1); `version_drift_detection` (0/1); `heavy_dependency_detection` (0/1); `unused_dependencies_detection` (0/1).

#### Testing

- Pydantic: `unit_tests_runnable` (1/2); `test_performance_tracking` (1/2); `flaky_test_detection` (0/2); `test_coverage_thresholds` (1/2); `test_naming_conventions` (0/2).
- pandas: `unit_tests_exist` (2/3); `integration_tests_exist` (2/3); `unit_tests_runnable` (1/3); `test_performance_tracking` (2/3); `flaky_test_detection` (0/3); `test_coverage_thresholds` (0/3); `test_naming_conventions` (1/3); `test_isolation` (2/3); `interactive_qa_exists` (2/3); `interactive_qa_runnable` (2/3).
- FastRTC: `unit_tests_runnable` (0/1); `test_performance_tracking` (0/1); `flaky_test_detection` (0/1); `test_coverage_thresholds` (0/1); `test_naming_conventions` (0/1).

#### Documentation

- Pydantic: `agents_md` (0/1); `agents_md_validation` (0/1).
- pandas: `skills` (0/1); `service_flow_documented` (0/1).
- FastRTC: `agents_md` (0/1); `skills` (0/1); `documentation_freshness` (0/1); `agents_md_validation` (0/1).

#### Dev Environment

- Pydantic: `devcontainer` (0/1); `env_template` (0/1).
- pandas: `devcontainer` (0/1); `env_template` (0/1).
- FastRTC: `devcontainer` (0/1); `env_template` (0/1).

#### Code Quality

- Pydantic: `tech_debt_tracking` (0/1); `cyclomatic_complexity` (1/2); `dead_code_detection` (1/2); `duplicate_code_detection` (0/2); `code_modularization` (0/2).
- pandas: `large_file_detection` (0/1); `tech_debt_tracking` (0/1); `cyclomatic_complexity` (0/3); `dead_code_detection` (2/3); `duplicate_code_detection` (0/3); `code_modularization` (2/3); `code_quality_metrics` (1/3).
- FastRTC: `large_file_detection` (0/1); `tech_debt_tracking` (0/1); `cyclomatic_complexity` (0/1); `duplicate_code_detection` (0/1); `code_modularization` (0/1).

#### Observability

- Pydantic: `runbooks_documented` (0/1); `structured_logging` (0/2); `distributed_tracing` (0/2); `metrics_collection` (0/2); `error_tracking_contextualized` (0/2); `alerting_configured` (0/2); `deployment_observability` (0/2); `product_analytics_instrumentation` (0/2); `error_to_insight_pipeline` (0/2).
- pandas: `runbooks_documented` (0/1); `structured_logging` (0/3); `distributed_tracing` (0/3); `metrics_collection` (0/3); `error_tracking_contextualized` (0/3); `alerting_configured` (2/3); `deployment_observability` (0/3); `health_checks` (0/3); `circuit_breakers` (1/3); `profiling_instrumentation` (0/3); `product_analytics_instrumentation` (0/3); `error_to_insight_pipeline` (2/3).
- FastRTC: `runbooks_documented` (0/1); `structured_logging` (0/1); `distributed_tracing` (0/1); `metrics_collection` (0/1); `error_tracking_contextualized` (0/1); `alerting_configured` (0/1); `deployment_observability` (0/1); `profiling_instrumentation` (0/1); `product_analytics_instrumentation` (0/1); `error_to_insight_pipeline` (0/1).

#### Security & Governance

- Pydantic: `codeowners` (0/1); `gitignore_comprehensive` (0/1); `issue_labeling_system` (0/1); `pr_templates` (0/1); `pii_handling` (1/2); `log_scrubbing` (1/2).
- pandas: `gitignore_comprehensive` (0/1); `issue_labeling_system` (0/1); `pr_templates` (0/1); `dast_scanning` (0/3); `log_scrubbing` (0/3).
- FastRTC: `codeowners` (0/1); `dependency_update_automation` (0/1); `gitignore_comprehensive` (0/1); `secrets_management` (0/1); `min_release_age` (0/1); `issue_templates` (0/1); `issue_labeling_system` (0/1); `backlog_health` (0/1); `pr_templates` (0/1); `pii_handling` (0/1); `log_scrubbing` (0/1).

</details>

### The reports' top remediation suggestions

| Repo | Native report suggestions, summarized |
|---|---|
| Pydantic | Expand root AGENTS.md and validate its commands in CI; check unused dependencies and test names; improve the PR template, priority labels, and CODEOWNERS. |
| pandas | Document a serve-and-drive path for the JupyterLite REPL; enforce a coverage minimum; ignore `.env` files and document build environment variables. |
| FastRTC | Add AGENTS.md with build, test, and local QA commands; pin Python dependencies and make test collection work from a fresh checkout; add contribution templates, priority labels, and dependency updates. |

These are the reports' suggestions. My priorities and reasons appear in Part II.

## Part II: Analysis

### Which pillars failed most?

Development Environment scored 0% for all three repositories. The two scored criteria were a devcontainer and an environment template or documented variables. Other criteria were skipped. That is a narrow result: it does not mean all three repositories lack setup instructions.

Observability was also weak: Pydantic scored 10.0%, pandas 13.9%, and FastRTC 0%. All three failed structured logging, distributed tracing, runtime metrics, contextual error tracking, deployment observability, and product analytics. These are consistent checklist gaps, but their importance depends on the software. Libraries usually run inside someone else's application. Requiring each library to own production dashboards or product analytics gives it responsibilities that may belong to its users.

FastRTC also scored 0% on the eleven evaluated Security & Governance criteria. Its missing issue and PR templates, dependency-update automation, CODEOWNERS, and priority labels are concrete process differences. Branch protection and native secret scanning were skipped for insufficient access, so the report does not establish that they are disabled. Pydantic and pandas both scored 54.5% in this group.

Pandas's weaker Testing and Style & Validation scores need a different explanation. Its library has extensive checks, but the report spreads application criteria across the library, website, and REPL. For example, unit tests exist scored 2/3, while type checking scored 1/3. The configuration-only REPL also lost linting, naming, and formatting credit. A whole-repository average can therefore hide strong library tooling.

### What explains the pattern?

The youngest and smallest repository, FastRTC, scored lowest. Its Python dependency set lacks a lockfile, and several GitHub process files are missing. Contributor commands are not collected in AGENTS.md. The older repositories provide more of that infrastructure.

Age and size do not explain the full ranking. Pandas is older, larger, and more starred than Pydantic, yet its score is lower. The different application boundaries explain part of that result. Size, age, popularity, project purpose, and the amount of non-library code vary together in this sample. Three observations cannot isolate their effects.

The recent contributor counts also resist a simple single-maintainer explanation. The last 100 non-merge commits contained 22 author names for Pydantic, 21 for pandas, and 23 for FastRTC. The most frequent author accounted for 60, 53, and 64 commits, respectively. These counts include automation and describe commits, not hours worked or funding. I cannot infer a corporate-backing effect from them. Pandas documents community maintenance and NumFOCUS support, but this sample does not provide a controlled comparison of staffing models. [Pandas README](https://github.com/pandas-dev/pandas/blob/0988929a21cdcc933b380871a622138eb18cc207/README.md)

Language is also only partly controlled. Pydantic includes Rust, pandas uses Cython and C/C++, and FastRTC includes browser code. Their build and test requirements differ even though their users write Python. I would need more repositories, with comparable application boundaries and prepared environments, before making claims about Python projects generally.

### Cheapest useful fix for each repository

| Repo | One change | Why I would prioritize it |
|---|---|---|
| Pydantic | Put a concise checkout-to-test procedure in root AGENTS.md, including the Rust prerequisite, matching core version, and a focused test command. | I agree with the report's first suggestion, but would focus on version-correct setup before adding further checks. The existing contributing guide already documents `make install` and testing. A clear entry point can help an agent avoid the version mismatch seen here without duplicating the whole guide. |
| pandas | Add a small automated smoke check for the JupyterLite REPL: build it, serve it, import pandas in the browser, and check one DataFrame result. | The report first recommends documenting how to serve and exercise the REPL. A smoke check would verify that path after dependency changes. It targets the application with no tests, while a coverage threshold for the large existing library suite requires a separate baseline decision. |
| FastRTC | Expose the existing CI dependency setup and a bounded test-collection command through one documented contributor check. | The report first recommends AGENTS.md. I would start with the executable procedure that such a file should reference. CI already installs the development and TTS extras before pytest. Reusing that path reduces setup guesswork. The missing-package error is evidence of an unprepared local environment, not proof that the CI recipe fails. |

These are proposed changes; I did not implement them or claim they would pass without verification. The source checks behind these choices are Pydantic's [AGENTS.md](https://github.com/pydantic/pydantic/blob/dd0c36a4be235522e34659ba372c59b43b55f33e/AGENTS.md) and [contributing guide](https://github.com/pydantic/pydantic/blob/dd0c36a4be235522e34659ba372c59b43b55f33e/CONTRIBUTING.md), pandas's [REPL guide](https://github.com/pandas-dev/pandas/blob/0988929a21cdcc933b380871a622138eb18cc207/web/interactive_terminal/README.md), and FastRTC's [test workflow](https://github.com/gradio-app/fastrtc/blob/59ca4f77e1669a9599c0895fd0d7c39f356bf89f/.github/workflows/tests.yml).

### Where the framework falls short

First, several criteria assume an application deployed as a service. Missing product analytics, incident runbooks, or distributed tracing can be reasonable for a reusable library. The skip rules help, but their application is uneven. FastRTC skips health checks as a library. Pandas receives 0/3, including the library, because the same repository contains static sites. Splitting applicable and inapplicable sub-applications would produce a more useful denominator.

Second, location matters too much in some documentation checks. Pydantic fails build-command documentation even though its contributing guide contains build and test commands. Its root AGENTS.md points directly to that guide. A discoverability check should follow that pointer and then test the procedure. Pandas receives a similar failure when its root instructions link to the development guide. Both repositories could improve their entry points, but these scores overstate how much information is missing.

Third, the report mixes observed execution with documented capability. `interactive_qa_runnable` can pass through a documentation fallback; no browser interaction occurred in these runs. Meanwhile, test collection can fail because the assessor did not install the repository. Those are different evidence types. I would report them separately as verified, documented, unavailable, and not applicable.

Finally, a single percentage gives equal weight to checks with very different consequences. A missing priority label, a dependency mismatch, and a missing test suite each affect the checklist. They do not obstruct an agent equally. I would use these reports to identify a small set of changes. I would then measure whether an agent can complete setup, a bounded change, and the relevant checks. That would test whether the proposed improvement actually reduces failed work.

## Raw output and reproducibility

The native reports and summaries are unchanged. Each report contains all 84 criterion values and rationales. The receipts record successful storage. The table calculations are saved in [derived-scores.json](reports/derived-scores.json).

| Repo | Native structured output | Native text output | Storage receipt |
|---|---|---|---|
| Pydantic | [pydantic.native.json](reports/pydantic.native.json) | [pydantic.summary.md](reports/pydantic.summary.md) | [Receipt](reports/pydantic.receipt.json) |
| pandas | [pandas.native.json](reports/pandas.native.json) | [pandas.summary.md](reports/pandas.summary.md) | [Receipt](reports/pandas.receipt.json) |
| FastRTC | [fastrtc.native.json](reports/fastrtc.native.json) | [fastrtc.summary.md](reports/fastrtc.summary.md) | [Receipt](reports/fastrtc.receipt.json) |

<details>
<summary>Pydantic: unchanged native summary</summary>

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

</details>

<details>
<summary>pandas: unchanged native summary</summary>

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

</details>

<details>
<summary>FastRTC: unchanged native summary</summary>

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

</details>
