> See probes-intro.md for confidence scoring reference.

## Category: `arch`

### Probe: circular-dependencies

**Activation:** Any project with import/require statements.

**Detection Method:**

**Preferred (language-mapper-supported projects):**

Call `extractSemanticSlices(filePath, { type: 'imports' })` from `scripts/lib/language-mappers/index.mjs` for each source file to obtain a typed list of import edges. The mapper handles TypeScript, JavaScript, and Markdown files natively; unsupported file types return an empty array (graceful degradation). Feed the resulting `{source_file -> [imported_file]}` adjacency map directly into the cycle-detection loop below.

```js
// Pseudocode — wire once per probe run
import { extractSemanticSlices } from '$PLUGIN_ROOT/scripts/lib/language-mappers/index.mjs';

for (const filePath of sourceFiles) {
  const imports = await extractSemanticSlices(filePath, { type: 'imports' });
  for (const { resolved } of imports) {
    adjacency.get(filePath).push(resolved);
  }
}
```

**Fallback (when language-mapper returns empty or for unsupported file types):**

```bash
# Build import graph from source files
# Step 1: Extract all import relationships
Grep pattern: (import\s+.*from\s+["']([^"']+)["']|require\s*\(\s*["']([^"']+)["']\s*\))
  --glob "*.{ts,tsx,js,jsx}" --glob "!**/node_modules/**"

# Step 2: Resolve relative paths to absolute
# Step 3: Build adjacency list

# Alternative for Node.js projects with madge installed:
npx madge --circular --extensions ts,tsx,js,jsx src/ 2>/dev/null
```

Algorithm (cycle detection — same for both paths above):
1. Build `{source_file -> [imported_file]}` adjacency map
2. Resolve relative imports to absolute paths
3. For each file, BFS through imports with depth limit of 10
4. If BFS revisits the starting file, record the cycle path

**Evidence Format:**
```
Cycle: <file_a> -> <file_b> -> ... -> <file_a>
Length: <number of files in cycle>
Files Involved:
  - <file_path_1>
  - <file_path_2>
```

**Default Severity:** High.

---

### Probe: complexity-hotspots

**Activation:** Any project with source files.

**Detection Method:**

```bash
# Long functions (>50 lines)
# Count lines between function declarations and closing braces
# Heuristic: find function starts and measure to next function or file end
Grep pattern: (function\s+\w+|const\s+\w+\s*=\s*(async\s+)?\([^)]*\)\s*=>|def\s+\w+|func\s+\w+)
  --glob "*.{ts,tsx,js,jsx,py,go,rs}"

# Deep nesting (>4 levels)
# Count leading whitespace indicating nesting depth
# For standard 2-space indent: >8 spaces = >4 levels
# For standard 4-space indent: >16 spaces = >4 levels
Grep pattern: ^(\s{16,}|\t{4,})\S
  --glob "*.{ts,tsx,js,jsx,py,go,rs}"

# Large files (>500 lines)
wc -l src/**/*.{ts,tsx,js,jsx,py,go,rs} 2>/dev/null | awk '$1 > 500 {print $0}'

# Functions with >5 parameters
Grep pattern: (function\s+\w+|def\s+\w+|func\s+\w+)\s*\([^)]*,[^)]*,[^)]*,[^)]*,[^)]*,
  --glob "*.{ts,tsx,js,jsx,py,go,rs}"
```

**Evidence Format:**
```
File: <path> Line: <n>
Hotspot: long-function | deep-nesting | large-file | many-parameters
Metric: <measured_value> (e.g., "73 lines", "6 levels", "612 lines", "8 params")
Threshold: <threshold_value>
```

**Default Severity:** Medium.

---

### Probe: dependency-security

**Activation:** Package manager detected (`package.json`, `requirements.txt`, `Pipfile`, `Cargo.toml`, `go.mod`).

**Detection Method:**

```bash
# Node.js
npm audit --json 2>/dev/null

# Python
pip-audit --format json 2>/dev/null

# Rust
cargo audit --json 2>/dev/null

# Go
govulncheck ./... 2>/dev/null
```

Parse JSON output for vulnerabilities. Focus on:
- Critical severity CVEs
- High severity CVEs
- Vulnerabilities with known exploits

**Evidence Format:**
```
Package: <name>
Version: <installed_version>
CVE: <CVE-ID>
Severity: critical | high | medium | low
Title: <vulnerability title>
Fix Available: <fixed_version or NONE>
```

**Default Severity:** Critical (critical CVEs), High (high CVEs).

---

### Probe: architectural-friction

**Activation:** Any project with TypeScript, JavaScript, Python, Go, or Rust source files. Targets structural design issues — shallow modules, pass-through adapters, and hypothetical seams — that indicate low leverage and poor locality in the codebase's interface design.

**Detection Method:**

Three heuristics are applied independently. Each produces its own findings.

---

**Heuristic A: shallow-module**

