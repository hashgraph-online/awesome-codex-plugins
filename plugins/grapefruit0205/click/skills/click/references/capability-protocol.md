# Structured Capability Protocol

Use protocol version `1` for inspection, mutation, managed local services, and explicit non-argv evidence completion. Final argv verification uses version `2` because every check is bound to a declared `evidence_id`. Every executable and argument is a separate JSON string. The Hook executes accepted argv arrays with `shell=False` in a new POSIX session or Windows process group; never hide a shell, pipeline, redirect, command substitution, or background job inside an entry.

## Inspection

Use for an ambiguous but read-only command, and during Evidence, approved Guarded implementation, or `click-gate review` for tracked evidence:

```text
click-gate inspect '{"version":1,"commands":[["git","status","--short"],["sed","-n","1,160p","src/app.py"]]}'
```

Every command must match the Hook's read-only argv policy. One request may contain up to eight commands, which run serially and stop on the first failure. The executable must be a bare name: names containing `/` or `\\`, Windows drive-prefixed forms such as `C:cat.exe`, and UNC forms are rejected. Immediately before execution, Click removes empty, relative, and repository-resolving PATH entries, rejects a candidate whose lexical path or resolved target is inside the nearest containing Git repository (or the current working directory outside Git), resolves the accepted program to an absolute real path, and executes that path with the sanitized PATH. Read children drop inherited `LD_*`, `DYLD_*`, `GCONV_PATH`, and `LOCPATH`. Recognized direct Bash reads are rewritten through this same runner even when no active contract or review ledger exists; they remain lightweight and untracked in that state, but the original shell no longer resolves their executable. Git inspection uses subcommand-specific positive option policies rather than a generic subcommand allowlist plus dangerous-option blacklist; `git grep` and `git cat-file` are not currently accepted. Global pagination and caller-supplied config overrides such as `-p`, `--paginate`, `-c`, and `--config-env` are rejected. Arbitrary `--format` and `--pretty` output, signature-rendering options, and `git status -v/-vv` are also excluded. Accepted Git reads run through a dedicated executor that additionally strips inherited `GIT_*` variables, ignores system/global Git config, forces a safe default log format with signature display disabled, uses `--no-pager` and `--no-optional-locks`, disables fsmonitor and external diff, and adds `--no-ext-diff` plus `--no-textconv` to supported diff-rendering commands. Local Git and SSH programs use the same absolute executable resolution. The Hook rejects shell interpreters and write-capable options. In active review and implementation the runtime ledger stores a request digest and result metadata, applies the existing output cap, and detects repository-wide inventory from the validated argv. Before any tracked read executes or returns a cached result, the runner atomically claims the managed state path, active status, current revision, request digest, one-use token, replay state, and freshness. An unclaimed startup reservation expires after 30 seconds; a claimed synchronous read has no elapsed-time release and continues to block mutation and final verification until its result is recorded or the user explicitly cancels. Tampered, unmanaged, stale, expired, cancelled, or replayed runners execute no read and return no cached content. A safe synchronous startup failure records failure and clears its claim. Broad classification, completed identical requests, and fixed failure counts are retained for advisory context only. A fresh repeat receives a new one-use token; an active same-digest reservation remains blocked so its exact token and result record cannot be replaced. All preceding runner claims, state and authority checks, mutation and verification interlocks, and operational limits remain unchanged.

A separate heuristic cache may retain the complete stdout and stderr of one
successful local `cat`, supported `sed -n`, or supported `rg` command. It is
available only when an Evidence, approved Guarded, or review state supplies the
one-use observation runner. Cache identity binds the normalized request, cwd,
trusted executable content, relevant environment, explicit file contents, and
for directory searches a conservative recursive inventory plus project ignore
files. The supported directory subset rejects follow/hidden/no-ignore modes;
other options or inputs that cannot be bounded execute normally. Results over
48 KB, failures, and incomplete output are never cached. Entries use an
owner-only plugin-data directory, an integrity digest, bounded count and bytes,
and a 24-hour TTL. Missing, expired, permission-invalid, corrupt, or changed
entries fail open to the normal read. A hit records `actual_process_executed`
as false and never enters the evidence registry, claims completion, or changes
verification reuse authority. The first hit at a revision gives a compact
source/bytes/lines notice; later identical hits do not repeat it. Add
`"fresh":true` to the version 1 inspection request to force the original
read/search process and refresh an eligible entry.

