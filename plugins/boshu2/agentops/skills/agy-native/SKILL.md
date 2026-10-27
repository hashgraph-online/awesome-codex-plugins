---
name: agy-native
description: 'Run a supplied task in headless AGY (Antigravity, Gemini) and collect its result. Use when: AGY, Antigravity or Gemini is requested by name; never a fallback.'
practices: [team-topologies, design-by-contract]
hexagonal_role: driving-adapter
consumes: [explicit-packet]
produces: [agy-run-evidence]
context_rel:
- kind: separate-ways
  with: codex-exec
skill_api_version: 1
user-invocable: true
metadata:
  tier: cross-vendor
  dependencies: []
  capabilities: [dispatch_explicit_packet, provide_fresh_context]
  effects: [start_agy_session]
  canonical_status: canonical
  disposition: keep_optional_adapter
output_contract: AGY runtime evidence
---

# AGY Native

Run a supplied packet in AGY (Antigravity) only when the caller explicitly
selects that runtime. Scope the run to the supplied workspace and packet,
return runtime evidence, and stop.

## Before launch

1. **Read the live surface.** The CLI changes faster than skill text.
   Re-checked on 2026-10-25 against Claude Code 2.1.309, codex-cli 0.163.0, AGY 1.4.7, gc edge 97503b2 (with Gas City v1.5.1 docs and source), bd 1.3.1 and ao 3.11.0.
   Run `agy --help` for flags, `agy changelog` for behavior the help omits,
   and `agy models` for ids. That list includes Claude and GPT-OSS: a Gemini
   or cross-family run needs a `gemini-*` id.
2. **Absent means stop.** If `agy` is missing or its help cannot be read,
   report the absence and stop. Never fall back silently to Codex, Claude or
   any other runtime; a substitute needs a new caller selection. Nothing routes
   work to AGY on its own either.
3. **Set an explicit bound.** Print mode (`agy -p` / `--print`) is the headless
   path, and it has no built-in limit: `--print-timeout` defaults to `0`, which
   waits until the turn completes. Pass `--print-timeout` from the caller's
   remaining deadline and hold the same bound outside the process. A run
   stopped at the bound is a timeout, not a result.
4. **Keep author and validator apart.** A validator is a new run in a new
   conversation, never `-c`/`--continue` or `--conversation <author-id>`, so
   its judgment stays fresh. Validators stay read-only and hand judgment to
   Validate; they never write the core verdict.

## Permission posture (disclose it; never assume it)

Name the posture before launch: the flags plus the user and project
`settings.json` permissions, which headless runs honor (disclose those or say
not inspected). No flag makes file access read-only.

- No posture flag: workspace reads are granted; other actions needing approval
  are denied and listed in the JSON `denied_actions`. With settings that allow
  no writes, this is the validator posture.
- `--sandbox` restricts terminal commands only. `--mode accept-edits` approves
  edits and `--mode auto` edits and safe commands; `--mode plan` is not
  documented as read-only, and headless runs pass plan review on their own.
- `--dangerously-skip-permissions` approves every tool call. It and the
  approving modes need declared effects and caller authorization covering
  that blast radius.

Take `git status --porcelain` in `$WORKSPACE` before and after; a validator's
write is out of authority.

## Command

In an AgentOps source checkout, review runs use `REVIEWER=agy` (the id in
`REVIEWER_MODEL`) with `codex_exec_guarded` from `scripts/lib/codex-exec.sh`
(call shape in [codex-exec](../codex-exec/SKILL.md#run-it)). It adds echo,
stall and output-cap handling and runs
`--sandbox --dangerously-skip-permissions`, a posture to disclose. An
installed skill lacks that library; use this block.
The packet goes by path, not inline: a short `-p` pointer plus `--add-dir` on
the packet's own directory only, because a large inline prompt can be dropped
while the run still looks scoped. That drop is an earlier-run observation, not
in the 1.4.7 help or changelog. Would verify: a run with an inline `-p` prompt
over ~100 KB that asks for a marker from its end.

```bash
TO=$(command -v timeout || command -v gtimeout) || { echo "no timeout: not launching" >&2; exit 2; }
[ -n "$MODEL" ] || { echo "MODEL unset: pick an id from agy models" >&2; exit 2; }
# DEADLINE_EPOCH: absolute Unix time fixed once by the caller; a later run gets what is left.
remaining=$(( DEADLINE_EPOCH - $(date +%s) ))
pt=$(( remaining - 15 ))  # AGY's bound fires first; 0 would mean no limit
[ "$pt" -gt 0 ] || { echo "deadline too close; not launched" >&2; exit 124; }
PKT=$(mktemp -d) && cp "$PROMPT_FILE" "$PKT/packet.md" || exit 2  # not $TMPDIR itself
cd "$WORKSPACE" || exit 2
# POSTURE: Bash array of the flags chosen above; empty is the default posture.
set -o pipefail  # bash and zsh: $? is the failing stage, not head's
"$TO" -k 10 "$remaining" \
  agy --print-timeout "${pt}s" --model "$MODEL" --output-format json \
  "${POSTURE[@]}" --add-dir "$PKT" \
  -p "Read the task packet at $PKT/packet.md and do what it describes." \
  </dev/null 2>"$ERR" | head -c 10485760 >"$OUT"
rc=$?
```

Put every flag before `-p`. The help does not say whether `-p` takes a value,
and this is untested on 1.4.7. Would verify: `agy -p hi --print-timeout 300`
exiting 2 (flags after `-p` are parsed) or starting a billed run (they are
not). `--print-timeout` needs a unit such as `300s`; a bare number or an
unknown flag exits 2. If the host shell tool's cap is under
`remaining` plus 10 s, handle it as [claude-exec](../claude-exec/SKILL.md#run) does.

**Did it finish?** Exit 0 is not proof: an expired `--print-timeout` returns
partial output, exits 0 and warns on stderr, so that run timed out. Exit 3
with an `AGY_ERROR:` line is a model or agent error; other non-zero is a
failed run; 124, or 137 after the grace, is the outer bound. Output repeating
the packet or pointer is an echo. No JSON field is documented for a finished
turn: judge by the expected artifact and the `git status` diff, else say
unknown. An `$OUT` of exactly 10 MiB was cut; its status is the closed pipe.

## Return

```text
command:        exact argv (prompt by reference)
posture:        flags used; settings permissions, or "settings not inspected"
model:          requested id; observed model if AGY reported one, else unknown
conversation:   id AGY reported, else unknown
bound:          --print-timeout value and the outer deadline
outcome:        exit status; finished | timed out (which bound) | echo | unknown | not run
denied_actions: list from the JSON output, else none reported
artifacts:      output path, bytes, truncated yes|no; changed-file paths
```

Installation, plugin mutation and recurring scheduling need separate explicit
authorization.