A module exposes a large interface relative to its implementation size — it is a pass-through with little leverage. Callers pay the full interface cost but get minimal depth in return.

```bash
# Step 1: Count exported symbols per file (TypeScript/JavaScript)
Grep pattern: ^\s*export\s+(default\s+)?(function|const|class|interface|type|enum)\s+\w+
  --glob "*.{ts,tsx,js,jsx}"

# Step 1b: Count exported symbols (Python)
Grep pattern: ^def\s+\w+
  --glob "*.py"

# Step 1c: Count exported symbols (Go)
Grep pattern: ^func\s+[A-Z]\w+
  --glob "*.go"

# Step 1d: Count exported symbols (Rust)
Grep pattern: ^pub fn\s+\w+|^pub struct\s+\w+|^pub enum\s+\w+|^pub trait\s+\w+
  --glob "*.rs"

# Step 2: Count non-comment, non-blank implementation lines (LOC approximation)
grep -cvE '^\s*(//|#|/\*|\*|$)' <file>

# Flag condition: (exported_symbols / LOC) >= 0.5  AND  exported_symbols >= 3
# The exported_symbols >= 3 guard avoids false positives on single-export utility files.
```

---

**Heuristic B: pass-through-adapter**

A class or module where most methods are 1–2 line delegations to a single dependency — it adds no leverage. The deletion test (LANGUAGE.md) reveals the module hides nothing; complexity would be identical across callers if it were removed.

```bash
# Detect single-line delegation methods in TypeScript/JavaScript classes
Grep pattern: ^\s+\w+\s*\([^)]*\)\s*\{\s*return\s+this\.\w+\.\w+\(.*\)\s*;?\s*\}
  --glob "*.{ts,tsx,js,jsx}"

# Detect single-line delegation methods in Python classes (two-line form)
# Match def line followed by a return self.<dep>.<method>(...) line
Grep pattern: ^\s+def\s+\w+\(self[^)]*\):\s*$
  --glob "*.py"
# Then verify next non-blank line matches: ^\s+return\s+self\.\w+\.\w+\(.*\)$

# Flag condition: (delegation_methods / total_methods) >= 0.7  AND  total_methods >= 3
# Count total_methods per file with:
Grep pattern: ^\s+(public\s+|private\s+|protected\s+|async\s+)*\w+\s*\([^)]*\)\s*\{
  --glob "*.{ts,tsx,js,jsx}"
```

---

**Heuristic C: one-adapter-seam**

A TypeScript `interface` or `abstract class` with exactly one concrete implementation — a hypothetical seam, not a real one (Ousterhout, LANGUAGE.md: "One adapter means a hypothetical seam. Two adapters means a real one."). The seam pays an interface-learning cost that no second adapter ever amortises.

```bash
# Step 1: Enumerate all interface and abstract class names in the codebase
Grep pattern: ^(export\s+)?(interface|abstract\s+class)\s+(\w+)
  --glob "*.{ts,tsx}"

# Step 2: For each name <N> found, count concrete implementations
grep -rE 'implements\s+\b<N>\b|extends\s+\b<N>\b' src/ --include="*.ts" --include="*.tsx" \
  | grep -v 'abstract class'

# Step 3: Count method signatures within the interface/abstract class body
Grep pattern: ^\s+\w+\s*\([^)]*\)\s*[:;]
  within the block following the interface/abstract class declaration

# Flag condition: implementation_count == 1  AND  method_signature_count >= 2
# The method_signature_count >= 2 guard avoids flagging trivial marker interfaces.

# Batch approximation when AST tooling is unavailable:
# Enumerate all interface names first, then:
grep -rE 'implements\s+(InterfaceName1|InterfaceName2|...)' src/ \
  --include="*.{ts,tsx}" | sort | uniq -c | awk '$1 == 1 {print $0}'
```

**Evidence Format:**

```
File: <file_path> Line: <line_number>
Probe: architectural-friction
Category: arch
Severity: medium
Pattern: shallow-module | pass-through-adapter | one-adapter-seam
Matched text: <relevant snippet>
Title: <short description — e.g. "Shallow module exposes 8 symbols across 16 LOC">
Description: <2-3 lines on why this is friction, using LANGUAGE.md vocabulary —
             reference depth, leverage, locality, seam, adapter as appropriate>
Recommended fix: invoke the `architecture` skill on this cluster (see skills/architecture/SKILL.md)
```

For `shallow-module`: describe the interface-to-depth ratio and what leverage is missing.
For `pass-through-adapter`: describe which dependency is being delegated to and what the module fails to hide.
For `one-adapter-seam`: name the interface and its single implementation; note that the seam cost has no second adapter to amortise it.

Severity may be raised to **High** when: a shallow module has `exported_symbols >= 10`; a pass-through adapter wraps a high-fan-out dependency (>5 dependents); or a one-adapter seam sits on a hot import path (imported by ≥10 files). Note the raise condition in the Description field — do not auto-promote.

**Default Severity:** Medium.

---
