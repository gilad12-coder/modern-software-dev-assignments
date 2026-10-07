# Week 3 Write-up

**Skill name**, and the repo you targeted:
> [`paper-to-code-audit`](paper-to-code-audit/SKILL.md), targeting [GEPA](https://github.com/gepa-ai/gepa). It compares GEPA's Combee implementation with [arXiv:2604.04247v2](https://arxiv.org/pdf/2604.04247v2).


## Part I: The Workflow

**What the workflow is**, and why it's worth encoding:
> Check a research paper's implementation against its paper, then report mistakes with source references and tests. I would use this when reviewing an algorithm I want to build on. The skill makes me trace the method through the code that runs, including defaults and delegated behavior.

**The decision point** in it (what the agent has to judge, not just execute):
> Decide whether a difference is a mistake, an equivalent implementation, a documented deviation, or a choice the paper leaves open. A finding needs evidence from the source and reachable code. If the sources conflict or a check cannot run, the report should explain what remains unresolved.

**What you learned running it manually** that you would not have guessed:
> I learned that the repository's tests verify existing behavior, which can include deliberate deviations from the paper. That led me to require the skill to trace each paper requirement through the code and check what the tests actually demonstrate.


## Part II: The Skill

I installed the skill at `~/.claude/skills/paper-to-code-audit` and `~/.codex/skills/paper-to-code-audit`, both linked to the submitted directory. The test checkout also had a project link at `.claude/skills/paper-to-code-audit`.

**Your description**, verbatim:
```
Audit an existing algorithm implementation against its research paper and relevant primary literature. Use when asked to check whether code follows a paper, compare an implementation with the published method, or find mistakes in a reproduction. Report discrepancies with source citations and verification evidence. Not for paper summaries, general code review, or implementing a method from scratch.
```

**Why it's worded that way** (what a user would type to trigger it):
> It uses requests I would make: "check whether code follows a paper," "compare an implementation," and "find mistakes in a reproduction." These phrases focus the skill on comparing existing code with a research paper.

**Judgment encoded in the body** (what it says to do when things are ambiguous, and what not to do):
> The skill compares specific versions of the paper and code, tracing how each requirement is implemented. If it finds a difference, it checks whether the code uses an equivalent approach, handles the requirement elsewhere, or makes a documented change. Related research helps clarify the requirements stated in the paper. The skill reports documented departures and treats details the paper leaves open as implementation choices. When the evidence is incomplete, it explains what remains uncertain and how to resolve it. It presents recommended corrections in a read-only report.

**Supporting files**, if any, and why they aren't inline:
> None, The workflow and decision rules fit in `SKILL.md`.


## Part III: Testing

**Triggering:**

| Prompt | Should fire? | Did it? |
|---|---|---|
| Check whether this repository implements Combee from arXiv:2604.04247v2 faithfully. | Yes | Yes, first tool call. |
| Compare the Combee code here with the published method and identify any mistakes. | Yes | Yes, first tool call. |
| Audit GEPA's reproduction of Combee, including its equations, defaults, and integration. | Yes | Yes, first tool call. |
| Summarize the Combee paper arXiv:2604.04247v2 and explain its main ideas. Do not inspect or compare repository code. | No  | No |

**End-to-end run** on your repo, and the result:
> [GEPA](https://github.com/gepa-ai/gepa) improves the prompts given to an LLM. It evaluates a selected candidate prompt on task examples, uses the resulting feedback to propose a revision, and evaluates that revision.
>
> [Combee](https://arxiv.org/pdf/2604.04247v2) changes how that feedback is used to form a revision. A batch contains feedback from multiple task executions using the selected prompt. Combee duplicates and shuffles the feedback, divides it into groups, and uses one model call per group to propose a revision. Those calls can run in parallel, and another call combines their revisions into one proposed prompt update.
>
> Batch size counts those task executions before feedback duplication. The paper's [batch-size controller](https://arxiv.org/html/2604.04247v2#S3.SS3) measures several trial batch sizes and estimates the time to process the training data. It chooses a size where further increases offer little speed benefit, subject to an upper bound intended to limit quality loss. In the audited GEPA version, the [built-in sampler](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/src/gepa/strategies/batch_sampler.py#L34-L102) keeps the user-configured batch size fixed throughout optimization; the controller is an [open implementation task](https://github.com/gepa-ai/gepa/issues/395).
>
> I gave the audit agent this prompt, verbatim, including its setup context:
>
> ```text
> Review this repository's Combee implementation against arXiv:2604.04247v2 and relevant primary literature. Check the full method and the paths users run. Report any mistakes, documented deviations, and evidence gaps with precise paper and code references. Run useful offline checks and recommend corrections where warranted. Produce the audit report without changing the implementation.
>
> Repository: gepa-ai/gepa, pinned at fb1ed589fd83372caef499cffc2c73173d3b096b. The complete versioned paper is available at /private/var/folders/mb/1djn4m8s3jdf9r4dkzs0dd_80000gn/T/cs146s-combee-audit-ghpmmo7c/paper.txt, extracted from https://arxiv.org/pdf/2604.04247v2. Rendered method and equation pages are at /private/var/folders/mb/1djn4m8s3jdf9r4dkzs0dd_80000gn/T/cs146s-combee-audit-ghpmmo7c/method-page.png and /private/var/folders/mb/1djn4m8s3jdf9r4dkzs0dd_80000gn/T/cs146s-combee-audit-ghpmmo7c/controller-page.png. Use the project instructions and available skills when relevant. All Python execution must use uv and Python 3.11. For offline checks, uv run --python 3.11 --with pytest pytest ... provides minimal tooling. Do not enable RECORD_TESTS or run llm_live tests.
> ```
>
> The skill reviewed GEPA at commit [fb1ed58](https://github.com/gepa-ai/gepa/commit/fb1ed589fd83372caef499cffc2c73173d3b096b). It identified the missing batch-size controller and a documented shortcut for one to three feedback records: a single model call produces a revision directly from the original feedback. It also found a blog example labeled batch size 3 where the paper reports 1.
>
> All 55 existing [Combee tests](https://github.com/gepa-ai/gepa/blob/fb1ed589fd83372caef499cffc2c73173d3b096b/tests/test_combee_reflection_lm.py) passed. They check feedback grouping and duplication, combining group proposals, the small-batch shortcut, and integration with GEPA. Additional checks called GEPA's optimization function, `gepa.optimize`, with synthetic feedback and scripted model replies, using batches of 9, 40, 60, 84, and 94 feedback records. For the first proposal in each check, they inspected the grouping, number of model calls, and information passed to the final model call. The tracked GEPA source files remained unchanged.
>
> The [reviewed audit](combee-audit.md) contains the findings, code references, test command, and limitations. Prompt quality, speedups, and behavior with real model providers remain unverified.
