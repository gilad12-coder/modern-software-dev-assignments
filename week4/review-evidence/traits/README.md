# Traits evidence

The explored upstream commit is `a22bcba49a25ced116eef0613964742c6180346b`.
The final fork adds only `CLAUDE.md`. Trials 1 and 2 used v1; Trial 3 used v2, which matches the final guide.

| File | Evidence |
|---|---|
| [repository.json](repository.json) | Tracked-file counts, inspected commit, fork, and absence of agent configuration files. |
| [environment.txt](environment.txt) | Installed versions for the development environment. This is a snapshot, not an upstream lockfile. |
| [checks.json](checks.json) | Commands, working directories, actual exit codes, and elapsed times for independent checks. |
| [checks.log](checks.log) | Complete output from those checks, including source/wheel tests, builds, and patch replay. Empty lint sections mean no diagnostics; exit codes are recorded separately. |
| [trial1.json](trial1.json) | Read of v1, full-suite commands, warning/count investigation, and the agent's report. |
| [trial2.json](trial2.json) | Read of v1, test edit, focused/full checks, Flake8, and the agent's report. |
| [trial2.patch](trial2.patch) | Temporary regression test, saved before restoring the checkout. |
| [trial3.json](trial3.json) | Read of v2, one full-suite run, and correct interpretation of the warnings. |
| [CLAUDE-v1.md](CLAUDE-v1.md), [CLAUDE-v2.md](CLAUDE-v2.md) | Exact guide versions used in the trials. |

The source suite and separately installed wheel each ran 1,628 tests successfully, with no failures, errors, or skips.
Both emitted two `RemovedInSphinx11Warning` messages under Sphinx 9.0.4.
The regression patch raises the count to 1,629. Clean-clone replay verified that count and passed Flake8.
Trial 2 piped test output through `tail`, so its printed full-suite status does not establish Python's exit status.
Its unittest summaries show `OK`; `patch-focused` and `patch-full` independently record Python's exit 0 without a pipeline.
Independent checks also verified normal/strict CI lint, source/wheel build, warnings-as-errors documentation build, and the library smoke test.

The initial exploratory environment used the framework CPython 3.11.9 interpreter directly.
The guide's `uv venv --python 3.11.9 --seed .venv` recipe was then verified in a clean clone.
The manifest omits an earlier host-launcher venv failure because its log was overwritten during setup recovery.
It retains the intentional unbuilt-import failure, which demonstrates why compiling the extension is necessary.

To replay the regression test, follow the guide's setup in a clean checkout at the upstream commit, then run:

```sh
git apply /absolute/path/to/week4/review-evidence/traits/trial2.patch
.venv/bin/python -m unittest traits.tests.test_integer.TestInt.test_rejected_float_preserves_value_and_does_not_notify -v
.venv/bin/python -m unittest discover -s traits -t . -v
.venv/bin/python -m flake8
```

Session exports preserve visible text, tool calls, and results. They omit internal reasoning, private initialization data, and telemetry.
`<traits-checkout>` and `<week4>` replace project paths; `<claude-executable>` replaces the local launcher path.
Each export includes a SHA-256 hash of the retained raw session record.
The prompts requested a root-guide read, and the launcher requested safe mode. The records prove those reads and subsequent actions,
not automatic discovery or complete instruction isolation. These were observed-use trials, not a controlled causal experiment.

Scope: macOS/Apple Silicon, CPython 3.11.9, installed test extras. Other platforms/Python versions, minimal-dependency CI, and interactive GUI flows were not tested.
