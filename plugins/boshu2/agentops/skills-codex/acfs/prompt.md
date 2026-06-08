# Codex Execution Profile — acfs

Read the sibling base skill `../SKILL.md` (full overview, constraints, output
spec, rubric, examples, troubleshooting) before acting. This profile is the
Codex-native, step-ordered execution path; the base SKILL.md is the source of truth.

## Steps

1. **Health — know the ground truth.** Run `$HOME/acfs/bin/acfs doctor`. It reads four
   bands: **lanes** (claude/codex/agy/gemini auth), **core flywheel**
   (br, bv, am, ntm, dcg, cass, cm, ubs), **extras** (caam, ru, rch, fsfs, casr,
   sbh, pt), and **wiring** (cm rule count, cass model, ntm `projects_base`, dcg
   hook, am daemon). Exit code = number of blocking gaps.
2. **Read past the binary check.** A ✓ means the binary is on PATH, NOT that it's
   fed. Read the **wiring** lines: `cm store (0 rules)`, a stale cass index, or a
   dead `am` daemon mean the loop is present but starved. Verify by use, not presence.
3. **Init — wire what's installed.** Run `$HOME/acfs/bin/acfs init` (idempotent +
   additive: `cm init`, sets `ntm config projects_base` default `~/dev`, reports
   cass freshness, reminds you to validate auth lanes). Override the swarm root per
   host with `ACFS_PROJECTS_BASE=~/dev $HOME/acfs/bin/acfs init`.
4. **Confirm zero gaps.** Re-run `$HOME/acfs/bin/acfs doctor` and confirm
   `0 blocking gap(s)` before real work. `$HOME/acfs/bin/acfs up` chains doctor → init
   → doctor in one shot.
5. **Validate auth lanes.** `caam doctor --validate`. An expired lane needs
   interactive `caam login <lane>` — never dispatch a worker on a dead lane.
6. **Operate — run one loop turn (Plan→Coordinate→Execute→Scan→Remember):**
   - **Plan** — `br ready` for available work; decompose into a work-DAG in `br`.
   - **Coordinate** — `am` for file reservations + inter-agent messaging; `caam` to
     pick the auth lane.
   - **Execute** — `codex exec` workers (Codex lane), or `ntm spawn` interactive
     Claude panes (sub auth). `dcg` guards destructive commands throughout.
   - **Scan** — `ubs` over the result before closing.
   - **Remember** — `cm` captures the learning; publish the compression to shared
     state (`br close` + committed artifact). Loop-close is required.
7. **Capture the verdict.** Relay the doctor `summary`
   (`core complete (N checks, 0 blocking gaps)` or `M blocking gap(s) of N`) plus
   the chosen next move into the session/handoff as the verification surface.

## Guardrails

- **Installed ≠ worked-on.** Presence of a binary is not proof of value. Always
  read the `wiring` band; a green core with `cm store (0 rules)` or a dead `am`
  daemon means the substrate lies green while the loop is starved.
- **Invoke, never rebuild.** These are forked tools — do not edit/recompile or
  "improve" the binaries mid-loop. Gaps are wiring, not design. Fork-and-own
  changes happen deliberately, never in-session. Resist the cathedral trap.
- **Never `claude -p` for workers.** Loop/swarm workers run on `ntm` panes
  (interactive Claude = OAuth/sub) or `codex exec` — never `claude -p`/`--print`,
  which bills metered API instead of the Max subscription.
- **`acfs` is additive.** It never truncates configs, reboots, or sudo-installs.
  Trust `acfs init` to be safe to re-run; per-tool *install* is still manual (see
  the base Troubleshooting table for the install-hint path).
- **dcg stays wired.** The destructive-command guard hook must be present in
  `~/.claude/settings.json` — it's the safety floor for autonomous loops.
- **Loop-close is mandatory.** Every iteration ends with a `Remember` write
  (cm rule + `br close` + committed artifact). An un-published result is invisible
  to the next agent and starves the flywheel.
- **`~/dev` is the work-root.** Use `mani`/fleet-ops for repo org — don't hand-walk
  repos; set `ntm projects_base` / `ACFS_PROJECTS_BASE` to it.
- **Backstage only.** Never surface these commands or framing (ACFS, the flywheel,
  the tool names) in client-facing AI Partner content.
