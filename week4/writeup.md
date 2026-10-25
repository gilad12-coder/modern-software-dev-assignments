# Week 4 Write-up

**Repo chosen:** [wroberts/fsed](https://github.com/wroberts/fsed), a Python library and command-line tool for replacing many fixed strings in one pass.

**Fork:** [gilad12-coder/fsed](https://github.com/gilad12-coder/fsed/tree/agent-config).
The file sits at the fork root on `agent-config`: [CLAUDE.md](https://github.com/gilad12-coder/fsed/blob/agent-config/CLAUDE.md).
The submission copy is [week4/CLAUDE.md](CLAUDE.md).

I chose a small legacy package instead of a large, active project. At review on October 25, 2026, `fsed` had 26 stars.
Its default branch last changed on November 25, 2019. The explored commit was
[`0227a62b0dd4ba64176d3e8394243fc8157296b5`](https://github.com/wroberts/fsed/commit/0227a62b0dd4ba64176d3e8394243fc8157296b5).
It contains 24 tracked files and 824 lines of package implementation. Including tests and setup, its Python files total 1,492 lines.
It has no `AGENTS.md` or `CLAUDE.md` at that commit. The assignment permits an independently chosen repository and sets no minimum size.

## Part I: Exploration

The exploration agent read `setup.py`, `setup.cfg`, `.travis.yml`, `MANIFEST.in`, the README, all four implementation modules, and both test modules.
It then ran the commands below in an isolated environment. Source inspection identified likely traps; command results established which traps actually fail.

The checked environment was macOS, Python 3.11.9, and a UTF-8 locale. These commands run from the fork root:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install pip==24.3.1 setuptools==75.3.0 wheel==0.45.1 build==1.2.2.post1 click==8.1.8
.venv/bin/python -m pip install --no-build-isolation -e .
```

| Area | Exact command and observed result |
|---|---|
| Full tests | `.venv/bin/python -m unittest discover -s fsed/tests -t . -v` — 16 tests pass: 11 trie tests and five replacement/CLI tests. |
| Focused integration test | `.venv/bin/python -m unittest fsed.tests.test_fsed.TestFsed.test_end2end -v` — one test passes. It runs the CLI against the compressed corpus and compares its output with saved Perl and sed results. |
| Build | `.venv/bin/python -m build --no-isolation` — builds `dist/fsed-0.5.4.tar.gz` and `dist/fsed-0.5.4-py2.py3-none-any.whl`. Existing setuptools deprecation warnings remain. |
| Run | `.venv/bin/python -m fsed.fsed --help` — exits zero and lists CLI options. `setup.py` also installs the `fsed` console command. The integration test exercises replacement behavior. |
| Lint | No linter or formatter is configured. `.venv/bin/python -m compileall -q fsed` passes, but this checks syntax only. |
| Misleading legacy command | `.venv/bin/python setup.py test` — exits one with `invalid command 'test'` under the pinned setuptools. The old Travis command is obsolete in this environment. |
| Wrong discovery root | `.venv/bin/python -m unittest discover -s fsed/tests` — exits one with two relative-import errors. Adding `-t .` finds the actual 16 tests. |

[Saved output and exit codes](review-evidence/fsed/README.md) support these results.

The main entry point is `main` in `fsed/fsed.py`. It detects the pattern format, builds a trie, and rewrites input streams.
`fsed/ahocorasick.py` contains `TrieNode`, `Trie`, and `AhoCorasickTrie`, including suffix links, greedy replacement, and slower chart-based replacement.
`fsed/utils.py` opens binary streams for regular files, compressed files, zip members, and standard input/output.
`fsed/compat.py` defines Python 2/3 type aliases. Packaging uses `setup.py`, `setup.cfg`, `MANIFEST.in`, and `fsed/VERSION`.

The tests reveal conventions that a new agent could miss. They use `unittest.TestCase`, `test_` methods, native assertions, and relative imports.
`CMStringIO` takes bytes and rewinds on context entry. Production code decodes file bytes before trie operations.
The source retains `__future__` imports and Python 2/3 syntax. Word-boundary matching uses an internal NUL token and paired transforms.

Two source details contradict plausible assumptions. The README describes `sed` as the default pattern format, but the code uses `auto`.
Also, `main` sets `by_line = True` even when the caller selects `--across-lines`. The guide warns about both without changing unrelated runtime behavior.

Build output, `dist/`, `fsed.egg-info/`, virtual environments, and bytecode are generated.
The compressed corpus and Perl/sed reference files are maintained fixtures, not disposable build output. Their README explains regeneration.
There is no vendored dependency directory in the tracked tree.

## Part II: The File

I chose `CLAUDE.md` because the trials used Claude Code, which loads that filename from the repository root.
The final guide contains 468 whitespace-delimited words. It covers the project, architecture, exact commands, observed conventions, and guardrails.

**Deliberate omissions:** I left out the full algorithm explanation, CLI option catalogue, installation marketing, and generic coding advice.
The source and `--help` already provide those details. I also avoided inventing a lint command or upgrading the package's runtime code.

**Hardest inclusion decision:** I kept the failed legacy test command and the ignored multiline option.
Both cost space, but both prevent believable mistakes when an agent follows the old documentation.
I stated that the old Python 2.7–3.8 Travis matrix was not rerun. A Python 3.11 pass does not validate those versions.

## Part III: Trying It Out

Each task ran in a fresh, headless Claude Code 2.1.308 session with the guide at the fork root.
The session records identify the model as `claude-opus-5-5`. The task prompts did not name the guide or supply its commands.
The environment was already installed. Personal global instructions also loaded, so these trials do not isolate the guide's effect.

**Task 1:** “Run this repository’s full test suite and report whether it passes. Do not change source files. Report the exact command, test count, exit status, and any setup or discovery pitfall you notice.”

The agent used the documented discovery command and reported all 16 tests passing.
It initially piped output through `tail` and tried `${PIPESTATUS[0]}`, which returned empty under zsh.
It then reran the tests without that pipeline and captured exit zero. It also confirmed the missing-`-t .` import failure.
It changed no source files. [Trial 1 record](review-evidence/fsed/trial1.json).

**Task 2:** “Add a small regression test showing that the CLI automatically detects TSV patterns and preserves a Unicode replacement. Exercise the actual CLI path and follow the existing test style. Run the relevant checks. Do not change production code or existing corpus fixtures. Do not commit or push. Report what you changed, exact check results, and any missing context that made the task harder.”

The agent added `TestFsed.test_cli_auto_tsv_unicode` through the existing `click_command_runner` helper.
It used temporary UTF-8 files, omitted `--pattern-format`, and asserted both exit zero and `a naïve ☺\n` output.
It followed the existing `unittest` style and preserved relative imports and older Python syntax.
A manual contrast produced unchanged text with forced `sed` format and replaced text with the automatic default.

The focused test passed; the full suite passed 17 tests. A separate direct run confirmed both results and captured their process exit codes.
The helper reads output with the host's default encoding, so this trial establishes behavior on the checked UTF-8 host only.
The trial changed no production code or corpus fixtures. Its [patch](review-evidence/fsed/trial2.patch) remains as evidence; the checkout was restored afterward.
[Trial 2 record](review-evidence/fsed/trial2.json).

**One grounded improvement:** Task 1 showed that knowing the test command did not ensure reliable reporting.
I added one command that saves the full output, captures `$?` before another command runs, and returns that status from a subshell.
The [v1](review-evidence/fsed/CLAUDE-v1.md) and [v2](review-evidence/fsed/CLAUDE-v2.md) copies show the exact addition.

I repeated Task 1 in another fresh session. The agent saved the full log and printed the captured status, correctly reporting 16 passing tests.
However, its executed command replaced the final `exit` with `echo`. Its final answer quoted the guide's stronger command instead.
It also used a pipeline for the negative discovery probe and recognized that the printed zero belonged to `tail`.
This was partial adoption, not proof that the agent always propagates failures correctly. [Trial 3 record](review-evidence/fsed/trial3.json).

I then checked the exact final wrapper directly in Bash and zsh. It returned zero for the full suite and one for broken discovery in both shells.
[Four checked cases](review-evidence/fsed/wrapper-checks.json) support the guide's command independently of the agent's summary.
