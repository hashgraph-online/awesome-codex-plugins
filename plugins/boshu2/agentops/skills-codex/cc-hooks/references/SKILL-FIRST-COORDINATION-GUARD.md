# Skill-First Coordination Guard (opt-in recipe)

A copy-paste PreToolUse hook pair that nudges an agent to **load the
coordination skill before hand-rolling the `am` / `atm` / `ntm` /
`tmux send-keys` CLI surfaces**. AgentOps 3.0 is hookless by design — nothing
here auto-installs. This is documentation plus a recipe you opt into per host.

## Why it exists

The dominant multi-agent failure mode is an agent reverse-engineering the
coordination CLI (Agent Mail, ATM/NTM, raw `tmux send-keys`) from first
principles instead of loading the skill that already carries the command surface
*and* the doctrine. The skill knows the reservation protocol, the inbox model,
the liveness truth stack; the hand-rolled invocation does not. This guard fires
one loud nudge the first time it sees a bare coordination command in a session,
then self-relaxes the moment the relevant skill loads.

## Context-budget doctrine for hooks

Hooks are the most powerful enforcement available — mechanical, can't be
reasoned past — but they **pollute context**, so use them sparingly:

- A hook must be **SILENT on the happy path**: exit 0, no stdout, no stderr.
- Fire **only on a real violation**, ideally **once per session**,
  sentinel-gated so it never repeats.
- Prefer **PreToolUse violation-guards** over `UserPromptSubmit` /
  `SessionStart` per-turn injectors — the latter pay context on every turn
  whether or not anything is wrong.
- **NEVER emit stray stdout on an exit-0 PreToolUse path** — stdout there is
  parsed as JSON and a stray line breaks the tool call. Block via **exit 2 +
  stderr** instead.

This recipe is built to that doctrine: silent on every non-coordination command,
one stderr message gated by a per-session sentinel file, self-relaxing after the
skill loads.

## The matching defect this recipe fixes

A naive line-based match —
`grep -qE '(^|[;&|]|&&|\|\|)[[:space:]]*(am|atm|ntm)([[:space:]]|$)'` —
**over-matches**: `grep` is line-oriented, so `^` matches *every* heredoc-body
line, and a quoted `|ntm` inside an argument reads as a top-level `|` delimiter.
A `br create "t" --body "...mentions am/atm/ntm and agent-mail|ntm|using-atm..."`
would falsely fire even though no coordination command is being *run*.

The fix below matches `am`/`atm`/`ntm`/`tmux send-keys` **only as an actual
command head** — never inside quoted strings, heredoc bodies, or prose. It
strips quoted spans (multiline-aware) and heredoc bodies, splits the remainder
on top-level separators (`;` `&` `|` newline), and tests only the head token of
each segment (skipping leading `VAR=val` assignments).

## Script 1 — the guard (`skill-first-coord-guard.sh`)

PreToolUse / Bash. Fires once per session on a real hand-roll; silent otherwise.

