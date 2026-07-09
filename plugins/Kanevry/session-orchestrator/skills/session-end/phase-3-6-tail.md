# Phase 3.6.x Tail — Detail Procedures

> Sub-file of the session-end skill. Full, unabridged procedures for the six Phase 3.6.x tail phases (Memory-Proposals, Expired-Sweep, Auto-Dream, Skill-Judge, Auto-Dialectic, Reconcile). The `SKILL.md` § "Phase 3.6.x Tail — Mechanical Skip-Plan (#724)" dispatcher computes a run/skip plan via `scripts/lib/session-end/phase-skip.mjs` (`planTailPhases()`) and loads ONLY the procedures below whose plan entry has `run: true`. Phase headings here match the `phase` id returned by the aggregator (e.g. `### 3.6.3 …`).
>
> Platform state-dir + project-instruction-file resolution notes are inherited from `SKILL.md`. For the full close-out flow, see `SKILL.md`.

### 3.6.3 Memory Proposals Collection (#501, F2.1)

> Gate: Skip this phase entirely when ANY of:
> - `persistence` is `false` in Session Config
> - `memory.proposals.enabled` is `false` (default: `true`)
> - `.orchestrator/metrics/proposals.jsonl` does not exist OR contains zero entries

After learnings are written (Phase 3.6) and BEFORE auto-dream dispatch (Phase 3.6.5), collect agent-proposed memory entries written during this session and present them to the operator via `AskUserQuestion` multiSelect. Approved entries flow to `learnings.jsonl` with `_provenance: agent-proposed@<wave-id>`. Rejected entries are archived to `.orchestrator/proposals.rejected.log`.

The proposals queue is populated mid-session by wave-executor agents calling `node scripts/memory-propose.mjs --type ... --subject ... --insight ... --evidence ... --confidence ...`. The CLI enforces:
- Quota per wave (default 5, configurable via `memory.proposals.quota-per-wave`)
- Confidence floor (default 0.5, configurable via `memory.proposals.confidence-floor`)
- Wrong-context guard (CLI exits non-zero when STATE.md `status` is not `active`)

#### Coordinator-direct procedure

