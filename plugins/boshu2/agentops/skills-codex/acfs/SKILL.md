---
name: acfs
description: Use when operating ACFS flywheel health
---
# acfs — drive the agent-flywheel substrate

The operator skill for the ACFS substrate. `~/acfs/bin/acfs` is a **fork-and-own provisioner** (idempotent, additive, cross-platform Mac + Ubuntu/WSL) over Dicklesworthstone's flywheel tools. This skill teaches you to check the substrate's health, wire it, and run the operating loop on top of it.

## Overview / When to Use

ACFS is the **runtime layer** of Bo's three-layer factory: AgentOps = the mind, Mount Olympus = the factory/control-plane, **ACFS = the substrate the work actually runs on**. The doctrine is **invoke-never-rebuild**: you operate these binaries, you do not re-author them.

Use this skill when you need to: confirm the flywheel is healthy before doing real work, init/wire a host, decide whether a tool is *installed* vs *actually working*, or run a session through the Plan→Coordinate→Execute→Scan→Remember loop. It composes with `ntm` (swarms), `caam` (auth lanes), `cass-memory` (procedural memory), `dcg` (destructive-command guard), and `fleet-ops` (the `~/dev` virtual monorepo).

## ⚠️ Critical Constraints

- **Installed ≠ worked-on.** `acfs doctor` printing ✓ for a tool means the binary is on PATH — NOT that it's wired, indexed, or producing value (e.g. `cm` present but 0 rules, `cass` index stale, `am` daemon down). **Why:** the substrate lies green while the loop is starved; always read past the binary check to the `wiring` section. **Verify by use, not by presence.**
- **Invoke, never rebuild.** These are forked tools. Do not edit/recompile the binaries or "improve" them here. **Why:** rebuilding the substrate is the cathedral trap — it's a runtime to *use*; gaps are wiring, not design. Fork-and-own changes happen deliberately, not mid-loop.
- **Never `claude -p` for workers.** Loop/swarm workers run on `ntm` panes (interactive Claude = OAuth/sub auth) or `codex exec` — never `claude -p`/`--print`, which bills the API per-token. **Why:** `claude -p` burns metered API instead of the Max subscription; it is banned for worker dispatch.
- **`acfs` is additive — it never truncates configs, reboots, or sudo-installs.** **Why:** upstream's installer overwrites `~/.zshrc` + `~/.codex/settings.json` and reboots; ours doesn't. Trust `acfs init` to be safe to re-run, but per-tool *install* is still manual (see Troubleshooting).
- **dcg stays wired.** The destructive-command guard hook must be present in `~/.codex/settings.json`. **Why:** it's the safety floor for autonomous loops; `acfs doctor` flags it if missing.

## Workflow / Methodology

### Phase 1: Health — know the ground truth
```bash
~/acfs/bin/acfs doctor      # lanes · core flywheel · extras · wiring · summary
```
Reads four bands: **lanes** (claude/codex/agy/gemini auth), **core flywheel** (br, bv, am, ntm, dcg, cass, cm, ubs), **extras** (caam, ru, rch, fsfs, casr, sbh, pt), and **wiring** (cm store rules count, cass semantic model, ntm `projects_base`, dcg hook, am daemon). Exit code = number of blocking gaps.

**Checkpoint:** Read the `wiring` lines, not just the ✓/✗ on binaries. A green core with `cm store (0 rules)`, a stale cass index, or a dead `am` daemon means the loop is present but **not fed**. Resolve gaps before running real work.

### Phase 2: Init — wire what's installed
```bash
~/acfs/bin/acfs init        # cm init · ntm projects_base · cass freshness · auth-lane reminder
ACFS_PROJECTS_BASE=~/dev ~/acfs/bin/acfs init   # override swarm root per host
```
Idempotent and additive: inits the `cm` mind store, sets `ntm config projects_base` (default `~/dev`), reports cass index freshness, and reminds you to validate auth lanes (`caam doctor --validate`; expired lanes need interactive `caam login <lane>`).

**Checkpoint:** Re-run `acfs doctor` and confirm `0 blocking gap(s)` before proceeding. `acfs up` does doctor → init → doctor in one shot.

### Phase 3: Operate — run the loop
The operating conventions on the wired substrate:

