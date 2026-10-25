# Week 4 write-up

**Repository:** [Enthought Traits](https://github.com/enthought/traits), a Python library for observable typed attributes.
**Fork:** [gilad12-coder/traits, agent-config branch](https://github.com/gilad12-coder/traits/tree/agent-config).
**Configuration:** [fork-root CLAUDE.md](https://github.com/gilad12-coder/traits/blob/agent-config/CLAUDE.md), identical to [the submission copy](CLAUDE.md).

I chose a substantial Python library that I did not write. At the explored commit,
[`a22bcba49a25ced116eef0613964742c6180346b`](https://github.com/enthought/traits/commit/a22bcba49a25ced116eef0613964742c6180346b),
Traits contains 454 tracked files, including 333 Python files and a 5,886-line C extension.
Those Python files total 65,211 lines, including tests, examples, and generated code. The repository had 464 stars on October 25, 2026.

Traits already has CI and documentation. Its gap is durable guidance for an agent crossing the Python/C boundary, finding distributed tests, and avoiding generated files.
The checked tree contains no `AGENTS.md` or `CLAUDE.md`, and no tracked `.claude/`, `.codex/`, `.cursor/`, or `copilot-instructions` paths.
The assignment sets no minimum repository size and permits an independently chosen repository.

## Part I: Exploration

An exploration agent inspected source, packaging, CI workflows, test helpers, and generated-file headers.
I checked those findings against command output. The tested environment was macOS on Apple Silicon, CPython 3.11.9, and Apple Clang 21.
[Evidence and exact commands](review-evidence/traits/README.md) include dependency versions, complete output, and exit codes.

### Commands

Run from the fork root:

```sh
printf '\n/.venv/\n/.mypy_cache/\n' >> .git/info/exclude
uv venv --python 3.11.9 --seed .venv
.venv/bin/python -m pip install -e '.[test,docs]' build
```

This installs test/documentation extras and compiles `traits.ctraits`. I verified this setup in a clean clone, including Git cleanliness.
An initial host-specific `python3.11` symlink broke standard venv creation; the checked `uv` recipe avoids that launcher problem.

| Purpose | Exact command | Observed result |
|---|---|---|
| Full source suite | `.venv/bin/python -m unittest discover -s traits -t . -v` | 1,628 tests; zero failures, errors, or skips; exit 0. |
| Focused tests | `.venv/bin/python -m unittest traits.tests.test_integer -v` | 10 baseline tests; exit 0. |
| Repository lint | `.venv/bin/python -m flake8` | Exit 0 with `flake8-ets` installed. |
| Strict CI copyright check | `.venv/bin/python -m flake8 --select H102 --copyright-end-year current` | Exit 0. |
| Package build | `.venv/bin/python -m build` | Builds the 7.2.0 source distribution and universal2 CPython 3.11 wheel; exit 0. |
| Documentation build | `(cd docs && ../.venv/bin/python -m sphinx -b html -W source build)` | Builds HTML with warnings treated as errors; exit 0. |
| Run the library | `.venv/bin/python -c 'from traits.api import HasTraits, Int; x = HasTraits(); x.add_trait("count", Int()); x.count = 2; assert x.count == 2; print(x.count)'` | Prints `2`; exit 0. Traits has no application server to start. |

I also installed the built wheel with test extras into a separate environment.
From outside the source checkout, `python -m unittest discover -v traits` passed all 1,628 tests.
Import paths confirmed that this run used the installed wheel and its compiled extension.
This checks upstream CI's distribution-testing approach separately from the editable install.

### Structure, conventions, and traps

`traits/api.py` exposes public imports. `HasTraits` and its metaclass in `has_traits.py` connect declarations to validation and notifications.
`trait_types.py` defines Python validators; `ctrait.py` extends the C-level machinery in handwritten `ctraits.c`.
Modern observation uses `traits/observation/` for parsing, expressions, graphs, and event notifiers.
Legacy listeners remain in `traits_listener.py` and `trait_notifiers.py`. Protocol adaptation lives in `traits/adaptation/`.

Tests use `unittest.TestCase`, `test_*` methods, and `self.assert*` assertions.
They span several packages; running only `traits/tests/` misses observation, adaptation, and stub tests.
`traits/testing/optional_dependencies.py` supplies skip decorators.
Modern callback tests use the exception-handler stack in `traits.observation.api`; the handler in `traits.api` belongs to legacy notifications.
Stub tests deliberately include expected mypy errors and check them through a unittest harness.

The code uses Enthought license headers and 79-column formatting. `pyproject.toml` configures Black/isort; CI runs Flake8 with `flake8-ets`.
The PR template links public API changes to `.pyi` stubs, the API reference, and the user manual.

An actual import before installation failed with `ModuleNotFoundError: traits.ctraits`; finding the Python package does not establish a working build.
Upstream ignores compiled extensions and build output, but omits `.venv/`, which explains the local exclude.
`setup.py` generates `traits/version.py`. The observation parser embeds generated code and a Lark runtime; its source is `_dsl_grammar.lark`.
Historical pickle fixtures are maintained compatibility data and must not be regenerated casually.

## Part II: The file

The final `CLAUDE.md` has 473 whitespace-delimited words. It covers the project, architecture, commands, conventions, and guardrails.
I kept directions to authoritative files instead of copying implementation details.
I omitted the complete API catalogue, release procedures, generic coding advice, and production infrastructure that this library does not need.

The hardest choice was keeping both the Python/C map and the modern/legacy observation distinction.
Both prevent plausible edits in the wrong layer. The generated parser and historical fixtures also warrant explicit protection.
Style details stay brief because Flake8 can enforce them.

The assignment's [AGENTS.md guidance](https://agents.md/), [HumanLayer article](https://www.hlyr.dev/blog/writing-a-good-claude-md),
and [Claude Code best practices](https://code.claude.com/docs/en/best-practices) informed the short operating guide and runnable checks.
I also reviewed the full transcript and key slides of [Factory's agent-readiness talk](https://ai.engineer/talks/ShuJ_CN6zr4-making-codebases-agent-ready)
and [Basis's complete article](https://www.getbasis.ai/blogs/how-we-made-our-monorepo-ergonomic-for-agents).
X blocked direct access to the linked post, so I used the author's article rather than claiming to read the thread.
For Traits, these ideas translate into one current guide, directions to the right subsystem, executable checks, and protected generated files.

## Part III: Trying it out

Each trial used a fresh Claude Code 2.1.308 session with `claude-opus-5-5` at medium effort and the environment already installed.
I requested `--safe-mode` and explicitly asked each session to read the checkout's `CLAUDE.md`.
The transcripts verify those reads. They do not prove complete instruction isolation or automatic guide discovery.
The task prompts supplied no test commands. These trials show observed use; there was no comparison against an agent without the guide.

### Task 1: Run the full test suite

I asked for the full suite, exact command, counts, exit status, and missing guide detail.
The agent used the guide's discovery scope and reported 1,628 tests, zero failures, errors, or skips, and exit 0.
It first omitted `-v`, then reran the documented verbose command to inspect results.
Two Sphinx deprecation warnings interrupted result lines, so its initial count of lines ending in `... ok` was 1,626.
It checked unittest's final summary and correctly reported 1,628. It changed no source files.
[Trial 1 record](review-evidence/traits/trial1.json).

### Task 2: Add a small regression test

I asked for one test showing that a rejected float assignment preserves an `Int` trait's existing value and sends no modern observation event.
A subsequent valid assignment had to prove the observer remained attached.

The agent added `TestInt.test_rejected_float_preserves_value_and_does_not_notify` in `traits/tests/test_integer.py`.
It reused the existing `A` fixture, started at `7`, attached `events.append` with `observe`, and rejected `23.0` with `TraitError`.
It checked the unchanged integer and empty event list, then assigned `8` and checked the event's object, name, old value, and new value.
Assertions stayed outside the callback, so no exception-handler override was needed.

The focused module passed 11 tests. The full suite passed 1,629 tests. Flake8 passed with the repository plugin installed.
The agent followed the existing unittest style and changed no production code or fixtures.
It suggested more detail about formatter expectations and test placement.
I kept that detail out of the root file because the local module and configuration already answer those questions.

I saved the [21-line test addition](review-evidence/traits/trial2.patch) and restored the checkout.
Applying the patch to a clean clone reproduced the focused test, all 1,629 tests, and Flake8 successfully.
The fork's final change is the guide; the temporary test remains inspectable evidence.
[Trial 2 record](review-evidence/traits/trial2.json).

### One grounded improvement

Task 1 exposed a result-reporting problem. I added the checked baseline count and the two known Sphinx warnings,
with an instruction to use unittest's summary and process status rather than count verbose lines.
The [v1](review-evidence/traits/CLAUDE-v1.md) and [v2](review-evidence/traits/CLAUDE-v2.md) copies show that change.

I repeated Task 1 with the same prompt in a fresh session.
The agent ran the documented verbose command once, reported 1,628 tests with zero skips and exit 0,
and used the final summary while recognizing the documented warnings.
It changed no source files. [Trial 3 record](review-evidence/traits/trial3.json).
This is one successful use of the revision, not proof that every future agent will follow it.

The checks cover macOS/Apple Silicon and Python 3.11.9. I did not run other CI platforms or Python versions,
the environment without optional dependencies, or interactive GUI flows. The source guide changes no runtime behavior.
