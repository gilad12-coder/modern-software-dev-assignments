# Assignment 6 (Writeup)

## Part I: Baseline

I ran the provided `run.sh` with `python tools/practice.py --keep` on the starter incident. Sonnet passed all 21 repair checks and ran out of budget before writing the impact report.

| Run | Repair | Impact | Cost | Model requests | Time |
| --- | ---: | ---: | ---: | ---: | ---: |
| `20261123-114914-1` | 1.00 | 0.00 | $2.0352 | 32 | 338.7 s |

| Model | Input | Output | Cache read | Cache write | Cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sonnet 5.5 | 17,619 | 41,086 | 3,397,733 | 312,459 | $2.0352 |

Sonnet loaded my local memory, read the API and router source several times, and pulled in design records and runbooks. Later requests carried those reads forward. Cache reads accounted for the most tokens and cost $0.3398. Cache writes cost $1.2493, including $1.2485 for one-hour writes.

| Category | Passed |
| --- | ---: |
| Incident | 9 / 9 |
| Regressions | 10 / 10 |
| Compatibility | 2 / 2 |

After reading the API’s key lookup, Sonnet suspected a restart or the 24-hour expiry could let the same key through twice. It checked repeated keys against restart times, moved the lookup into the database, and fixed the router’s handling of duplicates. Its last tool call ran the API and router tests. By then the run cost $2.0352, and the gateway refused the next request under its $2.00 cap. The scorer found no `out/impact.json`. Precision and recall were both 0.00, with zero of six figures correct.

## Part II: Experiments

I counted a starter run as a pass when repair and impact both scored 1.00. The averages include every metered run for that configuration, including failures.

| # | Change | Why I tried it | Passed / metered runs | Avg repair / impact | Avg cost | Decision |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 1 | One Sonnet session with a shorter system prompt, safe mode, and a report-first instruction | Skip local startup context and finish the report before the repair uses the budget | 0 / 1 | 1.00 / 0.93 | $1.0590 | Split the work next |
| 2 | Haiku for the report, Sonnet for repair, and five-minute caching | Give each task its own context and move evidence parsing to the cheaper model | 1 / 1 | 1.00 / 1.00 | $0.4000 | Kept separate sessions and five-minute caching |
| 3 | Run both sessions in parallel | Give each task the full ten-minute window | 2 / 2 | 1.00 / 1.00 | $0.6470 | Kept |
| 4 | Lower Sonnet repair effort from high to medium | Spend less on repair while covering the same scenarios | 0 / 1 | 0.44 / 1.00 | $0.4633 | Dropped |
| 5 | Luna for the report, Terra for repair | Test both Codex models in the two roles | 1 / 2 | 1.00 / 0.97 | $0.0922 | Tried Terra with Haiku next |
| 6 | Terra for the report, Luna for repair | See whether the smaller Codex model could repair the services | 0 / 1 | 0.44 / 1.00 | $0.1022 | Dropped |
| 7 | Sonnet for the report, Haiku for repair | Test the Claude models with their roles reversed | 1 / 1 | 1.00 / 1.00 | $0.5293 | Dropped |
| 8 | High-effort Haiku for the report, Terra for repair | Pair the most consistent reporter so far with a cheaper repair model | 2 / 2 | 1.00 / 1.00 | $0.1440 | Used this pair in attempt 1 |
| 9 | Give Haiku a prescribed parsing and verification order | Reduce repeated reads and get a report sooner | 0 / 1 | 1.00 / 0.93 | $0.1934 | Dropped |
| 10 | Medium-effort Haiku with the original report prompt | Reduce report time and cost while keeping accuracy | 2 / 2 | 1.00 / 1.00 | $0.1460 | Kept for both submissions |
| 11 | Give Terra a short map of contracts, functions, and tests | Reduce broad source reads during repair | 2 / 2 | 1.00 / 1.00 | $0.1275 | Dropped |
| 12 | High-effort Sonnet for repair with the original prompts and medium-effort Haiku | Try a different repair model after Terra missed nine graded incident checks | 2 / 2 | 1.00 / 1.00 | $0.5406 | Used in attempt 2 |
| 13 | Ask Sonnet to replay the current ticket before and after its fix | Check that the patch fixes the behavior the ticket describes | 1 / 1 | 1.00 / 1.00 | $0.8984 | Dropped |

