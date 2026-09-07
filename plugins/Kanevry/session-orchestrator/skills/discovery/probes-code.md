> See probes-intro.md for confidence scoring reference.

## Category: `code`

### Probe: hardcoded-values

**Activation:** Any project with source files.

**Detection Method:**

1. Hardcoded secrets:
```bash
# Grep for hardcoded secrets in source files (exclude tests, .env, config examples)
Grep pattern: (password|api_key|secret|token|api_secret)\s*[:=]\s*["'][^"']+["']
  --glob "!*.test.*" --glob "!*.spec.*" --glob "!.env*" --glob "!*.example"
  --glob "!*.sample" --glob "!**/test/**" --glob "!**/tests/**"
  --glob "!**/fixtures/**" --glob "!**/mocks/**"
```

2. Hardcoded URLs:
```bash
# Grep for hardcoded URLs in source files (exclude docs, configs, tests)
Grep pattern: https?://
  --glob "*.{ts,tsx,js,jsx,py,go,rs,java}" --glob "!**/test/**" --glob "!**/tests/**"
  --glob "!README*" --glob "!*.md" --glob "!*.config.*"
```

3. Magic numbers:
```bash
# Grep for magic numbers (numeric literals outside obvious contexts)
Grep pattern: [^a-zA-Z_]\b\d{4,}\b(?!\s*[;,\])}])
  --glob "*.{ts,tsx,js,jsx,py,go,rs,java}" --glob "!**/test/**"
```

**Evidence Format:**
```
File: <path> Line: <n>
Match: <matched_text>
Classification: secret | url | magic-number
```

**Default Severity:** Critical (secrets), High (URLs), Medium (magic numbers).

---

### Probe: orphaned-annotations

**Activation:** Any project with source files.

**Detection Method:**

```bash
# Grep for TODO/FIXME/HACK/XXX/TEMP/WORKAROUND annotations
Grep pattern: (TODO|FIXME|HACK|XXX|TEMP|WORKAROUND)[\s:()\-]
  --glob "*.{ts,tsx,js,jsx,py,go,rs,java,rb,swift,kt}"
```

For each match, check whether a corresponding VCS issue exists:
```bash
# Search for issue referencing the annotation text
gh issue list -R <OWNER>/<REPO> --search "<annotation text>" --limit 5
# or
glab issue list -R <OWNER>/<REPO> --search "<annotation text>" --per-page 5
```

Flag annotations with no corresponding issue.

**Evidence Format:**
```
File: <path> Line: <n>
Annotation: <TODO|FIXME|HACK|...>
Text: <annotation text>
Linked Issue: <#IID or NONE>
```

**Default Severity:** Low (TODO), Medium (FIXME/HACK/XXX/TEMP/WORKAROUND).

---

### Probe: dead-code

**Activation:** `package.json` exists (JS/TS projects).

**Detection Method:**

1. Unused exports:
```bash
# Find all export statements
Grep pattern: export\s+(default\s+)?(function|class|const|let|var|type|interface|enum)\s+(\w+)
  --glob "*.{ts,tsx,js,jsx}" --glob "!**/node_modules/**"

# For each exported name, check for importers
Grep pattern: import.*<exported_name>
  --glob "*.{ts,tsx,js,jsx}" --glob "!**/node_modules/**"

# Flag exports with 0 importers (exclude index files and entry points)
# Exclude: index.ts, index.js, main.ts, main.js, app.ts, app.js
```

2. Unused dependencies:
```bash
# List all dependencies from package.json
cat package.json | python3 -c "import json,sys; deps=json.load(sys.stdin).get('dependencies',{}); [print(d) for d in deps]"

# For each dependency, check if it is imported anywhere
Grep pattern: (import|require).*['"]<dependency_name>
  --glob "*.{ts,tsx,js,jsx}" --glob "!**/node_modules/**"
```

**Evidence Format:**
```
Type: unused-export | unused-dependency
Name: <export_name or dependency_name>
Defined In: <file_path>:<line>
Importers Found: 0
```

**Default Severity:** Low.

---

### Probe: ai-slop

**Activation:** Any project with source files.

**Detection Method:**

1. Slop patterns (reference `slop-patterns.md` for full pattern list):
```bash
# Filler phrases in comments
Grep pattern: (as you can see|it's worth noting|needless to say|it should be noted|obviously|of course|basically|essentially|simply|let's go ahead|let's proceed|moving on to)
  --glob "*.{ts,tsx,js,jsx,py,go,rs,java}"

# Over-documented trivial code (param docs repeating param name)
Grep pattern: @param\s+(\w+)\s+[-—]\s*(the\s+)?\1
  --glob "*.{ts,tsx,js,jsx}"

# Generic error messages
Grep pattern: catch.*throw new Error\(["'].*error occurred
  --glob "*.{ts,tsx,js,jsx,py}"

# Redundant type assertions
Grep pattern: as string(?=\s*[;,)\]])
  --glob "*.{ts,tsx}"
```

2. Hallucinated imports (verify every import resolves):
```bash
# Extract all relative imports and check they exist on disk
Grep pattern: from\s+["'](\.\.?/[^"']+)["']
  --glob "*.{ts,tsx,js,jsx}"

# For each match, verify the file exists:
# test -f <resolved_path>.ts || test -f <resolved_path>.tsx || test -f <resolved_path>/index.ts

# Extract package imports and verify against package.json
Grep pattern: from\s+["']([^./][^"']*)["']
  --glob "*.{ts,tsx,js,jsx}"
# Verify each package is in dependencies or devDependencies
```