```bash
#!/usr/bin/env bash
# skill-first-coord-guard (PreToolUse / Bash)
# Nudge to load the agent-mail / ntm (ATM) skill BEFORE hand-rolling the
# am / atm / ntm / tmux-send-keys CLI surfaces.
#
# Context-budget discipline (hooks are powerful but pollute context — use sparingly):
#   - SILENT on the happy path (non-coordination commands → exit 0, no output).
#   - Fires its one loud message ONLY on an actual hand-roll, and at most ONCE
#     per session. Self-relaxes after the coordination skill loads
#     (skill-first-coord-mark.sh) or after the single nag.
set -uo pipefail

input="$(cat)"
cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // ""')"
sid="$(printf '%s' "$input" | jq -r '.session_id // "nosession"')"

# Match the coordination CLI (am/atm/ntm) or `tmux send-keys` ONLY as an actual
# command HEAD — never inside quoted strings, heredoc bodies, or prose. A naive
# line-based grep over-matches: `^` matches every heredoc-body line, and a
# quoted `|ntm` reads as a top-level delimiter, so a `br create` whose BODY
# merely mentions am/atm/ntm would falsely fire. So we:
#   1. strip single/double-quoted spans (multiline-aware) and heredoc bodies,
#   2. split what remains on top-level separators ( ; & | newline ),
#   3. test only the HEAD token of each segment (skipping VAR=val assignments).
is_coord=0
stripped="$(printf '%s' "$cmd" | perl -0777 -pe "
  s/'[^']*'//g;                                      # single-quoted spans
  s/\"[^\"]*\"//g;                                   # double-quoted spans (multiline)
  s/<<-?\s*([A-Za-z_][A-Za-z0-9_]*).*?^\s*\1\b//gms; # heredoc bodies
")"
printf '%s' "$stripped" | awk '
  BEGIN { RS="[;&\n]|\\|\\|?"; FS="[ \t]+" }
  {
    i=1
    while (i<=NF && ($i=="" || $i ~ /^[A-Za-z_][A-Za-z0-9_]*=/)) i++  # skip VAR=val
    head=$i
    if (head=="am" || head=="atm" || head=="ntm") { found=1 }
    if (head=="tmux") { nxt=$(i+1); if (nxt=="send-keys") found=1 }   # tmux send-keys
  }
  END { exit (found?0:1) }
' && is_coord=1
[ "$is_coord" -eq 1 ] || exit 0

dir="${TMPDIR:-/tmp}/claude-coordguard"
sentinel="$dir/${sid//\//_}"
[ -f "$sentinel" ] && exit 0   # skill already loaded, or already nagged this session

mkdir -p "$dir" 2>/dev/null || true
: > "$sentinel" 2>/dev/null || true
cat >&2 <<'MSG'
⛔ SKILL-FIRST (coordination): load the skill before hand-rolling the AM/ATM CLI.
  • am  (Agent Mail)          → Skill tool: agent-mail
  • atm / ntm (ATM swarm)     → Skill tool: ntm   (or using-atm)
  • tmux send-keys to a pane  → Skill tool: ntm
The skill carries the command surface + doctrine — don't reverse-engineer the CLI.
Fires once per session and self-relaxes after the skill loads. Re-run your command.
MSG
exit 2
```

## Script 2 — the mark (`skill-first-coord-mark.sh`)

PreToolUse / Skill. Silently records that a coordination skill loaded so the
guard self-relaxes. Zero context output — pure side effect.

```bash
#!/usr/bin/env bash
# skill-first-coord-mark (PreToolUse / Skill)
# Silently record that a coordination skill loaded this session so the
# skill-first-coord-guard self-relaxes. ZERO context output — pure side effect.
set -uo pipefail

input="$(cat)"
skill="$(printf '%s' "$input" | jq -r '.tool_input.skill // ""')"
case "$skill" in
  agent-mail|ntm|using-atm)
    sid="$(printf '%s' "$input" | jq -r '.session_id // "nosession"')"
    dir="${TMPDIR:-/tmp}/claude-coordguard"
    mkdir -p "$dir" 2>/dev/null || true
    : > "$dir/${sid//\//_}" 2>/dev/null || true
    ;;
esac
exit 0
```

## Opt-in install

1. Save both scripts (e.g. to `~/.claude/hooks/`) and `chmod +x` them.
2. Add the hook pair to `~/.claude/settings.json` (user) or
   `.claude/settings.json` (project). Note the **two separate matchers** —
   `Bash` runs the guard, `Skill` runs the mark:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "~/.claude/hooks/skill-first-coord-guard.sh" }
        ]
      },
      {
        "matcher": "Skill",
        "hooks": [
          { "type": "command", "command": "~/.claude/hooks/skill-first-coord-mark.sh" }
        ]
      }
    ]
  }
}
```

Requires `jq`, `perl`, and `awk` on `PATH` (all standard on macOS and Linux).

## Test it (and prove it)

A small bats test exercising the fire / silent / once-per-session contract.
Save as `tests/skill-first-coord-guard.bats` and run with `bats <file>`:

```bash
#!/usr/bin/env bats
# Contract for skill-first-coord-guard.sh:
#   FIRE (exit 2):   am robot status · atm up · ntm --robot-attention
#                    git commit -m x && am mail send · tmux send-keys -t x hi
#   SILENT (exit 0): ls -la · npm test · team build · echo "I am here"
#                    br create "t" --body "...am/atm/ntm... agent-mail|ntm|using-atm..."
GUARD="${GUARD:-$HOME/.claude/hooks/skill-first-coord-guard.sh}"

