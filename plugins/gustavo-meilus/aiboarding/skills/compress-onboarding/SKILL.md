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
- **`ultra`** - telegraphic; every non-load-bearing word goes. Only for repos
  pressed against the 32 KiB Codex cap; confirm with the user before first use.

## Byte-preservation invariants (hard guarantees)
Compression must NEVER alter: fenced code blocks (including the fence lines),
inline backtick spans, shell commands, URLs, file paths, identifiers and symbol
names, quoted error strings, `<!-- aiboarding-* -->` markers, YAML frontmatter, and
table structure. If a protected span is wrong, fixing it is an *update*, not a
compression - route it through `update-agent-onboarding`.

While rewriting, keep commands/identifiers/paths/error strings backtick-quoted (add
backticks where the source lacks them - adding protection is allowed; removing it
is not). The checker treats backtick spans as protected.

## Auto-clarity exemptions
Never compress below full sentences, regardless of level:
- `Agent Guardrails` and `Escalation - Ask the User When` sections: cap at `lite`.
  A misread guardrail costs more than its tokens.
- Security warnings and destructive/irreversible-action instructions.
- Multi-step sequences where fragment order creates ambiguity ("migrate table drop
  column backup first" - unclear; keep explicit ordering words).

## Procedure
1. **Snapshot.** Copy the target file to a temp path (`before`).
2. **Compress** section by section at the resolved level, honoring the invariants
   and exemptions above.
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
   { "file": "AGENTS.md", "level": "full", "bytes_before": 8123, "bytes_after": 4310, "lines_before": 190, "lines_after": 121, "tokens_before_approx": 2031, "tokens_after_approx": 1078, "measured_at": "2026-07-02" }
   ```
   Report the saving to the user; since the file loads every session, note the
   per-session saving - never claim unlabeled exact token numbers without a real
   tokenizer.
6. **Size check.** Run `.aiboarding/tools/check-size-budget <file>`; if it still
   WARNs after `full`, suggest moving detail to `.claude/rules/` or nested
   `AGENTS.md` files rather than jumping to `ultra`.

## Writing into shared files
When compression output must land inside a file that also has user-owned content
(e.g. a hand-written `CLAUDE.md`), write only within the aiboarding marker fence
via `.aiboarding/tools/inject-fenced` - re-runs stay idempotent and uninstall stays
clean.
