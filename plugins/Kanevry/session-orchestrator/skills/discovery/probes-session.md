> See probes-intro.md for confidence scoring reference.

## Category: `session`

### Probe: gap-analysis

**Activation:** Active session exists (session plan in CLAUDE.md or AGENTS.md or memory).

**Detection Method:**

```bash
# Step 1: Extract planned items from session plan
# Parse the wave plan for task descriptions and acceptance criteria

# Step 2: Get all changes in current session
git diff --name-only HEAD~<session_commit_count>
git diff --stat HEAD~<session_commit_count>

# Step 3: For each planned item, verify corresponding changes exist
# Match task descriptions against changed files and diff content
git diff HEAD~<session_commit_count> -- <relevant_files>

# Step 4: Check acceptance criteria
# For each acceptance criterion, verify it can be confirmed from the diff
```

**Evidence Format:**
```
Planned Item: <task description>
Status: completed | partial | missing
Evidence: <files changed or NONE>
Acceptance Criteria Met: <list of criteria with pass/fail>
```

**Default Severity:** High.

---

### Probe: hallucination-check

**Activation:** Active session exists.

**Detection Method:**

```bash
# Step 1: Read recent commit messages
git log --oneline -20

# Step 2: For each commit message, extract claims:
# "Added X" -> verify X exists in the codebase
Grep pattern: <claimed_addition>
  --glob "*.{ts,tsx,js,jsx,py,go,rs}"

# "Fixed Y" -> verify the fix is present in the diff
git show <commit_hash> -- <relevant_files>

# "Closes #N" -> verify acceptance criteria from issue #N are met
gh issue view <N> --json body -q '.body'
# or
glab issue view <N>

# Step 3: Cross-reference claims against actual changes
git diff <commit_hash>~1..<commit_hash>
```

**Evidence Format:**
```
Commit: <hash> <message>
Claim: <extracted claim>
Verification: confirmed | UNVERIFIED | contradicted
Evidence: <what was found or not found>
```

**Default Severity:** Critical.

---

### Probe: stale-issues

**Activation:** VCS configured (git remote exists).

**Detection Method:**

```bash
# GitLab: list open issues sorted by last update
glab issue list --per-page 100 | head -50

# GitHub: list open issues sorted by last update
gh issue list --limit 100 --json number,title,labels,updatedAt,assignees --jq '.[] | select(.updatedAt < "<30_days_ago_iso>")'

# Flag:
# - Issues with no activity in stale-issue-days (default: 30 days)
# - Issues assigned but with no associated branch
# - Issues labeled priority:high or priority:critical that are stale

# Check for associated branches:
git branch -r | grep -i "<issue_number>"
```

Session Config field: `stale-issue-days` (default: 30).

**Evidence Format:**
```
Issue: #<number> <title>
Last Updated: <date>
Days Stale: <count>
Assigned To: <assignee or UNASSIGNED>
Has Branch: true | false
Priority: <priority label or NONE>
```

**Default Severity:** Low. Medium if `priority:high` or `priority:critical` is stale.

---

### Probe: issue-dependency-chains

**Activation:** VCS configured (git remote exists).

**Detection Method:**

```bash
# GitLab: fetch issue descriptions and look for cross-references
glab api "projects/<project_id>/issues?state=opened&per_page=100" | python3 -c "
import json, sys, re
issues = json.load(sys.stdin)
for issue in issues:
    refs = re.findall(r'(blocks|depends on|relates to|blocked by)\s+#(\d+)', issue.get('description',''), re.I)
    if refs:
        print(f'#{issue[\"iid\"]}: {refs}')
"

# GitHub: fetch issue bodies and parse cross-references
gh issue list --limit 100 --json number,body --jq '.[] | {number, body}' | python3 -c "
import json, sys, re
for line in sys.stdin:
    issue = json.loads(line)
    refs = re.findall(r'(blocks|depends on|relates to|blocked by)\s+#(\d+)', issue.get('body',''), re.I)
    if refs:
        print(f'#{issue[\"number\"]}: {refs}')
"

# Build dependency graph from parsed relationships
# Detect:
# - Circular chains (A blocks B, B blocks A)
# - Deep chains (>3 levels: A -> B -> C -> D -> ...)
```

