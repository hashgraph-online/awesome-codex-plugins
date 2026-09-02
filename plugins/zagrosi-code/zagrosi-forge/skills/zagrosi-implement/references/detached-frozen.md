# Detached frozen-planning mode

Read this file completely only when `implement-setup` uses
`--implementation-root`. It is the normative detached-mode contract. Do not
summarize, weaken, or replace any invariant with the lean mutable workflow.

## Setup

`{implementation_root}` must be disjoint from the planning tree.
`{admission_pinner}` must be a pre-existing external 0600 canonical JSON
regular single-link file that binds the admitted plan input.

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py implement-setup \
  --sections-dir "{sections_dir}" \
  --target-dir "{target_dir}" \
  --implementation-root "{implementation_root}" \
  --admission-pinner "{admission_pinner}" \
  --expected-admission-pinner-sha256 "{sha256_of_complete_admission_pinner}" \
  --expected-implement-tool-sha256 "{sha256_of_complete_scripts_zagrosi_skills_py}" \
  --expected-implement-skill-sha256 "{sha256_of_complete_zagrosi_implement_SKILL_md}" \
  --expected-implement-test-sha256 "{sha256_of_complete_test_zagrosi_skills_py}"
```

`--implementation-root` activates mode `detached-frozen`; it is not a generic
output-directory alias. Setup creates only external `code_review/`, `evidence/`
and `pinners/` directories plus canonical config, state and progress files. The
root top level is always exactly those six members; any unknown sibling fails
closed. Planning, target and detached roots must be pairwise descriptor-
disjoint in both ancestor directions, including case and mount aliases. Setup
holds the fixed `/` global lifecycle lock and U-root lock, keeps the planning
and target roots open read-only, verifies every identity and the complete
planning tree before and after the command, and makes no planning-root or
target-root write. Setup refuses unless the
reopened admission pinner equals `--expected-admission-pinner-sha256`.
That complete-file hash is the operator-supplied trust anchor. The reopened
pinner must have exactly `schema,start,end,o_sha256,verdict`, literal schema
`dec075-final-pinner-receipt-v1`, literal `PASS`, an exact lowercase SHA-256
`o_sha256`, and identical START/END `dec075-admission-state-v1` objects. Forge
rederives `A = H("dec075-a-v1\0" || raw(R) || raw(P) || raw(D))` and recomputes
`D` from the current exact section manifest and complete section bytes before
creating the detached root. It records START/END `a_sha256` verbatim as
`admission_state_sha256`; this is not a hash of the state object.
It also refuses unless the running plugin's exact `scripts/zagrosi_skills.py`,
`skills/zagrosi-implement/SKILL.md` and `tests/test_zagrosi_skills.py` complete
file hashes equal the three required `--expected-implement-*-sha256` values.
The pinned tool transitively authenticates this reference: setup and every later
source check reopen it no-follow and require the tool's built-in complete-file
SHA-256. Reference drift therefore fails without adding a fourth config field.

Setup emits `preflight`. Stop on `success: false`. Pause on protected-branch or
dirty-tree warnings that affect the target. Add `--pretty` only when showing a
human-readable command.

## Detached frozen-planning contract

The authenticated setup-prefix schema is exactly
`zagrosi-detached-implementation-setup-prefix-v2` with these 18 fields:
`schema,slot,planning_dir,sections_dir,target_dir,target_root_identity_digest,
implementation_root,planning_tree_sha256,planning_file_count,
planning_total_bytes,admission_pinner_path,admission_pinner_sha256,
admission_pinner_size,admission_state_sha256,implement_tool_sha256,
implement_skill_sha256,implement_test_sha256,self_digest`. `slot` is exactly
`config`, `state` or `progress`. `self_digest` hashes CJ0 without LF under
`zagrosi-detached-implementation-setup-prefix-v2-self\0`.

The external config schema is exactly
`zagrosi-detached-implementation-config-v2`, mode `detached-frozen`, with these
31 fields: `schema,mode,planning_dir,sections_dir,target_dir,
implementation_root,state_path,progress_path,reviews_dir,evidence_dir,
pinners_dir,planning_tree_sha256,planning_file_count,
planning_total_bytes,admission_pinner_path,admission_pinner_sha256,
admission_pinner_size,admission_state_sha256,
detached_implementation_root_identity_digest,target_root_identity_digest,
implement_tool_path,
implement_tool_sha256,implement_tool_size,implement_skill_path,
implement_skill_sha256,implement_skill_size,implement_test_path,
implement_test_sha256,implement_test_size,runtime,test_command`. The three
source paths name the current plugin files above and each size is its complete
byte count. State is exactly `zagrosi-detached-implementation-state-v2` with
nine fields `schema,mode,planning_tree_sha256,admission_pinner_sha256,
admission_state_sha256,detached_implementation_root_identity_digest,
target_root_identity_digest,created_at,completed_sections`. Progress alone
remains `zagrosi-detached-implementation-progress-v1`; it does not acquire the
target or detached-root identity fields. Config, state, progress, evidence JSON
and pinners are compact sorted-key UTF-8 canonical JSON with one terminal LF,
mode 0600, regular and single-link. Every path component is opened no-follow;
review Markdown and all three implementation sources are reopened as regular
single-link files.

Setup accepts only seven durable slot tuples: a fresh root with no slots; exact
pending `{config}`, `{config,state}` or `{config,state,progress}` prefixes; or
exact final-config shapes with `(pending state,pending progress)`, `(final
state,pending progress)` or `(final state,final progress)`. Once a config prefix
exists, the owner-0600 diagnostic marker must already exist. Fresh/pending
`code_review` and `evidence` directories must be empty and `pinners` may contain
only that marker. Unknown, out-of-order, missing-marker or planted nested
members are refused without creating, removing or rewriting anything. Fixed
root temps are admitted and cleaned only after the surrounding config and every
external authority have been authenticated.

Lexical disjointness is not authority. Planning, target and detached U roots
must be pairwise descriptor-disjoint in both ancestor directions at setup,
context open and every late authority closure, including case and mount aliases.
Planning-local admission pinners, symlink components and any aliasing root fail
closed. Each detached command first opens the fixed filesystem root `/` as a
root-owned non-group/other-writable no-follow directory, acquires an exclusive
nonblocking `flock`, then acquires an exclusive `flock` on a non-inheritable dup
of the already identity-bound U root descriptor. Both share the five-second
deadline and remain held through recovery, reads, mutation, rollback,
post-commit cleanup and the final point-in-time payload; release order is U then
`/`. The lexical `/` and U paths are reopened and byte/metadata identities
reproved during the critical section. Unsupported directory-flock semantics
fail closed. This global anchor intentionally serialises all compliant detached
commands and accepts availability/DoS contention. Its closure is limited to one
Darwin/APFS host and shared mount namespace; other mount or chroot namespaces
are outside the contract. The fixed `pinners/.record-section.lock` is an
owner-0600 diagnostic marker, not the serialization authority.
Every context open, transaction recovery and late authority closure first
reopens the canonical config no-follow and requires its complete bytes to equal
the in-memory canonical config before any descriptor, root or target authority
is consumed; the final rollback-capable closure repeats that exact-byte proof.
The detached-root digest is `sha256:` plus SHA-256 of literal domain
`zagrosi-detached-implementation-root-identity-v1\0` followed by compact
NFC sorted-key canonical JSON without LF of exactly
`device,inode,uid,gid,mode,link_count`. `mode` is `S_IMODE`; setup requires a
current-user-owned 0700 directory, derives the digest after creating the fixed
`code_review`, `evidence` and `pinners` children, and every later command
rederives it. Adding an LF changes the digest. Setup reserves authenticated
create-once pending objects for config, state and progress before promotion, so
a crash after any slot write/fsync or final promotion can resume only from that
exact prefix. A completed config is immutable: replay succeeds only when every
setup authority and final config byte is identical, and a different target,
admission pinner or implementation-source identity leaves all six members
unchanged.

The target-root digest is `sha256:` plus SHA-256 of literal domain
`zagrosi-detached-target-root-identity-v1\0` followed by CJ0 without LF of
exactly `device,gid,inode,link_count,mode,uid`, where `mode` is `S_IMODE`.
Config, state and every section pinner repeat the exact setup digest. Setup and
every context/late authority check reopen the lexical target, require the same
descriptor identity and digest, and reprove its pairwise ancestry joins.

`planning_tree_sha256` is the lower-hex SHA-256, prefixed `sha256:`, over literal
domain bytes `zagrosi-frozen-planning-tree-v1\0` followed by the framed records.
Membership is the root record `.` followed by descriptor-relative depth-first
records; each directory's immediate child names are ordered by strict UTF-8
bytes and its record precedes descendants. Every recursive directory and regular
file, including empty directories, is present. A record is exactly
`u32be(path_utf8_length) || path_utf8 || kind_byte || u32be(mode) ||
u64be(link_count) || u64be(content_length) || content`, where `kind_byte` is
literal ASCII `D` or `F`, directory content is empty and file content is the
complete bytes. Symlinks, special files, non-UTF-8 names, files over 64 MiB and
trees over 512 MiB fail. Every later detached command reopens the exact admission
pinner and requires both its complete-file SHA-256 and this planning-tree digest
to equal setup. At command admission and again before completion, detached
`implement-progress`, `implement-record-section` and `next-section` each reopen
all three implementation sources component by component without following
links, require the stored paths, complete-file hashes and sizes, and fail closed
on replacement or drift. Any intended source update requires a new detached
setup with newly reviewed expected hashes; an existing detached root is not
silently upgraded.

The section pinner schema is exactly
`zagrosi-implementation-section-pinner-v2` with these 20 fields:
`schema,section,planning_tree_sha256,admission_pinner_sha256,
admission_state_sha256,detached_implementation_root_identity_digest,
target_root_identity_digest,implement_tool_sha256,implement_skill_sha256,
implement_test_sha256,
completed_at,commit,commit_status,notes,files_changed,test_files,
review_artifacts,evidence_rows,verification,predecessor_pinners`. It has no
self-hash field. Its identity is the raw SHA-256 of the complete canonical
pinner file, and its content-addressed filename includes that hash. Each
predecessor row is exactly `section,pinner_path,pinner_file_sha256`; Forge derives
it only after reopening the predecessor pinner no-follow and recomputing the
canonical file hash. The current and every reopened predecessor pinner must bind
the same admission state, target-root digest and three implementation-source
hashes as the detached config. Every completed section's predecessor rows must
also equal the current state pointers for its exact direct predecessors.
Re-recording a section is refused while any completed direct or transitive
dependant pins its current receipt.

Section recording uses only the fixed owner-0700 directory
`pinners/.record-section-transaction-v1`. The eight-field canonical journal is
exactly `schema,section,base_state_sha256,candidate_state_sha256,
prior_state_record,state_record,pinner_path,pinner_file_sha256`, with schema
`zagrosi-section-record-transaction-v1`. Publication order is fixed:

Before opening or creating the transaction directory, Forge requires the exact
canonical candidate state bytes to differ from the exact base bytes. An
identical same-second leaf re-record is a zero-write
`section-record-state-conflict`, not a transaction.

1. Write and fsync canonical candidate pinner bytes to `pinner.tmp`; atomically
   no-replace rename it to `pinner.json`, fsync the transaction directory and
   reopen exact bytes.
2. Write and fsync the canonical journal to `transaction.write.tmp`; atomically
   no-replace rename it to `transaction.tmp`, fsync the directory, reopen the
   exact eight fields and require the exact distinct base-state projection.
   Atomically no-replace rename it to `transaction.json` and fsync again.
3. Install the final content-addressed pinner. A newly created final is a hard
   link to the retained stage and therefore the same exact two-link inode; an
   adopted exact pre-existing final is a distinct pair of single-link files.
4. Revalidate artifacts and all authorities, stage candidate `state.json`, CAS
   exact base to candidate and fsync U, then revalidate again. Immediately
   before commit, reopen the exact journal, candidate state, staged bytes and
   created/adopted final relation.
5. Unlink `transaction.json` and fsync the transaction directory. That unlink
   plus fsync is the forward commit point. Only then remove recognised stage
   residue and the transaction directory.

Any failure after the forward journal exists publishes durable abort intent by
atomically renaming the exact `transaction.json` to `rollback.json` and fsyncing
the transaction directory before changing final pinner or state. Rollback never
promotes: it deletes and fsyncs only a provably same-inode invocation-created
final, preserves a distinct adopted final, replaces an exact candidate with the
exact base through fixed `state.json`, validates base structural and authority
closure, then unlinks and fsyncs `rollback.json` before stage/directory cleanup.
The rollback marker has the same exact eight canonical fields. Missing stage,
both journal names, a third state, changed bytes or ambiguous link provenance
retain all evidence and fail closed. A drifted predecessor cannot block
candidate-to-base replacement; predecessor/base closure is checked before the
rollback marker is removed.

Recovery runs under both lifetime locks before any detached readiness snapshot.
A forward journal requires exact `pinner.json`, exact base or candidate root
state, and only a candidate `state.json` against an exact base. Candidate plus
an exact single-link stage but missing final is a rollback-only failed arm and
must never reinstall or promote the final. A rollback journal requires its
exact stage and resumes only rollback. With no journal, `state.json` is
unreachable and retained. Partial or complete `pinner.tmp` is prepublication
base residue. Partial `transaction.write.tmp` may be cleaned only after the
published canonical stage, current dependency projection and exact base are
proved; a complete canonical write temp must also join its exact eight-field
journal to that same stage/base. Published `transaction.tmp` must always be
canonical and project the exact current base. Published `pinner.json` must
always be canonical, known to the manifest, immediate-child content-addressed,
and have current predecessor rows. At base it may have no final or an exact
distinct single-link orphan; at candidate it must equal the current state
record and have either the exact same-inode two-link created final or exact
distinct single-link adopted final. All other combinations retain and fail.
No-journal committed cleanup validates only canonical state, the current final
pinner, predecessor joins, config/target/root/lock identities and stage/final
provenance; later mutable review or evidence drift cannot undo the commit point.
Successful record output reports `transaction_status` as `committed-clean` or
`committed-cleanup-pending` and the matching boolean
`transaction_cleanup_pending`; cleanup-pending recovery is idempotent.

`--evidence-row <name>=<path>` is repeatable. Each pinner evidence row is exactly
`name,path,sha256,size`, sorted by unique lower-snake-case name. The path is
implementation-root-relative and names a reopened 0600 canonical JSON regular
single-link file. This generic row binds bytes only: the section contract and a
recorded `--verification` command must validate the evidence's rich semantic
projection before recording. Sections 26 and 28 require the exact rows
`s26_privileged_darwin_apfs_gate=evidence/s26-privileged-darwin-apfs-gate-handoff-receipt-v1.json`
and `s28_privileged_darwin_apfs_gate=evidence/s28-privileged-darwin-apfs-gate-handoff-receipt-v1.json`
respectively, but Forge derives these reserved rows itself and rejects any
caller-supplied reserved name. Raw root-owned host results are never accepted,
copied, linked or chowned into the implementation root. Immediately before and
after creating a section pinner, and again after state mutation, Forge reopens
reviews and evidence, reruns the section-owned unprivileged verifier, reopens
the current admission pinner and all implementation sources, rechecks the
frozen planning tree, and verifies predecessor pinners against current state.
Any late replacement removes only a newly created exact pinner and rolls back
its matching state record; pre-existing bytes are never removed.

### Privileged Darwin/APFS evidence handoff

Sections 26 and 28 obtain their reserved evidence only through the public
detached command below. The public selector is the exact token `S26` or `S28`;
full section slugs, aliases, lowercase values, a missing selector or extra
arguments are silent exit 2 with empty stdout and stderr.

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py implement-evidence-handoff \
  --implementation-root "{implementation_root}" \
  --section S26
```