**Evidence Format:**
```
Type: slop-pattern | hallucinated-import
File: <path> Line: <n>
Pattern: <matched_text>
Category: filler | over-doc | generic-error | redundant | hallucinated
```

**Default Severity:** Medium (slop patterns), High (hallucinated imports).

---

### Probe: type-safety-gaps

**Activation:** `tsconfig.json` exists.

**Detection Method:**

```bash
# any type usage
Grep pattern: :\s*any\b
  --glob "*.{ts,tsx}" --glob "!*.test.*" --glob "!*.spec.*" --glob "!**/test/**"

# Type assertion to any
Grep pattern: as\s+any\b
  --glob "*.{ts,tsx}" --glob "!*.test.*" --glob "!*.spec.*"

# TypeScript directive suppressions
Grep pattern: @ts-ignore|@ts-expect-error
  --glob "*.{ts,tsx}"

# Non-null assertions
Grep pattern: \w+!\.
  --glob "*.{ts,tsx}" --glob "!*.test.*" --glob "!*.spec.*"
```

**Evidence Format:**
```
File: <path> Line: <n>
Pattern: any-type | as-any | ts-ignore | ts-expect-error | non-null-assertion
Code: <matched_text>
```

**Default Severity:** Medium.

---

### Probe: test-coverage-gaps

**Activation:** Test infrastructure exists (test directory, test config, or test files present).

**Detection Method:**

```bash
# Find all source files
Glob pattern: src/**/*.{ts,tsx,js,jsx,py,go,rs}
  --glob "!*.test.*" --glob "!*.spec.*" --glob "!**/test/**" --glob "!**/tests/**"
  --glob "!**/fixtures/**" --glob "!**/mocks/**" --glob "!**/__mocks__/**"

# For each source file, check if a corresponding test file exists:
# JS/TS: <name>.test.ts, <name>.spec.ts, <name>.test.tsx, <name>.spec.tsx
# Python: test_<name>.py, <name>_test.py
# Go: <name>_test.go
# Rust: tests/<name>.rs or #[cfg(test)] in same file

# List source files with no test counterpart
```

**Evidence Format:**
```
File: <path>
Test File Expected: <expected_test_path>
Status: MISSING
```

**Default Severity:** Medium.

---

### Probe: test-anti-patterns

**Activation:** Test files exist.

**Detection Method:**

```bash
# Tests with no assertions (assert-nothing)
# Find test functions/blocks, check for expect/assert within them
Grep pattern: (it|test)\s*\(
  --glob "*.{test,spec}.{ts,tsx,js,jsx}"
# Then verify each test block contains at least one:
Grep pattern: (expect|assert|should|toBe|toEqual|toMatch|toThrow|toHaveBeenCalled)
  # If absent in the same test block, flag as assert-nothing

# Excessive mocking (test-the-mock)
Grep pattern: (jest\.mock|vi\.mock|sinon\.stub|mock\()
  --glob "*.{test,spec}.{ts,tsx,js,jsx}"
# Flag files with >5 mock statements

# Flaky test indicators
Grep pattern: (setTimeout|sleep|delay|waitFor)\s*\(
  --glob "*.{test,spec}.{ts,tsx,js,jsx}"

# Snapshot abuse
Grep pattern: toMatchSnapshot|toMatchInlineSnapshot
  --glob "*.{test,spec}.{ts,tsx,js,jsx}"
# Flag files with >10 snapshot assertions

# Swallowed errors in tests
Grep pattern: catch\s*\([^)]*\)\s*\{\s*\}
  --glob "*.{test,spec}.{ts,tsx,js,jsx}"
```

**Evidence Format:**
```
File: <path> Line: <n>
Anti-Pattern: assert-nothing | test-the-mock | flaky-indicator | snapshot-abuse | swallowed-error
Code: <matched_text>
```

**Default Severity:** High.

---

### Probe: security-basics

**Activation:** Any project with source files.

**Detection Method:**

```bash
# eval usage
Grep pattern: \beval\s*\(
  --glob "*.{ts,tsx,js,jsx,py}" --glob "!**/node_modules/**"

# Dangerous HTML injection (React)
Grep pattern: dangerouslySetInnerHTML
  --glob "*.{tsx,jsx}"

# innerHTML assignment
Grep pattern: innerHTML\s*=
  --glob "*.{ts,tsx,js,jsx}"

# SQL injection via template literals
Grep pattern: `[^`]*SELECT[^`]*\$\{
  --glob "*.{ts,tsx,js,jsx}" --glob "!**/test/**" --glob "!**/tests/**"

# Permissive CORS
Grep pattern: cors.*\*|Access-Control-Allow-Origin.*\*
  --glob "*.{ts,tsx,js,jsx,py,go,java}" --glob "!**/test/**"

# Insecure randomness in security contexts
Grep pattern: Math\.random\(\)
  --glob "*.{ts,tsx,js,jsx}" --glob "!**/test/**"
# Cross-reference with nearby security-related terms (token, secret, key, auth, session)
```

**Evidence Format:**
```
File: <path> Line: <n>
Vulnerability: eval | xss-dangerous | xss-innerhtml | sql-injection | cors-wildcard | insecure-random
Code: <matched_text>
Context: <surrounding lines>
```

**Default Severity:** High. Critical for SQL injection and XSS patterns.

---
