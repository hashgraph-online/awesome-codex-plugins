# Package Manager Detection & Command Translation

Reference for any skill that needs to emit a JavaScript/TypeScript package-manager command (`install`, `add`, `run <script>`, `exec <bin>`, `test`).

## When to Read This

Read this file when you are about to:

- Suggest installing dependencies in a JS/TS project (`npm install`, `pnpm install`, `yarn`, `bun install`)
- Run a script defined in `package.json` (`npm run build`, `pnpm build`, etc.)
- Invoke a binary (`npx`, `pnpm exec`, `yarn dlx`, `bunx`)
- Resolve lockfile conflicts in a JS/TS project
- Provide a command-line example in a skill, tutorial, or generated config

## Detection Algorithm

Apply in order. **First match wins**.

### Step 1 — Check `packageManager` field in `package.json`

If `package.json` has a `"packageManager"` field, that wins. This is the [Corepack](https://nodejs.org/api/corepack.html) standard and represents an explicit choice by the project owner.

```json
// package.json
{ "packageManager": "pnpm@9.0.0" }   // → pnpm
{ "packageManager": "yarn@4.2.0" }   // → yarn
{ "packageManager": "npm@10.5.0" }   // → npm
{ "packageManager": "bun@1.1.0" }    // → bun
```

Parse the value before the `@`. Ignore the version pin for command-selection purposes.

### Step 2 — Check lockfiles

If no `packageManager` field, check for lockfiles in the project root in this priority order:

| Lockfile | Package manager |
|---|---|
| `bun.lock` or `bun.lockb` | **bun** |
| `pnpm-lock.yaml` | **pnpm** |
| `yarn.lock` | **yarn** |
| `package-lock.json` | **npm** |

### Step 3 — Multiple lockfiles present (collision)

If more than one lockfile exists, this is a project-hygiene smell. Pick using the priority order above (bun > pnpm > yarn > npm) and **warn the user**:

> "Multiple lockfiles detected: `<files>`. Using **<chosen-pm>** based on priority. Consider removing the unused lockfiles to avoid confusion."

### Step 4 — No detection signal

If neither `packageManager` field nor any lockfile is present, **stop and ask the user**. Do not guess.

Suggested prompt:

> "I couldn't detect a package manager (no lockfile, no `packageManager` field in `package.json`). Which would you like to use?
> 1. npm
> 2. pnpm
> 3. yarn
> 4. bun
>
> Reply with the number or name."

## Command Translation Table

Use this table to translate from a generic intent to the detected PM's syntax. The reference column shows the npm form for clarity — emit the column matching the detected PM.

| Intent | npm | pnpm | yarn | bun |
|---|---|---|---|---|
| Install all deps | `npm install` | `pnpm install` | `yarn` | `bun install` |
| Install one dep | `npm install <pkg>` | `pnpm add <pkg>` | `yarn add <pkg>` | `bun add <pkg>` |
| Install dev dep | `npm install -D <pkg>` | `pnpm add -D <pkg>` | `yarn add -D <pkg>` | `bun add -d <pkg>` |
| Remove dep | `npm uninstall <pkg>` | `pnpm remove <pkg>` | `yarn remove <pkg>` | `bun remove <pkg>` |
| Run package.json script | `npm run <script>` | `pnpm <script>` | `yarn <script>` | `bun run <script>` |
| Run a binary | `npx <bin>` | `pnpm exec <bin>` | `yarn <bin>` | `bunx <bin>` |
| Test (script) | `npm test` | `pnpm test` | `yarn test` | `bun run test` |
| Update deps | `npm update` | `pnpm update` | `yarn upgrade` | `bun update` |
| Audit | `npm audit` | `pnpm audit` | `yarn audit` | `bun pm ls` (limited) |

**Notes:**

- `pnpm <script>` works for any script not colliding with a built-in pnpm command. When in doubt, use `pnpm run <script>`.
- For `bun test`: prefer `bun run test` if the project defines a `test` script in `package.json`. Plain `bun test` invokes Bun's native test runner, which is different.
- `yarn <bin>` only works for project-installed binaries (analogous to running via `node_modules/.bin`). For ad-hoc fetches use `yarn dlx <bin>`.

## Lockfile Conflict Resolution

When merging branches with a lockfile conflict, regenerate rather than hand-merge:

| Detected PM | Resolution commands |
|---|---|
| npm | `git checkout --ours package-lock.json && npm install` (try `--theirs` if ERESOLVE) |
| pnpm | `git checkout --ours pnpm-lock.yaml && pnpm install` |
| yarn | `git checkout --ours yarn.lock && yarn install` |
| bun | `git checkout --ours bun.lock && bun install` (or `bun.lockb`) |

If `--ours` fails with a dependency resolution error, retry with `--theirs`. Verify with the project's test command after.

## Output Convention for Skills

When a skill emits a command after running detection, use this form:

> "Detected **pnpm** (via `pnpm-lock.yaml`). Running: `pnpm build`."

Always state the detected PM and the signal, then the command. This makes mis-detection visible to the user.

## Recording the Result Durably

In-context memory is wiped by `/compact`, subagent dispatch, and `/clear`. A skill that detects the PM at pre-step and re-derives it from memory during verification will be wrong on long sessions. Persist the result in the active plan's WORKFLOW STATE block:

```
Package Manager: pnpm (via pnpm-lock.yaml)
```

Downstream phases (and any subagent dispatched mid-task) read `<PM>` from this line, not from recall. If the plan file does not exist yet, the calling skill carries the value forward and writes it as the first WORKFLOW STATE field the moment Phase 1 creates the plan.