1. Read Session Config: `memory.proposals.enabled` (default `true`), `memory.proposals.quota-per-wave` (default 5), `memory.proposals.confidence-floor` (default 0.5), `auto-dream.min-confidence` (default 0.5 — issue #566; SECOND gate above the write-time `memory.proposals.confidence-floor`).

2. Invoke `collectProposals` from `scripts/lib/memory-proposals/collector.mjs`, passing the collect-emit confidence floor from Session Config:
   ```javascript
   import { collectProposals } from '${PLUGIN_ROOT}/scripts/lib/memory-proposals/collector.mjs';
   const { queue, stats, perWaveSummaries } = await collectProposals({
     repoRoot: process.cwd(),
     // Issue #566: collect-emit confidence floor. Records with
     // `record.confidence < minConfidence` are dropped from `queue` (but
     // counted in stats). When the key is absent, defaults to 0.5 via the
     // `_parseAutoDream` parser.
     minConfidence: config['auto-dream']?.['min-confidence'],
   });
   ```

3. If `queue.length === 0`: log `memory-proposals: queue empty (stats: ${JSON.stringify(stats)})` and continue.

4. **AUQ pagination logic**: partition the queue into FIFO batches of 4 inline:

   - Empty queue → silent skip (no AUQ rendered).
   - 1-4 items → single multiSelect call with all items as options.
   - 5+ items → sequential multiSelect calls in batches of 4 (FIFO order; final batch may have < 4 items).

   ```javascript
   // Inlined from former scripts/lib/memory-proposals/auq-partition.mjs (PRD F2.2 #502 closed; see #558 M2).
   const BATCH_SIZE = 4;
   const batches = [];
   if (Array.isArray(queue) && queue.length > 0) {
     for (let i = 0; i < queue.length; i += BATCH_SIZE) {
       batches.push(queue.slice(i, i + BATCH_SIZE));
     }
   }
   ```

   Then iterate `batches` and emit one `AskUserQuestion` per batch with `header: "Memory — Confirm Proposals (Batch N of M)"`. Option label format: `[<type-12>] | <subject-40> | conf=X.XX`. Option description: `evidence: <first 60 chars of insight>`. `multiSelect: true`.

5. After all batches answered, partition the queue into `approved` (any option selected across all batches) and `rejected` (all unselected).

6. Invoke `writeApproved` and `archiveRejected` from `scripts/lib/memory-proposals/sink.mjs`:
   ```javascript
   import { writeApproved, archiveRejected, clearProposalsJsonl } from '${PLUGIN_ROOT}/scripts/lib/memory-proposals/sink.mjs';
   const writeResult = await writeApproved({ approved, repoRoot, sessionId });
   const archiveResult = await archiveRejected({ rejected, repoRoot, reason: 'user-declined' });
   await clearProposalsJsonl({ repoRoot });
   ```

7. Log outcome for Phase 6 Final Report: `memory.proposals: <queued> queued → <approved> approved, <rejected> rejected (dropped: <dropped> quota, <below_floor> below-floor)`.

#### Failure modes

- If `collectProposals` fails (fs error): log warning `⚠ memory-proposals: collect failed (${err}) — skipping`, do not block session close.
- If `writeApproved` reports errors per-record: log each, but continue (per-record fault isolation per sink contract).
- If `clearProposalsJsonl` fails: log warning; do not block. The file may be re-collected at the next session-end, idempotent.

#### Cross-references

- Spec: issue #501 — memory-proposals (F2.1); no standalone PRD file
- Modules: `scripts/lib/memory-proposals/{schema,store,collector,sink}.mjs`
- CLI: `scripts/memory-propose.mjs` (agents call this)
- Hook: `hooks/pre-bash-memory-propose-audit.mjs` (audit trail)
- Coordinator AUQ spec: `agents/memory-proposal-collector.md` (reference doc)
- Sibling phases: 3.6.5 Auto-Dream (#502), 3.6.6 Skill-Applied Judge (#645 L3), 3.6.7 Auto-Dialectic (#506)
- Issue: #501

### 3.6.4 Expired-Learnings Sweep (Advisory — Epic #723 B4)

> Best-effort, non-blocking. Skip silently if the sweep script errors or `.orchestrator/metrics/learnings.jsonl` is absent.

After learnings are written (Phase 3.6), run `node scripts/sweep-expired-learnings.mjs --json` (dry-run) against the learnings store. If the summary reports `archived > 0`, follow with `node scripts/sweep-expired-learnings.mjs --apply --json` to move the stale-past-grace entries into `.orchestrator/metrics/learnings-archive.jsonl` (append-only, never deleted). Note the resulting counts for the Phase 6 Final Report; any error surfaces on stderr with a non-zero exit (`1` usage error, `2` sweep failure) and never blocks close — the CLI does not write to `.orchestrator/metrics/sweep.log` (that path is the session-registry's own sweep log, unrelated to this CLI).

### 3.6.5 Auto-Dream Dispatch (#502, F2.2)

> Skip this phase if `memory-cleanup-threshold: 0` (kill-switch per PRD F2.2). Also skip on non-Claude-Code platforms (memory dir at `~/.claude/projects/` is Claude Code-only, mirrors Phase 3.5 gate).

After learnings are written (Phase 3.6), determine whether to emit a **manual-cadence nudge** to run `/memory-cleanup --dry-run` in the next session. The decision uses MEMORY.md line count and a sessions-since-last-cleanup signal. There is no `memory-cleanup` agent in the registry, so the historical auto-dream subagent dispatch never fired (see #614) — the nudge replaces it. A manually-run `/memory-cleanup --dry-run` writes a complete-replacement MEMORY.md proposal (single fenced ` ```markdown ` block — never git-style diff hunks, see #717) to `.orchestrator/pending-dream.md` for the session after that to apply via `/memory-cleanup --apply-pending`.

1. Read `memory-cleanup-threshold` (default 5) and `memory-cleanup-soft-limit` (default 180) from `$CONFIG`.
2. Invoke `shouldDispatchAutoDream` from `scripts/lib/auto-dream.mjs`:

   ```javascript
   import { shouldDispatchAutoDream } from '${PLUGIN_ROOT}/scripts/lib/auto-dream.mjs';
   import { resolveMemoryDir } from '${PLUGIN_ROOT}/scripts/lib/memory-paths.mjs';
   const memoryDir = resolveMemoryDir();
   const decision = await shouldDispatchAutoDream({
     repoRoot: process.cwd(),
     memoryDir,
     threshold: config['memory-cleanup-threshold'] ?? 5,
     softLimit: config['memory-cleanup-soft-limit'] ?? 180,
   });
   ```
3. If `decision.trigger === false`: log `auto-dream: not triggered (${decision.reason})` and continue. Emit no nudge.
4. If `decision.trigger === true`: **do not dispatch a subagent** — there is no `memory-cleanup` agent in `agents/`, so the historical `Agent({…})` dispatch pointed at the agent name `memory-cleanup` (a subagent type that was never built) and never fired (see #614). Instead, emit a manual-cadence nudge and continue:

   `auto-dream: cadence reached (${decision.reason}) — run /memory-cleanup --dry-run manually in the next session, then apply the proposal with /memory-cleanup --apply-pending.`

   The `shouldDispatchAutoDream` decision helper and `scripts/lib/auto-dream.mjs` lib stay in use: they compute the signal that drives this nudge and back the manual `/memory-cleanup` path (`writePendingDream` / `readPendingDream` / `applyPendingDream`).
5. Record the outcome (skipped / nudge-emitted) so Phase 6 Final Report can surface a line: `auto-dream: manual /memory-cleanup --dry-run recommended (cadence reached) — apply with /memory-cleanup --apply-pending next session`.

The pending-dream sidecar at `.orchestrator/pending-dream.md` is intentionally outside the vault tree — vault-mirror (Phase 3.7) must exclude it from its scope so the proposal survives the session close without being mirrored into 50-sessions/.

Cross-reference: PRD F2.2 acceptance criteria; `scripts/lib/auto-dream.mjs` API (`shouldDispatchAutoDream`, `readDreamSignals`, `writePendingDream`, `readPendingDream`, `applyPendingDream`).

### 3.6.6 Skill-Applied Judge (#645, L3)

> **Default OFF.** Skip this phase — with NO module import and NO sidecar created — unless BOTH gates pass (evaluated in this order):
> 1. `config['skill-evolution'].judge !== true` → skip (the `judge:` key in the top-level `skill-evolution:` block; default `false`).
> 2. `persistence === false` in Session Config → skip.
>
> When skipped, log `skill-judge: disabled (skill-evolution.judge=false)` (or `persistence=false`) and return. **This is the disabled-path guarantee:** with the judge off, only L1 (`skill-invocations.jsonl`, written by the PreToolUse hook) and L2 (`scripts/lib/skill-health/join.mjs`) records exist — no judgment, no error, zero L3 code executes. Do NOT import `scripts/lib/skill-judge.mjs` on the disabled path.

After learnings are written (Phase 3.6) and the auto-dream decision is made (Phase 3.6.5), and when the judge is enabled, run a **bounded, read-only LLM-judge** over this session's selected skills to emit ADVISORY per-skill applied/completed judgments to `.orchestrator/metrics/skill-judgments.jsonl`.

**The #614 distinction (the whole point of L3's Design A):** unlike the 3.6.5 / 3.6.7 nudge-only paths — which cannot dispatch a live subagent because the target read-only agents (`memory-cleanup`, `dialectic-deriver`) cannot write their own sidecars — L3 performs a **LIVE read-only dispatch**. This is #614-safe because the read-only `skill-applied-judge` agent **RETURNS JSON** and the **COORDINATOR writes the sidecar**, not the agent. A read-only agent that returns judgments is allowed; a read-only agent that must write a file is the #614 trap.

**Advisory-only:** the judge output is written with `advisory: true` (schema-rejected otherwise) and **NEVER feeds an auto-action gate** — not a sunset decision, not a C2 repair (`scripts/lib/skill-evolution/*`), not a promotion. Per #645 R9(b) the C2 repair gate stays deterministic; L3 is a signal for humans/dashboards only.

1. Read `config['skill-evolution'].judge` (default `false`), `config['skill-evolution']['judge-budget-tokens']` (default 8000), and `persistence`. Apply the two skip gates above.

2. Determine the **judged set** — only THIS session's selected skills. Read `.orchestrator/metrics/skill-invocations.jsonl` and collect the distinct `skill` values whose `session_id` matches the current session id. If the judged set is empty, `runSkillJudge` returns `status: 'empty-input'` (no dispatch) — log and continue.

3. Invoke `runSkillJudge` from `scripts/lib/skill-judge.mjs`, wiring the real dispatch via the DI seam:

   ```javascript
   import { runSkillJudge } from '${PLUGIN_ROOT}/scripts/lib/skill-judge.mjs';
   import { appendSkillJudgment } from '${PLUGIN_ROOT}/scripts/lib/skill-judgments-schema.mjs';
   import path from 'node:path';

   const budgetTokens = config['skill-evolution']['judge-budget-tokens'] ?? 8000;
   const result = await runSkillJudge({
     // Claude Code path: wire the real read-only haiku subagent as dispatchAgent.
     dispatchAgent: ({ model, prompt, maxTokens }) =>
       Agent({ subagent_type: 'skill-applied-judge', model: 'haiku', prompt, max_tokens: maxTokens }),
     repoRoot: process.cwd(),
     sessionId,
     transcriptTail,                 // recent session transcript excerpt (UNTRUSTED — fenced by the lib)
     selectedSkills,                 // distinct skills from step 2
     model: 'haiku',
     budget: { input: budgetTokens, output: 4000 },
   });
   ```

   - **Claude Code path:** `dispatchAgent` wraps the real `Agent({ subagent_type: 'skill-applied-judge', model: 'haiku', … })`. The agent is `sandbox-tier: read-only` and RETURNS one fenced ```json block — it never writes files.
   - **Codex / Cursor path:** there is no subagent type. Wire `dispatchAgent` as a coordinator-inline call (the coordinator itself reasons over the prompt and returns `{ text }`), keeping the identical `runSkillJudge` signature. Same DI seam, no harness subagent.

4. On `result.status === 'ok'`: the **COORDINATOR** writes each returned judgment to the sidecar. Stamp the per-record metadata (`timestamp`, `event: 'judged'`, `session_id`, `advisory: true`, `model`, `schema_version: 1`) and append:

   ```javascript
   const judgmentsPath = path.join(process.cwd(), '.orchestrator/metrics/skill-judgments.jsonl');
   const nowIso = new Date().toISOString();
   for (const j of result.judgments) {
     await appendSkillJudgment(
       { timestamp: nowIso, event: 'judged', skill: j.skill, session_id: sessionId,
         applied: j.applied, completed: j.completed, confidence: j.confidence,
         advisory: true, model: 'haiku' },
       { path: judgmentsPath },
     );
   }
   ```

   `appendSkillJudgment` re-validates each record; `advisory !== true` is schema-rejected, so a tampered record can never be persisted.

5. On `result.status === 'empty-input'` or `'budget-exceeded'`: log the status (e.g. `skill-judge: skipped (budget-exceeded used=N budget=M)`) and continue. No sidecar write on either non-ok status.

6. **Failures are non-fatal.** Any error from the dispatch or write is logged to `.orchestrator/metrics/sweep.log` and the close continues — same posture as Phase 3.6.7. The judge is advisory; a failed judgment must never block session close.

Cross-reference: PRD §A L3 acceptance criteria (#645, epic #643); `scripts/lib/skill-judge.mjs` API (`runSkillJudge`, `validateModel`, `estimateInputTokens`, `checkBudget`, `buildJudgePrompt`, `parseJudgeResponse`); `scripts/lib/skill-judgments-schema.mjs` (`appendSkillJudgment`, `readSkillJudgments`, `validateSkillJudgment`); agent `agents/skill-applied-judge.md`.

### 3.6.7 Auto-Dialectic Dispatch (#506, F2.5)

> Skip this phase if `dialectic.cadence: 0` (kill-switch per PRD F2.5 AC3). Also skip if `persistence` is `false` in Session Config.

After learnings are written (Phase 3.6) and the auto-dream decision is made (Phase 3.6.5), determine whether to emit a **manual-cadence nudge** to run `/evolve --dialectic` in the next session. The decision uses sessions-since-last-dialectic counted against `.orchestrator/dialectic-last-run`. There is no `evolve` agent in the registry, and the nearest one (`dialectic-deriver`) is `sandbox-tier: read-only` and cannot write the sidecar — so the historical auto-dialectic subagent dispatch never fired (see #614). On trigger, emit the nudge and advance `.orchestrator/dialectic-last-run`; the timestamp is updated only when the nudge is emitted (not on skip), so the reminder surfaces once per cadence window rather than every session. A manually-run `/evolve --dialectic --dry-run` writes the proposed diff to `.orchestrator/dialectic-pending.md`.

1. Read `dialectic.cadence` (default 5), `dialectic.model` (default haiku), `dialectic.budget-tokens` (default 8000) from `$CONFIG`.

2. Invoke `shouldDispatchAutoDialectic` from `scripts/lib/auto-dialectic.mjs`:
   ```javascript
   import { shouldDispatchAutoDialectic } from '${PLUGIN_ROOT}/scripts/lib/auto-dialectic.mjs';
   const decision = await shouldDispatchAutoDialectic({
     repoRoot: process.cwd(),
     cadence: config.dialectic?.cadence ?? 5,
   });
   ```

3. If `decision.trigger === false`: log `auto-dialectic: not triggered (${decision.reason})` and continue. Emit no nudge. Do NOT update `.orchestrator/dialectic-last-run`.

4. **AC4 precondition guard:** Even if cadence met, if `signals.sessionsSinceLast === 0 && signals.learningsSinceLast === 0`, skip with reason `no-new-input-since-last-run`. The Final Report (Phase 6) MUST include the literal string `dialectic: skipped (no new input since last run)`.

5. If `decision.trigger === true`: **do not dispatch a subagent** (see #614 — no `evolve` agent exists; `dialectic-deriver` is read-only and cannot write the sidecar). Instead, emit a manual-cadence nudge and continue:

   `auto-dialectic: cadence reached (${decision.reason}) — run /evolve --dialectic --dry-run manually in the next session, review .orchestrator/dialectic-pending.md, then apply with /evolve --dialectic --apply.`

   The `shouldDispatchAutoDialectic` decision helper and `scripts/lib/auto-dialectic.mjs` lib stay in use: they compute the cadence signal that drives this nudge.

6. When the nudge is emitted (cadence reached), update `.orchestrator/dialectic-last-run` via `writeDialecticLastRun({ repoRoot, isoTimestamp: new Date().toISOString() })` so the cadence counter advances and the nudge does not repeat every session. Atomic; failures non-fatal.

7. Record outcome (skipped / nudge-emitted) for Phase 6 Final Report: `auto-dialectic: manual /evolve --dialectic --dry-run recommended (cadence reached) — apply with /evolve --dialectic --apply next session`.

The `.orchestrator/dialectic-pending.md` sidecar is intentionally outside the vault tree — vault-mirror (Phase 3.7) MUST exclude it from its scope.

Cross-reference: PRD F2.5 acceptance criteria (#506); `scripts/lib/auto-dialectic.mjs` API.

> **Dialectic chain rationale** — design choices in the manual `/evolve --dialectic` chain (`/evolve → runDialecticDeriver → dispatchAgent → Agent`). Session-end no longer auto-dispatches this chain (see #614 — the `evolve` agent never existed); the rationale below applies when you run `/evolve --dialectic` manually:
> - **/evolve → subagent (not direct invoke):** the manual `/evolve --dialectic` skill spawns a subagent so the dialectic pass runs in a fresh context window — keeping the deriver's input-heavy payload (top-50 learnings + last-10 sessions + 2 peer cards + steering) out of the invoking coordinator's context, and letting the deriver run as Haiku while the coordinator stays Opus.
> - **/evolve → runDialecticDeriver (not direct dispatchAgent):** /evolve owns argument parsing, config resolution, dry-run/apply gating, error-handling, and sidecar writes; runDialecticDeriver owns the pure derivation pipeline (load → payload → budget-check → dispatch → parse → guard). Separating skill-level orchestration from deriver business logic lets unit tests exercise the deriver without standing up the full evolve skill.
> - **runDialecticDeriver → dispatchAgent (DI boundary):** per `.claude/rules/prompt-caching.md:3`, session-orchestrator forbids direct `@anthropic-ai/sdk` imports in business logic (the harness manages caching at the platform layer). dispatchAgent is the injected boundary — the evolve skill wires the real `Agent({...})` harness call at runtime, tests pass a `vi.fn()` mock. Same DI shape as `scripts/lib/autopilot.mjs::runLoop({opts})` (cf. `scripts/dialectic-deriver.mjs:7-16,531`).

### 3.6.8 Reconciliation Rule Proposals (#696, FA3)

> Gate: Skip this phase entirely when ANY of:
> - `persistence` is `false` in Session Config
> - `reconcile.enabled` is `false` (default: `false` — opt-in; this is the silent no-op path for all repos that have not opted in)
> - `.orchestrator/metrics/learnings.jsonl` does not exist OR contains zero entries

After the auto-dialectic nudge decision is made (Phase 3.6.7), and when the reconcile engine is enabled, run the **reconciliation engine** to turn high-confidence learnings into conditional-rule proposals and present them to the operator via `AskUserQuestion` multiSelect. Approved proposals flow to `.claude/rules/` via `writeApprovedRules`. Rejected proposals are archived to `.orchestrator/reconcile.rejected.log`. The engine NEVER writes `.claude/rules/` itself — every write is operator-AUQ-gated (#693 FA2/FA3 brandmauer).

#### Coordinator-direct procedure

1. Read Session Config: `reconcile.enabled` (default `false`), `reconcile['rule-expiry-days']` (default `null` — falls back to per-type TTL in the engine), `reconcile['confidence-floor']` (default `0.5`), `reconcile['min-rule-days']` (default `7` — floor window (days) applied to a proposed rule's `expires-at` so a near-dead or already-elapsed natural expiry never produces a born-dead rule, issue #741.1), `reconcile['min-insight-chars']` (default `24` — opt-in minimum insight length gating the eligibility placeholder-insight check, issue #741.2). If `reconcile.enabled` is not `true`, log `reconcile: disabled (reconcile.enabled=false)` and skip all remaining steps.

2. Invoke `runReconcile` from `scripts/lib/reconcile/engine.mjs`:

   ```javascript
   import { runReconcile } from '${PLUGIN_ROOT}/scripts/lib/reconcile/engine.mjs';
   const { proposals, rejected, summary, error } = await runReconcile({
     repoRoot: process.cwd(),
     ruleExpiryDays: config.reconcile['rule-expiry-days'] ?? undefined,
     minRuleDays: config.reconcile['min-rule-days'] ?? undefined,
     minInsightChars: config.reconcile['min-insight-chars'] ?? undefined,
     now: new Date(),
   });
   ```

   `runReconcile` NEVER throws. If `error` is present on the return value, treat it as a non-fatal failure (see Failure modes below). `proposals` is an array of `{ learningKey, slug, path, content, confidence, candidateId, status: 'proposed' }`; `rejected` carries the ineligible or already-proposed learnings with their audit reasons; `summary` carries `{ eligible, proposed, rejected, errors }` counts.

   > **Note:** `runReconcile` does NOT itself apply a confidence floor — the engine proposes every *eligible* learning and carries each one's `confidence` through. The operator's `reconcile['confidence-floor']` is the **delivery gate**, applied in the next step.

2b. **Apply the confidence floor (delivery gate).** Filter the engine's proposals by `reconcile['confidence-floor']` (default `0.5`) BEFORE the sidecar write and AUQ, so only sufficiently-confident proposals reach the operator:

   ```javascript
   const floor = config.reconcile['confidence-floor'] ?? 0.5;
   const surfaced = proposals.filter((p) => typeof p.confidence === 'number' && p.confidence >= floor);
   ```

   For the remainder of this phase, operate on `surfaced` wherever "proposals" is referenced below. Low-confidence proposals are neither surfaced nor written; they remain eligible in a future session if their confidence rises (the idempotency sidecar does not mark them processed because they were never approved/written).

3. If `surfaced.length === 0`: log `reconcile: 0 proposals above confidence floor (eligible=${summary.eligible}, rejected=${summary.rejected}, floor=${floor})` and continue. No AUQ, no sidecar write.

4. **Write the human-readable proposal sidecar** `.orchestrator/metrics/reconcile-pending.md` so the operator can review raw content outside the AUQ:

   ```
   # Reconciliation Rule Proposals — <ISO timestamp>
   Session: <sessionId>
   Engine: ${summary.eligible} eligible → ${summary.proposed} proposed, ${summary.rejected} rejected; ${surfaced.length} above confidence floor
   
   ---
   
   ## Proposal 1 of N — <slug> (conf=<confidence>)
   
   <content>
   
   ---
   
   ## Proposal 2 of N — ...
   ```

   Write failures are non-fatal — log WARN and continue to the AUQ.

5. **AUQ pagination logic**: partition proposals into FIFO batches of 4 inline:

   - Empty proposals → silent skip (gate step 3 already handles this).
   - 1–4 proposals → single multiSelect call with all proposals as options.
   - 5+ proposals → sequential multiSelect calls in batches of 4 (FIFO order; final batch may have < 4 proposals).

   ```javascript
   const BATCH_SIZE = 4;
   const batches = [];
   if (Array.isArray(surfaced) && surfaced.length > 0) {
     for (let i = 0; i < surfaced.length; i += BATCH_SIZE) {
       batches.push(surfaced.slice(i, i + BATCH_SIZE));
     }
   }
   ```

   Iterate `batches` and emit one `AskUserQuestion` per batch with `header: "Reconciliation — Confirm Rule Proposals (Batch N of M)"`. Option label format: `<slug-40> | conf=<confidence>`. Option description: first 80 chars of the rendered `content` (the rule prose preview). `multiSelect: true`.

6. After all batches are answered, partition proposals into `approved` (any option selected across all batches) and `rejected` (all unselected). Proposals the operator rejected join the engine's `rejected` array for archival.

7. Invoke `writeApprovedRules` from `scripts/lib/reconcile/writer.mjs`:

   ```javascript
   import { writeApprovedRules } from '${PLUGIN_ROOT}/scripts/lib/reconcile/writer.mjs';
   const writeResult = await writeApprovedRules({
     approved,
     rejected: [...rejected, ...operatorRejected],
     repoRoot: process.cwd(),
     sessionId,
   });
   // writeResult = { written: number, archived: number, errors: string[] }
   ```

   `writeApprovedRules` is lock-serialised (via `withFileLock` on `.orchestrator/rules.lock`) and writes each approved proposal to `.claude/rules/<slug>.md`. Rejected proposals (engine-rejected + operator-rejected) are archived to `.orchestrator/reconcile.rejected.log` with reason `user-declined` for operator-rejected and the engine's own audit reason for engine-rejected.

8. Log outcome for Phase 6 Final Report: `reconcile: ${surfaced.length} surfaced → ${approved.length} approved (written: ${writeResult.written}), ${operatorRejected.length} operator-declined${writeResult.errors.length > 0 ? `, ${writeResult.errors.length} write-errors (see sweep.log)` : ''}`.

#### Failure modes

- If `runReconcile` returns an `error` field (top-level exception caught internally): log `⚠ reconcile: engine error (${error}) — skipping`; do not block session close. No AUQ, no sidecar write.
- If the sidecar write (step 4) fails: log warning `⚠ reconcile: reconcile-pending.md write failed (${err})`; continue to the AUQ regardless.
- If `writeApprovedRules` reports per-rule errors in `writeResult.errors`: log each to `.orchestrator/metrics/sweep.log` and continue. Per-rule fault isolation — one failed write does not prevent the others.
- All failures are non-fatal. Session close is never blocked by reconcile errors — same posture as Phase 3.6.7.

#### Cross-references

- Issues: #696 (FA3 Advisory Delivery), #693 (Epic — Reconciliation Engine), #695 (FA2 engine), #697 (FA4 Guardrails — next phase)
- Modules: `scripts/lib/reconcile/engine.mjs` (`runReconcile`) · `scripts/lib/reconcile/writer.mjs` (`writeApprovedRules`) · `scripts/lib/config/reconcile.mjs` (`_parseReconcile`)
- Sibling modules: `scripts/lib/reconcile/{eligibility,emitter,renderer,idempotency}.mjs`
- Sibling phases: 3.6.3 Memory-Proposals Collection (#501), 3.6.5 Auto-Dream (#502), 3.6.6 Skill-Applied Judge (#645 L3), 3.6.7 Auto-Dialectic (#506)
- AUQ spec: `.claude/rules/ask-via-tool.md` AUQ-004 (coordinator-only; this AUQ runs in the coordinator, not in a subagent)
