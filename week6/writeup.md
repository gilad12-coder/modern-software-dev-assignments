# Assignment 6 Write-up

## Part I: Baseline Analysis

I ran `python tools/practice.py --keep` with the stock `run.sh`. Starter run `20261123-114914-1` cost \$2.0352 across 32 Sonnet 5.5 requests in 338.7 seconds. Repair scored 1.00 (9/9 incident, 10/10 regression, 2/2 compatibility). Impact, precision, and recall all scored 0.00, with 0/6 figures correct.

| Input tokens | Output tokens | Cache reads | Cache writes |
| ---: | ---: | ---: | ---: |
| 17,619 | 41,086 | 3,397,733 | 312,459 |

Cache reads made up 90.2% of all tokens (3,397,733 of 3,768,897). Cache writes drove 61.4% of total spend (\$1.2493 of \$2.0352). Almost all of that write cost came from one-hour cache writes (\$1.2485).

Sonnet's behavior explains both the high cost and the missing report. At startup, Sonnet loaded my local memory. Over 32 requests, it repeatedly read source files and design records, inflating cache writes and reads. On the incident itself, the API kept idempotency keys in memory. Sonnet suspected that a restart or the 24-hour expiry could let a retry create a second event. It checked retries against restart times, moved key lookup into the database, and fixed duplicate handling in the router. Right after the API and router tests, spending crossed \$2.00 and the gateway refused the next request. Because repair ran first in one shared session, Sonnet exhausted the budget before writing `out/impact.json`.

## Part II: Experiments and Decisions

I ran 13 experiments on the starter incident to cut cost and finish the report accurately. A pass required 1.00 on both repair and impact. Mean values include every metered starter run. Experiment 5 included one extra launch that stopped before its first model request and cost \$0.

