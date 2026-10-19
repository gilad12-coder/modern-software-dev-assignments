# Day.js

Immutable date library with a Moment.js-compatible API. The core bundle has a hard
2.99 KB gzip budget, so most features live in plugins and locales, not the core.

## Architecture

- `src/index.js`: the `Dayjs` class and the `dayjs()` factory. Instance state is in
  `$`-prefixed fields (`$d` native Date, `$y $M $D $W $H $m $s $ms`, `$L` locale,
  `$u` UTC flag, `$x` plugin extras). Unit names and regexes are in `src/constant.js`
  (`C.M`, `C.D`, ...). Shared helpers are in `src/utils.js`.
- `src/plugin/<name>/index.js`: one folder per plugin, each `export default (o, c, d) => {}`
  (option, `Dayjs` class, `dayjs` factory). Plugins patch `c.prototype` and often wrap the
  old method (`const oldX = proto.x; proto.x = function () { ... oldX.bind(this)(...) }`).
- `src/locale/<code>.js`: one file per locale. First line must be `// Name [code]`. It
  imports `dayjs` from `'dayjs'` (not `'../index'`), calls `dayjs.locale(locale, null, true)`,
  and exports `locale`. `name` must equal the lowercase file name. Exception: `en.js` is
  built into the core and must stay import-free.
- `types/`: hand-written `.d.ts` files. Every plugin needs `types/plugin/<name>.d.ts`.
- `test/`: Jest tests. `test/plugin/<name>.test.js`, `test/locale/<code>.test.js`.
- `build/`: Rollup scripts that emit UMD files to the repo root, and `esm/`.

## Commands

- Install: `npm ci` (do not use `npm install`: it rewrites `package-lock.json`).
- Lint: `npm run lint`. Single file: `npx eslint src/plugin/isToday/index.js`
- Full tests: `TZ=UTC npm test`. It runs the tz suites in several zones, then all of Jest
  with a 100% line coverage threshold. Without `TZ=UTC`, `npm test` fails 6 tests on a
  US-timezone machine (dayOfYear, localizedFormat, timezone). CI runs in UTC.
  It runs Jest 9 times, so `| tail` shows only the last run. Check the exit code instead:
  `TZ=UTC npm test > /tmp/dayjs-test.log 2>&1; echo $?`
- One test file: `TZ=UTC npx jest test/plugin/isToday.test.js --coverage=false`
- Build: `NODE_OPTIONS=--openssl-legacy-provider npm run build`. The `size` step crashes on
  Node 17+ with `ERR_OSSL_EVP_UNSUPPORTED` without that flag. ESM: `npm run babel`.

## Conventions

- ESLint airbnb-base with no semicolons and no trailing commas. Use `function () {}` (not
  arrows) for prototype methods, because they need `this`.
- Methods never mutate: return `this.clone()` or a new instance. `badMutable` is the one
  intended exception.
- Tests import from `../../src` and `../../src/plugin/<name>`, call `dayjs.extend(...)` at
  the top, and wrap time-dependent tests in `MockDate.set()` / `MockDate.reset()`. Many
  tests compare against `moment` output, e.g. `expect(d.format()).toBe(moment(...).format())`.
- Any new `src/` line needs a test, or the 100% coverage gate fails `npm test`.
- New plugin = `src/plugin/<name>/index.js` + `types/plugin/<name>.d.ts` + a test file.
  `test/plugin/declarations.test.js` fails if the `.d.ts` is missing.
- Commit messages use semantic-release prefixes: `fix:`, `feat:`, `fix(plugin): ...`.
  PRs target `dev`. `master` is release-only.

## Guardrails

- Do not edit build output: `dayjs.min.js`, `index.d.ts`, `locale/`, `plugin/`, `esm/`,
  `locale.json` (root level, gitignored). Edit `src/` and `types/` instead. Note that
  root `locale/` and `plugin/` are not `src/locale/` and `src/plugin/`.
- Do not edit `CHANGELOG.md`. semantic-release writes it.
- Keep core changes small. Check with `NODE_OPTIONS=--openssl-legacy-provider npm run size`.
- `docs/` holds translated READMEs only. API docs are on day.js.org, not in this repo.
- Do not run `npm run sauce` or `npm run test:sauce`: they need Sauce Labs credentials.
