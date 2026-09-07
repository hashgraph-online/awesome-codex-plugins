---
name: journey-audit
description: >
  Use this skill when the user wants the PRODUCT audited from the outside in — what the website
  promises vs what the code does vs what a real user experiences vs what actually arrives by mail
  vs what the data says is used. Runs a 7-role read-only wave (R5 writes only under an explicit
  SAFETY block) against a per-repo `.orchestrator/journey-manifest.md` and writes a dossier to
  docs/audits/. Distinct from /discovery, which checks code quality inside-out — this checks
  product truth outside-in; they complement, neither replaces the other. Triggers "journey audit",
  "Nutzersicht-Audit", "audit the product from the user's side", "/journey-audit".
model: inherit
color: purple
tools: Read, Grep, Glob, Bash, Write, Task
---

# Journey Audit

> Outside-in product audit as a repeatable deep session. Code review checks code against code;
> this checks the product against the user's experience. Quarterly, never a CI component.

## Purpose

The most expensive defects of the first run (EventDrop `main-2026-08-28-a6`: a core feature with no
entry point anywhere in the UI, burned free quota, a plan gate that could be bypassed, a
claim-vs-code contradiction, EUR copy in a USD context) are **invisible to every code-centric
check**. They are not bugs in a function; they are gaps between five surfaces — marketing copy,
code constants, live UI, outbound mail, real usage data — that no single surface can reveal.

This skill dispatches seven roles that each own one surface, then makes the coordinator personally
re-verify every P0 before it is written down. The re-verification is the value, not the fan-out:
the first run caught 2 agent errors that way and confirmed 3 real P0s.

## Phase 0: Gates

### 0.1 Bootstrap Gate

Read `skills/_shared/bootstrap-gate.md` and execute the gate check. GATE_CLOSED → invoke
`skills/bootstrap/SKILL.md` first. GATE_OPEN → continue.

### 0.2 Manifest HARD-GATE

<HARD-GATE>
Read `.orchestrator/journey-manifest.md` in the target repo (or the path passed as `$ARGUMENTS`).

**A — File missing or empty → REFUSE the whole run.** Say exactly this, then stop:

> `/journey-audit` needs `.orchestrator/journey-manifest.md` in this repo and it is not there.
> The audit is repo-specific: without personas, entry points, truth-SSOTs, the chat-interview key
> and the SAFETY block, seven agents would invent their own definition of "correct" and every
> finding would be unfalsifiable.
> Copy the template — `templates/_shared/journey-manifest.md` in the session-orchestrator plugin —
> to `.orchestrator/journey-manifest.md`, fill it in, then re-run `/journey-audit`.

**B — Manifest present, `## SAFETY` heading absent or its body empty → REFUSE R5 ONLY.** R5 is the
only role that touches production with a real account. Say:

> The manifest has no filled `## SAFETY` block, so R5 (real end-to-end run against production) is
> NOT dispatched. Running as dry-run: R1–R4 + R7 (R6 additionally needs the read-only DB
> credentials named in the manifest). Fill in allowed accounts/events, no-go actions, the checkout
> limit and the cleanup rule to enable R5.

Do NOT infer a SAFETY block from other sections, do NOT ask the operator to dictate one into chat,
do NOT dispatch R5 "read-only, just this once". A production write without a written, committed
safety envelope is the one thing this skill never does.
</HARD-GATE>

Both gates are cheap and mechanical:

```bash
MANIFEST="${1:-.orchestrator/journey-manifest.md}"
[ -s "$MANIFEST" ] || { echo "GATE-A: no manifest"; exit 1; }
awk '/^## SAFETY/{f=1;next} /^## /{f=0} f&&NF{c++} END{exit c>0?0:1}' "$MANIFEST" \
  || echo "GATE-B: SAFETY block absent or empty → R5 disabled"
```

### 0.3 Peer-session check (before dispatch, not after)

Run `ListAgents` / read `.orchestrator/` session locks and check for peer sessions in this working
copy per `.claude/rules/parallel-sessions.md`. A journey audit reads wide and R5 writes to
production — a peer holding the same files must know before the wave starts, not from the diff.
Announce the audit and the file scope you will touch; the audit itself claims almost no write
scope, which is exactly why it is easy to forget.

