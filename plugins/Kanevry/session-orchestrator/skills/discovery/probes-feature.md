> See probes-intro.md for confidence scoring reference.

## Category: `feature`

### Probe: intent-drift

**Activation:** Documentation exists that makes behavioral or security claims (`README*`, `docs/architecture*`, or `docs/**` permission/authz files present).

**Detection Method:**

1. Extract claim sentences from documentation files:
```bash
# Grep for claim-marker sentences in docs (behavior/constraint assertions)
Grep pattern: \b(MUST|always|never|required|enforced|blocks|validates)\b
  --glob "README*" --glob "docs/architecture*" --glob "docs/**/*permission*"
  --glob "docs/**/*authz*" --glob "docs/**/*auth*" --glob "!**/CHANGELOG*"
  --glob "!**/node_modules/**"
```

2. For each matched sentence, extract the subject/verb phrase immediately around the claim marker (e.g. "requires authentication", "never exposes the service_role key", "blocks unauthenticated requests") and derive candidate code-enforcement tokens from it (e.g. `requireAuth`, `authorize`, `validate`, `guard`, `enforce`, or an identifier named explicitly in the sentence).

3. Direction A — `documented-but-unenforced`: grep source for the derived enforcement token(s):
```bash
# Grep source for the enforcement token(s) derived from step 2's claim keyword
Grep pattern: <derived_token>\s*\(
  --glob "*.{ts,tsx,js,jsx,mjs,py,go,rs}" --glob "!**/test/**" --glob "!**/tests/**"
  --glob "!**/fixtures/**" --glob "!**/mocks/**" --glob "!*.test.*" --glob "!*.spec.*"
```
Zero matches across the source tree => flag `documented-but-unenforced`. Anchor `file_path`/`line_number` to the DOC line found in step 1 — never to an absent code location — and set `matched_text` to the exact doc sentence.

4. Direction B — `undocumented-but-enforced`: grep source directly for known enforcement call patterns, independent of any doc claim:
```bash
# Grep source for enforcement calls that constitute a de-facto contract
Grep pattern: (requireAuth|checkPermission|assertPermission|authorize|validateInput|enforce\w*)\s*\(
  --glob "*.{ts,tsx,js,jsx,mjs}" --glob "!**/test/**" --glob "!**/tests/**"
  --glob "!**/fixtures/**" --glob "!**/mocks/**"
```
For each match, search the step 1 doc-claim corpus for the same identifier or an equivalent phrase. Zero matches => flag `undocumented-but-enforced`. Anchor `file_path`/`line_number` to the CODE line and set `matched_text` to the code line containing the enforcement call.

**Evidence Format:**
```
Direction: documented-but-unenforced | undocumented-but-enforced
File: <path> Line: <n>
Matched Text: <doc claim sentence | code enforcement line>
Claim Keyword: <matched claim-marker or enforcement token>
Counterpart: <doc_file:line or code_file:line of the missing counterpart, or NONE>
```

**Default Severity:** High for security/permission claims (auth, permission, access-control, secret-handling keywords); Medium for general feature/behavior claims.

---

### Probe: stubbed-dead-feature

**Activation:** Any project with source files exposing routes, handlers, or feature-flagged code paths.

**Detection Method:**

1. Not-implemented stubs:
```bash
# Grep for explicit not-implemented throws
Grep pattern: throw\s+.*[Nn]ot\s+[Ii]mplemented
  --glob "*.{ts,tsx,js,jsx,mjs,py,go,rs}" --glob "!**/test/**" --glob "!**/tests/**"
  --glob "!**/fixtures/**" --glob "!**/mocks/**" --glob "!*.test.*" --glob "!*.spec.*"
```
```bash
# Grep for TODO-tagged stub returns (placeholder return adjacent to a TODO/implement note)
Grep pattern: (TODO.*(stub|placeholder|implement)|return\s+(null|undefined|\[\]|\{\})\s*;?\s*//\s*TODO)
  --glob "*.{ts,tsx,js,jsx,mjs,py,go,rs}" --glob "!**/test/**" --glob "!**/tests/**"
  --glob "!**/fixtures/**" --glob "!**/mocks/**"
```

