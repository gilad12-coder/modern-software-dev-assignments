# fsed

`fsed` 0.5.4 replaces many fixed strings in one pass with an Aho-Corasick trie.
It is a Python library and Click CLI. Reviewed at upstream `0227a62`.

## Architecture

- `fsed/fsed.py`: Click entry point `main`; pattern detection, trie construction,
  and file rewriting. `setup.py` exposes it as the `fsed` command.
- `fsed/ahocorasick.py`: `TrieNode`, `Trie`, and `AhoCorasickTrie`; suffix links,
  greedy replacement, the slower chart-based replacement, and boundary transforms.
- `fsed/utils.py`: binary streams for normal files, gzip, xz, zip members, and `-`.
  `fsed/compat.py` holds the Python 2/3 type aliases.
- `fsed/tests/`: two `unittest.TestCase` modules and compressed reference fixtures.
  Tests import their parent package with relative imports.
- `setup.py`, `setup.cfg`, `MANIFEST.in`, and `fsed/VERSION` define packaging.
  `MANIFEST.in` includes the test corpus in source distributions.

## Commands

Run from the fork root. The following environment was checked on Python 3.11.9.
The old Python 2.7-3.8 Travis matrix was not rerun.

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install pip==24.3.1 setuptools==75.3.0 wheel==0.45.1 build==1.2.2.post1 click==8.1.8
.venv/bin/python -m pip install --no-build-isolation -e .
.venv/bin/python -m unittest discover -s fsed/tests -t . -v
.venv/bin/python -m unittest fsed.tests.test_fsed.TestFsed.test_end2end -v
.venv/bin/python -m build --no-isolation
.venv/bin/python -m fsed.fsed --help
```

The full suite has 16 tests at the baseline. Build produces an sdist and wheel in
`dist/`. No linter or formatter is configured; `.venv/bin/python -m compileall -q fsed`
checks syntax only. Do not describe it as a lint pass.

## Conventions

- Extend the existing `unittest.TestCase` classes with `test_` methods and
  `self.assertEqual`/`self.assertRaises`. Keep relative imports in test modules.
- Preserve the existing Python 2/3 syntax, `__future__` imports, and four-space
  indentation. Do not introduce annotations or f-strings during an unrelated edit.
- Pattern and file streams contain bytes; decode using the selected encoding before
  passing text to the trie. `CMStringIO` test fixtures take bytes and rewind on entry.
- Word boundaries use an internal NUL token (`\x00`), not Python regex matching.
  Keep the transform/untransform pair and greedy/slow behavior distinct.

## Guardrails

- Use the explicit test command above. Omitting `-t .` breaks relative imports.
  `setup.py test` from the old Travis workflow fails with the pinned setuptools;
  the standard-library runner exercises the existing tests without Nose.
- The README says pattern format defaults to `sed`; the code defaults to `auto`.
  `main` also forces line-by-line processing even with `--across-lines`.
  Do not promise multiline matching without changing and testing that implementation.
- Do not hand-edit `build/`, `dist/`, `fsed.egg-info/`, `.venv/`, or `*.pyc`.
  Keep the `.gz` corpus and Perl/sed reference files in `fsed/tests/` unchanged
  unless fixture regeneration is the task. The commands in its README regenerate data.
- Keep `fsed/VERSION` at 0.5.4 for ordinary changes. There is no release task here.
