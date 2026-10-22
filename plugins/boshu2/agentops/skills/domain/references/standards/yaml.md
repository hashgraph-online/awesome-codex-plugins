# YAML Standards (Tier 1)

## Validation
- `yamllint` must pass
- 2-space indentation
- No trailing whitespace

## Common Issues
| Pattern | Problem | Fix |
|---------|---------|-----|
| Tabs | Invalid YAML | 2 spaces |
| `yes`/`no` unquoted | Becomes boolean | Quote: `"yes"` |
| `:` in value | Parse error | Quote the value |
| Long lines | Readability | Use `>` or `\|` |

## Kubernetes/Helm
- Use `---` between documents
- Labels: `app.kubernetes.io/*`
- Always specify `resources.limits`
- Use ConfigMaps for config, Secrets for secrets

## Security
- Never use `yaml.load()` (Python) — always `yaml.safe_load()`
- Quote values that look like booleans (`"yes"`, `"no"`, `"true"`)
- Validate against schema before processing untrusted YAML
- Avoid anchors/aliases (`*`/`&`) in user-facing configs — confusing and exploitable

## Multiline Strings
```yaml
# Literal (preserves newlines)
description: |
  Line 1
  Line 2

# Folded (joins lines)
description: >
  This becomes
  one line
```