2. Permanently-off feature flags:
```bash
# Grep for hardcoded-false flag/config keys
Grep pattern: (enabled|feature\w*)\s*[:=]\s*false
  --glob "*.{ts,tsx,js,jsx,mjs,json,yaml,yml}" --glob "!**/test/**" --glob "!**/tests/**"
  --glob "!**/fixtures/**" --glob "!**/mocks/**"
```
For each matched flag/config key name, verify it is never toggled on elsewhere in the codebase:
```bash
# Zero matches confirms the flag is permanently off; any match means it is still toggleable -- do not flag
Grep pattern: <flag_name>\s*[:=]\s*true
  --glob "*.{ts,tsx,js,jsx,mjs,json,yaml,yml}"
```

3. Commented-out routes/handlers:
```bash
# Grep for commented-out route/handler registrations
Grep pattern: ^\s*(//|#).*(route|router\.|app\.(get|post|put|delete))
  --glob "*.{ts,tsx,js,jsx,mjs,py}" --glob "!**/test/**" --glob "!**/tests/**"
  --glob "!**/fixtures/**" --glob "!**/mocks/**"
```

**Evidence Format:**
```
Type: not-implemented-stub | permanently-off-flag | commented-out-route
File: <path> Line: <n>
Matched Text: <matched_text>
Export Status: exported/public | internal
```

**Default Severity:** Medium; High when the stub, flag, or commented-out route sits on an exported/public path.

---

### Probe: feature-request-cluster

**Activation:** A VCS platform is configured (`vcs: gitlab` or `vcs: github` in Session Config) — the probe queries the issue tracker directly rather than the source tree, so it activates whenever a VCS remote is resolvable.

**Detection Method:**

1. List open feature/enhancement issues via the VCS CLI (syntax reference: `skills/gitlab-ops/SKILL.md` § "Common CLI Commands" — do not duplicate CLI flags here beyond what's needed to name the call):
```bash
# GitLab
glab issue list --label "feature" --per-page 100
glab issue list --label "enhancement" --per-page 100
# GitHub
gh issue list --label "feature" --limit 100
gh issue list --label "enhancement" --limit 100
```

2. Extract theme keywords from each issue's title (and first paragraph of body where available): lowercase, strip stop-words, tokenize on non-alphanumeric boundaries. Group issues that share two or more significant keywords (e.g. "export", "csv", "invoice") into a candidate cluster.

3. For each candidate cluster with 3 or more issues, check whether ANY member issue is already linked to an epic (`epic` label, a GitLab Epic relationship, or an in-body reference such as `part of #<epic-iid>` / `Epic: #<epic-iid>`):
```bash
# GitLab -- inspect labels + description for epic linkage
glab issue view <IID>
  Grep pattern: (^Labels:.*\bepic\b|part of #|Epic:\s*#)
# GitHub -- same check against issue body/labels
gh issue view <NUMBER>
  Grep pattern: (^labels:.*\bepic\b|part of #|Epic:\s*#)
```

4. The largest cluster (by issue count) with ZERO epic-linked members is the finding. Ties are broken by the lowest minimum issue number (the oldest cluster wins).

**Evidence Format:**
```
Cluster Theme: <shared keyword(s)>
Location: <comma-separated issue IDs, e.g. #142, #156, #171 -- an issue-ID set, not a file:line>
Cluster Size: <n>
Sample Titles: <up to 3 issue titles as evidence>
verification_method: vcs-issue
```

**Default Severity:** Medium; High when cluster size >= 5 (a recurring, unaddressed theme at that size signals systemic backlog drift).

---

**Labels for auto-created issues:** `type:discovery`, `area:skills`, `priority:high` (High/Critical severity) or `priority:medium` (Medium severity), `status:ready`.