Experimental SSH inspection accepts only the same bounded Git policy further narrowed to `status`, `rev-parse HEAD`, `merge-base`, and `remote get-url`. It accepts no caller-supplied SSH options, assumes the remote login shell implements POSIX quoting, requires an already-known host key, disables interactive password flows, host-key updates, forwarding, local commands, and TTY allocation, and uses a 10-second connection timeout plus bounded keepalives. Unknown hosts, non-POSIX remote shells, unreachable hosts, and unsupported SSH implementations fail closed. This convenience is not a general remote-command capability or a security sandbox.

Recognized simple Bash reads remain compatible: the Hook converts safe direct syntax into the same internal argv request. It accepts direct `&&` sequencing only when every segment is independently read-only; it rejects pipelines and other shell control because their behavior is not represented by the protocol. `pdfinfo FILE` and stdout-only `pdftotext FILE -` are accepted reads; `pdftotext` with an implicit or explicit output file remains a mutation and is rejected by inspection. Use explicit `inspect` whenever a legitimate read is not recognized.

## Mutation

Use this for an implementation command that may write files or generated state. Evidence mode relies on host authority; Guarded mode first requires the later approval turn to pass the emitted `contract_id`:

```text
click-gate mutate '{"version":1,"argv":["python3","scripts/generate.py","--target","src"]}'
```

The Hook requires Evidence or approved Guarded state, rejects shell interpreters and direct process-control executables such as `kill`, `pkill`, `taskkill`, and `Stop-Process`, issues a one-use runner token, increments mutation revision, and invalidates stale evidence. The runner atomically claims the managed state path, runtime status, exact request digest, token, replay state, and expiry. A tampered, unmanaged, expired, or replayed request executes no mutation command. Stateful rewrites carry the Hook-selected canonical `gate-state` path instead of trusting ambient configuration. Each subprocess starts in an isolated process group. Continue to use `apply_patch`, `Edit`, or `Write` directly for ordinary file edits.

Recognizable long-running development servers are rejected here because a foreground server can hold the entire one-shot mutation open. Use the managed service capability instead.

## Automatic sharding setup

The setup facade keeps users out of capability JSON while retaining the same
one-use mutation and verification runners:

```text
click-gate sharding init
click-gate sharding init -- python3 -m unittest discover -s tests -q
click-gate sharding status
click-gate sharding refresh
```

Status and command selection are read-only. Approved `init -- ...` creates an
external review artifact. A fresh Guarded contract bound in plain language to
that proposal digest may use `refresh` to create absent policy files. After the
user commits those exact files, subsequent refreshes perform the candidate
parent/child bootstrap and submit the fixed
`E_AUTO_SHARDING_BASELINE` parent source through protocol-v2 verification. See
[automatic sharding setup](automatic-sharding-setup.md) for its state machine,
Git boundary, recovery, and dashboard measurement scope.

## Managed local service

Start one recognizable local development server under Evidence or approved Guarded state, and stop it when Browser or integration work is finished:

```text
click-gate service '{"version":1,"action":"start","argv":["python3","-m","http.server","4173","--bind","127.0.0.1"]}'
click-gate service '{"version":1,"action":"stop"}'
```