Use `S28` only for Section 28. Forge recovers the admitted planning and target
roots from the create-once detached config. It freshly requires the mapped
section to be incomplete and a member of the dependency-ready set; parallel
ready sections are allowed. It also reopens every current predecessor pinner
and state pointer. In this plan S26 requires current S01 and S27, while S28
requires current S26 and S27.

The caller must be a non-root user on Darwin arm64. Forge proves the held U root
is APFS with exactly `/usr/bin/stat -f %T .`, a descriptor cwd, environment
`LC_ALL=C,LANG=C,TZ=UTC`, five-second deadline, 64-byte stdout/stderr caps,
exit zero, empty stderr and exact stdout `apfs\n`. The fixed `stat` is reopened
no-follow as a root:wheel regular executable with a positive link count, no
group/other write bit and root-owned non-writable ancestors. The same strict
fixed-dependency treatment applies to `/usr/bin/sudo`, the pinned Python and
Git executables, the prerequisite and host-provisioning receipts, and the
selected root-owned gate runner.

The protected target source observation is independent of the installed
receipt. Forge uses only pinned Git
`/usr/local/libexec/santander-unit12-prereqs/git-2.50.1-apple-155`, with exact
environment `LC_ALL=C,LANG=C,TZ=UTC,GIT_CONFIG_NOSYSTEM=1,
GIT_CONFIG_GLOBAL=/dev/null,GIT_TERMINAL_PROMPT=0,GIT_OPTIONAL_LOCKS=0` and no
PATH, HOME or other Git variables. It runs exactly `status --porcelain=v1 -z
--untracked-files=all`, `rev-parse --verify HEAD^{commit}` and `ls-tree -r -z
--full-tree HEAD`, with deadlines 10/10/30 seconds, stdout caps 1/41/16777216
and stderr cap 65536. Success requires empty stderr, complete EOF, an empty
status frame and exactly 40 lowercase hexadecimal commit bytes plus LF. The
status reader requests exactly its remaining stdout allowance, so the first
read is literally one byte and no later porcelain bytes are consumed. It treats
that first non-empty byte as semantic `handoff-source-dirty`, then first
polls/reaps an already-absent group or boundedly terminates and reaps the complete
live process group. If a TERM or KILL attempt races with leader exit and returns
ESRCH or EPERM, the same at-most-two-second phase repeatedly polls/reaps the
leader and reproves group absence before termination is classified unproven. A
real dirty record is therefore
authority-invalid/exit 5; Git spawn, I/O, cap, timeout, residual-group or
termination failure remains fixed-dependency-unavailable/exit 3. The
root identity hashes CJ0 of exactly `device,inode,uid,gid,mode,link_count`
under `unit12-protected-source-root-identity-v1\0`; the tree hashes domain
`unit12-protected-source-tree-v1\0`, `u64be(tree_bytes)`, then the complete raw
tree frame.

