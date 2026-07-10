# Issue Templates for Discovery Findings

Templates used by the discovery skill when creating VCS issues from probe findings.
References the label taxonomy from the gitlab-ops skill.

---

## Labels

Discovery findings use the following labels from the gitlab-ops label taxonomy:

- **Type:** `type:discovery`
- **Priority:** `priority:critical` | `priority:high` | `priority:medium` | `priority:low` (mapped from probe severity)
- **Area:** `area:frontend` | `area:backend` | `area:security` | `area:testing` | `area:ci` | `area:infrastructure` (mapped from probe category)
- **Status:** `status:ready`

### Category-to-Area Mapping

| Probe Category | Default Area Label |
|---|---|
| `code` | `area:backend` (or `area:frontend` if file is in UI paths) |
| `infra` | `area:infrastructure` (or `area:ci` for pipeline probes) |
| `ui` | `area:frontend` |
| `arch` | `area:backend` |
| `session` | (no area label -- session-scoped) |

### Severity-to-Priority Mapping

| Probe Severity | Priority Label |
|---|---|
| Critical | `priority:critical` |
| High | `priority:high` |
| Medium | `priority:medium` |
| Low | `priority:low` |

---

## Template 1: Discovery Finding (Individual)

Used for a single finding from a single probe.

```
## [Discovery] <finding_title>

**Probe:** `<probe_name>` (`<category>`)
**Severity:** <priority_level>
**Detected:** <date>

### Finding

<description of what was detected and why it matters>

### Evidence

- **File:** `<file_path>`
- **Line:** <line_number>
- **Code:**
```<lang>
<matched_text with surrounding context>
```

### Impact

<concrete explanation of the risk or technical debt this introduces>

### Recommended Fix

<specific, actionable fix suggestion with code example if applicable>

### Acceptance Criteria

- [ ] <verifiable condition that confirms the fix>
- [ ] No new instances of this pattern introduced
- [ ] Quality gates pass after fix
```

**Labels:** `type:discovery`, `priority:<level>`, `area:<area>`, `status:ready`

**CLI Example:**
```bash
# GitHub
gh issue create \
  --title "[Discovery] <finding_title>" \
  --label "type:discovery,priority:<level>,area:<area>,status:ready" \
  --body "$(cat <<'EOF'
<template body filled in>
EOF
)"

# GitLab
glab issue create \
  --title "[Discovery] <finding_title>" \
  --label "type:discovery,priority:<level>,area:<area>,status:ready" \
  --description "$(cat <<'EOF'
<template body filled in>
EOF
)"
```

---

## Template 2: Batch Discovery Report

Used when multiple related findings from the same probe or category are grouped into a single issue.

```
## [Discovery] <category> audit: <summary>

**Probes:** <comma-separated probe names>
**Findings:** <total_count> (<critical_count> critical, <high_count> high, <medium_count> medium, <low_count> low)
**Detected:** <date>

### Summary

<overview of what was found and the overall health assessment for this category>

### Findings

#### Critical

| # | File | Line | Description |
|---|---|---|---|
| 1 | `<path>` | <n> | <brief description> |

#### High

| # | File | Line | Description |
|---|---|---|---|
| 1 | `<path>` | <n> | <brief description> |

#### Medium

| # | File | Line | Description |
|---|---|---|---|
| 1 | `<path>` | <n> | <brief description> |

#### Low

| # | File | Line | Description |
|---|---|---|---|
| 1 | `<path>` | <n> | <brief description> |

### Recommended Actions

1. **Immediate** (critical/high): <action items>
2. **Next Sprint** (medium): <action items>
3. **Backlog** (low): <action items>

### Acceptance Criteria

- [ ] All critical findings resolved
- [ ] All high findings resolved or have tracking issues
- [ ] No regressions introduced
- [ ] Quality gates pass after fixes
```

**Labels:** `type:discovery`, `priority:<highest_severity_found>`, `area:<area>`, `status:ready`

**CLI Example:**
```bash
# GitHub
gh issue create \
  --title "[Discovery] <category> audit: <summary>" \
  --label "type:discovery,priority:<level>,area:<area>,status:ready" \
  --body "$(cat <<'EOF'
<template body filled in>
EOF
)"

# GitLab
glab issue create \
  --title "[Discovery] <category> audit: <summary>" \
  --label "type:discovery,priority:<level>,area:<area>,status:ready" \
  --description "$(cat <<'EOF'
<template body filled in>
EOF
)"
```

---

## Template 3: Discovery Session Summary

Used as a comment or standalone issue to summarize a full discovery run across all categories.

```
## [Discovery] Session Summary — <date>

### Run Configuration

- **Categories scanned:** <list>
- **Probes executed:** <count>
- **Probes skipped:** <count> (activation conditions not met)
- **Total findings:** <count>

### Results by Category

| Category | Probes Run | Critical | High | Medium | Low | Total |
|---|---|---|---|---|---|---|
| code | <n> | <n> | <n> | <n> | <n> | <n> |
| infra | <n> | <n> | <n> | <n> | <n> | <n> |
| ui | <n> | <n> | <n> | <n> | <n> | <n> |
| arch | <n> | <n> | <n> | <n> | <n> | <n> |
| session | <n> | <n> | <n> | <n> | <n> | <n> |
| audit | <n> | <n> | <n> | <n> | <n> | <n> |
| vault | <n> | <n> | <n> | <n> | <n> | <n> |
| feature | <n> | <n> | <n> | <n> | <n> | <n> |
| **Total** | **<n>** | **<n>** | **<n>** | **<n>** | **<n>** | **<n>** |

### Issues Created

| Issue | Title | Severity | Category |
|---|---|---|---|
| #<n> | <title> | <severity> | <category> |

### Skipped Probes

| Probe | Reason |
|---|---|
| <probe_name> | <activation condition not met> |

### Health Score

**Overall: <score>/100**

Scoring: Start at 100, deduct per finding:
- Critical: -15 points each
- High: -8 points each
- Medium: -3 points each
- Low: -1 point each
- Minimum score: 0
```

**Notes:**
- This template is for reporting, not for issue creation (though it can be posted as an issue if the user requests it)
- The health score provides a quick at-a-glance metric for codebase quality
- Skipped probes are listed for transparency so users know what was not checked
