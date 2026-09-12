# Markdown Standards (Tier 1)

## Structure
- Single H1 (`#`) at top
- Hierarchical headings (don't skip levels)
- Blank line before/after headings

## Common Issues
| Pattern | Problem | Fix |
|---------|---------|-----|
| Multiple H1s | Confusing structure | Single H1 |
| Skipped heading | H1 → H3 | H1 → H2 → H3 |
| No blank lines | Rendering issues | Blank before/after blocks |
| Hard line breaks | Formatting | Let text wrap naturally |

## Tables
```markdown
| Header | Header |
|--------|--------|
| Cell   | Cell   |
```
- Align `|` for readability
- Use `-` for header separator

## Code Blocks
- Always specify language: ` ```python `
- Use inline `` `code` `` for short refs
- 4-space indent also works (but fenced preferred)

## Links
- Use descriptive link text, not generic "click here"
- Use relative paths for local references
- Check links aren't broken