Only `start` and `stop` are accepted. `start` requires direct argv for a recognizable development server and counts as a mutation, so prior completion evidence becomes stale. `stop` omits `argv`. Before either the start runner or its detached supervisor may spawn a process, it atomically claims the approved service id, request-plus-working-directory digest, and one-use token; replay, tampering, stale state, or cancellation before the corresponding claim therefore launches no additional server. A cancellation racing after a successful claim may briefly launch the child, which is then terminated when its state can no longer be recorded. The supervisor retains the exact child handle, starts the child in its own process group, and terminates only that retained group. It responds to explicit stop and `SessionEnd`, applies bounded start/stop waits, and enforces a final two-hour lifetime ceiling. One managed service may be active per contract. This avoids exposing a general process-control capability to the agent.

## Observer controls and Shadow dashboard

Observer collection is lifecycle-local. New Evidence lifecycles default to
`auto`; Guarded defaults to `off`. Explicit selection persists across completed
Evidence turns:

```text
click-gate observer auto
click-gate observer off
click-gate observer shadow
click-gate observer authoritative
click-gate observer runtime
click-gate observer status
```

`shadow` attaches the selected non-authoritative collector to compatible argv
verification and never grants reuse. `authoritative` is accepted only after a
separately approved Guarded contract and prepares the exact CPython 3.12.3
profile for the current platform: Linux with strace 6.8, privileged macOS with
`fs_usage`, or Windows with inbox ETW tools. Linux is validated on a real host;
the macOS and Windows profiles are implemented and await real-host validation.
Preparation is candidate state, not an observation or reuse grant. Only a
complete runner-signed v2 observation from the original one-time execution can
support successor requalification. These controls do not advance the mutation
revision or change evidence. Dashboard
activation is independent: opening the viewer does not enable collection, and
stopping the viewer does not disable it. See
[Authoritative Observer v2](authoritative-observer-v2.md) and
[Shadow Observer v1](observer-v1.md).

Open the current lifecycle's non-authoritative Evidence Map and ROI view only
when requested:

```text
click-gate dashboard start
click-gate dashboard status
click-gate dashboard stop
```

This viewer is distinct from a development service. It is read-only, does not
advance the mutation revision, and never changes evidence status. Start uses a
one-use launch token and prints a random access token in a `127.0.0.1` URL
fragment. Click persists only token digests. The server validates the loopback
Host header and Bearer token, serves no external assets, grants no CORS access,
uses a restrictive Content Security Policy and no-store responses, and exposes
only one sanitized snapshot endpoint. It has no mutation method, arbitrary
file reader, raw-state endpoint, or remote bind. Stop is state-cooperative;
`SessionEnd` also requests cleanup, and a two-hour lifetime is final. See
[Shadow Intelligence v1](shadow-intelligence-v1.md) for schema, privacy,
prediction, map, and ROI semantics.

## Verification

Submit a nonempty set of argv checks with stable evidence ids. Guarded ids are declared in the contract; Evidence ids register dynamically on first accepted use:

```text
click-gate verify '{"version":2,"workdir":"/absolute/path/to/repository","checks":[{"evidence_id":"E1","argv":["python3","-m","unittest","discover","-s","tests","-q"],"class":"broad"},{"evidence_id":"E2","argv":["git","diff","--check"],"class":"targeted"}]}'
```

Classes are `targeted`, `broad`, and `deep`. They remain compatibility metadata, not cost, sufficiency, or evidence strength. Several adjacent checks may share one id and all must pass. The first accepted group reserves its normalized digest for the active intent or contract; later attempts must match it. Guarded rejects unknown or wrong-kind ids. Evidence creates argv sources from valid ids but grants no runtime dependency authority. Protocol-v1 verification, empty requests, missing ids, and shell-string batches are rejected.

`workdir` is an optional top-level absolute path for compatibility with hosts whose session cwd is already the execution directory. Supply it whenever the execution tool selects a different directory. Click resolves and stores the canonical directory before shard discovery, preserves it through pending-check filtering and shard expansion, and the one-use runner compares it with its real cwd before claiming the batch. A missing directory, relative path, or mismatch executes no check. Codex Hook input exposes the session cwd rather than the unified exec call's selected workdir, so Codex callers using a per-call workdir must include this field explicitly.