**Evidence Format:**
```
Chain: #<a> -> #<b> -> #<c> [-> ...]
Type: circular | deep-chain
Depth: <level count>
Issues Involved:
  - #<number>: <title>
```

**Default Severity:** Medium.

---

### Probe: claude-md-audit

**Activation:** CLAUDE.md or AGENTS.md exists in project root.

**Detection Method:**

1. Session Config completeness (if session-orchestrator plugin is installed):
```bash
# Check if ## Session Config section exists
Grep pattern: ^## Session Config
  --glob "{CLAUDE,AGENTS}.md"

# If section exists, validate referenced paths:
# Extract file paths from Session Config values (pencil, cross-repos, ssot-files)
# For each referenced path:
test -e <path>
# Flag paths that don't exist
```

2. Rules freshness:
```bash
# List all <state-dir>/rules/ files
Glob pattern: "<state-dir>/rules/*.md"

# For each rule file:
# a) Extract key identifiers (function names, file paths, patterns mentioned)
# b) Grep for those identifiers in source code
Grep pattern: <extracted_identifier>
  --glob "*.{ts,tsx,js,jsx,py,go,rs}" --glob "!**/node_modules/**"
# Flag rules whose referenced patterns/functions/files no longer exist in the codebase
```

3. CLAUDE.md staleness:
```bash
# Check last modification date
# macOS:
stat -f "%Sm" -t "%Y-%m-%d" CLAUDE.md
# Linux:
stat -c "%y" CLAUDE.md

# Compare against ssot-freshness-days from Session Config (default: 5)
# Flag if CLAUDE.md is older than threshold
```

4. Technology references:
```bash
# Extract technology/framework mentions from CLAUDE.md
# Common patterns: "uses X", "built with X", framework names, library names
# Cross-reference against package.json dependencies:
cat package.json | python3 -c "
import json, sys
pkg = json.load(sys.stdin)
deps = set(pkg.get('dependencies', {}).keys()) | set(pkg.get('devDependencies', {}).keys())
print('\n'.join(sorted(deps)))
"
# Flag technologies mentioned in CLAUDE.md but absent from dependencies
# Also flag major dependencies NOT mentioned in CLAUDE.md (potential documentation gap)
```

**Evidence Format:**
```
File: CLAUDE.md or AGENTS.md (or <state-dir>/rules/<name>.md)
Issue: missing-session-config | invalid-path-reference | stale-rule | stale-claude-md | phantom-technology | undocumented-dependency
Detail: <specific finding>
Referenced: <what was referenced>
Actual: <what was found or NOT found>
```

**Default Severity:** Medium (staleness, phantom tech, undocumented deps), High (invalid paths, stale rules with no codebase match).

5. Token efficiency — CLAUDE.md size:
```bash
# Count lines in CLAUDE.md
wc -l CLAUDE.md

# Flag if > 150 lines (warning) or > 250 lines (high)
# Identify sections > 30 lines that could move to <state-dir>/rules/ or <state-dir>/docs/
# Check for inline code blocks > 10 lines (should be in separate files)
```

6. Token efficiency — .claudeignore coverage:
```bash
# Check if .claudeignore exists
test -f .claudeignore

# If not, scan for common excludable patterns:
# - Large binary/data directories (> 10MB total)
# - Test fixture directories with > 50 files
# Flag projects without .claudeignore that have > 500 files
find . -type f -not -path '*/node_modules/*' -not -path '*/.git/*' | wc -l
```

7. Token efficiency — state directory hygiene:
```bash
# Check state directory total size (platform-aware: .claude/, .codex/, .cursor/)
STATE_DIR="${SO_STATE_DIR:-.claude}"
du -sh "$STATE_DIR/" 2>/dev/null

# Flag if > 10MB
# Check for stale directories: backups/, screenshots/, temp-*
# Check for files not modified in > 90 days
find "$STATE_DIR/" -maxdepth 1 -type d -name "backups" -o -name "screenshots" -o -name "temp-*" 2>/dev/null
find "$STATE_DIR/" -type f -mtime +90 2>/dev/null | head -10
```

