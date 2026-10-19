# Week 4 Write-up

**Repo chosen** and link to your fork:
> [iamkun/dayjs](https://github.com/iamkun/dayjs), a small immutable date library with a Moment.js-style API.
> Fork: https://github.com/gilad12-coder/dayjs. The file is on branch
> [`agent-config`](https://github.com/gilad12-coder/dayjs/tree/agent-config)
> ([CLAUDE.md](https://github.com/gilad12-coder/dayjs/blob/agent-config/CLAUDE.md), PR inside the fork:
> https://github.com/gilad12-coder/dayjs/pull/1). Explored at upstream commit `436bde0` on `dev`.

**File you wrote** (`AGENTS.md` or `CLAUDE.md`):
> `CLAUDE.md` (copy in [`week4/CLAUDE.md`](CLAUDE.md)). I chose `CLAUDE.md` because I tested it with
> Claude Code, which loads `CLAUDE.md` on its own.


## Part I: Exploration

All commands below were run on macOS, Node 22.22.0, npm, machine timezone America/Los_Angeles.

| | Finding |
|---|---|
| Build / run | `npm ci` installs (9 s). `npm install` rewrites `package-lock.json` (+871/-447 lines), so `npm ci` is the right command. `npm run build` runs `build/index.js` (Rollup + terser, UMD output to the repo root) and then `npm run size`. On Node 22 the `size` step crashes with `ERR_OSSL_EVP_UNSUPPORTED`; `NODE_OPTIONS=--openssl-legacy-provider npm run build` works (2.79 KB of the 2.99 KB limit). The release workflow sets the same flag. `npm run babel` builds `esm/`. There is nothing to "run": it is a library. |
| Test | `npm test` runs Jest 9 times: `test/timezone.test.js` in 4 zones, `test/plugin/timezone.test.js` in 4 zones, then the full suite with a 100% **line** coverage threshold. The last run uses the machine's own timezone. In America/Los_Angeles it fails 6 tests (`dayOfYear`, `localizedFormat`, `timezone` plugin). `TZ=UTC npm test` passes: 93 suites, 794 tests. CI runs on ubuntu (UTC), so CI does not see this. One file: `TZ=UTC npx jest test/plugin/isToday.test.js --coverage=false`. |
| Lint / format | `npm run lint` = `eslint src/* test/* build/*` (ESLint 4, airbnb-base, no semicolons, no trailing commas). One file: `npx eslint <path>`. `npm run prettier` only formats `docs/**/*.md`, not code. A `pre-commit` hook runs lint. |
| Key directories and entry points | `src/index.js` (the `Dayjs` class and `dayjs()` factory, state in `$d $y $M $D ... $L $u $x` fields), `src/constant.js`, `src/utils.js`; `src/plugin/<name>/index.js` (37 plugins); `src/locale/<code>.js` (143 locales); `types/` (hand-written `.d.ts`); `test/` mirrors `src/`; `build/` (Rollup scripts). |
| Unstated conventions | Plugin signature `export default (o, c, d) => {}` (option, class, factory); plugins patch `c.prototype` and wrap the old method. Prototype methods use `function () {}` because they need `this`. Methods return clones (immutability); `badMutable` is the one exception. Locales import from `'dayjs'`, not a relative path; `test/__mocks__/dayjs.js` maps that to `src/` in Jest. A locale's first line must be `// Name [code]` and `name` must match the file name (`test/locale/keys.test.js` checks this). Every plugin needs `types/plugin/<name>.d.ts` (`test/plugin/declarations.test.js` checks this). Tests use `MockDate` and compare with `moment` output. Semantic commit prefixes; PRs go to `dev`, `master` is release-only. |
| Off-limits (generated, vendored) | Build output at the root, all gitignored: `dayjs.min.js`, `index.d.ts`, `locale/`, `plugin/`, `esm/`, `locale.json`. Root `plugin/` and `locale/` look like source but are built copies of `src/plugin/` and `src/locale/`. `CHANGELOG.md` is written by semantic-release. `patches/` is a patch-package fix for the release tool. `npm run sauce` needs Sauce Labs credentials. |

**How you figured it out**: what you asked the agent, what you had to read yourself:
> I used a coding agent. I asked it to read `package.json`, the CI workflows (`.github/workflows/*.yml`),
> `.gitignore`, `.npmignore`, `.eslintrc.json`, `babel.config.js`, `build/*.js`, `CONTRIBUTING.md`, and a
> few sample plugins, locales and tests, and then to run every command for real. The two most useful facts
> did not come from any file. They came from running commands: `npm test` fails in a US timezone, and
> `npm run size` crashes on Node 22. `npm install` changing the lockfile was also found by running it.
> I checked the conventions by hand with greps (for example, every locale except `en.js` imports `'dayjs'`
> and calls `dayjs.locale(locale, null, true)`), and the `__mocks__` trick by reading `test/__mocks__/dayjs.js`.


## Part II: The File

**Anything you deliberately left out**, and why:
> - The public API (`format`, `add`, `diff`, ...) and plugin usage examples. They are in the README and on
>   day.js.org, and a model already knows Day.js well.
> - The list of 37 plugins and 143 locales. `ls src/plugin` gives it, and it would cost context in every session.
> - Generic advice ("write tests", "keep functions small"). The quality bar says this is padding.
> - The Sauce Labs / Karma browser setup and the release process. An agent should not run them, so one
>   guardrail line is enough.
> - Contribution etiquette from `CONTRIBUTING.md` (issue search, "English please"). It is for humans filing issues.

**The hardest call** on what to include:
> The `$`-prefixed instance fields (`$d`, `$y`, `$L`, `$u`, `$x`). They look like internal detail that an
> agent can find by reading `src/index.js`, which argues for leaving them out. But 14 of the 37 plugins
> reads or writes them, and without them an agent will call public getters inside plugins or invent new
> fields. I kept them as one line. I also decided to say "`TZ=UTC npm test`" and explain why, instead
> of just "`npm test`". The explanation costs two lines, but without it an agent on a US machine sees 6
> failures and starts to "fix" correct code.


## Part III: Trying It Out

I ran each task in a fresh, headless Claude Code session (`claude -p --setting-sources project
--model sonnet`) from the fork root, with the file in place and no hint about it in the prompt. My
personal global instruction file was also loaded (I could not turn it off without losing login), so the
sessions had some extra context that is not part of this file.

| # | Task | Did the agent use your commands and conventions? |
|---|---|---|
| 1 | "Run this repo's test suite and tell me whether it passes. Do not change any files." | Yes. Its first and only command was `TZ=UTC npm test 2>&1 \| tail -60`, taken from the file. It reported 93/93 suites and 794/794 tests, and correctly said only line coverage is gated. But because of `tail -60` it saw only the last of the 9 Jest runs, and it said itself that it could not confirm the earlier per-timezone runs. |
| 2 | "Add a small new plugin, isWeekend, that adds an .isWeekend() method returning true on Saturday or Sunday. Make it ready for a PR: lint and tests must pass. Do not commit or push." | Yes, in 3 tool calls. It read `isToday` as a template, then created exactly the three files the file lists: `src/plugin/isWeekend/index.js` (`(o, c) =>` signature, `function ()` on `c.prototype`), `types/plugin/isWeekend.d.ts`, and `test/plugin/isWeekend.test.js` (imports from `../../src`, `dayjs.extend` at the top). It ran the single-file lint command form (`npx eslint <files>`) and then `TZ=UTC npm test`: 94 suites, 796 tests, coverage gate met. It did not touch the root `plugin/` build folder, which existed from my earlier build. It skipped the size check and said why: the change is a plugin, not core, which matches the guardrail. It did not use `MockDate`, which was right, because the test uses fixed dates. I checked `npm run lint` afterwards: it passed. I deleted the change after the trial. |

**One thing you'd change** about the file after watching it get used:
> In task 1 the agent piped `npm test` through `tail`, so it could only judge the last of the 9 Jest runs.
> The script chains the runs with `&&`, so a failure in an early per-timezone run stops it, and the tail
> then shows partial output that is easy to misread. I added two lines to the file: `npm test` runs Jest
> 9 times, so check the exit code, with the exact command `TZ=UTC npm test > /tmp/dayjs-test.log 2>&1; echo $?`.
> I ran task 1 again with the new file. The agent used that exact command, reported "exited with code 0",
> and based its answer on the exit code. This change is the second commit on the fork branch.
