# Shell Standards (Tier 1)

## Required Header
```bash
#!/usr/bin/env bash
set -euo pipefail
```

## Validation
- `shellcheck` must pass
- Quote all variables: `"$var"` not `$var`

## Common Issues
| Pattern | Problem | Fix |
|---------|---------|-----|
| Unquoted `$var` | Word splitting | `"$var"` |
| `cd` without check | Silent failure | `cd dir \|\| exit 1` |
| `[ ]` vs `[[ ]]` | Portability | Use `[[ ]]` in bash |
| Backticks | Nesting issues | Use `$(command)` |

## Best Practices
- Use `local` for function variables
- Clean up once on every exit: `trap cleanup EXIT` (adding `ERR` runs it twice on failure)
- Check command existence: `command -v foo >/dev/null`
- Use `readonly` for constants

## Cluster Scripts
- Always verify connectivity first:
  ```bash
  oc whoami &>/dev/null || { echo "Not logged in"; exit 1; }
  ```