S26 hashes the ASCII-sorted complete files
`scripts/cutover/_runtime_evidence_revocation_publication_store.py` and
`scripts/cutover/_runtime_evidence_revocation_publication_wire.py` under domain
`unit12-s26-privileged-gate-implementation-source-set-v1\0`. S28 similarly
hashes `_runtime_evidence_revocation_github_native.py`,
`_runtime_evidence_revocation_publication_transport.py`,
`runtime_evidence_revocation_toolchain.py` and
`runtime_evidence_revocation_toolchain_native.py` in `scripts/cutover/` under
the S28 domain. Each entry is `u32be(path_bytes) || path_bytes ||
raw_sha256(complete_file)`. The separate S26/S28 test source hash covers the
complete publication store/transport test file. No Git blob hash, path
normalisation or line conversion is allowed.

The only privileged scripts are fixed root:wheel 0555 single-link runners
under `/usr/local/libexec/santander-unit12-gates/`: the S26 and S28 files are
respectively `s26-privileged-darwin-apfs-gate-runner-v1.py` and
`s28-privileged-darwin-apfs-gate-runner-v1.py`. Their ancestors are root-owned
and non-writable. Immediately before each child and every final persistence or
record recheck, Forge no-follow reads the complete selected runner and requires
byte equality and identical raw SHA-256 with its current implementation source
(`_runtime_evidence_revocation_publication_store.py` for S26 or
`_runtime_evidence_revocation_publication_transport.py` for S28). No root child
executes or imports a user-writable repository path; repository tests are TDD
sources only.

