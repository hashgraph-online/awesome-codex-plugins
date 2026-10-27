# Session Protocol (Always-On)

The Live PM runs automatically. No commands needed. This document details the
internal procedures the skill follows at each phase of a conversation.

## Session Start (automatic)

### If `ara/` exists

1. **Read state silently**:
   - `ara/trace/sessions/session_index.yaml` → last session date, summary, open threads
   - `ara/logic/claims.md` → count by status
   - `ara/staging/observations.yaml` → pending count, promotion candidates

2. **Deliver briefing contextually**:
   - If user jumps straight into a task → weave context into your first response:
     "Before we dive in — last session you were testing C04, result was 92%. Two open threads."
   - If user asks what's going on / where we left off → give full briefing
   - Never lead with the briefing if the user clearly has a specific task in mind

3. **Create session record**:
   ```
   ara/trace/sessions/YYYY-MM-DD_NNN.yaml
   ```
   Initialize with start time and empty events list.

### If `ara/` does not exist

- Don't create it unprompted on the very first interaction
- If you detect research-significant discussion (decisions, hypotheses, experiments),
  ask once: "Want me to track this project's research process? I'll set up `ara/`."
- On confirmation → initialize full directory structure + bootstrap from current conversation

## During Session (continuous, invisible)

### Event Detection Loop

After every substantive exchange, evaluate:

```
1. Decision made?     → write to exploration_tree.yaml
2. Result observed?   → write to exploration_tree.yaml + evidence/
3. Approach failed?   → write dead_end to exploration_tree.yaml
4. Claim stated?      → write to claims.md
5. Trick discovered?  → write to heuristics.md
6. Direction changed? → write pivot to exploration_tree.yaml
7. AI wrote code?     → log to session record (ai_actions)
8. Interesting note?  → write to staging/observations.yaml
```

### Writing Protocol

1. **Read the target file first** to get the next available ID
2. **Append** new entries — never overwrite existing content
3. **Establish bindings immediately**: claim→proof, heuristic→code_ref, decision→evidence
4. **Use correct provenance tag** based on who generated the information
5. **Keep YAML valid** — verify structure mentally before writing
6. **Be silent about it** — don't mention the logging unless asked

### Provenance Decision Tree

```
User typed/said it explicitly?
  → provenance: user

AI ran code/test/command that produced this?
  → provenance: ai-executed

AI noticed pattern, inferred meaning, proposed interpretation?
  → provenance: ai-suggested

User corrected an AI suggestion?
  → provenance: user-revised

Uncertain?
  → provenance: ai-suggested  (conservative default)
```

### What Gets Logged to Session Record

The running session record (`trace/sessions/YYYY-MM-DD_NNN.yaml`) accumulates:

- Every event written to any ARA file (type, id, provenance, one-line summary)
- AI actions: code written, commands run, files created/modified
- Claims touched: which claims were created, advanced, weakened, confirmed
- Open threads: unresolved questions or incomplete work
- AI suggestions pending: things AI proposed that user hasn't confirmed

### Conflict Detection

When writing a new entry, check for conflicts:
- New claim contradicts existing claim → add `<!-- CONFLICT: see C{XX} -->` to both
- New evidence weakens existing claim → update claim status to `weakened`
- New decision reverses previous decision → log as `pivot` linking to original decision

## Session End (automatic)

### Triggers

Session end is detected when:
- Conversation is clearly wrapping up ("thanks", "that's all", user goes quiet)
- Context window is getting compressed (system is summarizing old messages)
- User explicitly says goodbye or indicates end of work

### Procedure

1. **Finalize session record**:
   - Set `ended` timestamp
   - Write summary (one line capturing the session's main outcome)
   - Ensure all buffered events are flushed to ARA files

2. **Update session index**:
   Append entry to `ara/trace/sessions/session_index.yaml`:
   ```yaml
   - id: "YYYY-MM-DD_NNN"
     date: "YYYY-MM-DD"
     summary: "{main outcome}"
     events_count: {N}
     claims_touched: [C{XX}, ...]
     open_threads: {N}
   ```

3. **Maturity check** on staging:
   - 3+ observations on same topic → auto-promote (with `ai-suggested` provenance)
   - Observation with evidence → promote to `evidence/`
   - Stale entries (3+ sessions old) → flag with `stale: true`

4. **Brief session close note** (keep to one line):
   ```
   [PM] Session captured: 3 decisions, 1 experiment, 2 claims advanced. 1 open thread.
   ```

## Cross-Session Continuity

### How Memory Persists

The agent has no built-in cross-session memory. The ARA itself IS the memory:
- `session_index.yaml` → what happened when
- `claims.md` → what's known vs. unknown
- `exploration_tree.yaml` → the full research trajectory
- `staging/observations.yaml` → loose threads
- Individual session records → detailed per-session history

### Session Start Reconstruction

At the start of each conversation, reading these files reconstructs full project context.
The agent effectively "remembers" everything through the artifact it built.

### Open Thread Tracking

Open threads carry forward automatically:
- Each session record lists `open_threads`
- At session start, the latest session's open threads are surfaced
- When a thread is resolved in a later session, note it in that session's events

## Emergency / Abrupt End

If conversation ends without proper session close:
- Events already written to ARA files are safe (written incrementally)
- Session record may be incomplete — next session should detect this and note it
- No data is lost because writes happen in real-time, not batched at end
