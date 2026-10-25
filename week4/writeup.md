# Week 4 Write-up

**Repo chosen** and link to your fork:

[Enthought Traits](https://github.com/enthought/traits) is a Python library for observable typed attributes. I did not write it.
My fork is [gilad12-coder/traits, agent-config branch](https://github.com/gilad12-coder/traits/tree/agent-config).
At the [explored commit](https://github.com/enthought/traits/commit/a22bcba49a25ced116eef0613964742c6180346b), the repository had no `AGENTS.md` or `CLAUDE.md`.

**File you wrote** (`AGENTS.md` or `CLAUDE.md`):

The [fork-root CLAUDE.md](https://github.com/gilad12-coder/traits/blob/agent-config/CLAUDE.md) matches [the submission copy](CLAUDE.md). It has 473 words and covers all five required areas.

## Part I: Exploration

| | Finding |
|---|---|
| Build / run | The setup below compiles `traits.ctraits`. `.venv/bin/python -m build` builds the source distribution and wheel. `(cd docs && ../.venv/bin/python -m sphinx -b html -W source build)` builds the documentation. Both passed. Traits has no server; the smoke command below prints `2`. |
| Test | `.venv/bin/python -m unittest discover -s traits -t . -v`: 1,628 tests, no failures, errors, or skips; exit 0. `.venv/bin/python -m unittest traits.tests.test_integer -v`: 10 baseline tests; exit 0. |
| Lint / format | `.venv/bin/python -m flake8` and `.venv/bin/python -m flake8 --select H102 --copyright-end-year current` both passed. Flake8 needs `flake8-ets`. `pyproject.toml` configures Black/isort with 79-column formatting. |
| Key directories and entry points | `traits/api.py` exposes the public API. `has_traits.py`, `trait_types.py`, and `ctrait.py` connect Python declarations to handwritten `ctraits.c`. Modern observation uses `traits/observation/`; legacy notifications use `traits_listener.py` and `trait_notifiers.py`. Protocol adaptation is in `traits/adaptation/`. |
| Unstated conventions | Tests use `unittest.TestCase`, `test_*`, and `self.assert*`. They span several packages; `traits/tests/` alone misses observation, adaptation, and stub tests. Stub tests include expected mypy errors. Keep Enthought license headers. Public API changes also need `.pyi` stubs and documentation. |
| Off-limits (generated, vendored) | Do not hand-edit `traits/version.py`, compiled extensions, or build output. The observation parser embeds generated code and a Lark runtime; edit `_dsl_grammar.lark` instead. Preserve historical pickle fixtures because they test compatibility with older releases. |

**How you figured it out**: what you asked the agent, what you had to read yourself:

I asked an exploration agent to find the commands, architecture, conventions, and generated files.
I checked its findings against packaging and CI configuration, style settings, parser headers, and command output.

I verified this setup in a clean clone. Run it from the fork root:

```sh
printf '\n/.venv/\n/.mypy_cache/\n' >> .git/info/exclude
uv venv --python 3.11.9 --seed .venv
.venv/bin/python -m pip install -e '.[test,docs]' build
```

The editable install builds the C extension. Importing Traits before that failed. The local exclude keeps the environment out of Git.

```sh
.venv/bin/python -c 'from traits.api import HasTraits, Int; x = HasTraits(); x.add_trait("count", Int()); x.count = 2; assert x.count == 2; print(x.count)'
```

Checks ran on macOS/Apple Silicon with CPython 3.11.9 and Apple Clang 21.
I also tested the installed wheel outside the checkout: `python -m unittest discover -v traits` passed all 1,628 tests.
[Commands, outputs, and exit codes](review-evidence/traits/README.md) are saved with the submission.

## Part II: The File

**Anything you deliberately left out**, and why:

I left out the full API catalogue and release procedures to focus on routine code changes.
I pointed to source files instead of repeating their contents. Generic advice adds no repository-specific detail, and this library needs no production infrastructure instructions.

**The hardest call** on what to include:

I kept both the Python/C map and the distinction between modern and legacy observation. Both help prevent edits in the wrong layer.
I also kept warnings about generated files and historical fixtures. Style guidance stays brief because Flake8 can enforce it.

## Part III: Trying It Out

Both tasks used fresh Claude Code 2.1.308 sessions with `claude-opus-5-5` at medium effort and dependencies already installed.
I requested `--safe-mode` and an explicit read of `CLAUDE.md`, but supplied no test commands.

| # | Task | Did the agent use your commands and conventions? |
|---|---|---|
| 1 | Run the full suite and report the command, results, and gaps in the guide. | It used the guide's discovery scope, first omitted `-v`, then ran the documented command. Sphinx warnings caused a line count of 1,626; unittest's summary correctly reported 1,628 tests and exit 0. No source changed. [Record](review-evidence/traits/trial1.json). |
| 2 | Add a regression test: a rejected float must preserve an `Int` value and send no observation event. A valid assignment must prove the observer still works. | It followed the existing unittest style and discovery scope. The focused module passed 11 tests; the full suite passed 1,629; Flake8 passed. No production code or fixtures changed. [Record](review-evidence/traits/trial2.json). |

Task 2 omitted the verbose flag and piped output through `tail`, so its printed status does not establish Python's exit status.
The unittest summaries show `OK`; independent clean-clone replay recorded Python's exit 0 for the new test and full suite.
I saved the [21-line test addition](review-evidence/traits/trial2.patch) and restored the checkout. The fork's final change is only the guide.

**One thing you'd change** about the file after watching it get used:

I added the baseline count and the two known Sphinx warnings, with instructions to use unittest's summary and exit status instead of counting result lines.
The [v1](review-evidence/traits/CLAUDE-v1.md) and [v2](review-evidence/traits/CLAUDE-v2.md) copies show the change.
A [fresh repeat of Task 1](review-evidence/traits/trial3.json) ran the documented command once and correctly reported 1,628 tests, zero skips, and exit 0.

These trials verify explicit guide reads, not automatic discovery or complete instruction isolation. I did not run a comparison without the guide.
Other platforms, Python versions, minimal-dependency environments, and interactive GUI flows were not tested.