The root arm is the exact 18-token `/usr/bin/sudo -n -- {pinned_python} -I -B
{fixed_runner} --privileged-darwin-apfs-handoff-root
--host-provisioning-receipt {fixed_HPR} --host-input {fixed_gate_input}
--result {fixed_H_result} --request-fd 0 --receipt-fd 1`. It uses the held
target descriptor cwd, the three-variable C/UTC environment, a 30-second
deadline and 65536-byte stdout/stderr caps. The unprivileged arm is the exact
nine-token pinned-Python runner command with
`--verify-privileged-darwin-apfs-handoff --host-provisioning-receipt
{fixed_HPR} --framed-input-fd 0`, a ten-second deadline, 4096-byte stdout and
65536-byte stderr caps. Both use a new process group, require exit zero, empty
stderr, one canonical object and final EOF. Timeout, cap or I/O failure sends
TERM to the whole group for at most two seconds, then KILL for at most two
seconds, requires bounded reap, and never retries. Apparent leader success is
rejected if any process-group member remains.

The request has exactly `schema,purpose,gate_id,admission_state_sha256,
admission_pinner_sha256,planning_tree_sha256,
detached_implementation_root_identity_digest,implement_tool_sha256,
implement_skill_sha256,implement_test_sha256,self_digest`. Its schema and
purpose are `unit12-privileged-darwin-apfs-gate-handoff-request-v1` and
`unit12_privileged_darwin_apfs_gate_handoff`. Self and final-wire digests use
their literal `...-self\0` and `...-final-wire\0` domains plus CJ0 without LF;
transport is CJ0 plus exactly one LF.

