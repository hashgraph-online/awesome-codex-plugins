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

The guard passes numeric-limit `Read` calls, missing/non-regular/binary files,
and commands containing pipes or redirects. Its Bash lexer recognizes a
conservative literal-command subset described below; unsupported syntax fails
open. Regression tests check both missed reads and false attribution. The
parser is not a full shell interpreter, and a passing test suite does not
establish that every possible shell command is classified correctly.

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
- Otherwise tokenize literal words and split on `;`, `&&` and newlines
  outside single/double quotes. Quoted and escaped spaces remain part of the
  same filename; concatenated literal fragments (`my" notes".md`) work too.
  Backslash-newline is deleted outside single quotes, including inside double
  quotes. Other quoted newlines remain literal filename bytes. A `#` at a word
  start begins a comment through the newline.
- Parsing completes before any segment is judged. Unmatched quotes, malformed
  separators, expansion syntax (`$VAR`, substitution, ANSI-C `$'...'`, unquoted globs), shell control
  syntax and directory-changing commands (`cd`, `pushd`, `popd`, including
  `builtin`/`command` wrappers) skip the whole call. Later segments are never
  attributed to the original `cwd` after a recognized directory change.
- Leading syntactic `VAR=value` assignments are removed; a quoted assignment
  word such as `"NAME=value"` is still a command word. An `AOP_WAIVE=...`
  prefix containing the policy id waives the whole call. The basename of the
  first remaining word must be `cat`, `head` or `tail`. Resolve that literal
  executable against the command cwd and PATH (including literal leading PATH
  assignments); missing or non-executable paths pass. Resolution never invokes
  the selected executable. An assignment-only segment followed by another
  nonempty segment (`PATH=/nonexistent; cat file`) skips the whole call because
  the assignment persists shell state; later segments must not reuse the hook
  environment. A trailing assignment alone does not hide an earlier read.
- On Darwin, compare executable identity (`-ef`, following symlinks) with
  `/bin/cat`, `/usr/bin/head` and `/usr/bin/tail`. The system `cat` rejects
  GNU-only `-A`, `-E`, `-T` (including combinations) and long flags; the system
  `head` rejects negative counts and quiet/verbose flags. Those forms pass
  because the native utility does not read the file. GNU executables named
  `cat`/`head`/`tail` retain the generic GNU forms below, even on Darwin.
- Unquoted leading `~/` expands against `HOME`; quoted/escaped tildes remain
  literal. Other files resolve against the input `cwd`; missing, non-regular
  and binary files are skipped. `--` ends flag parsing, including before an
  option-looking filename. `-` denotes stdin and is skipped.
- `cat`: effective = **sum** of resolved files' line counts; FIRE when over
  budget (the message names the largest file; `N` is the total). Known output
  formatting flags (`-n`, `-b`, `-s`, `-A`, `-e`, `-E`, `-t`, `-T`, `-u`,
  `-v`, their combinations and GNU long equivalents) do not bound the read.
- `head`: `-n N`, `-nN`, `-N`, `--lines=N`, `--lines N` (default 10).
  Positive counts, including `-n +N`, use `min(N, lines)` per file; GNU
  negative `-n -K` (all but the last K) uses `max(lines - K, 0)`. FIRE if any is over budget.
- `tail`: the same flag forms; negative counts use `min(K, lines)`;
  `-n +K` = `max(lines - K + 1, 0)`, with `+0` and `+1` both meaning the
  whole file. FIRE if any effective count is over budget.
- `--help`, `--version`, unknown flags, byte counts and follow modes skip the
  segment. Supported `head`/`tail` quiet/verbose formatting flags are accepted,
  except for the Darwin system `head` as described above. Invalid
  or missing numeric option values skip the segment.
- Decimal normalization removes leading zeroes before arithmetic. Budgets
  above `9223372036854775807` saturate at that value; command counts outside
  that range skip the segment because the utility may reject them. Huge
  positive values cannot wrap into tiny budgets or negative read indices.

### Always PASS (exit 0, zero output)

