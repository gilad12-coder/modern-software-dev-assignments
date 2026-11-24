# Assignment 6 (Writeup)

## Part I: Baseline

I ran `python tools/practice.py --keep` with the stock `run.sh`. Starter run `20261123-114914-1` cost $2.0352 for 32 Sonnet 5.5 requests over 338.7 seconds.

| Input tokens | Output tokens | Cache reads | Cache writes |
| ---: | ---: | ---: | ---: |
| 17,619 | 41,086 | 3,397,733 | 312,459 |

Sonnet loaded my local memory and repeatedly read source files and design records. Cache reads accounted for the most tokens. Cache writes cost the most ($1.2493), almost all from one-hour writes ($1.2485).

The API kept idempotency keys in memory. Sonnet suspected a restart or the 24-hour expiry could let a retry create a second event. It checked retries against restart times, moved the lookup into the database, and fixed duplicate handling in the router. Repair scored 1.00 (9/9 incident, 10/10 regression, 2/2 compatibility). After the API and router tests, spending crossed $2.00 and the gateway refused the next request. Sonnet never wrote `out/impact.json`. Impact, precision, and recall were all 0.00, with 0/6 figures correct.

## Part II: Experiments

A pass required 1.00 on both repair and impact. Means include every metered starter run. Experiment 5 had one additional launch that stopped before its first model request and cost $0.

| # | Change | Why I tried it | Passed / metered | Mean repair / impact | Mean cost | Kept? |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 1 | Single Sonnet session, short prompt, safe mode, report first | Skip local memory and finish the report within budget | 0 / 1 | 1.00 / 0.93 | $1.0590 | Replaced |
| 2 | Separate Haiku report and Sonnet repair, [five-minute caching](https://code.claude.com/docs/en/prompt-caching) | Reduce context and spend less on reporting | 1 / 1 | 1.00 / 1.00 | $0.4000 | Yes |
| 3 | Run both sessions in parallel | Give each task the full ten minutes | 2 / 2 | 1.00 / 1.00 | $0.6470 | Yes |
| 4 | Medium-effort Sonnet repair | Lower repair cost | 0 / 1 | 0.44 / 1.00 | $0.4633 | No |
| 5 | Luna report, Terra repair | Try a cheaper pair in Codex | 1 / 2 | 1.00 / 0.97 | $0.0922 | Terra only |
| 6 | Terra report, Luna repair | Test small-model repair in Codex | 0 / 1 | 0.44 / 1.00 | $0.1022 | No |
| 7 | Sonnet report, Haiku repair | Test small-model repair in Claude Code | 1 / 1 | 1.00 / 1.00 | $0.5293 | No |
| 8 | High-effort Haiku report, Terra repair | Pair the most consistent reporter with a cheaper repair | 2 / 2 | 1.00 / 1.00 | $0.1440 | Model pair for attempt 1 |
| 9 | Prescribed parsing order for Haiku | Reduce repeated evidence reads | 0 / 1 | 1.00 / 0.93 | $0.1934 | No |
| 10 | Original report prompt, medium-effort Haiku | Shorten report time and reduce cost | 2 / 2 | 1.00 / 1.00 | $0.1460 | Both attempts |
| 11 | Map of repair contracts, functions, and tests for Terra | Limit source reads | 2 / 2 | 1.00 / 1.00 | $0.1275 | No |
| 12 | High-effort Sonnet repair, original prompt | Recover missed graded incident checks | 2 / 2 | 1.00 / 1.00 | $0.5406 | Attempt 2 |
| 13 | Sonnet replays the ticket before and after editing | Verify the fix against the reported symptom | 1 / 1 | 1.00 / 1.00 | $0.8984 | No |

Experiment 1 saved the most ($0.9762). One-hour cache writes fell to $0.4390. I changed the prompt and startup settings together, so the run measures their combined effect. Separate sessions, Haiku reporting, and five-minute caching saved another $0.6590 in experiment 2.

The report-first run found every affected entry and got all five currency totals right. It counted 94 corrupt rows. In its own session, Haiku checked each file and counted all 97, fixing the only wrong figure. Luna and the prescribed Haiku prompt also missed that count. On repair, medium-effort Sonnet and Luna each missed five cases, including duplicates queued before deployment.

Lowering Haiku’s effort cut its average report cost from $0.0637 to $0.0463. Terra’s source map lowered its mean uncached input from 55,234 to 36,300 tokens. That saved $0.0061 per repair, while the time from Terra’s first to last metered reply rose from 106 to 131 seconds.

### Final setup and starter results

At attempt 1’s token counts, I estimated $0.5822 total with Sonnet. Full cost credit required $0.75 or less, half the staff’s $1.50 baseline. I kept the original repair prompt after testing five saved patches on six extra contract checks. Both original Sonnet patches and both Terra patches passed all six. The replay-prompt patch passed four and returned the second event on retry when the contract required the first.

`./run.sh task.md` starts two Claude Code sessions in parallel through the course gateway, with safe mode and five-minute caching. The report session runs `claude-haiku-5-5` at medium effort with `prompts/impact.md` and writes `out/impact.json`. The repair session runs `claude-sonnet-5-5` at high effort with `prompts/repair.md`, edits `app/services/`, and runs focused tests. The script waits for both sessions and checks that the report parses as JSON.

| Final starter run | Repair | Impact | Cost |
| --- | ---: | ---: | ---: |
| `20261123-172143-1` | 1.00 | 1.00 | $0.5036 |
| `20261123-172143-2` | 1.00 | 1.00 | $0.5776 |

The second run made 63 requests against 49 in the first. Most of the additional cost came from Sonnet’s repair ($0.4600 to $0.5107).

## Part III: Graded submissions

| Attempt | Setup | Repair | Impact | Passed? | Mean starter cost | Graded cost | Points / 70 |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| [1](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451327898) | Medium-effort Haiku report, high-effort Terra repair in Codex | 0.47 | 0.93 | No | $0.1460 | $0.3126 | 57.36 |
| [2 (active)](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451349618) | Same report, high-effort Sonnet repair in Claude Code | 1.00 | 1.00 | Yes | $0.5406 | $0.4952 | 70 |

Both setups scored 1.00 on repair and impact in practice. Terra passed 8/17 graded incident checks and Sonnet passed 17/17. Both passed all 51 regressions and 8 compatibility checks and earned 35/35 for cost. Gradescope reported category totals, so I couldn’t identify which cases Terra missed. With one graded run per setup, I can’t separate the effects of changing the repair model and harness. Haiku’s impact score also varied with the same settings.

On a new ticket I would keep the separate report session, reconcile evidence across files, and trace the repair through the current contracts. I would replace the starter’s duplicate-key restart check with a case that reproduces the new symptom. On a separate local ticket covering paused endpoints and worker recovery, both models passed five incident checks and three regressions. Terra cost $0.0926 for that repair and Sonnet cost $0.2117.
