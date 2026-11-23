# Assignment 6 (Writeup)

## Part I: Baseline

I ran the provided `run.sh` with `python tools/practice.py --keep` on the starter incident.

| Run | Repair | Impact | Cost | Model requests | Time |
| --- | ---: | ---: | ---: | ---: | ---: |
| `20261123-114914-1` | 1.00 | 0.00 | $2.0352 | 32 | 338.7 s |

| Model | Input | Output | Cache read | Cache write | Cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sonnet 5.5 | 17,619 | 41,086 | 3,397,733 | 312,459 | $2.0352 |

Cache reads had the largest token count. Cache writes cost the most, at $1.2493. One-hour writes accounted for $1.2485 of that amount. The trace shows that the agent loaded local memory and repeatedly read large sections of source and documentation. Later requests carried this growing context.

| Category | Passed |
| --- | ---: |
| Incident | 9 / 9 |
| Regressions | 10 / 10 |
| Compatibility | 2 / 2 |

The agent found the in-memory idempotency cache in the API code. It examined the evidence, then fixed the API and router and ran their tests. It reached $2.0352 after that test command. The gateway refused the next request. The scorer found no `out/impact.json`, so it recorded precision and recall of 0.00 and zero of six correct figures.

## Part II: Experiments

| # | Change | Why I expected it to help | Runs passed / attempted | Avg repair / impact | Avg cost | Kept? |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 1 | A single Sonnet session with a shorter system prompt, safe mode, and a report-first instruction | Remove local startup context and get the report onto disk before the repair consumes the budget | 0 / 1 | 1.00 / 0.93 | $1.0590 | No |
| 2 | Haiku for the report, Sonnet for the repair, and five-minute prompt caching | Give each stage its own context and let the smaller model do evidence processing | 1 / 1 | 1.00 / 1.00 | $0.4000 | Yes |
| 3 | Run the two sessions concurrently | Give both deliverables the full ten-minute window | 2 / 2 | 1.00 / 1.00 | $0.6470 | Yes |
| 4 | Lower Sonnet repair effort from high to medium | See whether a lower effort setting reduces the repair cost while keeping incident coverage | 0 / 1 | 0.44 / 1.00 | $0.4633 | No |

**What fixed the failing category.** The separate report session focused on the evidence packet and checked malformed rows per file. The single-session run found the full affected set and got five of six figures right. The split run returned the same currency totals and counted three more corrupt rows. The scorer accepted all six figures in that run.

**What saved the most money.** The split moved the report to Haiku, which cost $0.0548. The Sonnet repair cost $0.3452. Both models used five-minute cache writes. These changes were tested together, so the total savings include routing, separate contexts, and the cache setting. [Claude Code prompt caching](https://code.claude.com/docs/en/prompt-caching)

**What fell short.** The report-first instruction let the single session finish both artifacts. It still spent time exploring the repair before writing the report and miscounted corrupt rows. The medium-effort repair was cheaper than the high-effort average. It passed all regression and compatibility checks but missed five incident scenarios, including cancellation of deliveries already queued before deployment. Both high-effort concurrent runs passed all 21 repair checks.

**Setup.** `run.sh` reads the supplied ticket and launches two Claude Code sessions through the course gateway. Both run at high effort. Haiku uses the evidence contract and local parsing tools to write the report. Sonnet traces the affected service code and runs focused checks. The stages share the workspace and target different output paths. The wrapper waits for both and checks that the report is readable JSON. The practice scorer measures the correctness of both artifacts.

**Final setup on the starter incident.**

| Run | Repair | Impact | Cost | Time |
| --- | ---: | ---: | ---: | ---: |
| `20261123-123015-1` | 1.00 | 1.00 | $0.4350 | 269.7 s |
| `20261123-123512-1` | 1.00 | 1.00 | $0.8590 | 478.6 s |

The first concurrent run finished 146.1 seconds sooner than the sequential run. The repeat took 149 seconds to return its first metered response. Sonnet output grew from 16,972 to 34,010 tokens, and cache reads grew from 751,126 to 2,397,355 tokens. The repeat exceeded the $0.75 full-credit cost threshold. The two runs averaged $0.6470 and finished within ten minutes.

**What should transfer.** Each phase reads the current ticket and the relevant contracts. The report phase checks evidence sources, grouping, units, and malformed rows. The repair phase traces the current symptom through the active services. The measured scores apply to the starter incident. The held-out run will test whether these instructions work with different evidence and a different bug.

## Part III: Graded Submissions

Gradescope results are pending.