| # | Change | Why I tried it | Passed / metered | Mean repair / impact | Mean cost | Kept? |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 1 | Single Sonnet session, short prompt, safe mode, report first | Skip local memory and finish the report within budget | 0 / 1 | 1.00 / 0.93 | \$1.0590 | Replaced |
| 2 | Separate Haiku report and Sonnet repair, [five-minute caching](https://code.claude.com/docs/en/prompt-caching) | Reduce context and spend less on reporting | 1 / 1 | 1.00 / 1.00 | \$0.4000 | Yes |
| 3 | Run both sessions in parallel | Give each task the full ten minutes | 2 / 2 | 1.00 / 1.00 | \$0.6470 | Yes |
| 4 | Medium-effort Sonnet repair | Lower repair cost | 0 / 1 | 0.44 / 1.00 | \$0.4633 | No |
| 5 | Luna report, Terra repair | Try a cheaper pair in Codex | 1 / 2 | 1.00 / 0.97 | \$0.0922 | Terra only |
| 6 | Terra report, Luna repair | Test small-model repair in Codex | 0 / 1 | 0.44 / 1.00 | \$0.1022 | No |
| 7 | Sonnet report, Haiku repair | Test small-model repair in Claude Code | 1 / 1 | 1.00 / 1.00 | \$0.5293 | No |
| 8 | High-effort Haiku report, Terra repair | Pair the most consistent reporter with a cheaper repair | 2 / 2 | 1.00 / 1.00 | \$0.1440 | Model pair for attempt 1 |
| 9 | Prescribed parsing order for Haiku | Reduce repeated evidence reads | 0 / 1 | 1.00 / 0.93 | \$0.1934 | No |
| 10 | Original report prompt, medium-effort Haiku | Shorten report time and reduce cost | 2 / 2 | 1.00 / 1.00 | \$0.1460 | Both attempts |
| 11 | Map of repair contracts, functions, and tests for Terra | Limit source reads | 2 / 2 | 1.00 / 1.00 | \$0.1275 | No |
| 12 | High-effort Sonnet repair, original prompt | Recover missed graded incident checks | 2 / 2 | 1.00 / 1.00 | \$0.5406 | Attempt 2 |
| 13 | Sonnet replays the ticket before and after editing | Verify the fix against the reported symptom | 1 / 1 | 1.00 / 1.00 | \$0.8984 | No |

### What Saved the Most Money

Experiment 1 produced the largest cost drop, saving \$0.9762 (\$2.0352 to \$1.0590). One-hour cache writes dropped from \$1.2485 to \$0.4390. Because I changed the prompt and startup settings together, this run measures their combined effect.

Experiment 2 saved another \$0.6590 (\$1.0590 to \$0.4000) by splitting reporting into a separate Haiku session and switching to five-minute caching. In Experiment 3, I ran both sessions in parallel so each task got the full ten minutes. Both runs passed at \$0.6470 mean cost, and I kept parallel execution in every later setup.

### What Fixed the Reporting Failure

Experiment 1 avoided the \$2.00 cutoff by writing the report first. It found every affected entry and got all five currency totals right, but it counted 94 corrupt rows (0.93 impact).

Experiment 2 fixed that one wrong figure. In its own session, Haiku checked each file and counted all 97 corrupt rows (1.00 impact). Two later runs reinforced this result: Luna (Experiment 5) and the prescribed Haiku prompt (Experiment 9) both missed the same count. Giving Haiku an isolated session and letting it inspect each file worked better than prescribing a parsing order.

### Cheaper Models, Effort, and Prompt Tuning

Full cost credit required \$0.75 or less, half the staff's \$1.50 baseline. With parallel Sonnet runs averaging \$0.6470 (Experiment 3), I tested cheaper models and lower effort to widen the budget margin (Experiments 4–8).

Two repair downgrades failed and changed my mind about small or reduced-effort repair models. Medium-effort Sonnet (Experiment 4, \$0.4633) and Luna repair (Experiment 6, \$0.1022) each scored 0.44 on repair. Both missed five cases, including duplicates queued before deployment. Haiku repair passed in Experiment 7 (1.00 / 1.00), but the Sonnet-report pair cost \$0.5293—more than Experiment 2—so I discarded it.

Experiment 5 tested Luna and Terra in Codex (\$0.0922 mean cost). Terra passed repair (1.00), but Luna missed the corrupt-row count on one run (1/2 passed, 0.97 mean impact). I kept Terra for repair and paired it with high-effort Haiku in Experiment 8, passing 2/2 starter runs at \$0.1440 mean cost.

I then tuned prompts and effort on that hybrid pair (Experiments 9–11) and kept only one change:

- **Prescribed parsing order for Haiku (Experiment 9, discarded):** Cost rose to \$0.1934, and Haiku missed the corrupt-row count (0.93 impact, 0/1 passed).
- **Medium-effort Haiku with the original report prompt (Experiment 10, kept):** Both runs passed (\$0.1460 total mean). Lowering effort cut Haiku's average report cost from \$0.0637 to \$0.0463.
- **Source map of repair contracts, functions, and tests for Terra (Experiment 11, discarded):** Both runs passed (\$0.1275 total mean). Terra's mean uncached input fell from 55,234 to 36,300 tokens, saving only \$0.0061 per repair. Time from Terra's first to last metered reply rose from 106 to 131 seconds, so I dropped the map.

### Switching Back to Sonnet and Choosing the Final Setup

I submitted the Experiment 10 setup as Attempt 1 (medium-effort Haiku report, high-effort Terra repair). It scored 0.47 on graded repair (8/17 incident checks), which changed my mind about relying on Terra.

Using Attempt 1's token counts, I estimated \$0.5822 total cost with high-effort Sonnet repair. That estimate sat comfortably below the \$0.75 cap, so I traded extra spend for stronger repair. In Experiment 12, high-effort Sonnet with the original prompt passed 2/2 starter runs at \$0.5406 mean cost.

Next, I tested a replay prompt that asked Sonnet to replay the ticket before and after editing (Experiment 13). That run passed the starter incident (1.00 / 1.00), but cost rose to \$0.8984, above the \$0.75 cap. I also evaluated five saved patches on six extra contract checks. Both original Sonnet patches and both Terra patches passed 6/6. The replay-prompt patch passed only 4/6 and returned the second event on retry when the contract required the first. I rejected the replay prompt because it broke both the budget target and the retry contract.

### Final Configuration and Starter Results

`./run.sh task.md` launches two parallel Claude Code sessions through the course gateway with safe mode and five-minute caching:

- **Report session:** `claude-haiku-5-5` at medium effort runs `prompts/impact.md` and writes `out/impact.json`.
- **Repair session:** `claude-sonnet-5-5` at high effort runs `prompts/repair.md`, edits `app/services/`, and runs focused tests.

The script waits for both sessions and checks that `out/impact.json` parses as JSON.

| Final starter run | Repair | Impact | Cost |
| --- | ---: | ---: | ---: |
| `20261123-172143-1` | 1.00 | 1.00 | \$0.5036 |
| `20261123-172143-2` | 1.00 | 1.00 | \$0.5776 |

The second run made 63 requests against 49 in the first. Most of the extra cost came from Sonnet's repair, which rose from \$0.4600 to \$0.5107.

## Part III: Graded Submissions and Generalization

| Attempt | Setup | Repair | Impact | Passed? | Mean starter cost | Graded cost | Points / 70 |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| [1](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451327898) | Medium-effort Haiku report, high-effort Terra repair in Codex | 0.47 | 0.93 | No | \$0.1460 | \$0.3126 | 57.36 |
| [2 (active)](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451349618) | Same report, high-effort Sonnet repair in Claude Code | 1.00 | 1.00 | Yes | \$0.5406 | \$0.4952 | 70 |

### Starter vs. Graded Comparison

Both setups scored 1.00 on repair and impact in practice, so the starter incident did not distinguish Terra from Sonnet. On the held-out graded incident, Terra passed 8/17 incident checks and Sonnet passed 17/17. Both passed all 51 regressions and 8 compatibility checks, and both earned 35/35 for cost. Terra's graded cost more than doubled from its starter mean (\$0.1460 to \$0.3126). Sonnet's graded cost came in slightly under its starter mean (\$0.5406 to \$0.4952).

The evidence supports only narrow conclusions:

- **Withheld scenarios:** Gradescope reported category totals only, so I could not identify which cases Terra missed.
- **One run and two changes:** Each setup received one graded run. Attempt 2 changed both the repair model and the harness (Codex to Claude Code). I cannot separate model effects from harness effects or run-to-run variance.
- **Reporter variance:** Haiku ran with identical settings in both attempts, yet its graded impact score varied from 0.93 to 1.00.

### What I Will Reuse on Another Incident

On a new incident, I will keep three parts of this setup:

- Run reporting in its own session so repair work never exhausts the report budget.
- Reconcile evidence across every file instead of forcing a fixed parsing order.
- Trace repairs through the current contracts rather than fitting only a single replayed symptom.

I will replace the starter's duplicate-key restart check with a test case that reproduces the new symptom.

Terra still remains viable on some incidents. On a separate local ticket covering paused endpoints and worker recovery, both models passed five incident checks and three regressions. Terra cost \$0.0926 for that repair, while Sonnet cost \$0.2117. Still, when a \$0.75 budget allows it, I will start with high-effort Sonnet after its 17/17 graded result.