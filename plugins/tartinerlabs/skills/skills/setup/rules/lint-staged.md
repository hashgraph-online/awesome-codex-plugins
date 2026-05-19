# lint-staged

Run linters on staged files before committing.

## Install

```bash
<pm> add -D lint-staged
```

## Config

Add to `package.json`:

```json
{
  "lint-staged": {
    "*": ["biome check --write --no-errors-on-unmatched"]
  }
}
```

## Hook

Add to `.husky/pre-commit` (after GitLeaks, before any other commands):

```bash
pnx lint-staged
```
