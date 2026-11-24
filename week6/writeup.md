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

**What fixed the failing category.** The separate report session focused on the evidence packet and checked malformed rows per file. The single-session run found the full affected set and got five of six figures right. The split run returned the same currency totals and counted three more corrupt rows. The scorer accepted all six figures in that run.

**What saved the most money.** Splitting the original Claude session reduced the context carried by each model and moved evidence parsing to Haiku. The first four Terra repairs passed and cost $0.0771 to $0.0836 each. High-effort Sonnet cost $0.3452 to $0.8124 per repair across the three comparable runs. Paired with Terra, high-effort Haiku averaged $0.1440 per run, compared with $0.6470 for the previous parallel Claude pair. The Claude report session uses five-minute cache writes. [Claude Code prompt caching](https://code.claude.com/docs/en/prompt-caching)

**What fell short.** The report-first instruction let the single session finish both artifacts. It still spent time exploring the repair before writing the report and miscounted corrupt rows. Medium-effort Sonnet and Luna each missed five repair scenarios, including cancellation of deliveries queued before deployment. Luna found every affected entry in both reporting runs and missed the corruption count in the repeat. The prescribed parsing prompt also missed the corruption count. It took 443.5 seconds and cost $0.1934.

**Repair map check.** The mapped runs passed both scores. Terra averaged 36,300 uncached input tokens, down from 55,234 in the two comparable runs. Its repair cost fell from $0.0996 to $0.0935. The time from its first to last metered response rose from 106 to 131 seconds, and it still read several large sections of code. Haiku finished sooner in the two mapped runs, which brought the average full runtime down to 190 seconds. I kept the original repair prompt for the final setup.

**Setup.** `run.sh` reads the supplied ticket and starts two sessions through the course gateway. Claude Code runs Haiku 5.5 at medium effort for the impact report. Codex runs GPT-6.1 Terra at high effort for the service repair. The sessions share the workspace and target different output paths. The wrapper waits for both and checks that the report is readable JSON. The practice scorer measures the correctness of both artifacts.

**Final setup on the starter incident.**

| Run | Repair | Impact | Cost | Time |
| --- | ---: | ---: | ---: | ---: |
| `20261123-162420-2` | 1.00 | 1.00 | $0.1301 | 364.0 s |
| `20261123-163823-1` | 1.00 | 1.00 | $0.1618 | 220.4 s |

Both final runs passed all 21 repair checks and got all six report figures right. Haiku's time from its first to last metered reply fell from 323 to 230 seconds on average. Its report cost fell from $0.0637 to $0.0463. Full runtime averaged 292 seconds, down from 325 seconds, even though one medium-effort run waited 120 seconds for its first metered reply. Full cost averaged $0.1460, compared with $0.1440 before, because Terra's repair cost varied.

**What should transfer.** Each phase reads the current ticket and the relevant contracts. The report phase checks evidence sources, grouping, units, and malformed rows. The repair phase traces the current symptom through the active services. The practice runs measured these instructions on the starter incident.

## Part III: Graded Submissions

| Attempt | Repair | Impact | Passed? | Cost | Correctness points | Cost points | Total |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 0.47 | 0.93 | No | $0.3126 | 22.36 / 35 | 35 / 35 | 57.36 / 70 |

The first attempt used medium-effort Haiku for the report and high-effort Terra for the repair. Gradescope recorded an exit code of zero and a runtime of 374.8 seconds. The repair passed 8 of 17 incident scenarios, all 51 regression scenarios, and all 8 compatibility scenarios. The gateway metered 65 model requests. Haiku accounted for about $0.043 and Terra for about $0.270.

Both starter runs scored 1.00 on repair and impact. The held-out run missed nine incident scenarios while preserving regression and compatibility coverage. It scored 0.93 on impact. The published result gives aggregate scores and category counts, which leaves the specific causes of those misses uncertain. The held-out cost was $0.3126, up from the $0.1460 starter average and within the $0.75 full-credit threshold. [Gradescope result](https://www.gradescope.com/courses/1396510/assignments/9065912/submissions/451327898)