The returned receipt has exactly `schema,purpose,gate_id,
handoff_request_final_wire_digest,admission_state_sha256,
admission_pinner_sha256,planning_tree_sha256,
detached_implementation_root_identity_digest,
privileged_evidence_root_identity_digest,implement_tool_sha256,
implement_skill_sha256,implement_test_sha256,
host_provisioning_receipt_final_wire_digest,host_input_final_wire_digest,
result_final_wire_digest,result_sha256,result_bytes,result_mode,result_uid,
result_gid,result_nlink,gate_command_sha256,handoff_command_sha256,
protected_source_root_identity_digest,source_commit,source_tree_sha256,
implementation_source_sha256,test_source_sha256,result_finished_at,verdict,
attestation_key_id,self_digest,signature_b64u`. Forge requires every request,
config, source and selected gate-command echo, root-owned result metadata
0600/uid0/gid0/nlink1, literal PASS, canonical digests and a strict 64-byte
Ed25519 signature envelope. The fixed unprivileged runner independently
validates the prerequisite/HPR trust chain, key and signature domains and
returns the exact current ten-field PASS projection before U persistence.

Success emits only exact schema `zagrosi-privileged-evidence-handoff-result-v1`
fields `schema,section,evidence_name,evidence_path,sha256,size,status`, with
status `created` or `reopened`. Failure emits only exact schema
`zagrosi-privileged-evidence-handoff-error-v1` fields
`schema,purpose,section,status,closed_error_code` on stdout, with empty stderr,
literal purpose `zagrosi_privileged_evidence_handoff_error`, status `failed`
and a closed exit-3 or exit-5 code. It never includes paths, digests, keys,
child bytes or exception text. The U receipt is create-once 0600 with file and
parent fsync; retry reruns both arms and accepts only byte equality. Every late
A/U/plugin/source/predecessor/evidence drift removes only a newly created exact
receipt and leaves no section pinner or state mutation.