An earlier Luna/Terra launch stopped at zero metered requests and $0. Experiment 5 passed once in three starts. I used the two metered runs for its averages.

### Where the cost fell

Experiment 1 gave me the largest cost drop. The shorter single-session setup cost $1.0590 against the $2.0352 baseline, a saving of $0.9762. One-hour cache writes alone fell from $1.2485 to $0.4390. I changed the prompt and startup settings together. One run apiece tells me what the changes saved as a group.

Splitting the work, moving the report to Haiku, and using five-minute caching cut another $0.6590 in experiment 2. Changing the repair model also mattered. Terra’s first four repairs cost $0.0771 to $0.0836 each. High-effort Sonnet cost $0.3452 to $0.8124 across its first three repairs with Haiku. With high-effort Haiku reporting, the parallel pair averaged $0.6470 with Sonnet and $0.1440 with Terra. [Claude Code prompt caching](https://code.claude.com/docs/en/prompt-caching)

### What failed on the starter

The report-first instruction raised impact from 0.00 to 0.93. Sonnet still explored the repair first, then wrote a report before the budget ran out. It found every affected entry and got all five currency totals right, but it counted 94 corrupt rows. In its own session, Haiku checked malformed rows file by file and counted 97. That sixth figure brought impact to 1.00.

Luna also found every affected entry in both reporting runs and missed the corrupt-row count in the repeat. Prescribing a parsing order for Haiku produced the same kind of error. That run took 443.5 seconds and cost $0.1934. On repair, medium-effort Sonnet and Luna each missed five scenarios, including a duplicate already queued when the new release took over.

### What went into attempt 1

I used medium-effort Haiku in Claude Code for the report and high-effort Terra in Codex for repair. The sessions shared a workspace and wrote to different paths. The wrapper waited for both and checked that the report parsed as JSON. The practice scorer checked the contents and ran the repair scenarios.

| Starter run | Repair | Impact | Cost | Time |
| --- | ---: | ---: | ---: | ---: |
| `20261123-162420-2` | 1.00 | 1.00 | $0.1301 | 364.0 s |
| `20261123-163823-1` | 1.00 | 1.00 | $0.1618 | 220.4 s |

Both runs passed all 21 repair checks and got all six report figures right. At medium effort, Haiku’s average cost fell from $0.0637 to $0.0463. The time between its first and last metered replies fell from 323 to 230 seconds. One medium-effort run waited 120 seconds for its first metered reply. Full runs still averaged 292 seconds, down from 325. Variation in Terra’s repair cost brought the total average to $0.1460, up from $0.1440.

The map cut Terra’s average uncached input from 55,234 to 36,300 tokens across two runs per setup. Repair cost fell from $0.0996 to $0.0935. Terra still read large sections of code. Its average time from first to last metered reply rose from 106 to 131 seconds. Both mapped runs passed. They averaged 190 seconds overall because Haiku finished sooner. I kept the original repair prompt.

### Choosing the final repair

After the first graded run, I tried high-effort Sonnet in Claude Code with five-minute caching. At that cache duration, Sonnet’s token rates are twice Terra’s. At Terra’s attempt 1 token counts and the same Haiku cost, I estimated $0.5822 for the run. That left $0.1678 below the full-credit cutoff. An earlier run with high-effort Haiku and Sonnet cost $0.8590.

| Starter run with the final setup | Repair | Impact | Sonnet cost | Total cost | Time |
| --- | ---: | ---: | ---: | ---: | ---: |
| `20261123-172143-1` | 1.00 | 1.00 | $0.4600 | $0.5036 | 247.2 s |
| `20261123-172143-2` | 1.00 | 1.00 | $0.5107 | $0.5776 | 325.9 s |

The longer run made 63 model requests, compared with 49 in the first. Most of the extra cost came from Sonnet ($0.4600 to $0.5107). Haiku’s cost rose from $0.0437 to $0.0668.

In run `20261123-174001-1`, I asked Sonnet to replay an API restart before and after editing. The retry got a new event ID before the patch and the original ID afterward. All 21 repair checks and all six report figures passed in 315.2 seconds. The run cost $0.8984, including $0.8489 for Sonnet. That put it $0.1484 over the full-credit cutoff.

I applied five saved patches to separate copies of the starter app and ran six extra checks without any model calls. Both Terra patches and both original Sonnet patches passed all six. The unrepaired app passed one, and the Sonnet patch with replay instructions passed four. When the old release accepted two events seconds apart with the same key, the replay patch returned the second event on retry after upgrade. The API contract calls for the first. The patch also accepted a new event after three days. An older design record gives keys a 24-hour window, so the retry seconds apart was the clearer failure.

I tested repair alone on a different ticket by seeding four defects around paused endpoints and worker recovery. The clean app passed five incident checks and three regressions. The broken app failed all five incident checks. Each repair agent got one run with a $0.70 budget. Terra passed all eight checks in 89.7 seconds for $0.0926. Sonnet passed them in 67.3 seconds for $0.2117. Both could handle this second local ticket. I chose the original Sonnet prompt for attempt 2 because Terra missed nine graded incident checks and both Sonnet starter runs fit under $0.75. The replay version cost more and returned the wrong event on retry. I never ran it on the held-out incident.

### Final setup

| Stage | Model | Effort | Prompt | Output |
| --- | --- | --- | --- | --- |
| Impact | `claude-haiku-5-5` | Medium | `prompts/impact.md` | `out/impact.json` |
| Repair | `claude-sonnet-5-5` | High | `prompts/repair.md` | `app/services/` changes |

`./run.sh task.md` reads the supplied ticket and starts both Claude Code sessions in parallel through the course gateway. Both use safe mode and five-minute caching. The report prompt and the report function in `run.sh` match attempt 1 byte for byte. Sonnet follows the original repair prompt through the active services and contracts, then runs focused tests. The wrapper waits for both sessions and checks that the report parses as JSON.

Gradescope supplies its own app, ticket, and evidence. I verified that the 239 files in `week6-attempt-2-sonnet.zip` include the runner and prompts from both final starter runs. Its SHA-256 is `4def1c386a18b24bc1f15be22e5699488f3ee1e880741e01b71730deee09a94d`. The gateway caps spending at $2.00, and the grader allows ten minutes.

## Part III: Graded Submissions

| Attempt | What I ran | Repair | Impact | Passed? | Cost | Correctness points | Cost points | Total |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | Haiku report, Terra repair | 0.47 | 0.93 | No | $0.3126 | 22.36 / 35 | 35 / 35 | 57.36 / 70 |
| 2 | Same report, switched repair to Sonnet in Claude Code | 1.00 | 1.00 | Yes | $0.4952 | 35 / 35 | 35 / 35 | 70 / 70 |

The staff baseline on the held-out incident was $1.50. Both attempts earned full cost credit because they finished below $0.75.

On attempt 1, Terra passed 8 of 17 incident checks, all 51 regressions, and all 8 compatibility checks. Both starter runs scored 1.00 on repair and impact. The same setup cost $0.1460 on average in practice and $0.3126 on the held-out incident. The runner exited with code zero after 374.8 seconds. It made 65 model requests. Haiku cost about $0.043 and Terra about $0.270. Gradescope reports category counts, so I couldn’t identify which behaviors caused the nine incident misses. [Gradescope result](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451327898)

On attempt 2, Sonnet passed all 17 incident checks, all 51 regressions, and all 8 compatibility checks. Haiku scored 1.00 on impact. Both scores matched the final starter runs. The held-out run cost $0.4952 against the $0.5406 starter average. The runner exited with code zero after 205.0 seconds and 54 model requests. Haiku cost $0.0407 and Sonnet cost $0.4545. Attempt 2 cost $0.1826 more than attempt 1 and earned 12.64 more points. It finished $0.2548 below the full-credit cutoff. Gradescope lists attempt 2 as active. [Gradescope result for attempt 2](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451349618)

### What I would reuse

On another Switchyard ticket, I would again give the report its own session to reconcile evidence files, check units, and count malformed rows. For repair, I would start with the ticket and trace the behavior through the current contracts and services. The paused-endpoint test gave me some evidence for that approach beyond the starter. Retrying the same key seconds later and canceling duplicates queued before an upgrade tested the starter’s particular failure. I would choose a new regression case from the next ticket.

Gradescope ran each setup once. Switching from Terra to Sonnet also changed the repair harness from Codex to Claude Code. Even Haiku’s impact score went from 0.93 to 1.00 with the same settings. I would compare both repair models on a new incident before paying Sonnet’s higher rate.
