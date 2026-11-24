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
| 5 | Luna report and Terra repair | Test Codex models on the same two roles | 1 / 2 | 1.00 / 0.97 | $0.0922 | Terra repair |
| 6 | Terra report and Luna repair | See whether the smaller Codex model can also repair the services | 0 / 1 | 0.44 / 1.00 | $0.1022 | No |
| 7 | Sonnet report and Haiku repair | Measure both Claude models in their alternative roles | 1 / 1 | 1.00 / 1.00 | $0.5293 | No |
| 8 | High-effort Haiku report and Terra repair | Pair the most consistent reporter with the cheaper full-scoring repair model | 2 / 2 | 1.00 / 1.00 | $0.1440 | Models |
| 9 | Prompt with a prescribed parsing and verification sequence | Reduce repeated evidence inspection and get an initial report sooner | 0 / 1 | 1.00 / 0.93 | $0.1934 | No |
| 10 | Medium-effort Haiku report with the original prompt | Reduce report latency and token use while preserving accuracy | 2 / 2 | 1.00 / 1.00 | $0.1460 | Yes |
| 11 | Short map of repair contracts, functions, and tests | Reduce Terra's broad source reads | 2 / 2 | 1.00 / 1.00 | $0.1275 | No |
| 12 | High-effort Sonnet for repair, with the existing prompts and medium-effort Haiku for the report | Measure the cost of changing the repair model after nine incident misses in attempt 1 | 2 / 2 | 1.00 / 1.00 | $0.5406 | Selected for attempt 2 |
| 13 | Replay checks for the requirements in the current ticket | Check that the repair passes a scenario that reproduces the reported problem | 1 / 1 | 1.00 / 1.00 | $0.8984 | No |

**What fixed the failing category.** The separate report session focused on the evidence packet and checked malformed rows per file. The single-session run found the full affected set and got five of six figures right. The split run returned the same currency totals and counted three more corrupt rows. The scorer accepted all six figures in that run.

