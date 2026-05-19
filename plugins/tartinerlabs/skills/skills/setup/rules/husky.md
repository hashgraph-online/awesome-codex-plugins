# Husky

Git hooks manager for running scripts on git events.

## Install

```bash
pnx husky init
```

This creates a `.husky/` directory and a default `pre-commit` hook.

## Pre-commit Hook

The final `.husky/pre-commit` is assembled by other rules (GitLeaks, lint-staged). The expected order is:

```bash
gitleaks protect --staged --verbose
pnx lint-staged
```

Replace the default content created by `husky init` with the above.
