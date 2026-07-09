# YAML/Helm Standards Catalog - Vibe Canonical Reference

**Version:** 1.0.0
**Last Updated:** 2026-01-21
**Purpose:** Canonical YAML/Helm standards for vibe skill validation

---

## Table of Contents

1. [yamllint Configuration](#yamllint-configuration)
2. [Formatting Rules](#formatting-rules)
3. [Helm Chart Conventions](#helm-chart-conventions)
4. [Kustomize Patterns](#kustomize-patterns)
5. [Template Best Practices](#template-best-practices)
6. [Validation Workflow](#validation-workflow)
7. [Compliance Assessment](#compliance-assessment)
8. [Anti-Patterns Avoided](#anti-patterns-avoided)
9. [Code Quality Metrics](#code-quality-metrics)
10. [Prescan Patterns](#prescan-patterns)

---

## yamllint Configuration

### Full Configuration

```yaml
# .yamllint.yml
extends: default
rules:
  line-length:
    max: 120
    allow-non-breakable-inline-mappings: true
  indentation:
    spaces: 2
    indent-sequences: consistent
  truthy:
    check-keys: false
  comments:
    min-spaces-from-content: 1
  document-start: disable
  empty-lines:
    max: 2
  brackets:
    min-spaces-inside: 0
    max-spaces-inside: 0
  colons:
    max-spaces-before: 0
    max-spaces-after: 1
  commas:
    max-spaces-before: 0
    min-spaces-after: 1
  hyphens:
    max-spaces-after: 1
```

### Usage

```bash
# Lint all YAML files
yamllint .

# Lint specific directory
yamllint apps/

# Lint with format output
yamllint -f parsable .
```

---

## Formatting Rules

### Quoting Strings

```yaml
# Quote strings that look like other types
enabled: "true"      # String, not boolean
port: "8080"         # String, not integer
version: "1.0"       # String, not float

# No quotes for actual typed values
enabled: true        # Boolean
port: 8080           # Integer
replicas: 3          # Integer
```

### Multi-line Strings

```yaml
# Literal block scalar (preserves newlines)
script: |
  #!/bin/bash
  set -euo pipefail
  echo "Hello"

# Folded block scalar (folds newlines to spaces)
description: >
  This is a long description that will be
  folded into a single line with spaces.

# BAD - Escaped newlines (hard to read)
script: "#!/bin/bash\nset -euo pipefail\necho \"Hello\""
```

### Comments

```yaml
# Section header (full line)
# =============================================================================
# Database Configuration
# =============================================================================

database:
  host: localhost      # Inline comment (1 space before #)
  port: 5432
  # Subsection comment
  credentials:
    username: admin
```

---

## Helm Chart Conventions

### Chart Structure

```text
charts/<chart-name>/
├── Chart.yaml
├── values.yaml
├── values.schema.json    # Optional: JSON Schema for values
├── templates/
│   ├── _helpers.tpl
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ...
└── charts/               # Nested charts (if needed)
```

### Chart.yaml

```yaml
apiVersion: v2
name: my-app
description: A Helm chart for my application
type: application
version: 1.0.0
appVersion: "2.0.0"

dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: postgresql.enabled
```

### values.yaml Conventions

```yaml
# =============================================================================
# Application Configuration
# =============================================================================

app:
  name: my-app
  replicas: 3

# Resource limits (adjust for environment)
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

# =============================================================================
# Image Configuration
# =============================================================================

image:
  repository: myregistry/my-app
  tag: ""  # Defaults to appVersion
  pullPolicy: IfNotPresent
```

### Validation Commands

```bash
# Lint chart
helm lint charts/<chart-name>/

# Template with values (dry-run)
helm template <release> charts/<chart-name>/ -f values.yaml

# Validate rendered output
helm template <release> charts/<chart-name>/ | kubectl apply --dry-run=client -f -

# Debug template rendering
helm template <release> charts/<chart-name>/ --debug
```

---

## Kustomize Patterns

### Overlay Structure

```text
apps/<app>/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── overlays/
    ├── dev/
    │   └── kustomization.yaml
    ├── staging/
    │   └── kustomization.yaml
    └── prod/
        └── kustomization.yaml
```

### kustomization.yaml Template

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml

# Environment-specific patches
patches:
  - path: ./patches/replicas.yaml
    target:
      kind: Deployment
      name: my-app
```

### Patch Types

**Strategic Merge Patch:**
```yaml
# patches/extend-rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: my-role
rules:
  - apiGroups: ["custom.io"]
    resources: ["widgets"]
    verbs: ["get", "list"]
```

**JSON Patch:**
```yaml
# patches/add-annotation.yaml
- op: add
  path: /metadata/annotations/custom.io~1managed
  value: "true"
```

**Delete Patch:**
```yaml
# patches/delete-resource.yaml
$patch: delete
apiVersion: v1
kind: ConfigMap
metadata:
  name: unused-config
```

---

## Template Best Practices

### Use include for Reusable Snippets

```yaml
# templates/_helpers.tpl
{{- define "app.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}

# templates/deployment.yaml
metadata:
  labels:
    {{- include "app.labels" . | nindent 4 }}
```

### Whitespace Control

```yaml
# GOOD - Use {{- and -}} to control whitespace
{{- if .Values.enabled }}
apiVersion: v1
kind: ConfigMap
{{- end }}

# BAD - Extra blank lines in output
{{ if .Values.enabled }}

apiVersion: v1

{{ end }}
```

### Required Values

```yaml
# Fail fast if required value missing
image: {{ required "image.repository is required" .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}
```

### Default Values

```yaml
# Safe defaults
replicas: {{ .Values.replicas | default 1 }}

# Nested defaults
resources:
  {{- with .Values.resources }}
  {{- toYaml . | nindent 2 }}
  {{- else }}
  requests:
    cpu: 100m
    memory: 128Mi
  {{- end }}
```

---

## Validation Workflow

### Pre-commit Checks

```bash
# 1. Lint YAML
yamllint .

# 2. Lint Helm charts
for chart in charts/*/Chart.yaml; do
    helm lint "$(dirname "$chart")"
done

# 3. Build Kustomize overlays
kustomize build apps/<app>/ --enable-helm > /dev/null
```

### CI Pipeline Example

```yaml
# .github/workflows/validate.yaml
- name: Lint YAML
  run: yamllint .

- name: Lint Helm
  run: |
    for chart in charts/*/Chart.yaml; do
      helm lint "$(dirname "$chart")"
    done

- name: Validate Kustomize
  run: |
    for kust in apps/*/kustomization.yaml; do
      kustomize build "$(dirname "$kust")" --enable-helm > /dev/null
    done
```

---

## Compliance Assessment

**Use letter grades + evidence, NOT numeric scores.**

### Assessment Categories

| Category | Evidence Required |
|----------|------------------|
| **Formatting** | yamllint violations, tab count, indentation |
| **Helm Charts** | helm lint output, template rendering |
| **Kustomize** | kustomize build success, patch correctness |
| **Documentation** | values.yaml comments, section headers |
| **Security** | Hardcoded secrets, external secret refs |

### Grading Scale

| Grade | Criteria |
|-------|----------|
| A+ | 0 yamllint errors, 0 helm lint errors, documented, 0 secrets |
| A | <3 yamllint warnings, <3 helm lint warnings, documented |
| A- | <10 warnings, partial docs |
| B+ | <20 warnings |
| B | <40 warnings, templates render |
| C | Significant issues |

### Validation Commands

```bash
# Lint YAML
yamllint .
# Output: "X error(s), Y warning(s)"

# Check for tabs
grep -rP '\t' --include='*.yaml' --include='*.yml' . | wc -l
# Should be 0

# Helm lint
for chart in charts/*/Chart.yaml; do
  helm lint "$(dirname "$chart")"
done

# Check for hardcoded secrets
grep -r "password:\|secret:\|token:" --include='*.yaml' apps/
# Should only return external references
```

### Example Assessment

```markdown
## YAML/Helm Standards Compliance

| Category | Grade | Evidence |
|----------|-------|----------|
| Formatting | A+ | 0 yamllint errors, 0 tabs |
| Helm Charts | A- | 3 lint warnings (docs) |
| Kustomize | A | All overlays build |
| Security | A | 0 hardcoded secrets |
| **OVERALL** | **A** | **3 MEDIUM findings** |
```

---

## Anti-Patterns Avoided

### ❌ **Implicit Typing Traps (Norway Problem)**

Unquoted values silently coerced to unexpected types:

```yaml
# BAD - These become booleans (false, true)
country: NO       # false
feature: YES      # true
enabled: on       # true
disabled: off     # false

# GOOD - Quote ambiguous strings
country: "NO"
feature: "YES"
enabled: "on"
disabled: "off"
```

### ❌ **Anchor/Alias Abuse**

Overuse of `&` anchors and `*` aliases creates unreadable configs:

```yaml
# BAD - Excessive aliasing obscures intent
defaults: &defaults
  timeout: 30
  retries: 3

service_a:
  <<: *defaults
  name: a

service_b:
  <<: *defaults
  name: b

# GOOD - Explicit values for clarity (or use Kustomize overlays)
service_a:
  timeout: 30
  retries: 3
  name: a
```

**Rule:** Anchors acceptable for DRY in 2-3 references. Beyond that, use templating (Helm, Kustomize).

### ❌ **Deeply Nested Configs**

Nesting beyond 6 levels signals structural problems:

```yaml
# BAD - 7+ levels deep
app:
  server:
    routes:
      api:
        v1:
          users:
            endpoints:
              list:
                timeout: 30

# GOOD - Flatten with dotted keys or restructure
app:
  server:
    routes:
      api-v1-users-list:
        timeout: 30
```

### ❌ **Missing Document Markers**

Multi-document YAML files without `---` separators cause parse failures:

```yaml
# BAD - Two documents, no separator
apiVersion: v1
kind: ConfigMap
metadata:
  name: config-a
apiVersion: v1
kind: ConfigMap
metadata:
  name: config-b

# GOOD - Explicit document markers
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: config-a
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: config-b
```

### ❌ **Mixed Indentation**

Tabs or inconsistent indent widths cause silent parse errors:

```yaml
# BAD - Tabs mixed with spaces (invisible breakage)
app:
	name: broken    # Tab character

# BAD - Inconsistent indent width
app:
  name: my-app     # 2 spaces
  config:
      port: 8080   # 4 spaces

# GOOD - Consistent 2-space indentation throughout
app:
  name: my-app
  config:
    port: 8080
```

---

## Code Quality Metrics

### Validation Thresholds

| Metric | Threshold | Status | Action |
|--------|-----------|--------|--------|
| yamllint errors | 0 | ✅ Required | Fix before merge |
| yamllint warnings | <5 | ✅ Acceptable | Fix in next PR |
| yamllint warnings | 5-20 | ⚠️ Warning | Refactor recommended |
| yamllint warnings | 20+ | ❌ Critical | Block merge |
| Nesting depth | ≤6 levels | ✅ Acceptable | Flatten if deeper |
| Line length | ≤256 chars | ✅ Maximum | Prefer ≤120 |
| Helm lint errors | 0 | ✅ Required | Fix before merge |
| Kustomize build | Pass | ✅ Required | All overlays must build |
| Hardcoded secrets | 0 | ✅ Required | Use external refs |

### Tool Commands

```bash
# Full validation pass
yamllint -f parsable . | wc -l          # Total findings
yamllint -f parsable . | grep error     # Errors only
helm lint charts/*/                      # Helm validation
grep -rP '\t' --include='*.yaml' . | wc -l  # Tab detection
```

---

## Prescan Patterns

| ID | Pattern | Detection Command | Severity |
|----|---------|-------------------|----------|
| P01 | Implicit boolean detection | `yamllint -d '{extends: default, rules: {truthy: {check-keys: true}}}' .` | HIGH |
| P02 | Duplicate keys | `yamllint -d '{extends: default, rules: {key-duplicates: enable}}' .` | HIGH |
| P03 | Excessive nesting (>6 levels) | `awk '/^( ){14}[^ ]/' *.yaml` | MEDIUM |
| P04 | Long lines (>256 chars) | `yamllint -d '{extends: default, rules: {line-length: {max: 256}}}' .` | MEDIUM |
| P05 | Missing document marker | `grep -rL '^---' --include='*.yaml' .` | LOW |

### Pattern Details

**P01: Implicit Boolean Detection**
Catches the Norway problem — unquoted values like `NO`, `YES`, `on`, `off` silently become booleans. The `truthy` rule with `check-keys: true` flags these in both keys and values.

**P02: Duplicate Keys**
Duplicate keys in the same mapping silently overwrite earlier values. YAML spec allows it but most parsers keep only the last value, causing hard-to-debug configuration drift.

**P03: Excessive Nesting**
Detects indentation at 14+ spaces (7+ levels at 2-space indent). Deep nesting indicates config structure should be flattened or split into overlays.

**P04: Long Lines**
Lines beyond 256 characters indicate inline lists or values that should use block scalars. Default yamllint threshold is 120; 256 is the hard maximum.

**P05: Missing Document Marker**
Multi-resource YAML files (common in Kubernetes) require `---` separators. Missing markers cause concatenation errors during apply.

---

## Additional Resources

- [YAML Spec](https://yaml.org/spec/)
- [Helm Documentation](https://helm.sh/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [yamllint Documentation](https://yamllint.readthedocs.io/)

---

**Related:** Quick reference in Tier 1 `yaml.md`