setup() { export TMPDIR="$(mktemp -d)"; }

run_guard() { # $1=command $2=session_id
  jq -nc --arg c "$1" --arg s "$2" '{tool_input:{command:$c},session_id:$s}' | bash "$GUARD"
}

@test "FIRE: am robot status"               { run run_guard 'am robot status' "s1";              [ "$status" -eq 2 ]; }
@test "FIRE: atm up"                         { run run_guard 'atm up' "s2";                       [ "$status" -eq 2 ]; }
@test "FIRE: ntm --robot-attention"          { run run_guard 'ntm --robot-attention' "s3";        [ "$status" -eq 2 ]; }
@test "FIRE: chained && am mail send"        { run run_guard 'git commit -m x && am mail send' "s4"; [ "$status" -eq 2 ]; }
@test "FIRE: tmux send-keys"                 { run run_guard 'tmux send-keys -t x hi' "s5";       [ "$status" -eq 2 ]; }

@test "SILENT: ls -la"                       { run run_guard 'ls -la' "s6";                       [ "$status" -eq 0 ]; [ -z "$output" ]; }
@test "SILENT: npm test"                     { run run_guard 'npm test' "s7";                     [ "$status" -eq 0 ]; [ -z "$output" ]; }
@test "SILENT: team build"                   { run run_guard 'team build' "s8";                   [ "$status" -eq 0 ]; [ -z "$output" ]; }
@test "SILENT: echo quoted am"              { run run_guard 'echo "I am here"' "s9";             [ "$status" -eq 0 ]; [ -z "$output" ]; }
@test "SILENT: br create body mentions am/atm/ntm (false-positive guard)" {
  run run_guard 'br create "t" --body "...am/atm/ntm... agent-mail|ntm|using-atm..."' "s10"
  [ "$status" -eq 0 ]; [ -z "$output" ]
}

@test "once-per-session: first fires, second self-relaxes" {
  run run_guard 'am robot status' "same"; [ "$status" -eq 2 ]
  run run_guard 'atm up' "same";          [ "$status" -eq 0 ]
}
```

Proven output of an equivalent pure-shell harness against all contract cases
(every FIRE → exit 2, every SILENT → exit 0 with zero stderr bytes, including
the `br create` false-positive case and a multiline heredoc body):

```
=== FIRE (expect exit 2) ===
  exit=2  am robot status
  exit=2  atm up
  exit=2  ntm --robot-attention
  exit=2  git commit -m x && am mail send
  exit=2  tmux send-keys -t x hi
=== SILENT (expect exit 0, no stderr) ===
  exit=0  ls -la                                                       [stderr-bytes=0]
  exit=0  npm test                                                     [stderr-bytes=0]
  exit=0  team build                                                   [stderr-bytes=0]
  exit=0  echo "I am here"                                             [stderr-bytes=0]
  exit=0  br create "t" --body "...am/atm/ntm... agent-mail|ntm|..."   [stderr-bytes=0]
=== once-per-session sentinel ===
  1st am : exit=2
  2nd atm: exit=0
```

## Known limitations

The guard tests only the actual command **head**, so it intentionally does NOT
fire when a coordination CLI is reached indirectly — via command-substitution
(`$(am …)`), backticks, or a command-prefix wrapper (`time am …`, `env X=1 am …`).
This is by design: the guard is an opt-in *nudge*, not a security boundary. The
cost of a missed case is exactly one un-nudged hand-roll — no false fire, no
broken command. Erring toward silence keeps it cheap on context and safe to run.
The recipe also requires `jq`, `awk`, and `perl` on `PATH`.
