# Complexity Analysis (Step 2)

**Filter by language present in the change set first.** Run only the
analyzers whose language actually appears in the diff. A docs/shell/BATS-only
epic must NOT trigger `gocyclo` against the entire `cli/` tree (it has hung
in past runs); a Python-free epic must NOT trigger `radon`.

```bash
# Detect which languages are present in the diff (or in <path> for full audits).
# Use `git diff --name-only <base>...HEAD` for a PR; fall back to listing
# files under <path> when no diff base is available.
mkdir -p .agents/council
HAS_GO=false; HAS_PY=false
DIFF_FILES="$(git diff --name-only "${BASE:-HEAD~1}"...HEAD 2>/dev/null || find <path> -type f)"
echo "$DIFF_FILES" | grep -q '\.go$'  && HAS_GO=true
echo "$DIFF_FILES" | grep -q '\.py$'  && HAS_PY=true
echo "$(date -Iseconds) preflight: HAS_GO=$HAS_GO HAS_PY=$HAS_PY" >> .agents/council/preflight.log
```

**For Python (only when `HAS_PY=true`):**
```bash
if [ "$HAS_PY" = "true" ]; then
  echo "$(date -Iseconds) preflight: checking radon" >> .agents/council/preflight.log
  if ! which radon >> .agents/council/preflight.log 2>&1; then
    echo "⚠️ COMPLEXITY SKIPPED: radon not installed (pip install radon)"
  else
    radon cc <path> -a -s 2>/dev/null | head -30
    radon mi <path> -s 2>/dev/null | head -30
  fi
else
  echo "ℹ️ COMPLEXITY SKIPPED: no .py files in diff"
fi
```

**For Go (only when `HAS_GO=true`):**
```bash
if [ "$HAS_GO" = "true" ]; then
  echo "$(date -Iseconds) preflight: checking gocyclo" >> .agents/council/preflight.log
  if ! which gocyclo >> .agents/council/preflight.log 2>&1; then
    echo "⚠️ COMPLEXITY SKIPPED: gocyclo not installed (go install github.com/fzipp/gocyclo/cmd/gocyclo@latest)"
  else
    gocyclo -over 10 <path> 2>/dev/null | head -30
  fi
else
  echo "ℹ️ COMPLEXITY SKIPPED: no .go files in diff"
fi
```

**For other languages:** Skip complexity with explicit note: "⚠️ COMPLEXITY SKIPPED: No analyzer for <language>"

**Interpret results:**

| Score | Rating | Action |
|-------|--------|--------|
| A (1-5) | Simple | Good |
| B (6-10) | Moderate | OK |
| C (11-20) | Complex | Flag for council |
| D (21-30) | Very complex | Recommend refactor |
| F (31+) | Untestable | Must refactor |

**Include complexity findings in council context.**
