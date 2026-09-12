# Read-Budget Guard (opt-in)

A PreToolUse `Read|Bash` guard that blocks an **unbounded read of a file over
the line budget** — a `Read` with no `limit`, or a `cat` / `head` / `tail`
whose effective line count exceeds `AOP_READ_BUDGET_LINES` (default 350) — and
names the two correct moves: read a slice, or delegate the file to a cheap
reader that returns line-referenced bullets. AgentOps is hookless by default —
this guard ships **inert**; you activate it with the opt-in installer.

## Why it exists — the rule CLAUDE.md could not enforce

Spotify open-sourced its internal Claude Code setup and reports (its claim, not
re-measured here) a ~90% token cut. The part that transfers is not the number
but the finding behind it: v1 put "never read a large file whole" in CLAUDE.md
and the rule was ignored — advisory context, delta≈0, the same result AgentOps
measured in #511. The rule only held once it moved into a PreToolUse hook that
refuses the tool call and points at the bounded alternatives.

The cost it guards is compounding, not one-shot. An unbounded read of an N-line
file puts N lines into this context **and re-sends them on every later turn**
of the session. A 2,000-line read on turn 3 is paid again on turns 4 through
40. A bounded slice costs its slice once; a delegated read costs a few bullets,
because the file bytes never enter the caller's context at all.

## The predicate — a LOOKUP, so a standalone guard

The policy dispatcher registry (`policies/policies.json`) only lets a
`predicate_class: pure` regex over the raw command or `file_path` `deny` (the #511
anti-lesson). "Is this file over 350 lines?" is not a regex: it is a
**lookup** — one deterministic local check, `wc -l` on the exact argument, no
repo state, no history, no model. So this guard ships as a standalone opt-in
recipe next to [INSTALLED-SKILL-EDIT-GUARD.md](INSTALLED-SKILL-EDIT-GUARD.md)
and never as a registry policy, even though it borrows the registry's id form
(`core.context:unbounded-read`), its waiver mechanics and its telemetry line.

No false-positive surface by construction for the shapes it judges: a `Read`
with a numeric `limit` never fires (a bounded slice is the correct move,
whatever `offset` says); a file at or below budget never fires; a path that is
missing, a directory or binary never fires; a pipe or redirect never fires;
quoted text that merely mentions `cat` (a commit message, an `echo`) is skipped
by the quote rule below. The only thing that fires is a whole-file read that
would exceed the budget — and that is the mistake.

## Deny, not route

The installed-skill-edit guard routes because a wrong edit is recoverable. An
over-budget read is not: once the bytes land in context, nothing un-reads them.
So this guard **denies** (exit 2 + stderr) and **every attempt blocks** — it
never self-relaxes, because the second unbounded read costs exactly what the
first would have. What is once-per-session is the *explanation*: the first fire
in a session prints the full message; later fires print one short line (still
exit 2). The message names the two correct moves and nothing else.

Context-budget doctrine still applies: silent on every happy path (exit 0, zero
stdout, zero stderr — a stray stdout line on an exit-0 PreToolUse path is parsed
as JSON and breaks the tool call), block via exit 2 + stderr only, fail OPEN.

## The contract

Ships as `skills/cc-hooks/hooks/read-budget-guard.sh` (inert until the opt-in
installer wires it; `set -uo pipefail`, no `-e`). It reads the real PreToolUse
JSON on stdin (`{tool_name, tool_input, session_id, cwd}`) with `jq`; a missing
`session_id` is `nosession`. Policy id and `token_class`:
`core.context:unbounded-read`.

### `Read`

- `tool_input.limit` is a number → **PASS**. `offset` alone does not bound a
  read and does not pass.
- Otherwise resolve `tool_input.file_path` (relative → against the JSON `cwd`,
  else `$PWD`). Not an existing regular readable file, or binary (a NUL byte in
  the first 8192 bytes) → **PASS**.
- `lines = wc -l < file`; `lines > budget` → **FIRE**.

### `Bash`

- The command contains any of `|`, `<`, `>` → **PASS**. A pipe feeds a bounded
  consumer, a redirect feeds a file sink; neither lands whole in context. Out
  of scope by design, not by accident.
