# Assignment 4: source guidance review

Reviewed on October 25, 2026. The [assignment](assignment.md) remains the grading authority.
It requires one concise root guide, repository exploration, two small agent tasks, and one improvement based on observations.
It permits a repository the student did not write and sets no minimum size.

## Sources examined

**Eno Reyes, Factory AI: “Making Codebases Agent Ready.”**
I read the full timestamped transcript and inspected the eight-pillar and verification-loop slides on the publisher's page.
This covers the talk through its closing at 15:07; I did not inspect every video frame.
The talk connects automation with explicit acceptance criteria and reliable checks.
Its loop is specify, generate, verify, and iterate. Verification includes automation and human judgment.
The eight pillars span testing, documentation, code quality, builds, development environments, observability, security, and standards.
At 4:40–7:35, the talk explains how implicit knowledge and unreliable checks obstruct that loop.
The final section describes improving the environment as agents reveal gaps.
These are broader engineering principles, not eight additional assignment deliverables.
Sources: [requested video](https://www.youtube.com/watch?v=ShuJ_CN6zr4), [publisher transcript and slides](https://ai.engineer/talks/ShuJ_CN6zr4-making-codebases-agent-ready).

**Michael Crabtree, Basis: “How We Made Our Monorepo Ergonomic for Agents.”**
I read the complete article on Basis's website, dated May 19, 2026.
The requested X page returned HTTP 403. I could not inspect that post's replies or verify its exact wording.
Basis organizes its approach around canonicality, localization, verifiability, interoperability, and default-no.
It separates current instructions from historical context, favors operational directives, and evaluates instructions through agent behavior.
Its large monorepo uses layered instructions, skills, agent roles, shared tools, and automated checks.
Those implementation choices reflect its scale. Its reported productivity changes do not establish results for this assignment.
Sources: [requested X post](https://x.com/trybasis/status/2056881705269580023), [complete Basis article](https://www.getbasis.ai/blogs/how-we-made-our-monorepo-ergonomic-for-agents).

## Application to fsed

The chosen package has 824 implementation lines across four modules at the explored commit.
One root `CLAUDE.md` gives enough navigation without a directory hierarchy of instruction files.
The final guide has 463 whitespace-delimited words. The submission copy matches the fork root.

| Decision | Application and evidence |
|---|---|
| One current guide | The fork root and [submission copy](CLAUDE.md) contain v4. The [evidence index](review-evidence/fsed/README.md) labels v1–v3 as historical snapshots. |
| Put guidance near its use | The root guide names the small set of modules and directs matching, CLI, testing, and packaging work to their owners. |
| Make directions executable | The full-suite command saves output and returns the actual test exit status. Shell checks cover both success and known failure. |
| Keep content portable | Architecture and shell/Python commands are repository knowledge. Trials establish Claude Code use only; other agents' automatic file discovery was not tested. |
| Limit permanent context | Full transcripts, trial logs, the rubric discussion, and source analysis stay outside the root guide. No nested rules, custom skills, or MCP setup were added. |

The v4 architecture section now tells an agent where to act, rather than only describing each file.
It pairs exact paths with entry-point names such as `main` and `AhoCorasickTrie`.
Paths satisfy the assignment's navigation requirement; symbol names provide another search target if files move.

Trial 3 exposed a reporting gap: the agent printed a saved status but omitted the final shell `exit`.
V4 makes the verified wrapper the sole full-suite example and explicitly requires the final `exit`.
This preserves the task-derived improvement and makes it easier to follow.
The [write-up](writeup.md) reports the fresh follow-up trial without changing the earlier observations.

## Verification coverage and limits

This table assesses fsed against the talk's areas. It does not claim complete production readiness.
The supporting commands, outputs, and source links are in the [evidence index](review-evidence/fsed/README.md).

| Area | What this assignment establishes | Remaining limit |
|---|---|---|
| Testing | All 16 baseline tests pass. A temporary CLI regression passes in a 17-test suite. Known discovery failures were reproduced. | No coverage measurement or complete behavior audit. |
| Documentation | The guide explains architecture, commands, conventions, and observed README/code contradictions. | It does not replace the package's API documentation. |
| Code quality | Existing style and test idioms were inspected; syntax compilation passes. | No configured linter, formatter, or type checker. |
| Builds | The pinned environment builds both source and wheel distributions. | No separate clean wheel installation test; legacy metadata warnings remain. |
| Development environment | Python 3.11.9 setup works. The guide excludes generated environments from Git staging. | The old Python 2.7–3.8 matrix was not rerun. |
| Observability | Test output and process exits are retained for checking claims. | This is task evidence, not application telemetry or tracing. |
| Security | Generated files and fixture boundaries are explicit. | No dependency scan, security audit, or secret-scanning setup was performed. |
| Standards | Guidance follows actual `unittest`, bytes/text, compatibility, and fixture conventions. | Enforcement depends on existing tests and review. |

## Rubric result

- **Part I, 20 points:** exact commands, source navigation, implicit conventions, and file boundaries have supporting evidence.
- **Part II, 55 points:** the compact guide covers all five required areas with package-specific directions.
- **Part III, 25 points:** two distinct tasks, actual tool records, and a grounded improvement are present.

The evidence supports all published full-credit criteria. The course staff determine the grade.
The source guidance improves precision without expanding this assignment into a package modernization project.
Neither source justifies claiming that passing tests proves complete agent reliability or production safety.

For submission preparation and remaining portal steps, use the [handoff checklist](submission-checklist.md).