An exact broad group may be decomposed by committed [Evidence Shards v1](evidence-shards-v1.md). The submitted parent id and argv remain the approval identity; stable internal child ids cannot be called directly. Each child uses the normal runner and evidence receipt path, so a successful child survives a same-revision sibling failure and a retry runs only unresolved children. The runner revalidates the committed map, identical working copy, complete inventory, and exact child bindings immediately before execution. Any absent, changed, malformed, incomplete, unsupported, or racing plan falls back to the original parent suite or executes no child. The map authorizes decomposition, never reuse.

Python checks must use an explicit supported pytest, unittest, or coverage module runner; Windows `py -3 -m ...` and `uv run pytest` are recognized. Python `-c` and direct Python scripts are not verification capabilities. Exact-file `node --check` and `node --test` are targeted; project-wide `node --test` is broad, while Node eval/print forms are not verification. The verification child receives the full environment except shell and launcher bookkeeping, but the receipt fingerprints only the variables that change how a check runs: `PATH`, `HOME`, temp directories, locale and time zone, CI markers, proxy and certificate settings, and the interpreter and toolchain families (`PYTHON*`, `VIRTUAL_ENV`, `CONDA_*`, `PIP_*`, `NODE_*`, `NPM_CONFIG_*`, `JEST_*`, `VITEST*`, `GO*`, `CARGO_*`, `RUST*`, `JAVA_*`, `DOTNET_*`, `LD_*`, `DYLD_*`, and similar). Host, IDE, agent and shell session variables are outside the fingerprint by design; a value they carry is a documented runtime assumption. A repository owner widens the fingerprint with a working-tree `.click/environment.json` (`{"version": 1, "fingerprint": ["DATABASE_URL", "APP_*"]}`); the file can only add reruns, never reuse, and a malformed file adds nothing. The same fingerprint function runs in the Hook and in the one-use runner, so a variable that only a launcher adds cannot separate the prepared and executed bindings. The prepared key/value HMAC records are protected by an aggregate runner-token binding. If a prepared value changes or disappears before the runner claims the batch, the runner projects current values onto the prepared key set, ignores runner-only additions, re-fingerprints the canonical environment, and rebinds the reserved environment digest without another approval. The exact resolved executable fingerprint remains fixed, so an executable change or malformed or tampered binding still fails closed. A successful receipt records the actual rebound environment digest. If runner admission otherwise fails before any check executes, only the exact digest/token-matched unclaimed reservation returns to `ready`; it records no evidence and consumes no test-failure retry. Claimed, stale, unavailable, tampered, and replayed state remains fail-closed. A claimed batch remains running until it records a result, the runner receives an interrupt and records exit `130`, or the contract is explicitly cancelled; only an unclaimed reservation may expire into a retry. Click terminates the retained isolated child process group before recording an interrupted check as non-passing, so an ordinary Ctrl-C does not leave a permanent claimed-runner lock.

The Hook skips a successful same-revision check only when the receipt still matches the active intent or contract, normalized group, protected tree, environment, executable, and host coverage. For dependency-aware cross-revision reuse, an approved Guarded contract may use approval-bound `dependencies`, a committed manifest entry, or both, but the baseline must carry a complete `runtime-dependency-observation-v2` attestation produced by that invocation's one-use runner. Evidence uses host execution authority and the same signed observation boundary; absent owner dependency policy, the versioned runtime-observed-inputs-v1 provider binds built-in capture rules. Caller-provided JSON cannot mint this authority. Complete observed inputs are rechecked even on the same-revision and successor exact-receipt paths. Approval-bound paths and concrete manifest paths remain hard dependencies. A complete observation may refine expanding manifest patterns (`*`, `**`, and directory prefixes) to repository inputs actually consumed, and the resulting effective inputs are hashed. An unavailable or failed observer, an unsupported input, or incomplete process coverage makes only cross-revision reuse unavailable; it does not change the check's PASS/FAIL result and never causes a hidden second execution. A native observation whose only gaps are a followed child process, concurrent threads, or dynamic runtime introspection is stored as `conditional`: it may back an explicitly conditional cross-revision reuse (authority `conditional-python-observation`) only while every snapshotted input stays unchanged, and every host output and status view discloses that completeness is unproven. The provider, profile, backend and companion identities, relevant normalized entry, observation digest, input snapshots, check, shard, original execution, identity, Git root and tree, contract, environment, executable, host coverage, and host-recorded mutation snapshot must match. Missing post state or later drift runs the check. Reuse never occurs outside Git.