- Otherwise split on `;`, `&&` and newlines into segments — a quote-aware
  split: a separator counts only outside single or double quotes (backslash
  escapes honored outside single quotes), so quoted text that mentions `cat`
  stays inside its own command's segment and is never judged, a `# comment`
  runs to end of line and is dropped before splitting, and a backslash-newline
  is deleted exactly as the shell does (`cat big\` + newline + `.txt` is
  `cat big.txt`). `git commit -m "fix; cat big.txt; now routes"` never
  fires. Per segment: whitespace-tokenize; a word whose quotes are not a
  matched pair around the whole word (or around a `NAME=value` value) — a
  quoted path with a space, `foo"bar"`, `-n"500"` — is unparseable and skips
  the segment; strip leading `VAR=value` assignments (an
  `AOP_WAIVE=...` prefix whose list contains the id waives the WHOLE call — see
  below). The command word is the basename of the first remaining token and
  must be `cat`, `head` or `tail`; any other command skips the segment.
- Per remaining token: strip one layer of surrounding single or double quotes.
  A token starting with `$` or containing a backtick, `*`, `?` or `[` is
  unresolvable and is skipped. Flags start with `-`. Files are the non-flag
  tokens, resolved against `cwd`; missing, non-regular and binary files are
  skipped.
- `cat`: effective = **sum** of the resolved files' line counts → FIRE if over
  budget (the message names the largest file; `N` is the total).
- `head`: `-n N`, `-nN`, `-N`, `--lines=N`, `--lines N` (default 10). A
  negative count (`-n -K`, "all but the last K") makes effective = the file's
  lines. Any `-c` / `--bytes` form skips the segment. Effective =
  `min(N, lines)` per file → FIRE if any is over budget.
- `tail`: same flag forms; `-n +K` → effective = `lines - K + 1` (min 0);
  `-f` / `--follow` skips the segment → FIRE if any effective is over budget.

### Always PASS (exit 0, zero output)

Any other `tool_name` (an `Edit` of a huge file is a write, not a read); an
empty or unparseable command; `cat` with no file; `git status`; `grep -n`,
`sed -n '1,400p'`, `awk`, `less`, `more` — bounded or paged consumers, silent
by design because they *are* the correct moves.

### Waiver, kill switch, budget

| Control | Effect |
|---|---|
| `AOP_READ_BUDGET_LINES=<n>` | the budget; default 350, and anything that is not a positive integer falls back to 350. Hook env only — an operator setting, never honored as a command prefix (that would be an uncounted self-relax) |
| `AOP_WAIVE=core.context:unbounded-read` | waive once — as hook env, or as a prefix on the Bash command itself (comma list; the id must be in it) |
| `AOP_WAIVER_FILE` line `core.context:unbounded-read <expiry-epoch>` | timed waiver; default file `${AGENTOPS_HOME:-$HOME/.agents/ao}/policy-waivers`, same semantics as the dispatcher; an expired line still fires |
| `AGENTOPS_HOOKS_DISABLED=1` | kill switch: exit 0, silent, no telemetry |

A waived call exits 0 with zero output and writes one telemetry line with
`decision: "waived"`, so waivers are counted — they are the countermetric.

### Fail OPEN

No `jq` on `PATH` → exit 0. Malformed JSON → exit 0, silent. Empty or unknown
tool → exit 0. A guard that cannot decide must never brick the tool call.
Telemetry failure never changes the exit decision.

### The message

First fire in a session (full):

```text
⛔ policy core.context:unbounded-read
<path> is <N> lines (budget <B>). An unbounded read puts every line into this context and re-sends it on every later turn.
→ Read a slice: Read(file_path, offset, limit) with limit ≤ <B>, or Bash: sed -n '1,<B>p' <path> / grep -n <pattern> <path>.
→ Or delegate the whole file to a cheap reader that returns line-referenced bullets and keeps the bytes out of this context:
    Agent tool: subagent_type "bulk-reader", prompt "<question>\nfiles: <path>"
    Workflow: bulk-read { question: "<question>", files: ["<path>"] }
Waive once: AOP_WAIVE=core.context:unbounded-read (hook env, or a prefix on the Bash command). Raise the budget: AOP_READ_BUDGET_LINES=<N> in the hook env (an operator setting, not a command prefix).
```

Later fires in the same session (short, still exit 2):

```text
⛔ policy core.context:unbounded-read: <path> is <N> lines (budget <B>) — slice it (offset+limit / sed -n) or delegate to bulk-reader (full reason shown earlier this session).
```

The per-session sentinel lives under `${TMPDIR:-/tmp}/aop-read-budget-guard/`
(one file per `session_id`, `/` replaced by `_`).

### Telemetry

Exactly one JSONL line per FIRE and per WAIVED call — none on pass, disabled or
fail-open — appended to
`${AGENTOPS_GUARDRAIL_TELEMETRY:-${AGENTOPS_HOME:-$HOME/.agents/ao}/guardrail-telemetry.jsonl}`:

```json
{"ts":"2026-09-12T10:00:00Z","session":"<session_id>","token_class":"core.context:unbounded-read","path_sha256":"<64-hex>","mode":"deny","decision":"deny","tool":"Read","lines":412,"budget":350}
```

`path_sha256` is the SHA-256 of the **resolved** offending path — never the raw
path, never the command. `lines` and `budget` are JSON numbers. No hasher
(`sha256sum` / `shasum -a 256` / `openssl dgst -sha256`) → no line rather than
a raw path. Methodology and the pre-registered KEEP/CUT rule:
[GUARDRAIL-VALUE-PROOF.md](GUARDRAIL-VALUE-PROOF.md).

## The delegation pairing

The guard's second arrow points at the delegation layer; without it the guard
only says "no". Three bounded, one-shot, cheap-model delegations ship next to
it — Claude Code plugin agents and Workflow-tool conveyors; the caller sees
bullets or a receipt, never bytes, and nothing is kept between calls:

| Piece | What the caller gets |
|---|---|
| `agents/bulk-reader.md` — subagent `bulk-reader` (`Read`/`Grep`/`Glob`/`Bash`, no `Write`/`Edit`, haiku) | line-referenced bullets (`path:line`, at most 40 unless the caller sets another cap), no prose |
| `workflows/bulk-read.js` — `bulk-read { question, files, root?, model?, maxBullets?, budgetLines? }` | one reader per file in parallel; `{question, files:[{file, bullets, lines_covered, complete, note?, error?}], bullets_total}` |
| `workflows/code-write.js` with `agents/code-writer.md` — `code-write { items:[{key, spec, reference, target, check?}] }` | a receipt per item (`written`, `lines`, `check_ok`, `summary`); the caller never reads the file back; a reference file is REQUIRED |

Guard compatibility: the reader and writer prompts read in **slices** (`Read`
with `offset` + `limit ≤ budgetLines`, advancing until a slice comes back
short), never an unbounded `Read`/`cat`/`head`/`tail`. So a delegate's own
reads pass this guard on a host where it is installed — the delegation is not
an exemption, it is a reader that obeys the same rule. A follow-up question
about the same file costs another delegation, not another copy of the file in
this context.

A receipt or a bullet list is a runtime fact, not validation. Whatever a writer
lands still gets fresh, author-distinct judgment like any other change. Pattern
and doctrine in AgentOps terms:
[context-budget delegation](../../agent-native/references/context-budget-delegation.md);
workflow install and args: `workflows/README.md` in the repository checkout.

## Opt-in install

```bash
# user scope (~/.claude/settings.json) — the default
scripts/install-read-budget-guard.sh

# project scope (.claude/settings.json)
scripts/install-read-budget-guard.sh --project

# explicit target
SETTINGS=/path/to/settings.json scripts/install-read-budget-guard.sh
```

The installer copies the guard to `~/.claude/hooks/read-budget-guard.sh`, takes
a timestamped `.bak` of the settings file before mutating it, and adds
(idempotently) one PreToolUse `Read|Bash` matcher:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read|Bash",
        "hooks": [
          { "type": "command", "command": "~/.claude/hooks/read-budget-guard.sh" }
        ]
      }
    ]
  }
}
```

Requires `jq` on `PATH`. The plugin manifest `hooks/hooks.json` is not touched:
nothing wires this guard automatically, on any install path. Uninstall is the
line the installer prints: remove the matcher, then `rm` the copied script.

## Test it

Three bats files round-trip the real PreToolUse JSON (built with `jq -nc`,
never hand-written strings) under an isolated `TMPDIR` and `HOME`, with
`AGENTOPS_GUARDRAIL_TELEMETRY` pointed into `TMPDIR`:

- `tests/scripts/read-budget-guard.bats` — **FIRE** (exit 2, stderr names the
  policy id): an unbounded `Read` of a 400-line file, `Read` with `offset`
  only, `cat big.txt`, `cat -n big.txt`, `head -n 500` / `-500` /
  `--lines=500`, `tail -n 400`, `tail -n +5`, `cat a.txt b.txt` (200 + 200), a
  relative path resolved through the JSON `cwd`, a second fire in the same
  session (short line, still exit 2), the first fire's output contains
  `bulk-reader`. **SILENT** (exit 0, zero output): `Read` with `limit 100`, a
  100-line file, a NUL-bearing binary with 400 newlines, a missing path, a
  directory, `cat big.txt | head -20`, `cat big.txt > out.txt`, `head big.txt`,
  `head -n 50`, `tail -n 20`, `grep -n`, `sed -n '1,400p'`, `cat small.txt`,
  `git status`, bare `cat`, `cd sub && cat big.txt`, an `Edit` of a big file.
  **WAIVERS**: env, command prefix, waiver file (future expiry passes, expired
  still fires), `AGENTOPS_HOOKS_DISABLED=1`, `AOP_READ_BUDGET_LINES=1000`.
  **FAIL-OPEN**: malformed JSON `{`, no `jq` on `PATH`.
- `tests/scripts/read-budget-guard-telemetry.bats` — one line per fire; valid
  JSON with every field; `lines` and `budget` are numbers; `path_sha256` is 64
  hex and equals the hash of the resolved path; the raw path and the raw
  command never appear; nothing on the happy path; `waived` on a waiver; two
  lines for two fires in one session; nothing when disabled.
- `tests/scripts/install-read-budget-guard.bats` — mode 755; exactly one
  `Read|Bash` matcher whose command is the installed path; idempotent re-run;
  `--project` writes `.claude/settings.json` in the cwd; a `.bak` when settings
  pre-existed; the installed file byte-equals the repo source.

```bash
bats tests/scripts/read-budget-guard.bats \
     tests/scripts/read-budget-guard-telemetry.bats \
     tests/scripts/install-read-budget-guard.bats
```

## Known limitations

Every gap errs toward silence: a missed case is one un-guarded read, never a
broken tool call. Known false-negative shapes:

- **Pipes and redirects** pass wholesale (`cat big.txt | cat` included) — the
  `|` / `<` / `>` check does not inspect the consumer.
- **Globs and variables** (`cat *.log`, `cat "$f"`, backticks) are
  unresolvable tokens and are skipped, not expanded. A leading `~/` is the one
  expansion mirrored (against `HOME`).
- **Command prefixes** (`sudo cat`, `time cat`, `env X=1 cat`) are silent:
  only a segment whose first word is `cat`, `head` or `tail` is judged.
- **Quoted paths with spaces** (`cat "my notes.md"`) tokenize on whitespace
  into words whose quotes are not a matched pair → the segment is skipped,
  silent. The same rule silences `-n"500"` and `foo"bar"` forms; a whole
  quoted word or a quoted `NAME=`/`--opt=` value (`cat "big.txt"`,
  `head -n "500"`, `head --lines="500"`, `LC_ALL="C" cat`) is judged.
- **`cd`-chained segments** (`cd sub && cat big.txt`) resolve against the
  original `cwd`, not `sub` → not found → silent (a bats-documented gap).
- **`sed`, `awk`, `less`, `more`, `grep`, `xargs`, `sh -c`** are silent by
  design; only `cat`, `head` and `tail` are inspected. `head -c` and `tail -f`
  skip their segment.
- **Lines, not bytes**: `wc -l` is the predicate, so a one-line multi-megabyte
  file passes.
- **A subagent's own reads run under the same hook.** A `bulk-reader` that
  issues an unbounded `Read` is blocked like anyone else — which is why the
  shipped reader prompt slices. A hand-written reader that does not slice is
  denied, not exempted.
