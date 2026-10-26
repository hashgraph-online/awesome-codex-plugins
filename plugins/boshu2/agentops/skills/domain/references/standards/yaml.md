# YAML Standards (Tier 1)

## Validation
- `yamllint` must pass; it never reads frontmatter inside Markdown, so check
  that by hand against the table below
- 2-space indentation
- No trailing whitespace

## Common Issues
| Pattern | Problem | Fix |
|---------|---------|-----|
| Tabs | Invalid YAML | 2 spaces |
| `yes`/`no` unquoted | Becomes boolean | Quote: `"yes"` |
| `:` in value | Parse error | Quote the value |
| Long lines | Readability | Use `>` or `\|` |
| ` #` in an unquoted value (`title: Fix issue #123`) | The rest of the line becomes a comment, with no error | Quote the value |
| Value or list item meant as plain text that starts with `*`, `&`, `!`, `%`, `@`, `[`, `{`, `>`, `\|` or a backtick | Parse error, or a silently changed value (`&` and `!` start an anchor or tag) | Quote it (an intended flow list or map, or a `\|`/`>` block scalar, stays unquoted) |

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