8. Token efficiency — duplicate pattern detection:
```bash
# Hash the ## Session Config section across repos
# If cross-repos is configured, compare CLAUDE.md patterns
# Flag identical sections that could be consolidated into per-project rules at `<state-dir>/rules/`
```

**Evidence Format (token efficiency):**
```
File: CLAUDE.md (or <state-dir>/)
Issue: oversized-claude-md | missing-claudeignore | bloated-state-dir | stale-state-artifacts | duplicate-patterns
Detail: <specific finding>
Current: <size/count>
Threshold: <limit>
Recommendation: <action>
```

**Default Severity:** Medium (oversized CLAUDE.md, missing .claudeignore), Low (stale artifacts, duplicate patterns), High (state dir > 50MB).

---

### Probe: cross-repo-duplicate-implementation

**Activation:** Discovery finding recommends implementing something that lives in a known plugin repo (session-orchestrator, projects-baseline, claude-code-skills). Specifically: the finding mentions a path under `session-orchestrator/skills/`, `session-orchestrator/scripts/`, or `session-orchestrator/hooks/`, OR proposes creating a new skill/script whose name could already be in flight upstream.

**Motivation:** A discovery finding that says "implement skill X" is only useful if X does not already exist on the plugin repo. Without a cross-repo check, a consumer repo can spend hours rebuilding work that already sits in an open MR or on a feature branch. First observed in the vault session on 2026-04-19 (session-orchestrator issue #179): vault#58 was filed ~7 h after the feature already existed as MR !11 — the next vault session began rebuilding the same work from scratch before catching the duplication mid-wave.

**Detection Method:**

```bash
# Identify the plugin repo project path. Prefer the Session Config `cross-repos`
# entry that points at session-orchestrator; fall back to the hardcoded default.
PLUGIN_REPO="${SO_PLUGIN_REPO:-infrastructure/session-orchestrator}"

# SKILL_NAME is extracted from the finding text (path segment after skills/,
# or the proposed new skill name).
SKILL_NAME="<extracted from finding>"

# 1) Open MRs whose title mentions the skill/script name.
glab mr list --repo "$PLUGIN_REPO" --state opened 2>/dev/null \
  | grep -i "$SKILL_NAME"

# 2) Feature branches matching `feat/<skill>` or containing the name.
glab api "projects/${PLUGIN_REPO//\//%2F}/repository/branches?search=$SKILL_NAME" 2>/dev/null \
  | jq -r '.[].name' 2>/dev/null

# 3) Recently closed issues referencing the skill/script name.
glab issue list --repo "$PLUGIN_REPO" --closed --search "$SKILL_NAME" 2>/dev/null | head -10

# If any query returns a match → flag as pre-existing-work.
# If glab is offline / unauthenticated → degrade to SKIP with evidence note, do not fabricate findings.
```

**Evidence Format:**
```
Finding (original): <discovery finding that triggered this probe>
Cross-repo target: <PLUGIN_REPO>
Candidate name: <SKILL_NAME>
Matches:
  - MR !NN <title>  (opened <date>)          # when open MR matches
  - branch feat/<name>  (last commit <date>) # when branch matches
  - issue #NN <title>  (closed <date>)       # when closed issue matches
Recommendation: STOP before opening a new issue — inspect the existing work. If
  duplicate, close this finding with a reference. If complementary, scope the
  new issue against the existing implementation.
```

**Default Severity:** High when an open MR or active feature branch matches (wasted work is imminent); Medium when only closed issues match (historical context).

**Dependencies:** Requires `glab` (GitLab CLI) for the three queries; `gh` equivalent for GitHub-hosted plugin repos. Auto-degrade to SKIP with a note when CLI unavailable or unauthenticated — never fabricate matches.

**Scope:** Runs after any other probe surfaces a finding of the form "add/create/implement [skill|script|hook] …" that could live in the plugin repo. Not a standalone probe — it validates other probes' output before a new issue is filed.

---

### Probe: state-md-staleness

**Activation:** `<state-dir>/STATE.md` exists AND Session Config `persistence: true`.

**Detection Method:**

Read STATE.md frontmatter and compare `updated` timestamp against today. The `updated` field is optional (added in #184, schema-version 1). When absent, fall back to file mtime.

```bash
STATE_FILE="$(git rev-parse --show-toplevel)/.claude/STATE.md"
[[ -f "$STATE_FILE" ]] || exit 0
# Prefer the frontmatter `updated:` field; fall back to file mtime.
UPDATED="$(node --input-type=module -e "
import {readFileSync} from 'node:fs';
import {parseStateMd} from '${PLUGIN_ROOT}/scripts/lib/state-md.mjs';
try {
  const p = parseStateMd(readFileSync('$STATE_FILE', 'utf8'));
  if (p && p.frontmatter.updated) process.stdout.write(p.frontmatter.updated);
} catch {}
" 2>/dev/null)"
if [[ -z "$UPDATED" ]]; then
  # Fallback: file mtime (cross-platform)
  UPDATED_EPOCH=$(stat -f %m "$STATE_FILE" 2>/dev/null || stat -c %Y "$STATE_FILE" 2>/dev/null)
else
  UPDATED_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$UPDATED" +%s 2>/dev/null \
    || date -d "$UPDATED" +%s 2>/dev/null)
fi
NOW_EPOCH=$(date +%s)
AGE_DAYS=$(( (NOW_EPOCH - UPDATED_EPOCH) / 86400 ))
```

**Thresholds:**
- `AGE_DAYS >= 7` → **warn** ("stale — last updated N days ago")
- `2 <= AGE_DAYS < 7` → **info** ("stale-ish — last updated N days ago")
- `AGE_DAYS < 2` → no finding

**Evidence Format:**

```
File: <state-dir>/STATE.md
Issue: state-md-staleness
Detail: STATE.md last updated <UPDATED> (<AGE_DAYS> days ago)
Source: <frontmatter.updated | file-mtime-fallback>
Recommendation: Run /session to refresh state, or delete the file if work has been abandoned.
```

**Default Severity:** Medium when `AGE_DAYS >= 7` (warn); Low when `2 <= AGE_DAYS < 7` (info).

**Rationale (#184):** Consumer repos with long-dormant STATE.md files risk the next session-start resuming a ghost session. The probe surfaces this before it becomes a resume-prompt surprise. Uses the optional `updated` frontmatter field introduced in #184; degrades to file mtime for backward compatibility.

---

### Probe: bootstrap-lock-freshness

**Activation:** Every session-start on a bootstrapped repo (`.orchestrator/bootstrap.lock` exists).

**Motivation:** Plugin upgrades between releases can change templates/rules/hooks that an older lock does not reflect. Silent drift between harness version and repo scaffold. All 6/6 Advanced-adoption repos have the lock but none validate its freshness. Issue #186 (Epic #181 harness-retro promotion list #5).

**Detection Method:**

```bash
LOCK_FILE="$(git rev-parse --show-toplevel)/.orchestrator/bootstrap.lock"
[[ -f "$LOCK_FILE" ]] || exit 0
CURRENT_VERSION="$(node -e "process.stdout.write(require('${PLUGIN_ROOT}/package.json').version)")"
node --input-type=module -e "
import { checkBootstrapLockFreshness } from '${PLUGIN_ROOT}/scripts/lib/bootstrap-lock-freshness.mjs';
const result = checkBootstrapLockFreshness({
  repoRoot: '$(git rev-parse --show-toplevel)',
  currentPluginVersion: '${CURRENT_VERSION}',
});
if (result.severity !== 'info') {
  process.stdout.write(JSON.stringify(result, null, 2));
  process.exit(result.severity === 'alert' ? 2 : 1);
}
" 2>/dev/null
```

**Evidence Format:**

```
Severity: info | warn | alert
Message:  bootstrap.lock: age=<N>d, plugin-version=<lock-ver> (current=<plugin-ver>)
Details:
  ageDays:              <integer or null>
  pluginVersion:        <version in lock or "unknown">
  currentPluginVersion: <running plugin version>
  bootstrappedAt:       <ISO timestamp used for age calculation — ORIGINAL provenance, unchanged by a refresh>
  refreshedAt:          <ISO timestamp of the last /bootstrap --refresh-lock, or null>
  versionMismatch:      true | false
  reason:               missing-repoRoot | missing | read-error | stale-age | unparseable-timestamp
                         | version-mismatch-major | version-mismatch-unparseable | null (#57)
Remediation: reason-aware (#57) — see below.
```

**Default Severity:** info <30d, warn 30–89d or version-mismatch, alert ≥90d or unparseable.

**Remediation (reason-aware, #57):** `/bootstrap --retroactive` only helps when the lock is missing entirely (`reason: 'missing'`) — once a lock already has valid `version`/`tier` fields, re-running `--retroactive` is an idempotent no-op (see the Retroactive Flow's idempotency guard in `skills/bootstrap/SKILL.md`) and never actually refreshes anything. For a present-but-stale/drifted lock, branch on `result.details.reason`:
- `stale-age` or `unparseable-timestamp` → `/bootstrap --refresh-lock` to acknowledge and reset the freshness clock.
- `version-mismatch-major` or `version-mismatch-unparseable` → check for a plugin update first (git pull / marketplace update), then `/bootstrap --refresh-lock` to acknowledge the current version.
- `missing` → `/bootstrap --retroactive` (or `/bootstrap` for a fresh scaffold) — this is the one case where no lock exists to refresh.

**Dependencies:** Requires `${PLUGIN_ROOT}/scripts/lib/bootstrap-lock-freshness.mjs` (issue #186). Degrades gracefully when the helper is absent (pre-#186 plugin install) — skip with a note, do not fabricate findings.

---

### Probe: agent-frontmatter-invalid

**Activation:** `.claude/agents/*.md` files exist in the repo.

**Motivation:** Claude Code agent frontmatter has fragile YAML rules (tools as comma-string not array, description single-line not block-scalar, required fields per CLAUDE.md). Broken frontmatter causes silent "agents: Invalid input" validation failures at session start. Issue #189 (Epic #181 harness-retro promotion list #3).

**Detection Method:**

```bash
AGENTS_DIR="$(git rev-parse --show-toplevel)/.claude/agents"
[[ -d "$AGENTS_DIR" ]] || exit 0
node --input-type=module -e "
import { validateAgentFile } from '${PLUGIN_ROOT}/scripts/lib/agent-frontmatter.mjs';
import { readdirSync } from 'node:fs';
import { join } from 'node:path';
const dir = '${AGENTS_DIR}';
const files = readdirSync(dir).filter(f => f.endsWith('.md'));
let hasErrors = false;
for (const f of files) {
  const result = validateAgentFile(join(dir, f));
  if (!result.ok) {
    hasErrors = true;
    console.log('INVALID: ' + f);
    for (const e of result.errors) {
      console.log('  - ' + e.path + ' (' + e.rule + '): ' + e.message);
    }
  }
}
if (!hasErrors) console.log('OK: all agent files passed validation');
" 2>/dev/null
```

**Evidence Format:**

```
File: .claude/agents/<filename>.md
Issue: agent-frontmatter-invalid
Violations:
  - tools (no-json-array): tools must be a comma-separated string, not a JSON array
  - description (no-block-scalar): description must be inline, not a block scalar
  - color (enum): color must be one of "blue"|"cyan"|"green"|"yellow"|"magenta"|"red"
Recommendation: Run /bootstrap --retroactive to auto-surface violations, or manually fix per CLAUDE.md Agent Authoring Rules.
```

**Default Severity:** High — broken agents fail at runtime silently.

**Remediation:** Run `/bootstrap --retroactive` (validator auto-surfaces violations) or manually fix per CLAUDE.md Agent Authoring Rules.

**Dependencies:** Requires `${PLUGIN_ROOT}/scripts/lib/agent-frontmatter.mjs` (issue #189). Degrades gracefully when the helper is absent — skip with a note, do not fabricate findings.