## Phase 1: Read the manifest

Parse the manifest into `$MANIFEST` and derive per-role inputs. Every role prompt below is filled
from these fields — an empty field is reported to the operator, never guessed:

`personas` · `entry_points` · `truth_ssots` · `touchpoints` (template dir, send path, cron sources,
render idiom) · `chat_interview` (question → expected answer → SSOT) · `safety` · `credentials`
(env-var NAMES) · `realdata_queries` · `platform_expectation` · `known_exceptions`.

## Phase 2: The wave — R1–R7

All roles are **read-only** except R5. All run in parallel in one wave; none depends on another's
output (the coordinator, not an agent, joins their findings).

| R | Rolle | Generisch | Aus dem Manifest |
|---|-------|-----------|------------------|
| R1 | Flow-Zensus | Trigger→Empfänger→Zeitpunkt→Dedupe map of every outbound touchpoint (mail/push/webhook) | Template dir, send path, cron sources |
| R2 | Artefakt-Rendering | Render templates to HTML, screenshots desktop/mobile/dark, consistency matrix | Render idiom, example props |
| R3 | Claim-vs-Code-Matrix | Every marketing/FAQ/chat claim against the SSOT constants; feature inventory × surfaces | SSOT files, i18n namespaces, chat fact source |
| R4 | Anonymer Live-Rundgang | agent-browser desktop+mobile, chat interview against the truth key, dead links, console | Route list, chat questions + expected answers |
| R5 | Echter E2E-Durchstich | Prod, real account, actually execute each core flow, DB counter-check, mail-log reconciliation | **SAFETY block (mandatory)** |
| R6 | Realdaten-Funnel | Usage funnel, never-fired flows, delivery defects, name what is not measurable | Read-only DB access, identity rules, mail-provider API |
| R7 | Plattform-Ausnutzung | Self-built vs platform matrix (hosting/DB/realtime/queues/CDN/WAF), limits at 10× | CLI logins, expected plan, open perf issues |

### Shared prompt preamble (prepend to every role)

> You are role `<R#>` of a journey audit of `<repo>`. Manifest: `.orchestrator/journey-manifest.md`
> — read it first; it is your only definition of "correct". You are **read-only**: no `Edit`, no
> `Write` outside your own report, no git write operations (PSA-007), no production writes.
> Every distributional claim ("all N routes", "no template does X") carries the executed command
> and its output (PSA-006). A finding you cannot reproduce with a quoted command is a suspicion —
> label it as one. Findings listed under `Bekannte Ausnahmen` in the manifest are reported as
> `known-exception`, never as new. Severity: **P0** = money, data loss, or a core flow unreachable ·
> **P1** = a broken flow or a UX dead end · **P2** = content/platform. Return the FULL report as
> your last message.

### Role prompt skeletons

Each is self-contained; fill the `<…>` from `$MANIFEST`.

**R1 — Flow-Zensus.** Inputs: template dir `<…>`, send path `<…>`, cron sources `<…>`.
Task: enumerate every outbound touchpoint and produce one row per flow: trigger (code location) →
recipient (which persona) → timing → dedupe/idempotency → is it reachable at all. Grep the send
path for callers; a template with zero callers is a P1 finding, a caller with no dedupe on a
money-relevant flow is P0. Output: Markdown table + a list of `never-fired` candidates with the
grep that proves zero callers.

**R2 — Artefakt-Rendering.** Inputs: render idiom `<…>`, example props `<…>`.
Task: render every template found by R1's directory to HTML, screenshot desktop + mobile + dark,
and build a consistency matrix (logo, sender, footer, legal block, CTA, language, currency).
Output: matrix table + the artifact paths under `.orchestrator/journey-audit/<date>/`, plus every
divergence as a finding. Do not fix a template; report it.

