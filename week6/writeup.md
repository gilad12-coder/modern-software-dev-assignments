# Assignment 6 Write-up

## Part I: Baseline

I ran the stock `run.sh` on the starter incident with `python tools/practice.py --keep`.

| Run | Repair | Impact | Cost | Model requests | Time |
| --- | ---: | ---: | ---: | ---: | ---: |
| `20261123-114914-1` | 1.00 | 0.00 | $2.0352 | 32 | 338.7 s |

| Model | Input | Output | Cache read | Cache write | Cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| `claude-sonnet-5-5` | 17,619 | 41,086 | 3,397,733 | 312,459 | $2.0352 |

### Where did the money go?

Cache reads made up 90.2% of all tokens (3,397,733 of 3,768,897) and cost $0.3398 (16.7%). Cache writes drove most of the spend at $1.2493 (61.4%), almost all from 312,131 one-hour cache write tokens at $4.00 per million ($1.2485). Output cost $0.4109 (20.2%), and uncached input cost $0.0352 (1.7%).

Stock `run.sh` ran `claude -p` with my local settings. Request 1 alone wrote 49,433 one-hour cache tokens ($0.1983) while loading 825 tools from 25 local MCP servers and personal hooks. Sonnet then ran local memory commands, read `assignment.md`, `writeup.md`, all ADRs, runbooks, and postmortems, and read all three services. Context hit 172,139 tokens and auto-compacted to 37,946 tokens ($0.1582 for compaction, then $0.3018 to rewrite 75,455 cache tokens on the next turn), which forced Sonnet to re-read the API, router, and evidence docs. Later turns re-read that growing prefix from cache.

### What did the baseline get wrong?

| Category | Passed |
| --- | ---: |
| Incident | 9 / 9 |
| Regressions | 10 / 10 |
| Compatibility | 2 / 2 |

Impact precision and recall were both 0.00, with 0/6 exact figures, because `out/impact.json` did not exist.

From `app/services/api/src/keys.ts` and `app/docs/adr/0013-idempotency-keys-in-memory.md`, Sonnet saw that the API stored idempotency keys in memory with a 24-hour window. It suspected a restart or expiry let retries create duplicate events, checked `incident/api.ndjson` against `api.started` restart timestamps to confirm, moved key lookup into SQLite, updated the router to cancel repeat deliveries, and added API and router tests. Because it worked sequentially in one session and did repair first, spend hit $2.0352 on request 32 right after those tests. The gateway refused request 33 under the $2.00 cap (`budget_exhausted`) before Sonnet wrote `out/impact.json`.

## Part II: Experiments

A starter run passed when both repair and impact scored 1.00. The table counts runs that made at least one model request. Experiment 5 also had one launch that stopped at zero requests and $0 after two parallel Codex processes hit a lock on `state_5.sqlite`.