- **`~/dev` is the work-root** (the `ntm` swarm base / `ACFS_PROJECTS_BASE`). Use `mani` (fleet-ops) for repo org — don't hand-walk repos.
- **Spawn a swarm:** `ntm spawn <name>` to start a pane/agent on a repo; coordinate via `am` (Agent Mail) for locks/messaging. (See the `ntm` skill for send/read/triage.)
- **The loop — Plan → Coordinate → Execute → Scan → Remember:**
  1. **Plan** — decompose into a work-DAG in `br` (beads): `br ready` for available work.
  2. **Coordinate** — `am` for file reservations + inter-agent messaging; `caam` to pick the auth lane.
  3. **Execute** — `ntm spawn` workers (interactive Claude on sub, or `codex exec`); `dcg` guards destructive commands throughout.
  4. **Scan** — `ubs` (ultimate bug scanner) over the result before closing.
  5. **Remember** — `cm` (cass-memory) captures the learning; publish the compression to shared state (beads close + committed artifact). **Loop-close is required** — an un-published result is invisible to the next agent.

**Checkpoint:** Every loop iteration ends with a `Remember` write (cm rule + br close + committed artifact). Skipping it leaves work stranded and starves the flywheel.

## Output Specification

**Format:** terminal report (human-readable bands from `acfs doctor`/`init`) plus a stated next action. This skill writes **no files** of its own.
**Persisted state (by sub-tools):** `cm` rules in the XDG mind store; `br` issues in `.beads/*` JSONL; `ntm`/`am` runtime state. Report these as evidence, not as skill output.
**Verdict line to relay:** the doctor `summary` (`core complete (N checks, 0 blocking gaps)` or `M blocking gap(s) of N`) + the chosen next move.

## Quality Rubric

- [ ] Ran `acfs doctor` and read the **wiring** band, not just binary presence.
- [ ] Confirmed `0 blocking gaps` (or named each gap + its install-hint) before real work.
- [ ] Auth lanes validated (`caam doctor --validate`); no expired lane in use.
- [ ] No worker dispatched via `claude -p` — only `ntm` panes or `codex exec`.
- [ ] `dcg` hook confirmed present in `~/.codex/settings.json`.
- [ ] Did not edit/rebuild any flywheel binary (invoke-never-rebuild held).
- [ ] Loop iterations closed with a `Remember` write (cm + br + committed artifact).
- [ ] Used `~/dev` as work-root and `mani`/fleet-ops for repo org.

## Examples

**Pre-session check:** `~/acfs/bin/acfs doctor` → core green but `cm store (0 rules)` and `am daemon not responding` → start `am`, plan to mine sessions into `cm`, then begin.

**Fresh host bring-up:** install missing tools from the doctor install-hints → `ACFS_PROJECTS_BASE=~/dev ~/acfs/bin/acfs up` → confirm `0 blocking gaps` → `ntm spawn build-1` on the target repo.

**Run one loop turn:** `br ready` → reserve files via `am` → `ntm spawn` a worker → `ubs` scan → `cm` capture + `br close` + commit.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `acfs doctor` shows a CORE tool MISSING | Binary not on PATH | Install from the doctor install-hint (fork-and-own; canonical sources are Dicklesworthstone repos). `acfs install` is not yet auto-wired. |
| Core green but `cm store (0 rules)` | Mind store empty | `cm init` then mine sessions into it; presence ≠ populated. |
| `cass semantic model not installed` | Consent-gated model absent | `cass models install && cass index --semantic` (only if you want semantic search). |
| `ntm projects_base` ≠ `~/dev` | Swarm root mis-set | `acfs init` (or `ntm config set projects_base ~/dev`). |
| `dcg hook not found` | Guard not wired | Wire the dcg hook into `~/.codex/settings.json` (see the `dcg` skill). |
| `am daemon not responding` | Coordination bus down | Start the `am` daemon before multi-agent work (see the `agent-mail` skill). |
| Auth lane MISSING/expired | Lane not logged in | `caam doctor --validate`; `caam login <lane>` (interactive). |
| Tempted to fix a binary's behavior | Cathedral/rebuild trap | Stop — invoke-never-rebuild; file the gap as wiring, fork-and-own only deliberately. |

## See Also / References

- `ntm`, `vibing-with-ntm` — swarm spawn/send/triage on the substrate.
- `caam` — auth-lane management for the four lanes (claude/codex/agy/gemini).
- `cass-memory` — the `cm` Remember step (procedural memory / trauma guard).
- `dcg` — destructive-command guard wiring (safety floor).
- `fleet-ops` — `~/dev` virtual monorepo + `mani` repo org (the work-root layer).
- `agent-mail` — `am` coordination bus (locks, messaging, inboxes).
- `~/acfs/image-skills.manifest.md` — what ships in each vendor image; ACFS as the runtime layer.