Any other `tool_name` (an `Edit` of a huge file is a write, not a read); an
empty or unparseable command; `cat` with no file; `git status`; `grep -n`,
`sed -n '1,400p'`, `awk`, `less`, `more` — bounded or paged consumers, silent
by design because they *are* the correct moves.

### Waiver, kill switch, budget

| Control | Effect |
|---|---|
| `AOP_READ_BUDGET_LINES=<n>` | the budget; default 350, and anything that is not a positive integer falls back to 350; larger than signed 64-bit values saturate as described above. Hook env only — an operator setting, never honored as a command prefix (that would be an uncounted self-relax) |
| `AOP_WAIVE=core.context:unbounded-read` | waive once — as hook env, or as a prefix on the Bash command itself (comma list; the id must be in it) |
| `AOP_WAIVER_FILE` line `core.context:unbounded-read <expiry-epoch>` | timed waiver; default file `${AGENTOPS_HOME:-$HOME/.agents/ao}/policy-waivers`, same semantics as the dispatcher; an expired line still fires |
| `AGENTOPS_HOOKS_DISABLED=1` | kill switch: exit 0, silent, no telemetry |

A waived call exits 0 with zero output and writes one telemetry line with
`decision: "waived"`, so waivers are counted — they are the countermetric.

### Fail OPEN

No `jq` on `PATH` → exit 0. Malformed JSON → exit 0, silent. Empty or unknown
tool → exit 0. Bash judging also passes without `awk` or `uname`. A guard
that cannot decide must never brick the tool call.
Telemetry failure never changes the exit decision.

### The message

First fire in a session (full):

```text
⛔ policy core.context:unbounded-read
<path> is <N> lines (budget <B>). An unbounded read puts every line into this context and re-sends it on every later turn.
→ Read a slice: Read(file_path, offset, limit) with limit ≤ <B>, or Bash: sed -n '1,<B>p' <path> / grep -n <pattern> <path>.
→ Or delegate the whole file to a cheap reader that returns line-referenced bullets and keeps the bytes out of this context:
    Agent tool: subagent_type "agentops:bulk-reader", prompt "<question>\nfiles: <path>"
    Workflow: agentops:bulk-read { question: "<question>", files: ["<path>"] }
    These names require the AgentOps plugin. Use bare names only when the runtime lists standalone definitions or links under those names.
Waive once: AOP_WAIVE=core.context:unbounded-read (hook env, or a prefix on the Bash command). Raise the budget: AOP_READ_BUDGET_LINES=<N> in the hook env (an operator setting, not a command prefix).
```

Later fires in the same session (short, still exit 2):

