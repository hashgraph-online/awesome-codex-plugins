# Markdown Standards Catalog - Vibe Canonical Reference

**Version:** 1.0.0
**Last Updated:** 2026-01-21
**Purpose:** Canonical Markdown standards for vibe skill validation

---

## Table of Contents

1. [AI-Agent Optimization](#ai-agent-optimization)
2. [Document Structure](#document-structure)
3. [Heading Conventions](#heading-conventions)
4. [Code Blocks](#code-blocks)
5. [Tables](#tables)
6. [Links](#links)
7. [Lists](#lists)
8. [Emphasis and Blockquotes](#emphasis-and-blockquotes)
9. [Validation](#validation)
10. [Compliance Assessment](#compliance-assessment)

---

## AI-Agent Optimization

### Principles

| Principle | Implementation | Why |
|-----------|----------------|-----|
| **Tables over prose** | Use tables for comparisons | Parallel parsing, scannable |
| **Explicit rules** | ALWAYS/NEVER, not "try to" | Removes ambiguity |
| **Decision trees** | If/then logic in lists | Executable reasoning |
| **Named patterns** | Anti-patterns with names | Recognizable error states |
| **Progressive disclosure** | Quick ref → details JIT | Context window efficiency |
| **Copy-paste ready** | Complete examples | Reduces inference errors |

---

## Document Structure

### SKILL.md Template

```markdown
# Skill Name

> **Triggers:** "phrase 1", "phrase 2", "phrase 3"

## Quick Reference

| Action | Command | Notes |
|--------|---------|-------|
| ... | ... | ... |

## When to Use

| Scenario | Action |
|----------|--------|
| Condition A | Do X |
| Condition B | Do Y |

## Workflow

1. Step one
2. Step two
3. Step three

## Common Errors

| Symptom | Cause | Fix |
|---------|-------|-----|
| Error message | Root cause | Solution |

## References

- [Reference 1](./references/detail1.md) - Load when needed
- [Reference 2](./references/detail2.md) - Load when needed
```

### Reference Doc Template

```markdown
# Reference: Topic Name

<!-- Load JIT when skill needs deep context -->

## Context

Brief overview of when this reference applies.

## Details

### Section 1

...

## Decision Tree

```text
Is X true?
├─ Yes → Do A
│   └─ Did A fail? → Try B
└─ No → Do C
```

## Anti-Patterns

| Name | Pattern | Why Bad | Instead |
|------|---------|---------|---------|
| ... | ... | ... | ... |
```

---

## Heading Conventions

### Hierarchy Rules

| Level | Use For | Example |
|-------|---------|---------|
| `#` | Document title (one per file) | `# Style Guide` |
| `##` | Major sections | `## Installation` |
| `###` | Subsections | `### macOS Setup` |
| `####` | Minor divisions (sparingly) | `#### Homebrew` |

**NEVER:**
- Skip heading levels (`#` → `###`)
- Use bold text as fake headings
- Start with `##` (missing `#` title)

### Heading Text

```markdown
# Good - Title Case for Title
## Good - Sentence case for sections
### Good - Sentence case continues

# Bad - all lowercase title
## Bad - ALL CAPS SECTION
### Bad - Using: Colons: Everywhere
```

---

## Code Blocks

### Language Hints (Required)

ALWAYS specify language for syntax highlighting:

````markdown
```python
def hello():
    print("world")
```
````

### Common Language Hints

| Language | Fence | Use For |
|----------|-------|---------|
| `bash` | ` ```bash ` | Shell commands |
| `python` | ` ```python ` | Python code |
| `go` | ` ```go ` | Go code |
| `typescript` | ` ```typescript ` | TypeScript |
| `yaml` | ` ```yaml ` | YAML config |
| `json` | ` ```json ` | JSON data |
| `text` | ` ```text ` | Plain text, diagrams |
| `diff` | ` ```diff ` | Code diffs |

### Command Output

```markdown
```bash
$ kubectl get pods
NAME         READY   STATUS    RESTARTS   AGE
my-pod       1/1     Running   0          5m
```
```

---

## Tables

### When to Use

| Situation | Use Table? | Alternative |
|-----------|------------|-------------|
| Comparing 3+ items | Yes | - |
| Key-value mappings | Yes | - |
| Command reference | Yes | - |
| Step-by-step | No | Numbered list |
| Narrative | No | Paragraphs |
| Two items only | No | Inline comparison |

### Table Formatting

```markdown
# Good - Aligned, readable
| Column A | Column B | Column C |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |

# Bad - Misaligned
|Column A|Column B|Column C|
|-|-|-|
|Value 1|Value 2|Value 3|
```

### Table Cell Content

| Content Type | Formatting |
|--------------|------------|
| Code/commands | Backticks: `` `cmd` `` |
| Emphasis | Bold: `**required**` |
| Links | Inline: `[text](url)` |
| Long text | Under 50 chars |

---

## Links

### Internal Links

```markdown
# Good - Relative paths
[Guide](./other-doc.md)

# Good - Anchor links
[Code Blocks](#code-blocks)

# Bad - Absolute paths
[Guide](/Users/me/project/docs/guide.md)
```

### Reference Links

For repeated URLs:

```markdown
See the [official docs][k8s-docs] for more info.
The [Kubernetes documentation][k8s-docs] covers this.

[k8s-docs]: https://kubernetes.io/docs/
```

---

## Lists

### Unordered Lists

Use `-` consistently:

```markdown
# Good
- Item one
- Item two
  - Nested item

# Bad - Mixed markers
* Item one
+ Item two
- Item three
```

### Ordered Lists

Use `1.` for all items:

```markdown
# Good - All 1s
1. First step
1. Second step
1. Third step

# Acceptable - Explicit numbering
1. First step
2. Second step
3. Third step
```

### Task Lists

```markdown
- [ ] Incomplete task
- [x] Completed task
- [ ] Another incomplete
```

---

## Emphasis and Blockquotes

### Emphasis

| Purpose | Syntax | Example |
|---------|--------|---------|
| Important terms | `**bold**` | **required** |
| File names, commands | `` `backticks` `` | `config.yaml` |
| Titles, emphasis | `*italic*` | *optional* |
| Keyboard keys | `<kbd>` | <kbd>Ctrl</kbd>+<kbd>C</kbd> |

**NEVER use bold for:**
- Entire paragraphs
- Headings (use `#`)
- Code (use backticks)

### Callout Patterns

```markdown
> **Note:** Supplementary information.

> **Warning:** Something that could cause issues.

> **Important:** Critical information.

> **Tip:** Helpful suggestion.
```

---

## Validation

### markdownlint Configuration

```yaml
# .markdownlint.yml
default: true

MD013:
  line_length: 100
  code_blocks: false
  tables: false

MD033:
  allowed_elements:
    - kbd
    - br
    - details
    - summary

MD034: false

MD004:
  style: dash

MD003:
  style: atx
```

### Validation Commands

```bash
# Lint Markdown files
npx markdownlint '**/*.md' --ignore node_modules

# Check links
npx markdown-link-check README.md

# Format with Prettier
npx prettier --write '**/*.md'
```

---

## Compliance Assessment

**Use letter grades + evidence, NOT numeric scores.**

### Assessment Categories

| Category | Evidence Required |
|----------|------------------|
| **Structure** | Heading hierarchy, single H1 |
| **Formatting** | markdownlint violations, code fence hints |
| **Links** | Broken link count, relative paths |
| **AI Optimization** | Table usage, explicit rules |
| **Accessibility** | Alt text, semantic markup |

### Grading Scale

| Grade | Criteria |
|-------|----------|
| A+ | 0 errors, single H1, 100% code hints, 0 broken links |
| A | <5 warnings, good structure |
| A- | <15 warnings, mostly correct |
| B | <30 warnings |
| C | Significant issues |

### Validation Commands

```bash
# Lint Markdown
npx markdownlint '**/*.md' --ignore node_modules

# Check heading hierarchy
grep -r "^# " docs/*.md | wc -l
ls docs/*.md | wc -l
# Should match (1 H1 per file)

# Code blocks without language
grep -rP '```\s*$' docs/ | wc -l
# Should be 0

# Check links
npx markdown-link-check docs/**/*.md
```

### Example Assessment

```markdown
## Markdown Standards Compliance

| Category | Grade | Evidence |
|----------|-------|----------|
| Structure | A+ | 47/47 single H1, 0 skipped |
| Formatting | A- | 18 warnings (MD013) |
| Links | A | 0 broken, 93% relative |
| AI Optimization | A | 85 tables, 23 decision trees |
| **OVERALL** | **A** | **18 MEDIUM findings** |
```

---

## Additional Resources

- [CommonMark Spec](https://spec.commonmark.org/)
- [markdownlint Rules](https://github.com/DavidAnson/markdownlint)
- [GitHub Flavored Markdown](https://github.github.com/gfm/)

---

**Related:** Quick reference in Tier 1 `markdown.md`
