# Week 3 Write-up

**Skill name**, and the repo you targeted:
> [`paper-to-code-audit`](paper-to-code-audit/SKILL.md), targeting the AutoSaddler adapter in [Skynet](https://github.com/gilad12-coder/skynet) against [AutoSaddler, arXiv v1](https://arxiv.org/abs/2608.23041v1).


## Part I: The Workflow

**What the workflow is**, and why it's worth encoding:
> Check whether a research implementation matches its paper or pinned upstream implementation. I repeatedly need this when integrating optimization methods into Skynet: extract the requirements, trace the actual execution path, and report supported matches, adaptations, discrepancies, and gaps in evidence.

**The decision point** in it (what the agent has to judge, not just execute):
> Decide whether a difference preserves the required behavior, intentionally changes it, contradicts it, or needs more evidence. Passing tests or importing the original engine is not enough; adapters and configuration can change the method.

**What you learned running it manually** that you would not have guessed:
> Before authoring the skill, I compared the paper's separate training/development splits ([§4](https://arxiv.org/html/2608.23041v1#S4)) with Skynet commit `c9b9201e895661b96cf8c689b5ac2012369ecbfe`. Its [`execute`](https://github.com/gilad12-coder/skynet/blob/c9b9201e895661b96cf8c689b5ac2012369ecbfe/backend/core/service_gateway/optimization/blackbox/autosaddler_runner.py#L1341) builds both splits from the same examples. [`visible_examples`](https://github.com/gilad12-coder/skynet/blob/c9b9201e895661b96cf8c689b5ac2012369ecbfe/backend/core/service_gateway/optimization/blackbox/autosaddler_runner.py#L222) explicitly documents this choice: an intentional adaptation, not independent development-set validation. This showed why an unchanged upstream engine is insufficient evidence of fidelity. The manual review covered adapter wiring; upstream execution and benchmark results were not tested.


## Part II: The Skill

Installed for discovery at `~/.claude/skills/paper-to-code-audit` and `~/.codex/skills/paper-to-code-audit`, both linked to the submitted skill directory.

**Your description**, verbatim:
```
Audits an algorithm implementation against a research paper or pinned upstream code and reports matches, adaptations, and discrepancies with source evidence. Use when asked whether a repository implements a paper faithfully, preserves an upstream algorithm, or leaves out required behavior. Not for paper summaries without a code comparison or general code reviews.
```

**Why it's worded that way** (what a user would type to trigger it):
> It names the action and the questions I ask: whether code implements a paper faithfully, preserves upstream behavior, or leaves something out. The explicit exclusions keep paper summaries and general reviews outside its scope, following the [Agent Skills description guidance](https://agentskills.io/skill-creation/best-practices).

**Judgment encoded in the body** (what it says to do when things are ambiguous, and what not to do):
> Pin both sides, read and test the same revision, trace adapters and delegated code, and verify operators in raw source. Check that the reference states a requirement before judging fidelity. Separate method requirements from experimental settings. Classify each finding as equivalent, an intentional adaptation, a discrepancy, or insufficient evidence. Do not infer intent, equivalence, or performance from names or passing tests. The final check requires a source obligation and implementation evidence for each finding; implementation edits require a request to fix it.

**Supporting files**, if any, and why they aren't inline:

| File | Contents | Why it's separate |
|---|---|---|
| [references/assessment-guide.md](paper-to-code-audit/references/assessment-guide.md) | Classification guidance, four worked examples, and a report table. | Keeps detailed examples and the report format outside the main procedure; the skill reads this guide before an audit. |


## Part III: Testing

**Triggering:**

Each prompt ran in a fresh Claude Code 2.1.289 session (`claude-fable-5-1`) with the pinned checkout and full paper text supplied as context. None named the skill. A successful `Skill` tool call counted as activation; positive probes stopped after loading, while the near-miss ran to completion.

| Prompt | Should fire? | Did it? |
|---|---|---|
| Does Skynet's AutoSaddler implementation match arXiv:2608.23041v1? Review only. | Yes | Yes; its first tool call loaded the skill. |
| Check whether our AutoSaddler adapter preserves the upstream algorithm, including its split and selection rules. | Yes | Yes; its first tool call loaded the skill. |
| Compare the AutoSaddler paper with this repository and tell me what we left out or changed. | Yes | Yes; its first tool call loaded the skill. |
| Summarize arXiv:2608.23041v1; do not inspect a repository or implementation. | No (near-miss) | No; it read only the paper and returned a summary. |

**End-to-end run** on your repo, and the result:
> Audited Skynet commit `c9b9201e` against arXiv v1 for data separation, acceptance-policy wiring, and returned-candidate selection. The skill read its assessment guide, inspected the pinned adapter, and checked the raw upstream source at `9df6d2e3e1d3946057243690bca28e136fa81179`. The reviewed result:

| Behavior | Assessment | Result and evidence |
|---|---|---|
| Separate training/development data | Intentional adaptation | Both splits wrap the same examples; the docstring documents re-scoring the same pool. This does not provide independent development-set validation. [Adapter](https://github.com/gilad12-coder/skynet/blob/c9b9201e895661b96cf8c689b5ac2012369ecbfe/backend/core/service_gateway/optimization/blackbox/autosaddler_runner.py#L222). |
| Acceptance on valid observations | Equivalent | The wired policy requires identical case/repetition keys and strict improvement; ties are rejected. [Upstream policy](https://github.com/microsoft/AutoSaddler/blob/9df6d2e3e1d3946057243690bca28e136fa81179/src/autosaddler/v2/core/policies.py#L102). |
| Invalid rollout handling | Insufficient evidence | The policy filters invalid pairs; the paper does not specify this case. [Filtering](https://github.com/microsoft/AutoSaddler/blob/9df6d2e3e1d3946057243690bca28e136fa81179/src/autosaddler/v2/core/policies.py#L112). |
| Selection on normal completion | Equivalent | Upstream selects the highest development score, and the adapter returns that candidate. [Ranking](https://github.com/microsoft/AutoSaddler/blob/9df6d2e3e1d3946057243690bca28e136fa81179/src/autosaddler/v2/core/policies.py#L146), [return path](https://github.com/gilad12-coder/skynet/blob/c9b9201e895661b96cf8c689b5ac2012369ecbfe/backend/core/service_gateway/optimization/blackbox/autosaddler_runner.py#L1446). |
| Timeout or evaluator failure | Insufficient evidence | The runner attaches a recovered candidate to an error; the parent normally raises `ServiceError`. The paper does not specify interruption recovery. [Recovery](https://github.com/gilad12-coder/skynet/blob/c9b9201e895661b96cf8c689b5ac2012369ecbfe/backend/core/service_gateway/optimization/blackbox/autosaddler_runner.py#L1490), [parent](https://github.com/gilad12-coder/skynet/blob/c9b9201e895661b96cf8c689b5ac2012369ecbfe/backend/core/service_gateway/optimization/blackbox/native_runtime.py#L892). |

Earlier trials exposed an overbroad dependency search, a fetched summary that reversed a tie-break, and overclassification of unspecified behavior. I restricted source lookup, required raw code, ordered the classification rules, and added a cancellation counterexample. A fresh regression test and full rerun correctly left unspecified interruption recovery unverified. The four trigger results above remain applicable because the description did not change.

No implementation files changed. These are source-inspection findings: the checkout lacked the upstream runtime, test commands were unavailable under the evaluation permissions, and no Skynet tests or benchmarks ran.


## Submission
1. Check that no unanswered placeholders remain.
2. Confirm the skill directory itself is committed under `week3/`.
3. Push all changes to your remote repository and submit via Gradescope.