```text
⛔ policy core.context:unbounded-read: <path> is <N> lines (budget <B>) — slice it (offset+limit / sed -n) or delegate to agentops:bulk-reader (full reason shown earlier this session).
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
| `agents/bulk-reader.md` — subagent `agentops:bulk-reader` (`Read`/`Grep`/`Glob`/`Bash`, no `Write`/`Edit`, haiku) | line-referenced bullets (`path:line`, at most 40 unless the caller sets another cap), no prose |
| `workflows/bulk-read.js` — `agentops:bulk-read { question, files, root?, model?, maxBullets?, budgetLines? }` | one reader per file in parallel; `{question, files:[{file, bullets, lines_covered, complete, note?, error?}], bullets_total}` |
| `workflows/code-write.js` with subagent `agentops:code-writer` (`agents/code-writer.md`) — `agentops:code-write { items:[{key, spec, reference, target, check?}] }` | metadata-only realpath/stat preflight for batches, then sequential writers; bounded receipts (`written`, `lines`, `check_ok`, `summary`), no check output; a reference file is REQUIRED |

These invocation names require the AgentOps plugin. Bare names apply only to
standalone definitions or links when the runtime actually lists those names.
The plugin adds the prefix; source agent names and workflow `meta.name` stay bare.

Guard compatibility: the reader and writer prompts read in **slices** (`Read`
with `offset` + `limit ≤ budgetLines`), never an unbounded
`Read`/`cat`/`head`/`tail`. Readers start at offset 1 and continue through EOF;
the limit is per call, and the bullet cap does not limit coverage. Truncated
responses require smaller slices from the first unread line, not an EOF claim.
An early answer does not establish the final decision while lines remain unread.
So a delegate's own
reads pass this guard on a host where it is installed — the delegation is not
an exemption, it is a reader that obeys the same rule. A follow-up question
about the same file costs another delegation, not another copy of the file in
this context.

Malformed worker replies produce explicit errors. Missing reader receipts leave coverage unknown (`lines_covered: null`); missing writer receipts leave write and check state unknown, never proving that no file changed. Metadata preflight and target-only edits still require worker compliance; the Workflow surface is not a filesystem sandbox.

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
a uniquely named timestamped `.bak` before changing existing settings, and adds
(idempotently, matching command type and matcher) one PreToolUse `Read|Bash` matcher:

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

Five bats files round-trip the real PreToolUse JSON (built with `jq -nc`,
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
- `tests/scripts/read-budget-guard-regression.bats` — independent-review
  reproductions for ANSI-C quoted prose, cwd collisions, negative-head counts,
  help/unknown flags, literal spaced paths, quoted continuations, `--`, integer
  overflow, quoted tildes, malformed syntax and shell control flow. Every case
  captures stdout and stderr separately. The legacy negative-head expectation
  was corrected from 400 to 395 for GNU `head -n -5` on a 400-line file; the legacy
  silent expectation for a 400-line spaced filename was corrected to denial.
  Both changes restore the effective-read contract; a separate small spaced
  file with a large sibling checks that paths are not misattributed.
- `tests/scripts/read-budget-guard-utility.bats` — compare actual utility exit
  status and stdout line counts with guard decisions. Darwin system rejects
  remain silent; positive signed head reads block; GNU formatting and negative
  counts remain guarded. GNU-specific tests use the installed GNU executable
  through a command named `cat`/`head`, and explicitly skip when GNU is absent.
  Darwin-only tests explicitly skip on other hosts. The earlier negative-head
  tests use this same distinction instead of claiming BSD rejected input reads.
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
     tests/scripts/read-budget-guard-regression.bats \
     tests/scripts/read-budget-guard-telemetry.bats \
     tests/scripts/read-budget-guard-utility.bats \
     tests/scripts/install-read-budget-guard.bats
```

## Known limitations

The parser deliberately skips unsupported shapes instead of guessing. Known
false-negative shapes:

- **Pipes and redirects** pass wholesale (`cat big.txt | cat` included) — the
  `|` / `<` / `>` check does not inspect the consumer.
- **Expansions and shell grammar** (`cat *.log`, `cat "$f"`, backticks,
  ANSI-C quotes, conditionals, subshells) skip the whole call. The hook never
  evaluates shell input. Literal quoted/escaped special characters are
  preserved, and unquoted leading `~/` is the one expansion mirrored.
- **Command prefixes** (`sudo cat`, `time cat`, `env X=1 cat`) are silent:
  only a segment whose command word is `cat`, `head` or `tail` is judged.
- **Persistent assignments**: an assignment-only segment before a later
  nonempty segment skips the whole call; persistent shell state is not tracked.
  An assignment prefix attached to a command remains supported.
- **Directory changes and evaluation builtins** (`cd`, `pushd`, `popd`,
  `builtin`, `command`, `source`, `eval`, `exec`) skip the whole call. Shell
  functions, aliases and the exit status of earlier commands are not resolved;
  this guard cannot establish runtime reachability or arbitrary shell state.
- **`sed`, `awk`, `less`, `more`, `grep`, `xargs`, `sh -c`** are silent by
  design; only `cat`, `head` and `tail` are inspected. `head -c` and `tail -f`
  skip their segment.
- **Other utility implementations**: executable names use the generic flag
  set unless they match the Darwin system identities above. Arbitrary custom
  replacements and their option contracts are not inspected or executed.
- **Lines, not bytes**: `wc -l` is the predicate, so a one-line multi-megabyte
  file passes.
- **A subagent's own reads run under the same hook.** A `bulk-reader` that
  issues an unbounded `Read` is blocked like anyone else — which is why the
  shipped reader prompt slices. A hand-written reader that does not slice is
  denied, not exempted.