Exit 3 codes are exactly `HANDOFF_PLATFORM_UNAVAILABLE`,
`HANDOFF_FIXED_DEPENDENCY_UNAVAILABLE`, `HANDOFF_ROOT_UNAVAILABLE` and
`HANDOFF_VERIFIER_UNAVAILABLE`. Exit 5 codes are exactly
`HANDOFF_CALLER_REFUSED`, `HANDOFF_SECTION_NOT_READY`,
`HANDOFF_AUTHORITY_INVALID`, `HANDOFF_ROOT_OUTPUT_INVALID`,
`HANDOFF_VERIFIER_OUTPUT_INVALID`, `HANDOFF_EVIDENCE_CONFLICT` and
`HANDOFF_INTERNAL_FAILURE`. Fixed-Git spawn, I/O, output-cap, timeout,
residual-process-group or termination failure is fixed-dependency-unavailable;
its clean-source, revision, tree or source-hash semantic mismatch is authority-
invalid. Root/verifier spawn, I/O, timeout or unproven process-group termination
is unavailable; a root/verifier semantic nonzero or malformed frame is output-
invalid.

## Detached section loop

Before each section, run:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py next-section \
  --planning-dir "{planning_dir}" \
  --implementation-root "{implementation_root}"
```

Implement only a dependency-ready section. The admitted planning tree is
immutable: never write packets, skeletons, diffs, reviews, decisions, evidence,
usage, traceability, or section updates beneath it. Any generated output must
stay in the fixed external directories. Parallel implementation is allowed only
for ready sections with disjoint ownership; serialize section recording.

Use targeted TDD and an adversarial review. Detached recording requires these
two concise external files even when there are no findings:

```text
{implementation_root}/code_review/{section}-review.md
{implementation_root}/code_review/{section}-decisions.md
```

For Sections 26 or 28, run the privileged handoff above first; Forge derives
the reserved evidence row. Record all other canonical evidence explicitly:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py implement-record-section \
  --sections-dir "{sections_dir}" \
  --implementation-root "{implementation_root}" \
  --section "{section}" \
  --commit "{commit_hash_or_none}" \
  --file "{changed_file}" \
  --test-file "{test_file}" \
  --review-artifact "code_review/{section}-review.md" \
  --review-artifact "code_review/{section}-decisions.md" \
  [--evidence-row "{name}=evidence/{canonical_result}.json"] \
  --verification "{targeted_test_or_gate_command}"
```

Never re-record a pinned predecessor with completed dependants. If final hashes
must replace it, create a new detached root/state and replay dependency order.

## Detached completion

Run the configured full test command once. Then rerun `next-section` with
`--implementation-root` and require empty `remaining_sections`, null
`next_section`, unchanged planning/admission/source identities, and successful
reopening of every completed pinner. Do not run plan-local report,
traceability, or documentation writers.
