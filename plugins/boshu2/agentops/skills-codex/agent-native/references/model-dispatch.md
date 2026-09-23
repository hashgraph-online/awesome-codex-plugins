# Model Dispatch (controller-session)

Judgment defaults to a fresh, author-distinct context in the author's model
family: Codex/OpenAI reviews Codex/OpenAI work, and Claude/Anthropic reviews
Claude/Anthropic work. Use that runtime's configured capable model unless the
caller pins one. Other execution roles retain their caller-selected runtime.
Factories are optional adapters; the current session passes requests and
returns runtime facts without adding a mailbox, AO queue or scheduler.

`--cross-model [model]` on Validate or RPI, or an explicit "cross-model review"
request, adds a fresh judge from a different family. The optional model pins
that leg; absent a pin, select an authorized capable other-family model.
Council and other judgment strategies use fresh same-family contexts unless
the caller selects mixed models. These are skill prompt selections, not new
native CLI flags. Selection never grants source-disclosure or provider access.

Risk changes evidence depth; it does not automatically select another family.
An explicitly required unavailable leg remains `diversity_unsatisfied`: a
single-family PASS is `NOT_PROVEN` for the combined request. Optional unavailable
diversity may accompany the same-family result with that disclosure. A delivered
FAIL stands. Neither agreement nor majority vote establishes truth. Authors
cannot issue their own binding PASS.

## Request and independent inputs

One request selects one worker and one result destination. Before dispatch,
resolve role, exact subject/acceptance references, authorized input bytes,
workspace, read/write scope, output/evidence destination, requested model,
requirement for a fresh context distinct from the author and every peer, finite
input/output limits and time bounds from the caller and native runtime. Actual
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

Prefer the matching native runtime for same-family judgment. A Claude-family
checkpoint may use the bounded adapter below when the actual host permits it;
Codex-family judgment may use a fresh native Codex context or `codex exec`.
A selection is not permission to override a host prohibition, missing controls,
quota ceiling or provider guard in a specialist skill.

## Review duration

Do not impose a fixed ten-minute timeout. Use an explicit caller-selected
review timeout or derive the invocation timeout from the remaining caller/native
deadline; when both exist, the earlier bound wins. A headless call still needs
finite time and input/output bounds under host policy. If neither time bound is
available, report the missing invocation bound before launching; do not invent
a universal review limit. Native cancellation, output caps and cleanup remain.

For the repository's shared adapter, supply `CODEX_EXEC_TIMEOUT` in seconds or
`CODEX_EXEC_DEADLINE_EPOCH` as an absolute timestamp. With no explicit timeout,
the adapter uses the remaining deadline without a ten-minute clamp. Reuse the
same goal deadline across invocations; retries, context resets and renewed
connections do not renew the caller's allowance. Record a timeout as an
incomplete review, preserve its bounded output, and return control to the caller.

## Authorized bounded Claude invocation

For a caller-selected Fable profile, the native command is:

```sh
claude --print --model claude-fable-5-1 --effort xhigh
```

This is one caller-selected profile, not a mandatory model pin. Select another
authorized capable Claude profile when requested. For native model evidence,
request `--output-format stream-json --verbose`; preserve assistant-envelope
model/context fields and the terminal result, not just rendered text. Inspect the
installed CLI contract before choosing flags. An authorized public/toy read can
use native safe-mode/restricted controls with tools, customizations, MCP and
session persistence disabled when the installed runtime supports them. Those
controls and cleared toy bytes do not establish restricted-source isolation.

The command is supplied to a native bounded invocation, not a standalone
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
model/context identities in [native judgment receipt references](judgment-receipts.md)
and freshness attestation notes. `ao provenance verify-judgments` compares all
caller-required profiles with exact native transcript spans, independently
supplied subject and acceptance, actual termination and omissions. Requested
profile echo or unknown native identity cannot satisfy required diversity.
No verdict schema change is required, and these attestations are not
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
- Validate: fresh same-family and explicitly selected cross-family judgments; this
  reference is the invocation owner and Validate remains the verdict writer.
