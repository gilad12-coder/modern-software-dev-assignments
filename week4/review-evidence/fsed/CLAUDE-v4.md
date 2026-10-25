# fsed

`fsed` 0.5.4 replaces many fixed strings in one pass with an Aho-Corasick trie.
It is a Python library and Click CLI. Reviewed at upstream `0227a62`.

## Architecture

- For pattern detection and CLI behavior, start at `main` in `fsed/fsed.py`.
  It builds the trie and rewrites files; `setup.py` exposes it as `fsed`.
- For matching changes, inspect `TrieNode`, `Trie`, and `AhoCorasickTrie` in
  `fsed/ahocorasick.py`. Keep suffix links, greedy/chart-based replacement,
  and boundary transforms consistent.
- Use `fsed/utils.py` for binary streams: normal files, gzip, xz, zip members,
  and `-`. Keep Python 2/3 type aliases in `fsed/compat.py`.
- Add regressions in `fsed/tests/`, alongside the existing trie or CLI tests.
  Use `click_command_runner` for CLI behavior; keep relative imports.
- For packaging changes, check `setup.py`, `setup.cfg`, `MANIFEST.in`, and
  `fsed/VERSION`. Preserve the test corpus in source distributions.

## Commands

Run from the fork root. These commands were checked on Python 3.11.9.
The old Python 2.7-3.8 Travis matrix was not rerun.
Upstream does not ignore `.venv/`; the setup adds a local Git exclude.

```sh
printf '/.venv/\n' >> "$(git rev-parse --git-path info/exclude)"
python3.11 -m venv .venv
.venv/bin/python -m pip install pip==24.3.1 setuptools==75.3.0 wheel==0.45.1 build==1.2.2.post1 click==8.1.8
.venv/bin/python -m pip install --no-build-isolation -e .
```

After changes under `fsed/`, run the full suite. Save its output and return its
actual exit status; keep the final `exit` when reporting results:

```sh
(.venv/bin/python -m unittest discover -s fsed/tests -t . -v > .venv/test-results.log 2>&1; test_exit=$?; cat .venv/test-results.log; exit "$test_exit")
```

The baseline has 16 tests. For a focused CLI/corpus check, packaging validation,
syntax compilation, and CLI options, respectively:

```sh
.venv/bin/python -m unittest fsed.tests.test_fsed.TestFsed.test_end2end -v
.venv/bin/python -m build --no-isolation
.venv/bin/python -m compileall -q fsed
.venv/bin/python -m fsed.fsed --help
```

Packaging edits need the build check; it produces an sdist and wheel in `dist/`.
No linter or formatter is configured. `compileall` checks syntax only.

## Conventions

- Extend existing `unittest.TestCase` classes with `test_` methods and
  `self.assertEqual`/`self.assertRaises`.
- Preserve Python 2/3 syntax, `__future__` imports, and four-space indentation.
  Avoid annotations or f-strings during unrelated edits.
- File and pattern streams contain bytes; decode using the selected encoding
  before trie operations. `CMStringIO` fixtures take bytes and rewind on entry.
- Word boundaries use an internal NUL token (`\x00`); preserve the paired
  transform/untransform operations and distinguish greedy/slow behavior.

## Guardrails

- Keep `-t .` in test discovery; omitting it breaks relative imports.
  The old Travis `setup.py test` fails with the pinned setuptools. Use unittest.
- The README says format defaults to `sed`; the code defaults to `auto`.
  `main` forces line-by-line processing even with `--across-lines`.
  Do not promise multiline matching without changing and testing that implementation.
- Do not hand-edit `build/`, `dist/`, `fsed.egg-info/`, `.venv/`, or `*.pyc`.
  Keep the `.gz` corpus and Perl/sed reference files unchanged unless regenerating
  fixtures. Follow `fsed/tests/README.rst` for regeneration commands.
- Change `fsed/VERSION` only for an explicit release task.
