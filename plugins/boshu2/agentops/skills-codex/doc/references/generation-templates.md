# Documentation Generation Templates

## CODING: Code-Map Template

**CRITICAL**: Load `code-map-standard` skill before generating.

```markdown
---
title: "[Feature Name]"
sources: [path/to/main.py]
last_updated: YYYY-MM-DD
---

# [Feature Name]

## Current Status

[One-liner with date]

## Overview

[2-3 sentences]

## State Machine

[ASCII diagram if applicable]

## Inputs/Outputs

| Type | Name | Description |
|------|------|-------------|

## Data Flow

[ASCII diagram]

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|

## Code Signposts

| Component | Location | Purpose |
|-----------|----------|---------|

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|

## Prometheus Metrics

| Metric | Type | Labels | PromQL Example |
|--------|------|--------|----------------|

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|

## Unit Tests

| Test File | Coverage |
|-----------|----------|

## Integration Tests

| Test | What It Validates |
|------|-------------------|

## Example Usage

### curl
### SDK

## Related Features

## Known Limitations

## Learnings

### What Worked
### What We'd Change
```

---

## INFORMATIONAL: Corpus Section Template

```markdown
---
title: "Document Title"
summary: "One-line summary for search"
tags: [tag1, tag2]
tokens: 1500
last_updated: YYYY-MM-DD
---

# Title

## Overview

[Introduction paragraph]

## Key Concepts

### Concept 1
### Concept 2

## Practical Application

## Related Topics

- `Link label — ../replace/with/real-doc.md`
- `Link label — ../replace/with/real-doc.md`

## References

- External sources
```

---

## OPS: Helm Chart Template

```markdown
# [Chart Name]

## Overview

[Description from Chart.yaml]

## Quick Start

```bash
helm install [release] ./charts/[name]
```

## Values Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|

## Dependencies

| Chart | Version | Condition |
|-------|---------|-----------|

## Common Overrides

### Development
### Staging
### Production

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
```

---

## Stub Template (--create mode)

For undocumented features:

```markdown
---
title: "[Feature Name]"
status: STUB
created: YYYY-MM-DD
sources: [detected source files]
---

# [Feature Name]

> AUTO-GENERATED STUB - Replace with actual content

## Current Status

[Discovered but not documented]

## Overview

[Brief description of this feature]

## Sources

- `path/to/source.py`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
```

---

## Section Markers

Use markers to control auto-generation behavior:

```markdown
<!-- HUMAN-MAINTAINED: Do not auto-generate -->
[This section is preserved during updates]

<!-- AUTO-GENERATED: Safe to replace -->
[This section is regenerated from source]
```

**Merge Strategy**:
1. HUMAN-MAINTAINED sections: Always preserve
2. AUTO-GENERATED sections: Replace with fresh data
3. Frontmatter: Merge (add missing, update tokens/dates)
