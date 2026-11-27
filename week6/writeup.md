# Assignment 6 Write-up

## Part I: Baseline

I ran the stock `run.sh` with `python tools/practice.py --keep` on the starter incident.

| Run | Repair | Impact | Cost | Model requests | Time |
| --- | ---: | ---: | ---: | ---: | ---: |
| `20261123-114914-1` | 1.00 | 0.00 | $2.0352 | 32 | 338.7 s |

### Where did the money go?

| Model | Input tokens | Output tokens | Cache reads | Cache writes |
| --- | ---: | ---: | ---: | ---: |
| Sonnet 5.5 | 17,619 | 41,086 | 3,397,733 | 312,459 |

Cache reads made up 90.2% of tokens. Later calls reused context from my local memory, source files, and design records. Cache writes were the largest cost at $1.2493 (61.4%). One-hour writes accounted for $1.2485 of that.

### What did the baseline get wrong?

The API kept retry keys in memory. Sonnet suspected a restart or the 24-hour expiry could turn a retry into a new event. It checked retries against restart times, moved the key lookup into the database, and fixed duplicate handling in the router. The repair passed 9/9 incident checks, 10/10 regressions, and 2/2 compatibility checks.

Spending crossed $2.00 after the repair tests. The gateway refused the next request before Sonnet could write `out/impact.json`. The grader recorded zero precision, zero recall, and 0/6 correct figures.

## Part II: Experiments

A pass required 1.00 on both repair and impact. The table counts runs that made model calls. Experiment 5 also had one launch that stopped at zero requests and cost $0.

| # | Change | Why I tried it | Passed / runs | Mean repair / impact | Mean cost | Kept? |
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
| 13 | Sonnet runs the same check before and after repair | Verify the fix against the reported symptom | 1 / 1 | 1.00 / 1.00 | $0.8984 | No |

### The change that fixed the most failing categories

In Experiment 1, Sonnet wrote the report before editing the services. It matched every affected entry and all five currency totals. It counted 94 corrupt rows. In Experiment 2, Haiku checked each file in its own session and counted all 97, bringing impact to 1.00. One Luna run and Haiku's prescribed parsing order also missed the corrupt-row count.

### The change that saved the most money

Experiment 1 saved $0.9762, the largest single drop. One-hour cache writes fell to $0.4390 after I shortened the prompt and changed the startup settings together. Experiment 2 saved another $0.6590 when I split the sessions, gave reporting to Haiku, and switched to five-minute caching.

### A change that did not work

I asked Sonnet to reproduce the failure, then run the same check after editing. The run passed the starter at $0.8984, above the full-credit cutoff. Its saved patch passed four of six extra contract checks. In one check, the old service accepted two events under the same key. A retry had to return the first event. The replay patch returned the second. The extra checks caught a retry failure that the starter score missed. Both Terra patches and both original Sonnet patches passed all six, so I kept the original Sonnet prompt.

### Final setup

I kept medium-effort Haiku with the original report prompt. Its average report cost fell from $0.0637 to $0.0463. Terra's source map cut uncached input by about a third and saved $0.0061 per repair. The average time between Terra's first and last metered replies rose from 106 to 131 seconds, so I dropped the map.

The first graded run's incident misses led me to try high-effort Sonnet. Using Attempt 1's token counts, I estimated $0.5822 for a full run with Sonnet. Both starter runs fit the $0.75 full-credit cutoff, half the staff's $1.50 baseline.

`./run.sh task.md` sends the ticket to two Claude Code sessions in parallel through the course gateway. Both use safe mode and five-minute caching under one $2.00 spending cap. Medium-effort `claude-haiku-5-5` uses `prompts/impact.md` to write `out/impact.json`. High-effort `claude-sonnet-5-5` uses `prompts/repair.md` to edit `app/services/` and run focused tests. The script checks the report parses as JSON and waits for both sessions.

### Final setup on the starter incident

| Final starter run | Repair | Impact | Cost |
| --- | ---: | ---: | ---: |
| `20261123-172143-1` | 1.00 | 1.00 | $0.5036 |
| `20261123-172143-2` | 1.00 | 1.00 | $0.5776 |

The second run made 63 requests, compared with 49 in the first. Most of the added cost came from Sonnet's repair, which rose from $0.4600 to $0.5107.

### What will transfer?

I would keep reporting in a separate session, cross-check evidence files, and trace the repair through the current contracts. I would replace the duplicate-key restart check with a regression test for the new symptom.

On a separate local ticket about paused endpoints and worker recovery, Terra and Sonnet each passed five incident checks and three regressions. Terra cost $0.0926 and Sonnet cost $0.2117 for repair. I would compare the models again on a new ticket.

## Part III: Graded Submissions

| Attempt | Setup | Repair | Impact | Passed? | Mean starter cost | Graded cost | Points / 70 |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: |
| [1](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451327898) | Medium-effort Haiku report, high-effort Terra repair in Codex | 0.47 | 0.93 | No | $0.1460 | $0.3126 | 57.36 |
| [2 (active)](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451349618) | Same report, high-effort Sonnet repair in Claude Code | 1.00 | 1.00 | Yes | $0.5406 | $0.4952 | 70 |

### Starter incident versus held-out incident

Both setups passed every starter check. Terra passed 8/17 graded incident checks and Sonnet passed 17/17. Both passed 51 regressions and eight compatibility checks and earned 35/35 for cost. Terra's setup cost more than twice its starter average, with repair alone rising from $0.0996 to $0.2696. Sonnet's graded run cost slightly less than its starter average.

Gradescope ran each setup once and reported totals by category. Attempt 2 changed both the repair model and the harness. The same Haiku setup scored 0.93 and 1.00 across the two runs. I treat the result as a comparison of the full setups.