**What saved the most money.** Splitting the original Claude session reduced the context carried by each model and moved evidence parsing to Haiku. The first four Terra repairs passed and cost $0.0771 to $0.0836 each. High-effort Sonnet cost $0.3452 to $0.8124 per repair across the three comparable runs. Paired with Terra, high-effort Haiku averaged $0.1440 per run, compared with $0.6470 for the previous parallel Claude pair. The Claude report session uses five-minute cache writes. [Claude Code prompt caching](https://code.claude.com/docs/en/prompt-caching)

**What fell short.** The report-first instruction let the single session finish both artifacts. It still spent time exploring the repair before writing the report and miscounted corrupt rows. Medium-effort Sonnet and Luna each missed five repair scenarios, including cancellation of deliveries queued before deployment. Luna found every affected entry in both reporting runs and missed the corruption count in the repeat. The prescribed parsing prompt also missed the corruption count. It took 443.5 seconds and cost $0.1934.

**Repair map check.** The mapped runs passed both scores. Terra averaged 36,300 uncached input tokens, down from 55,234 in the two comparable runs. Its repair cost fell from $0.0996 to $0.0935. The time from its first to last metered response rose from 106 to 131 seconds, and it still read several large sections of code. Haiku finished sooner in the two mapped runs, which brought the average full runtime down to 190 seconds. I kept the original repair prompt for the final setup.

**Setup for attempt 1.** `run.sh` reads the supplied ticket and starts two sessions through the course gateway. Claude Code runs Haiku 5.5 at medium effort for the impact report. Codex runs GPT-6.1 Terra at high effort for the service repair. The sessions share the workspace and target different output paths. The wrapper waits for both and checks that the report is readable JSON. The practice scorer measures the correctness of both artifacts.

**Attempt 1 setup on the starter incident.**

| Run | Repair | Impact | Cost | Time |
| --- | ---: | ---: | ---: | ---: |
| `20261123-162420-2` | 1.00 | 1.00 | $0.1301 | 364.0 s |
| `20261123-163823-1` | 1.00 | 1.00 | $0.1618 | 220.4 s |

Both runs passed all 21 repair checks and got all six report figures right. Haiku's time from its first to last metered reply fell from 323 to 230 seconds on average. Its report cost fell from $0.0637 to $0.0463. Full runtime averaged 292 seconds, down from 325 seconds, even though one medium-effort run waited 120 seconds for its first metered reply. Full cost averaged $0.1460, compared with $0.1440 before, because Terra's repair cost varied.

**Sonnet repair follow-up.** I ran Sonnet 5.5 through Claude Code at high effort, with five-minute prompt caching.

| Run | Repair | Impact | Sonnet cost | Total cost | Time |
| --- | ---: | ---: | ---: | ---: | ---: |
| `20261123-172143-1` | 1.00 | 1.00 | $0.4600 | $0.5036 | 247.2 s |
| `20261123-172143-2` | 1.00 | 1.00 | $0.5107 | $0.5776 | 325.9 s |

Sonnet's token rates are twice Terra's. Before attempt 2, I estimated a total of $0.5822 using Terra's token counts from attempt 1 and the same Haiku cost. That estimate left $0.1678 below the full-credit cutoff. An earlier high-effort Sonnet run with high-effort Haiku cost $0.8590. Both repair models reached the maximum starter score.

**Replay follow-up.** In run `20261123-174001-1`, Sonnet replayed an API restart case before and after editing. The repeat received a new event ID before the patch and the original ID after it. All 21 repair checks and all six report figures passed in 315.2 seconds. Sonnet accounted for $0.8489. The total was $0.1484 above the full-credit cutoff. Both repair prompts reached the maximum starter score with Sonnet. The effect of the replay instructions on held-out scoring is unknown.

**Additional contract checks.** I applied the service diffs from five saved practice runs to separate copies of the starter app and ran six new cases locally. Both Terra patches and both original Sonnet patches passed all six cases. The unrepaired app passed one. The Sonnet patch with the replay instructions passed four. When the old release accepted two events seconds apart under one key, the replay patch returned the second event on retry after upgrade. The API contract calls for the first event. The replay patch also accepted a new event after three days. The older design record specifies a 24-hour window, so the retry within seconds provides a clearer result. These checks compare the saved repairs on the starter and use zero model calls.

**Independent repair ticket.** I seeded four defects in an isolated copy to test paused endpoints and worker recovery. The clean control passed five new incident checks and three existing regression checks. The broken control failed all five incident checks. I ran each original repair stage once through the practice gateway with the same $0.70 metered budget. Terra passed all eight checks in 89.7 seconds at $0.0926. Sonnet passed all eight in 67.3 seconds at $0.2117. This comparison measured the repair phase on one new local incident.

**What should transfer.** Each phase reads the current ticket and the relevant contracts. The report phase checks evidence sources, grouping, units, and malformed rows. The repair phase traces the current symptom through the active services. The practice runs measured these instructions on the starter incident.

## Part III: Graded Submissions

| Attempt | Repair | Impact | Passed? | Cost | Correctness points | Cost points | Total |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 0.47 | 0.93 | No | $0.3126 | 22.36 / 35 | 35 / 35 | 57.36 / 70 |
| 2 | 1.00 | 1.00 | Yes | $0.4952 | 35 / 35 | 35 / 35 | 70 / 70 |

The first attempt used medium-effort Haiku for the report and high-effort Terra for the repair. Gradescope recorded an exit code of zero and a runtime of 374.8 seconds. The repair passed 8 of 17 incident scenarios, all 51 regression scenarios, and all 8 compatibility scenarios. The gateway metered 65 model requests. Haiku accounted for about $0.043 and Terra for about $0.270.

Both starter runs scored 1.00 on repair and impact. The held-out run missed nine incident scenarios while preserving regression and compatibility coverage. It scored 0.93 on impact. The published result gives aggregate scores and category counts, which leaves the specific causes of those misses uncertain. The held-out cost was $0.3126, up from the $0.1460 starter average and within the $0.75 full-credit threshold. [Gradescope result](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451327898)

### Configuration for attempt 2

| Stage | Model | Effort | Prompt | Output |
| --- | --- | --- | --- | --- |
| Impact | `claude-haiku-5-5` | Medium | `prompts/impact.md` | `out/impact.json` |
| Repair | `claude-sonnet-5-5` | High | `prompts/repair.md` | `app/services/` changes |

`./run.sh task.md` sends the current ticket to both Claude Code sessions through the course gateway. The sessions run in parallel with five-minute prompt caching and safe mode. The wrapper waits for both and checks that the impact file parses as JSON. The impact prompt and runner match attempt 1 byte for byte. Sonnet uses the original repair prompt, which asks it to trace the current ticket through the relevant contracts and active services, then run focused tests.

I selected experiment 12 because the graded Terra run missed nine incident checks. The Sonnet setup passed both starter runs below $0.75. Its saved repairs also passed the six additional local checks. The replay version returned the later event on the retry case and cost $0.8984 in practice. Terra and Sonnet tied on the independent local ticket.

The verified package is `week6-attempt-2-sonnet.zip` (239 files). Its SHA-256 is `4def1c386a18b24bc1f15be22e5699488f3ee1e880741e01b71730deee09a94d`. The archive contains the exact runner and prompts used in both Sonnet practice runs. Gradescope supplies its own app, ticket, and incident evidence. Full cost credit requires a total of $0.75 or less. The gateway sets a $2.00 spending cap and the grader allows ten minutes.

### Attempt 2 result

The Sonnet repair passed all 17 incident scenarios, all 51 regression scenarios, and all 8 compatibility scenarios. The Haiku impact report scored 1.00. The runner exited with code zero after 205.0 seconds.

The gateway metered 54 model requests. Haiku cost $0.0407 and Sonnet cost $0.4545. The total was $0.2548 below the full-credit cutoff. Compared with attempt 1, the score rose by 12.64 points and the cost rose by $0.1826. Gradescope lists attempt 2 as the active submission. [Gradescope result for attempt 2](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451349618)