The separate [Shadow Observer v1 contract](observer-v1.md) emits non-authoritative telemetry beside compatible argv verification only after `click-gate observer shadow` explicitly enables it for the lifecycle. Shadow remains opt-in. New Evidence lifecycles select automatic input capture; Guarded defaults to `off`. The selected backend may use trusted Linux `strace`, native macOS `fs_usage` when the current process already has permission, or the trusted Windows inbox `logman.exe` and `tracerpt.exe` ETW tools. Its bounded aggregate is retained only in the active lifecycle; raw events are discarded. Click never elevates privilege. [Shadow Intelligence v1](shadow-intelligence-v1.md) may fingerprint that aggregate after a successful run, freeze a prediction before the next real rerun, and evaluate it afterward. Neither layer has a conversion or bridge into `runtime-dependency-observation-v2`, evidence reuse, approval, completion, or receipt export, and neither can authorize a skipped check. Collector or analysis absence and failure leave the established verification path and result unchanged.

The observer-free alternative is a committed `.click/evidence-reuse.json` file with exact `checks` groups and `reuse_if_only_changed` patterns. A successful run stores its unchanged policy digest and an effective Git baseline consisting of the commit identity plus bounded fingerprints for dirty and untracked files. Preflight compares that baseline with the current commit and worktree, reports net changed paths, and reuses only if every path matches the same policy entry. The policy and dependency-map paths are protected from self-authorization. Missing or edited policy, duplicate groups, malformed patterns, unsupported file types, excessive or racing changes, unmerged state, unavailable Git data, and any unlisted path rerun without asking. Environment, executable, contract, host coverage, and the host-recorded mutation boundary remain mandatory. A complete runtime observation takes precedence, so a safe-change entry cannot override a changed observed input. This policy is explicit repository-owner authority rather than automatic dependency discovery and needs no platform observer or extra install.

Host coverage identity is a compact receipt containing the canonical host, a deterministic digest of its registered pre/post tool surface, and the assurance `known-surfaces-only`. Verification preparation binds it to the one-use runner, the runner requires the registry to remain current before execution, and a successful argv source records it for later exact or dependency-aware reuse. Legacy evidence without this receipt remains readable but is rerun. This identity detects host or registry drift; it does not claim that a host emitted an event for a capability outside the registered surface, and it does not turn the Hook into an operating-system monitor.

Version 2 of `.click/evidence-reuse.json` additionally requires `inputs` on
every entry. The owner declares the complete file-content boundary before the
baseline. Both the allowed-change envelope and unchanged input fingerprints
must hold, including ignored files, directory membership and absent literal
inputs. Input drift during execution cannot mint a reusable scoped baseline.
Policy v1 semantics remain unchanged. Static graphs and proposed shards never
generate this authority automatically. See the [file-input policy example and
limits](../../../docs/architecture/verification-economics.md).

The optional repository manifest is `.click/evidence-dependencies.json`:

```json
{
  "version": 1,
  "entries": [
    {
      "checks": [["python3", "-m", "pytest", "tests/auth"]],
      "paths": ["src/auth/", "tests/auth/", "pyproject.toml"]
    }
  ]
}
```

