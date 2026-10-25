# fsed verification evidence

These checks ran on October 25, 2026, against upstream commit
`0227a62b0dd4ba64176d3e8394243fc8157296b5` and Python 3.11.9 on macOS.
The final fork changes only its root `CLAUDE.md`. Trial 2's temporary test was restored after verification.

## Baseline checks

| Check | Result | Record |
|---|---|---|
| Pinned build tools and Click installation | Exit 0 | [tools](install-tools.log) |
| Editable package installation | Exit 0 | [package](install-project.log) |
| Full suite | 16 pass; exit 0 | [test output](tests.log) |
| CLI/corpus integration test | 1 pass; exit 0 | [focused output](focused-test.log) |
| Syntax compilation | Exit 0; no diagnostic output | [syntax output](syntax.log) |
| Source distribution and wheel | Both built; exit 0; existing deprecation warnings | [build output](build.log) |
| CLI help | Exit 0 | [CLI output](cli-help.log) |
| Old `setup.py test` | Expected failure; exit 1 | [legacy failure](legacy-test-command.log) |
| Discovery without `-t .` | Expected failure; two import errors; exit 1 | [discovery failure](wrong-discovery-root.log) |

[baseline-checks.json](baseline-checks.json) records exact argument arrays and process exit codes.
The explicit test runner replaces the obsolete Nose/setuptools test entry point; it runs the existing unittest cases unchanged.
No linter is configured. Syntax compilation is not a lint result.

## Fresh agent trials

All three trials used separate Claude Code sessions with `CLAUDE.md` present and no task-prompt hint about the file.
The recorded model is `claude-opus-5-5`. The default model was used for these assignment trials.
The trials are separate from the independent PR review gate.

- [Trial 1](trial1.json): run the full suite with [guide v1](CLAUDE-v1.md); 16 tests pass.
- [Trial 2](trial2.json): add a CLI regression test with v1; 17 tests pass with the temporary change.
- [Trial 2 patch](trial2.patch): the only source edit made during the trials.
- [Independent trial 2 checks](trial2-independent-checks.json): direct process exits for the [focused test](trial2-independent-focused.log) and [full suite](trial2-independent-full.log).
- [Trial 3](trial3.json): repeat Task 1 with [guide v2](CLAUDE-v2.md); 16 tests pass. The agent partially adopted the logging wrapper.
- [Shell wrapper checks](wrapper-checks.json): Bash and zsh each return 0 for the full suite and 1 for the known discovery failure.

Each trial JSON contains its prompt, model, tool calls, tool results, and final answer.
Exports omit initialization, personal global instructions, hidden reasoning, and billing metadata.
Raw session records remain in the ignored local `.work/` directory; their SHA-256 hashes identify them in the exports.
`<FSed_CHECKOUT>` and `<TASK_TMP>` replace absolute local paths in saved output. No test result or exit code was changed.
Agent summaries are evidence of what the agent said, not independent proof of every claim.
The write-up explicitly identifies the mismatch between Trial 3's actual command and its final answer.

The task prompts used existing local dependencies. MCP servers and additional agents were disabled.
Personal global instructions still loaded, so the trials do not measure the guide in isolation.
Only Python 3.11.9 and the host's UTF-8 locale were tested. The old Python 2.7–3.8 matrix was not run.
Build output retains legacy metadata warnings. The wheel was built, but a clean wheel installation was not separately tested.

## Source references

- [Pinned source tree](https://github.com/wroberts/fsed/tree/0227a62b0dd4ba64176d3e8394243fc8157296b5)
- [CLI and pattern handling](https://github.com/wroberts/fsed/blob/0227a62b0dd4ba64176d3e8394243fc8157296b5/fsed/fsed.py)
- [Existing tests and helper](https://github.com/wroberts/fsed/blob/0227a62b0dd4ba64176d3e8394243fc8157296b5/fsed/tests/test_fsed.py)
- [Python 3.11 unittest discovery](https://docs.python.org/3.11/library/unittest.html#test-discovery)
- [PyPA build documentation](https://build.pypa.io/en/stable/)

The documentation index did not have a matching `fsed` or build-version entry.
Repository source and official documentation supplied the reference material; the pinned commands were verified locally.
