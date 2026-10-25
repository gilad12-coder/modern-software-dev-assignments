# Assignment 4 submission handoff

The deliverables use `fsed`, a small legacy Python package. The assignment sets no minimum repository size.
This file records preparation checks. It is not the assignment write-up.

## Rubric assessment

| Rubric section | Available points | Readiness assessment |
|---|---:|---|
| I. Exploration | 20 | Covered: checked setup, test, build, and run commands; honest absence of lint; architecture; conventions; generated files and fixtures. |
| II. Agent file | 55 | Covered: all five required areas in a 463-word root guide, with concrete repository details and working commands. |
| III. Trials | 25 | Covered: two fresh task records, a temporary test patch, a grounded improvement, and an honest follow-up account. |

The evidence supports the full-credit criteria in all three sections. This assessment does not assign the course grade.
The write-up states the material limits: one Python version, a UTF-8 host, inherited instructions, and imperfect exit propagation in agent tool calls.
Parent-guide content during Trials 1–3 remains unknown; the evidence does not isolate the guide's effect.
The final follow-up used the guide's inner wrapper correctly; direct shell checks cover its failure behavior.

## Files and branches

- [Write-up](writeup.md)
- [Submission copy of CLAUDE.md](CLAUDE.md)
- [Evidence index](review-evidence/fsed/README.md)
- [Assignment repository, grading branch `week4-agent-config`](https://github.com/gilad12-coder/modern-software-dev-assignments/tree/week4-agent-config/week4)
- [Assignment PR #4](https://github.com/gilad12-coder/modern-software-dev-assignments/pull/4)
- [fsed fork, branch `agent-config`](https://github.com/gilad12-coder/fsed/tree/agent-config)
- [Root guide at the exact fork commit](https://github.com/gilad12-coder/fsed/blob/2735f46513fc490d6769af7c475f2ade2845433c/CLAUDE.md)
- [Internal fork PR #1](https://github.com/gilad12-coder/fsed/pull/1)

The two guide copies match. The fork changes only `CLAUDE.md`; the trial test is saved as a patch, not shipped as a package change.
The assignment PR compares against `week3-skill` so its diff contains Week 4 only.
Neither PR needs a merge for these branch links to expose the deliverables.
Independent review results belong to the PR descriptions and comments, where they identify the exact reviewed commits.

All new local content, environments, logs, and scratch work remain inside `week4/`.
The `.work/` directory is ignored and is not part of the grading branch.

## Access and final submission

On October 25, the assignment repository showed `isaackann` and `vdaita` as write collaborators.
The existing write invitation for `mihail911` remained pending. Its acceptance is outside the student's control.
The repository and fork are public, and the deliverable links identify the grading branches explicitly.

Gradescope was not inspected after sign-in was required. The user requested file preparation only.
No Gradescope submission was made.

Before submitting:

1. Open Assignment 4 in Gradescope.
2. Select `gilad12-coder/modern-software-dev-assignments` and `week4-agent-config` if the form uses GitHub submission.
3. If it asks for links, use the grading branch and fork links above. Check the form's exact requirements.
4. Confirm that the preview shows the `fsed` write-up and matching root guide.
5. Complete the final submission yourself.