Only the manifest blob committed at `HEAD` is policy authority. A changed, deleted, malformed, or replaced working-tree copy cannot narrow or replace it; if the verification command reads that copy, runtime observation makes its content an effective input. Each committed entry maps one exact adjacent argv group to deterministic patterns. Approval-bound contract paths remain hard dependencies. Concrete manifest paths remain hard dependencies, while a complete runtime observation may refine expanding manifest patterns to the members actually consumed. Cache identity uses the relevant committed entry rather than the whole manifest, so a committed change to an unrelated entry does not invalidate this source; a committed changed, removed, duplicate, malformed, or unmatched relevant entry does. `*` remains within one segment, `**` as a complete segment crosses directories, and trailing `/` is a prefix. The receipt records the sorted effective inputs. Observed missing-path lookups and directory listings may also be represented so later creation or membership changes invalidate the receipt. Repository-internal relative symlinks are accepted; the link text, resolved path, and target content are hashed, while absolute, external, broken, cyclic, or unsupported special-file targets rerun verification. Ordinary unchanged failures may receive fresh separately authorized retries with advisory context rather than a fixed count denial. A verification batch that observably changed protected repository content remains blocked until an approved mutation repairs or reconciles the workspace.

In a Git worktree, the runner compares tracked and pre-existing non-ignored untracked content before and after the batch. If the initial protected snapshot cannot be established, no check executes. A protected-content change fails stale, increments the mutation revision, and invalidates every evidence source. Every new non-ignored untracked path created during the batch also fails stale and advances the mutation revision; source or configuration classification affects only the clarity of the message, not whether the workspace changed. Expected generated artifacts should be ignored or created during the approved mutation phase. Git-ignored paths, external dependencies, and external system state are outside this protected snapshot. Non-Git worktrees are outside the content snapshot and receipt-reuse boundary.

## Verification status

```text
click-gate status
click-gate status --json
```

`click-gate status` prints at most three short lines in the dashboard language selected by `CLICK_LANGUAGE`, then `LC_ALL`, `LC_MESSAGES`, or `LANG` (Korean by default): executed and reused counts with the estimated avoided time when a reuse has timing evidence, the runtime mode with the mutation revision and verification completion, and the next action. `click-gate status --json` (alias `status detail`) returns the full read-only progress report: task, summary counts, batch timing, per-check decisions with reason codes, the readiness projection, and the actionable report with bounded failure details. Both forms read ledger facts only; they never execute a check, change evidence status, or grant reuse.

## Completion receipt export and offline integrity verification

After every declared source is current for the final mutation revision and no
managed service or capability claim remains active, export the canonical
unsigned envelope once:

```text
click-gate receipt export
```

Receipt v2 binds an explicit authority block. Guarded binds contract identity
and approval turns; Evidence sets `contract: null`, `approval_bound: false`, and
`execution_authority: host`, while binding intent and follow-up turn digests.
Both bind capability claim commitments, final protected workspace digest, and per-source evidence result,
environment, executable, host-coverage, and dependency lineage. It excludes
raw argv, runner tokens and token digests, contract prose, and the workspace
path. Save the stdout JSON separately, then verify it without network access or
active contract state:

Unsharded exports remain receipt v2. A completion containing Evidence Shards
uses strict receipt v3 with the parent, complete child count, plan, relevant
entry, inventory, and per-child lineage digests. Offline verification continues
to accept legacy v1 and unsharded v2, and rejects incomplete v3 shard sets.

A completion that actually reuses evidence requalified from an earlier Evidence
task in the same host session and workspace uses receipt v4. It records the
origin batch, origin Evidence session, candidate digest, origin revision, and
the authoritative requalification mode (`exact`, `dependency`, or
`safe-change`). If that completion also contains shards, v4 retains the same
complete shard provenance required by v3. Merely retaining a successor
candidate never selects v4 and never creates reuse authority. Offline
verification accepts and validates v4 while retaining legacy v1-v3 support.

