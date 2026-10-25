# Working on Traits

Traits is a Python library for typed attributes, validation, defaults, and change notifications. It combines Python classes with the compiled `traits.ctraits` extension. It is not a web app; GUI support belongs to optional TraitsUI/Pyface dependencies.

## Find the right layer

- Start at `traits/api.py` for public imports. Trace declarations through `has_traits.py` (`HasTraits`, metaclass), `trait_types.py` (validators), and `ctrait.py` into handwritten `ctraits.c` for accelerated behavior.
- For modern `observe` behavior, use `traits/observation/`: `parsing.py`, observer expressions/graphs, and event notifiers. Legacy `on_trait_change` uses `traits_listener.py` and `trait_notifiers.py`.
- Protocol conversion lives in `traits/adaptation/`. Test helpers live in `traits/testing/`. Tests span `traits/tests/`, subsystem `tests/` directories, and `traits/stubs_tests/`.
- Public API changes also need corresponding `.pyi` stubs and documentation under `docs/source/traits_api_reference/` and `docs/source/traits_user_manual/`.

## Set up and verify

Traits requires CPython 3.10+ and a C compiler. This checked setup uses `uv` and Python 3.11.9. Run commands from the repository root.

```sh
printf '\n/.venv/\n/.mypy_cache/\n' >> .git/info/exclude
uv venv --python 3.11.9 --seed .venv
.venv/bin/python -m pip install -e '.[test,docs]' build
.venv/bin/python -m unittest discover -s traits -t . -v
.venv/bin/python -m flake8
.venv/bin/python -m build
(cd docs && ../.venv/bin/python -m sphinx -b html -W source build)
```

The editable install builds the C extension. Repeat it after C changes. `.venv/` is absent from upstream Git ignores, so keep the local exclude. Flake8 needs the `flake8-ets` plugin from the test extra; plain Flake8 alone misses repository checks.

For a focused test, use the module name, for example `.venv/bin/python -m unittest traits.tests.test_integer -v`. The full discovery command includes observation, adaptation, and stub tests; `traits/tests/` alone does not. Upstream CI instead installs a distribution and discovers `traits` from an empty `testdir`.

Run a library smoke check:

```sh
.venv/bin/python -c 'from traits.api import HasTraits, Int; x = HasTraits(); x.add_trait("count", Int()); x.count = 2; assert x.count == 2; print(x.count)'
```

## Follow existing tests and protect generated files

Use `unittest.TestCase`, `test_*` methods, and `self.assert*` assertions. Reuse optional-dependency decorators from `traits/testing/optional_dependencies.py`. Modern observation tests that assert inside callbacks use `traits.observation.api.push_exception_handler(reraise_exceptions=True)` and register matching cleanup; the handler exported by `traits.api` belongs to the legacy stack.

Keep the existing Enthought license header and 79-column style. Black/isort configuration is in `pyproject.toml`; required style checks are in `setup.cfg`. Stub examples contain expected mypy errors, so run their unittest harness rather than treating those examples as error-free programs.

Do not hand-edit `traits/version.py`, compiled extensions, `build/`, `dist/`, or `docs/build/`. `setup.py` generates version metadata. `_generated_parser.py` embeds a generated parser and Lark runtime; edit `_dsl_grammar.lark` and follow its regeneration command instead. Preserve historical pickle fixtures under `traits/tests/test-data/`; they verify compatibility with older releases.