| # | Change | Why I expected it to help | Runs passed / attempted | Avg repair / impact | Avg cost | Kept? |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 1 | Single Sonnet session, short prompt, safe mode (6 tools, no MCP), report-first order | Skip local hooks and memory; finish report within budget | 0 / 1 | 1.00 / 0.93 | $1.0590 | Replaced |
| 2 | Separate Haiku report and Sonnet repair (sequential), [five-minute caching](https://code.claude.com/docs/en/prompt-caching) | Separate contexts, use cheaper reporter, drop 1-hour cache rate | 1 / 1 | 1.00 / 1.00 | $0.4000 | Yes |
| 3 | Run report and repair sessions in parallel | Give each task the full 10-minute timeout | 2 / 2 | 1.00 / 1.00 | $0.6470 | Yes |
| 4 | Lower Sonnet repair effort from high to medium | Cut repair cost while keeping incident coverage | 0 / 1 | 0.44 / 1.00 | $0.4633 | No |
| 5 | Luna report and Terra repair in Codex | Test cheaper OpenAI models in the two roles | 1 / 2 | 1.00 / 0.97 | $0.0922 | Terra only |
| 6 | Terra report and Luna repair in Codex | Test whether the small Codex model can handle repair | 0 / 1 | 0.44 / 1.00 | $0.1022 | No |
| 7 | Sonnet report and Haiku repair in Claude Code | Test Claude models in reversed roles | 1 / 1 | 1.00 / 1.00 | $0.5293 | No |
| 8 | High-effort Haiku report and high-effort Terra repair | Pair the most consistent reporter with the cheapest passing repair | 2 / 2 | 1.00 / 1.00 | $0.1440 | Attempt 1 pair |
| 9 | Prescribed parsing order in Haiku's report prompt | Cut repeated evidence reads and finish faster | 0 / 1 | 1.00 / 0.93 | $0.1934 | No |
| 10 | Medium-effort Haiku with original report prompt and Terra repair | Lower report latency and cost while keeping accuracy | 2 / 2 | 1.00 / 1.00 | $0.1460 | Report kept; Attempt 1 setup |
| 11 | Short map of contracts, functions, and tests for Terra | Reduce broad source reads during repair | 2 / 2 | 1.00 / 1.00 | $0.1275 | No |
| 12 | High-effort Sonnet repair with original prompt and medium-effort Haiku report | Recover the 9 graded incident misses from Attempt 1 | 2 / 2 | 1.00 / 1.00 | $0.5406 | Yes (Attempt 2) |
| 13 | Ask Sonnet to run an `app/bin/replay` check before and after editing | Verify the patch reproduces and fixes the ticket symptom | 1 / 1 | 1.00 / 1.00 | $0.8984 | No |

### The change that fixed the most failing categories

On the starter incident, impact was the failing category (0.00). Cutting startup bloat and writing the report before repairing (Experiment 1) kept the run in budget and raised impact to 0.93: Sonnet matched all 53 affected entries and all five currency totals, and counted 94 of 97 corrupt rows (missing three in `router.log`). Splitting reporting into its own Haiku session (Experiment 2) let Haiku check malformed rows file by file without repair context, and it counted all 97 corrupt rows (1.00). On the held-out incident, moving repair from Terra in Codex to high-effort Sonnet in Claude Code (Experiment 12) fixed all nine missed incident checks (8/17 to 17/17).

### The change that saved the most money

Experiment 1 produced the largest drop: cost fell by $0.9762 from $2.0352 to $1.0590. Turning on safe mode (`CLAUDE_CODE_SAFE_MODE=1`), limiting tools to six built-ins (`--tools`), disabling MCP (`--strict-mcp-config`), and using a short prompt cut request 1 from 49,433 to 6,240 cache-write tokens. That skipped local hooks and memory and avoided auto-compaction, so one-hour cache writes fell from $1.2485 to $0.4390.

Experiment 2 cut another $0.6590 to $0.4000: separate sessions kept the two contexts apart, Haiku billed reporting at 1/20th of Sonnet's rates, and five-minute caching (`CLAUDE_CODE_PROMPT_CACHE_TTL=5m`) lowered cache writes from $4.00 to $2.50 per million tokens. Pairing Haiku with Terra in Experiment 8 pushed starter cost down to $0.1440 before Attempt 1's graded misses led me back to Sonnet.

### A change that did not work

In Experiment 13, I asked Sonnet to reproduce the ticket with `app/bin/replay` before editing and rerun the check afterward. The run passed the starter (1.00/1.00) at $0.8984 ($0.8489 for Sonnet), which sat $0.1484 above the $0.75 full-credit cutoff. I also tested five saved practice patches offline against six extra contract checks on the starter app (zero model calls). Both Terra patches and both original Sonnet patches passed 6/6, while the replay patch passed 4/6: when the old release accepted two events seconds apart under one key, the replay patch returned the second event on retry after upgrade, even though the API contract requires the first. (It also accepted a new event after three days, where ADR-0013 specifies a 24-hour window.) A mandatory replay loop raised cost past the cutoff and still allowed a contract bug that the starter score missed.

Other dropped runs ruled out cheaper shortcuts. Medium-effort Sonnet (Experiment 4) and Luna (Experiment 6) both fell to 0.44 on starter repair by missing the same five checks for canceling repeats already queued or in flight before an upgrade. Prescribing Haiku's parsing order (Experiment 9) raised cost to $0.1934 and miscounted 158 corrupt rows. Adding a source map for Terra (Experiment 11) cut uncached input by about a third (55,234 to 36,300 tokens) and saved only $0.0061 per repair ($0.0996 to $0.0935), while Terra's active time rose from 106 to 131 seconds. Haiku passed starter repair in Experiment 7 (1.00), yet took 60 requests and 516.4 s total, close to the 10-minute limit.

### Final setup

After Attempt 1 missed nine graded incident checks with Terra, I moved repair back to high-effort Sonnet and kept medium-effort Haiku for reporting (which lowered Haiku's starter average from $0.0637 in Experiment 8 to $0.0463 in Experiment 10). Sonnet's five-minute rates are twice Terra's, so doubling Terra's $0.2696 graded repair cost plus Haiku's $0.0430 estimated $0.5822 for Attempt 2, well below the $0.75 cutoff (half the staff's $1.50 baseline).

Step by step, `./run.sh task.md`:

1. Verifies that `CS146S_GATEWAY_URL` and `ANTHROPIC_BASE_URL` point to the course gateway, then reads `task.md`.
2. Launches two parallel Claude Code sessions under the shared $2.00 cap with safe mode, five-minute caching, `--tools 'Bash,Edit,Glob,Grep,Read,Write'`, `--strict-mcp-config`, `--no-session-persistence`, and `--permission-mode bypassPermissions`.
3. Report (`claude-haiku-5-5`, medium effort, `prompts/impact.md`): reads `app/contracts/evidence.md` and `incident/`, cross-checks the logs with a local script, counts corrupt rows before filtering, and writes `out/impact.json`.
4. Repair (`claude-sonnet-5-5`, high effort, `prompts/repair.md`): traces the ticket through `app/contracts/` and the active `api`, `router`, and `worker` services in `app/services/`, patches them while keeping older bus versions working, and runs focused tests plus `app/bin/evaluate --quiet`.
5. Waits for the report session, checks `out/impact.json` with `python3 -m json.tool`, waits for the repair session, and exits with the report status.

### Final setup on the starter incident

| Run | Repair | Impact | Cost |
| --- | ---: | ---: | ---: |
| `20261123-172143-1` | 1.00 | 1.00 | $0.5036 |
| `20261123-172143-2` | 1.00 | 1.00 | $0.5776 |

Both runs passed all 21 repair checks and all six report figures below $0.75. Run 2 cost $0.0740 more and took 325.9 s compared with 247.2 s in run 1. Haiku drove the request jump from 49 to 63 (44 requests and $0.0668, up from 28 requests and $0.0437) and set the slower finish time; Sonnet made two fewer requests (19 vs. 21) yet cost $0.0507 more ($0.5107 vs. $0.4600) from higher output tokens (21,534 vs. 17,728) and cache writes (78,665 vs. 73,672).

### What will transfer?

Harness isolation, the parallel split, and both prompts target Switchyard generally. Safe mode, tool limits, and five-minute caching cut startup waste on any ticket, and separate sessions keep report and repair contexts apart. `prompts/impact.md` encodes Switchyard's evidence rules (cross-checking files that omit records, stable-ID joins, shipper duplicates, and separating documented empty values from truncated lines), and `prompts/repair.md` checks outdated docs against `app/contracts/` and active service code. To test repair transfer locally before Attempt 2, I seeded four defects for a separate ticket on paused endpoints and worker recovery; with the same `prompts/repair.md` under a $0.70 budget, Terra ($0.0926 in 89.7 s) and Sonnet ($0.2117 in 67.3 s) both passed all five incident checks and three regressions.

Model sizing and ticket-specific checks transferred less reliably. Terra passed every starter check and the paused-endpoint ticket for around $0.09 to $0.10, yet missed nine held-out incident checks. Medium-effort Haiku scored 1.00 on starter runs and Attempt 2, and 0.93 on Attempt 1. My six offline contract checks tested the starter's duplicate-event failure and would need new cases for another ticket.

## Part III: Graded Submissions

| Submission | Repair | Impact | Passed? | Cost | Points / 70 | What I changed before it |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| [1](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451327898) | 0.47 | 0.93 | No | $0.3126 | 57.36 | Initial submission: medium-effort Haiku report (Claude Code) and high-effort Terra repair (Codex) from Experiment 10 |
| [2 (active)](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451349618) | 1.00 | 1.00 | Yes | $0.4952 | 70 | Kept report unchanged; switched repair to high-effort Sonnet in Claude Code (Experiment 12) |

### Starter incident versus held-out incident

Attempt 1 did not carry over. Both starter runs scored 1.00/1.00 at a mean cost of $0.1460, while the held-out run scored 0.47 on repair (8/17 incident checks, 51/51 regressions, 8/8 compatibility) and 0.93 on impact in 374.8 s across 65 requests. Graded cost more than doubled to $0.3126 as Terra repair jumped from $0.0996 to $0.2696, while Haiku stayed flat ($0.0430 vs. $0.0463). Attempt 2 carried over on repair, impact, and cost: 17/17 incident checks, 51/51 regressions, 8/8 compatibility, and 1.00 impact in 205.0 s across 54 requests. Its total cost was $0.4952 ($0.0407 Haiku, $0.4545 Sonnet), slightly below its $0.5406 starter average and $0.2548 under the $0.75 cutoff. Both attempts earned 35/35 for cost against the staff's $1.50 baseline.

Two limits narrow what these runs prove. The held-out suite was larger (17 incident scenarios and 51 regressions vs. 9 and 10 on the starter), which helps explain Terra spending nearly triple its starter cost while missing nine incident checks; because Gradescope reports category totals without logs or failing test names, I cannot tell which cases failed. Each submission also gets one graded run, and Attempt 2 changed both the repair model and the harness (Terra in Codex to Sonnet in Claude Code). Even the untouched Haiku setup moved from 0.93 on Attempt 1 to 1.00 on Attempt 2, so a single run carries noticeable noise. I treat the result as a one-trial comparison of the two full setups, and on a new ticket I would compare both repair models again before paying Sonnet's higher rate.