An actually applied successor from a completed Guarded contract selects v5
and records `origin_contract_id` instead of the v4 Evidence session identity.
The new contract's separate staging and approval remain current authority;
earlier approval, claims, tokens and unfinished work never transfer. Candidates
must requalify against current exact declared checks, dependency declaration,
workspace, environment, executable, known Hook coverage and existing change
rules. Incomplete or uncertain bindings run the check. v5 retains complete v3
shard provenance where present; offline validation still accepts v1–v4.

If a host omits the working directory selected by a nested execution tool,
export may recover it only from the sole canonical Git root shared by every
current argv evidence source. A stale, missing, non-canonical, or conflicting
root binding never selects an implicit workspace. Click still recomputes the
final protected tree and requires it to match current evidence before export.

If a supported host omits a mutation's matching `PostToolUse`, export never
invents an exit code. It may project that admitted host claim as `observed`
only after a later passing one-use verification at the same or a newer revision
and after final evidence/workspace matching succeeds. An unwitnessed host claim
or any active one-use runner still blocks export.

```text
click-gate receipt verify ./completion-receipt.json
```

This command performs strict schema, canonicalization, and digest checks and
reports `unsigned-integrity-only`. It does not claim publisher authenticity: a
coordinated rewrite of both body and digest remains detectable only after a
separate public-key signing layer is configured.

## Non-argv evidence completion

After collecting the assigned source, record it once:

```text
click-gate evidence '{"version":1,"evidence_id":"E-browser"}'
```

The id in this command must name a declared non-argv source. The Hook hashes the id before storing its typed per-revision state. It accepts `browser` only after a successful current-revision Browser observation and accepts `hosted`, `manual`, or `existing` as explicit agent attestations. It rejects unknown ids, duplicate current-revision completion, and every `argv` id. This makes each contract source visible to the state machine without pretending an unmatched hosted, manual, or existing event was independently proven.

## Browser primary evidence

Browser MCP calls are not an argv capability, but the Hook observes the canonical `mcp__node_repl__js` tool on `PreToolUse` and `PostToolUse`. During an approved contract it permits that tool only when `verification.evidence` contains one source with `kind: "browser"` and at least one `done_when.primary_evidence` references its id. The source description and condition prose are never searched for Browser keywords. Calls remain serial and require a stable `tool_use_id`; the matching result is recorded only against the assigned source and current mutation revision. The Hook hashes normalized input for advisory context. Repeats after success or repeated failure remain available with guidance, as do calls requesting a timeout above 30 seconds or an obvious wait above five seconds. There is no normal call-count or elapsed-session cap; after 256 normalized inputs, Click compacts the oldest per-input guidance while preserving the source receipt. A successful call marks the source observed, and that status remains observed if a later call fails. The evidence-completion command finalizes it after sufficient assigned proof. A mutation resets the Browser ledger, and current-revision completion rejects replay. Thus source admission, serial result binding, current revision, and finalization replay remain Core while input repetition, retry count, and timing are non-authoritative workflow advice.

## Enforcement boundary

This protocol removes shell-string classification from accepted capability execution and makes supported argv behavior deterministic. Compatibility class normalization cannot measure work concealed inside an allowed program and is not used to judge sufficiency. Direct process-control names are blocked and child groups are isolated, but an allowed custom program can still target unrelated processes explicitly or conceal other work internally. Executable resolution excludes repository-controlled paths but is not an operating-system capability sandbox: concurrent same-user replacement of an accepted executable outside the repository is outside this guardrail. The evidence ledger proves exact argv execution and matched Browser observation at the workflow level; hosted, manual, and existing completion remain declared attestations. Protected Git receipts exclude ignored content and do not prove external dependency or service state. The protocol does not cover unmatched hosted tools, specialized paths that opt out of hooks, hidden reasoning, semantic boundary correctness, or arbitrary custom code executed by an allowed program. Click remains a workflow guardrail, not an operating-system sandbox.