**R3 — Claim-vs-Code-Matrix.** Inputs: SSOT files `<…>`, i18n namespaces `<…>`, chat fact source `<…>`.
Task: extract every quantitative or capability claim from marketing pages, FAQ, pricing, chat facts
and mail copy; compare each against the SSOT constant. One row: claim · where it is said · SSOT
value · verdict (`match` / `drift` / `unbacked`). Then a feature inventory × surfaces grid: a
feature that exists in code but appears on no surface is a P0 candidate ("no entry point").
**i18n files are owned by R3 alone** — no other role opens them.
Output: two tables + findings.

**R4 — Anonymer Live-Rundgang.** Inputs: route list `<…>`, chat questions + expected answers `<…>`.
Task: `agent-browser`, logged OUT, desktop and mobile viewport. Walk every route: dead links,
console errors, layout breaks, CTA that goes nowhere. Then run the chat interview verbatim and
score each answer against the expected answer from the manifest (`match` / `drift` / `refused` /
`hallucinated`). Output: route table (status, console, findings), interview table, screenshots.
Read-only: never submit a form that creates data, never sign up.

**R5 — Echter E2E-Durchstich.** Inputs: SAFETY block `<…>`, credentials by env-var NAME `<…>`.
Task: with the allowed account only, actually execute each core flow end to end in production;
counter-check in the DB read-only that the expected records exist; reconcile against the mail log.
**Before every step, re-read the SAFETY block and state which rule permits this step.** Stop at the
first no-go, do not improvise around a block, honour the checkout limit exactly, and run the
cleanup rule at the end and prove it ran. Output: per-flow trace (step → observed → expected →
verdict), the DB counter-check output, the cleanup proof.

**R6 — Realdaten-Funnel.** Inputs: read-only queries `<…>`, identity rules `<…>`, mail-provider API `<…>`.
Task: run the manifest's `SELECT`s only. Build the funnel per persona, list flows that never fired
in production, and pull delivery defects from the mail provider (bounces, suppressions, a
permanently silenced owner address). Then name explicitly what the data CANNOT answer — an unnamed
blind spot reads as a zero. Output: funnel table, never-fired list, delivery-defect list,
`not-measurable` list. No writes, no schema changes, no query outside the manifest.

**R7 — Plattform-Ausnutzung.** Inputs: CLI logins `<…>`, expected plan/tier `<…>`, open perf issues `<…>`.
Task: self-built vs platform matrix across hosting, DB, realtime, queues, CDN, WAF, cron, mail:
what does the repo hand-roll that the paid platform already provides, and what breaks at 10× today's
load (quote the actual limit from the provider CLI/API, not from memory). Output: matrix
(capability · self-built? · platform feature · effort to switch · limit at 10×) + findings.

## Phase 3: Koordinator-Disziplin

Numbered MUSTs. This phase is the skill; the wave is only its input.

1. **Every P0 claim is re-verified by the coordinator, individually, with its OWN grep/curl/DB read,
   before it enters the dossier.** Not "the agent quoted a command" — you run one yourself, and the
   dossier carries YOUR command and output. An unreproduced P0 is downgraded to P1 with the note
   `agent claim, not reproduced`, or dropped. First run: 2 of 5 P0 claims were agent errors
   ("instantly unreachable" — it was selectable in the UI; "USD on prod" — a session artifact).
2. **A finding is attributed.** Every dossier row names the role that found it and the command that
   proves it — the reader must be able to re-run it without asking anyone.
3. **i18n files are owned by exactly ONE agent (R3).** They were the known contention point in the
   first run: many roles want to quote them, and a second reader turns into a second writer the
   moment a fix is suggested. Same rule for any other file two roles both want.
4. **Peer-session check before the wave starts** (Phase 0.3), not after the diff.
5. **The coordinator never lets an agent write the dossier.** Agents return reports; the joining,
   de-duplication and severity decision are the coordinator's, because contradictions between two
   agents are only visible in one place.
6. **Contradictions are reported as contradictions.** Two roles disagreeing is a finding about the
   product, not a merge conflict to smooth over.
7. **No fixes during the audit.** Findings only. The fix wave is Phase 5 and is a separate decision.

## Phase 4: Dossier

Write `docs/audits/YYYY-MM-DD-user-journey-audit.md` with this fixed section order:

