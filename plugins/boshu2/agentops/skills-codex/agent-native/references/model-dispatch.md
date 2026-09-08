# Model Dispatch (controller-session)

The caller selects multi-model judgment from the current session. Native Codex
plus the local shell is the default execution shape. Factories are optional
adapters; no mailbox, Agent Mail judgment path, AO queue or scheduler is added.
The working session passes bounded requests and returns runtime facts.

Risky-surface Validate requires a second fresh, cross-family exact-subject leg
under ADR-0017; elsewhere diversity is caller-elected. A required unavailable
leg remains `diversity_unsatisfied`: a single-family PASS is `NOT_PROVEN`.
Optional unavailable diversity may accompany the same-model result with that
disclosure. A single-family FAIL stands. Neither same-family agreement nor
majority vote establishes truth. Authors cannot issue their own binding PASS.

## Request and independent inputs

One request selects one worker and one result destination. Before dispatch,
resolve role, exact subject/acceptance references, authorized input bytes,
workspace, read/write scope, output/evidence destination, requested model,
requirement for a fresh context distinct from the author and every peer, finite
input/output limits and timeout from the caller and native runtime. Actual
context identity remains unknown until the native runtime reports it; verify
freshness and distinctness against that observed identity before relying on
judgment. These are invocation facts, not a new AO packet schema,
work store or budget account. Retry remains the caller's decision. Judge legs
receive read-only subject access; only their declared evidence output is writable.

Both the fresh and required cross-family legs receive the same exact subject
and unchanged acceptance with independently supplied initial inputs. Do not
include the author's desired verdict or a peer's conclusion. Seal initial
perspectives before cross-review; preserve findings and dissent afterward.
Each leg must actually load the required skill, subject and authorized evidence;
a skill-name mention or restating the procedure is not activation evidence.

Check task, source owner, model/provider and destination authorization before
reading pages, private citations, session-search hits or tracker comments.
Read permission is not permission to transmit to a reviewer or store in Git.
Native runtime/OS filesystem and egress controls enforce the declared profile;
prompt restrictions, a worktree or a same-user unrestricted process do not.
Unsupported protection prevents restricted-source dispatch. The repository
contract is ADR-0016, State tiers; this installed skill carries the requirements
above without depending on a repository-relative documentation link.

## Association before execution

Before launch, pass source-store/project/work identity and permitted frozen
intent references through the selected runtime input. The caller records the
dispatch association in native work comments/metadata or existing runtime facts
before execution can fail, with worker identity explicitly unknown if not yet
observed. At startup, capture actual runtime/session/context identity and return
it to that caller-owned channel before substantive work; final handoff is only
an additional reference. Do this for a child or resumed execution as well.

Keep requested model/ID, observed model/ID, controller identity, native parent
and resume predecessor distinct. Use the selected runtime's observed resume
identity even if it retains the original session ID; invocation observations
must still remain distinguishable. Never infer parentage from workspace,
filename, title or proximity. An unavailable startup/recording operation stays
a named failure with unknown identity, not a fabricated successful launch.

[Session associations](../../cass/references/SESSION_FORMATS.md#work-to-session-associations)
owns the fact distinctions: provenance, permitted locators, source bounds and
multi-work spans. Record only metadata authorized for the source owner and
recipient/destination; BD/Dolt is versioned, not secret storage. Neither this
reference nor the core phases gain tracker mutation, a new association store,
or runtime lifecycle authority. Required judgment freshness remains unsatisfied
when observed identities or their provenance are missing.

## Selected adapters

Check readiness only for the selected execution shape; never start a factory
merely because it is installed. No substitute can satisfy a required family.

| Selected shape | Readiness and use |
|---|---|
| Native Codex or `codex-exec` | Native fresh context or available `codex exec`; close stdin or supply the finite prompt for non-TTY runs. |
| Bounded Claude print | Available `claude` with the requested model/effort and a host-authorized native control profile; recipe below. |
| Interactive runtime / NTM | Only when the caller selects interactive hosting; verify native readiness, observation and stop support. NTM itself is never required. |
| Test runner | Synthetic conformance only; never evidence of a live model or semantic judgment. |

Prefer native Codex for Codex-family work. A Claude-family checkpoint may use
the explicitly selected bounded adapter below when the actual host permits it.
A selection is not permission to override a host prohibition, missing controls,
quota ceiling or provider guard in a specialist skill.

## Authorized bounded cross-family invocation

The first selected Claude-family profile is:

```sh
claude --print --model claude-fable-5-1 --effort xhigh
```

This is the command supplied to a native bounded invocation, not a standalone
unbounded shell recipe. Before starting it, the native runtime must:

1. Freeze exact authorized input and subject/acceptance identities; declare
   finite input and captured-output byte limits, wall-clock timeout and the
   allowed tools, source paths, output paths and egress endpoints. Missing
   limits or unsupported controls make this adapter unavailable.
2. Supply only that input on stdin, close stdin, and start a fresh context with
   the declared profile. Keep transcripts, stderr, diagnostics and review
   output in caller-selected protected non-Git storage; new recorders use
   native umask 077. Do not request permission bypass or broaden the profile.
3. Observe engagement and enforce the timeout and output cap through the native
   process/job control. On abnormal termination, capture available bounded
   state, stop the owned process tree through native controls and verify no
   owned descendants or hook/probe loops remain. Unverified cleanup is a
   disclosed runtime failure, never a successful review or permission to retry.
4. Return actual command/model/context identity, loaded input/skill/subject
   identities, exit or signal, timeout/truncation facts, output references and
   cleanup observations. Distinguish requested model from observed identity;
   missing identity or a wrong family cannot satisfy the required leg.

The selected native runtime retains process, timeout and output control. AO
does not become a scheduler or semantic workflow engine. This non-executable
reference does not change
Door9's policy for tracked executable code or production Go, introduce a
shipped runner, or relax specialist provider-name guards.

## Receipts and judgment

A successful prompt send proves transport, not engagement. Output bytes, exit
zero, a terminated process and clean cleanup prove only those facts. Only fresh
Validate can judge acceptance and persist `verdict.v2` when requested. Keep
model/context identities in evidence references and freshness attestation notes;
no verdict schema change is required and these attestations are not
cryptographic proof of independence.

Both required legs must pass the same exact subject for convergence. A split
never certifies PASS and findings do not disappear because a judge was preferred.
Return both results and unresolved dissent to the caller. Do not convene a
third judge, retry, or resolve truth by a vote on this recipe's initiative.

## Consumers

- Council: per-judge methodology and model/context identity, sealed initial
  perspectives, preserved dissent and no majority-derived PASS.
- Idea Genie duel: optional selected model pins and sealed perspectives within
  its owning challenge contract; specialist provider guards remain intact.
- Validate: fresh and required cross-family exact-subject judgments; this
  reference is the invocation owner and Validate remains the verdict writer.
