---
name: compress-onboarding
description: Use to compress any agent-instruction file (AGENTS.md, CLAUDE.md, .claude/rules/*.md, legacy AIBOARDING.md) into terse, high-signal prose without altering commands, code, URLs, or paths. Standalone compression engine with levels (off/lite/full/ultra), byte-preservation verification, and token receipts. Also invoked by the create/update onboarding skills.
---

# Compressing onboarding files

Instruction files load **every session**, so every saved token compounds. Compress
prose aggressively while never touching the technical payload - and never trading
away clarity where ambiguity is dangerous.

**Announce at start:** "Using compress-onboarding on <file> at level <level>."

**Usage:** `compress-onboarding <file> [--level off|lite|full|ultra]`
Default file: the repo's `AGENTS.md`. Works under any SKILL.md-compatible runtime.

## Levels (sticky per repo)
Resolve the level from `--level` if given, else `.aiboarding/config.json:
compression_level`, else `full`. When `--level` is given, persist it back to
`config.json` - the level is a per-repo decision, not per-run.

- **`off`** - no rewriting. Still run the size report (step 5) so bloat is visible.
- **`lite`** - remove filler, pleasantries, hedging, and restatement. Full sentences
  kept. ("In order to build the project, you should run…" → "To build, run…")
- **`full`** (default) - additionally drop articles, compress to fragments and
  short synonyms, allow `X → Y` notation. ("The dev server can be started with
  `npm run dev`" → "Dev server: `npm run dev`.")
- **`ultra`** - telegraphic; every non-load-bearing word goes. Use only when the
  effective instruction-chain audit needs it; confirm with the user before first use.

## Byte-preservation invariants (hard guarantees)
Compression must NEVER alter: fenced code blocks (including the fence lines),
inline backtick spans, shell commands, URLs, file paths, identifiers and symbol
names, quoted error strings, `<!-- aiboarding-* -->` markers, YAML frontmatter, and
table structure. If a protected span is wrong, fixing it is an *update*, not a
compression - route it through `update-agent-onboarding`.

While rewriting, keep commands/identifiers/paths/error strings backtick-quoted (add
backticks where the source lacks them - adding protection is allowed; removing it
is not). The checker treats backtick spans as protected.

## High-consequence preservation
Before rewriting, classify complete high-consequence regions. Preserve every
identified region verbatim, byte-for-byte, by default. `full` or `ultra` never
authorize rewriting one.

Always classify complete `Agent Guardrails` and `Escalation - Ask the User When`
sections. Outside those headings, classify smallest complete paragraph, list item,
warning, or ordered procedure needed to retain context when it governs security,
authorization, approval or escalation, destructive or irreversible actions, or
required ordering or prerequisites for destructive or migration work. Record each
region's source section or line location and category. Do not classify ordinary
project purpose, architecture, domain, or routine descriptive prose solely because
it is important or technical; compress that prose at selected level.

If user asks to rewrite identified high-consequence content, name affected regions
and obtain explicit opt-in for selected regions in current operation. Level choice
and final diff approval do not count. Do not persist consent. Rewrite only selected
regions, retain unselected regions verbatim, preserve all protected spans, and keep
behavioral force unambiguous. Then show final diff and obtain normal approval.

## Procedure
1. **Snapshot.** Copy the target file to a temp path (`before`).
2. **Classify and compress.** Identify high-consequence regions, report their
   locations and categories, and copy them verbatim unless current-operation,
   per-region explicit opt-in permits rewriting. Compress remaining prose at
   resolved level.
3. **Verify.** Run `.aiboarding/tools/check-preservation <before> <after>` (fall
   back to the plugin's `templates/tools/check-preservation` if not installed).
   Fix every reported span and re-run until clean. Never hand-wave this step.
4. **Approval gate.** Show the user a diff of the compressed file against the
   original. Write only after approval.
5. **Receipt.** Measure before/after: exact bytes and lines always; token counts
   with a real tokenizer if one is available in the environment (e.g. Python
   `tiktoken`), otherwise `tokens_approx = bytes / 4`, explicitly labeled
   approximate. Append to `.aiboarding/state.json:receipts` (one object per line,
   keeping the file hook-readable):
   ```json
   { "file": "AGENTS.md", "level": "full", "bytes_before": 8123, "bytes_after": 4310, "lines_before": 190, "lines_after": 121, "tokens_before_approx": 2031, "tokens_after_approx": 1078, "high_consequence_regions": [{ "location": "Agent Guardrails", "category": "guardrails", "outcome": "preserved", "explicit_opt_in": false }], "measured_at": "2026-07-02" }
   ```
   `high_consequence_regions` is optional for backward compatibility. Each entry
   records location, category, outcome (`preserved` or `rewritten`), and explicit
   opt-in status; never copy instruction text. Include `[]` when classification
   verified no such regions. Report same evidence to user.
   Report the saving to the user; since the file loads every session, note the
   per-session saving - never claim unlabeled exact token numbers without a real
   tokenizer.
   Also write a compact `compression-verification` record with the subject, level,
   measurements, preservation and size outcomes through `write-evidence`. Keep the
   legacy receipt unchanged; a failed preservation or size check is recorded when
   possible and never authorizes a sync-pointer advance.
6. **Size check.** Run `.aiboarding/tools/check-size-budget <file>` as a local
   sensor. It does not prove chain safety; run
   `.aiboarding/tools/audit-onboarding-evidence <repo-root>` before claiming an
   effective Codex chain fits. If local guidance still WARNs after `full`, suggest
   moving detail to `.claude/rules/` or nested `AGENTS.md` files rather than jumping
   to `ultra`.

## Writing into shared files
When compression output must land inside a file that also has user-owned content
(e.g. a hand-written `CLAUDE.md`), write only within the aiboarding marker fence
via `.aiboarding/tools/inject-fenced` - re-runs stay idempotent and uninstall stays
clean.
