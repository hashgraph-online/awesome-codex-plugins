# commitlint

Conventional commit message enforcement via git hooks.

## Install

```bash
<pm> add -D @commitlint/cli @commitlint/config-conventional
```

## Config Detection

Treat commitlint as already configured when any of these exist:

- `commitlint.config.ts`
- `commitlint.config.cts`
- `commitlint.config.mts`
- `commitlint.config.js`
- `commitlint.config.cjs`
- `commitlint.config.mjs`
- `.commitlintrc.ts`
- `.commitlintrc.cts`
- `.commitlintrc.mts`
- `.commitlintrc.js`
- `.commitlintrc.cjs`
- `.commitlintrc.mjs`
- `.commitlintrc.json`
- `.commitlintrc.yaml`
- `.commitlintrc.yml`
- `.commitlintrc`
- `commitlint` key in `package.json` or `package.yaml`

## Config Creation

Create `commitlint.config.ts`:

```ts
import type { UserConfig } from "@commitlint/types";

const config: UserConfig = { extends: ["@commitlint/config-conventional"] };

export default config;
```

## Hook

Create `.husky/commit-msg`:

```bash
pnx --no -- commitlint --edit $1
```