1. `## P0 — Geld & Kern-Flows` (each: symptom · evidence (coordinator's own command + output) ·
   impact · suggested fix · role)
2. `## P1 — Flows`
3. `## P1 — UX`
4. `## P2 — Inhalt`
5. `## P2 — Plattform`
6. `## Realdaten` (funnel, never-fired flows, delivery defects, explicitly not-measurable)
7. `## Marketing-Hebel` (what the product does well and says nowhere)

Header carries: date, repo, HEAD SHA, roles dispatched (and which were skipped, with the reason —
"R5 skipped: no SAFETY block" is a result, not a gap), manifest path, artifact directory.

## Phase 5: Closing AskUserQuestion

One `AskUserQuestion` call, per `.claude/rules/ask-via-tool.md` (option 1 `(Recommended)`, every
description carries reason + cost + consequence, `header` ≤ 12 codepoints):

```
AskUserQuestion({ questions: [
  { question: "Which fix packages should the follow-up wave carry?",
    header: "Fix-Wellen", multiSelect: true,
    options: [
      { label: "P0 money+core (Recommended)", description: "The <N> P0s I re-verified myself. Blocks revenue/core flow today; ~<X>h; freezes nothing else." },
      { label: "P1 flows",  description: "<N> broken/undedupliced flows. ~<X>h; needs the R1 map as input." },
      { label: "P1 UX",     description: "<N> dead ends. Cheap individually, touches i18n — one owner." },
      { label: "P2 content+platform", description: "<N> items. No user impact today; do in cooldown." } ] },
  { question: "Create issues for the selected packages?",
    header: "Issues", multiSelect: false,
    options: [
      { label: "Yes, batch now (Recommended)", description: "One issue per finding via gitlab-ops; labels priority::critical|high|medium + area:* + type:bug/feature. ~<N> issues; respects issue-budget." },
      { label: "Dossier only", description: "No issues; the dossier stays the record. Choose when the backlog is already over budget." } ] } ] })
```

Issue creation follows `skills/gitlab-ops/SKILL.md` § Label Taxonomy: `priority::critical` for P0,
`priority::high` for P1, `priority::medium` for P2, plus the repo's `area:` and `type:` axes. Each
issue links back to the dossier section that produced it.

## Offload note (R6/R7)

R6 and R7 are pure CLI/API roles — no browser, no repo writes — so they can run headless on a
second machine (`claude -p "<prompt>"`, see the `m5-offload` skill). Two rules from the first run,
both learned the hard way:

- **`claude -p` prints only the LAST message.** The prompt MUST end with: *"Return the complete
  report in your last message — not a summary, not a pointer to a file. Nothing you say before the
  last message will be read."*
- **No background processes.** The prompt MUST forbid `&`, `run_in_background`, and any "I'll keep
  it running" pattern: the process is killed when `-p` returns, and a half-finished role looks
  identical to a clean one.

## Cadence & Abgrenzung

- **Quarterly, or after a large feature drop.** Deliberately **not a CI component** — it is
  expensive and judgment-heavy, and a judgment-heavy gate that runs on every pipeline becomes a
  rubber stamp.
- **Optional monthly light variant:** R3 + R4 only, as a scheduled cloud session.
- **vs `/discovery`:** discovery checks code quality inside-out (probes over the tree);
  journey-audit checks product truth outside-in (five user-facing surfaces against each other).
  Neither replaces the other; a repo needs both.
- **Follow-through:** after each run, freeze the mechanizable parts per repo — a `report:*` script,
  a claim-drift test pinned to the SSOT constant — so the next run is cheaper. The audit's job is
  to find what no test knows how to look for yet.

## Anti-Patterns

- Dispatching R5 without a SAFETY block "because the operator said it's fine in chat" — the block
  is a committed artifact for a reason.
- Copying an agent's P0 into the dossier because its command looked convincing (Phase 3.1).
- Two roles both editing/owning the i18n files (Phase 3.3).
- Running the audit as a CI job to "keep it honest" — it turns into a stamp nobody reads.
- Fixing findings mid-audit, so the later roles measure a moving product.
