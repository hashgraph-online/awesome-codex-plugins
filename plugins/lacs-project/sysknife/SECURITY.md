# Security Policy

SysKnife handles privileged local system operations, so security bugs
matter.

## Reporting a Vulnerability

Please do not open a public issue for security-sensitive problems.

Use GitHub's private vulnerability reporting flow for this repository
if it is available.
If a private report is not available in your environment, contact the
maintainers privately before publishing details.

## What to Include

- a short summary of the issue
- affected action family or component
- exact reproduction steps
- expected vs actual behavior
- logs or traces, with secrets removed
- impact assessment

## What We Will Do

We will:

- acknowledge the report
- triage the issue
- work on a fix
- coordinate disclosure timing with the reporter

## Rules for Contributors

- Never paste secrets into issues or pull requests.
- Never disclose a zero-day publicly before coordination.
- Treat approval, authorization, and transaction data as sensitive.

---

## Security Model

SysKnife uses a layered enforcement model. Every layer is independent; a
bypass of one does not bypass the others.

### Layer 1 — Intent validation (sysknife-brain, before LLM call)

Every intent string is checked before it is forwarded to the LLM
provider:

- **Length cap** (`INTENT_MAX_BYTES = 2048`): intents whose byte length
  exceeds 2048 are rejected with `PlanningError::IntentTooLong`. Oversized
  payloads are almost always copy-paste accidents or injection attempts.
- **Secret scan**: the same pattern list used to guard the preferences
  file (`SENSITIVE_PATTERNS` + `SENSITIVE_PREFIXES` in
  `crates/sysknife-brain/src/prefs.rs`) is applied to the raw intent.
  Intents containing API key prefixes (`sk-`, `ghp_`, `xoxb-`, …),
  the words `password`, `token`, `api_key`, and similar are rejected
  with `PlanningError::IntentContainsSensitiveData` before any network
  call is made.
- **Rate limit** (`RateLimiter` in `crates/sysknife-brain/src/rate_limit.rs`,
  `DEFAULT_MAX_RPM = 20` in `planner.rs`): a sliding 60-second window
  caps planning requests per session. When the window is full,
  `plan_intent` and `summarize` return
  `PlanningError::RateLimitExceeded { retry_after_secs }` before any
  network call is made. The default limit is 20 requests per minute,
  applied automatically by `LlmPlanner::from_config`; override with
  `SYSKNIFE_MAX_RPM` (must be ≥ 1). Call timestamps are persisted to
  `$XDG_DATA_HOME/sysknife/rate-limit.log` so the limit survives process
  restarts.

### Layer 2 — Action name allowlist (sysknife-brain, after LLM call)

The `ActionName` newtype in `crates/sysknife-brain/src/action_name.rs`
validates every action name proposed by the LLM against `KNOWN_ACTIONS`
at the type boundary. An action name not in that list (e.g.
`"RunShellCommand"`) is rejected with `UnknownActionName` and the
planning loop returns an error. The LLM cannot invent actions.

### Layer 3 — Role-based authorization (sysknife-daemon)

The daemon resolves the caller's Linux group membership via
`SO_PEERCRED` on the Unix socket and maps it to a `CallerRole`:

| Group | Role | Can call |
|---|---|---|
| `sysknife-observer` | Observer | Read-only actions |
| `sysknife-dev` | Dev | Read + medium-risk mutations |
| `sysknife-admin` or `wheel` | Admin | All including rpm-ostree, reboot |
| `sysknife-boot` | Boot | Everything (reserved for boot-time automation) |

The per-action minimum role is a compile-time exhaustive match in
`crates/sysknife-daemon/src/policy.rs`. Unknown actions return `None` and
are denied unconditionally. The caller's role is never supplied by the
client — it is always derived server-side from kernel credentials.

The same `SO_PEERCRED` read yields the peer's **uid**, which is recorded as the
caller principal alongside the role and signed into the audit chain
(`chain_version = 3`). Role answers "was this permitted"; principal answers
"which account asked", and two members of `sysknife-admin` are no longer
indistinguishable in the signed record. Three forms exist, and the scheme is
part of the signed value so an auditor can tell them apart:

| Principal | Meaning |
|---|---|
| `uid:<n>` | Unix-socket peer, uid attested by the kernel at `connect()` |
| `token:vsock` | vsock peer authenticated by the pre-shared token: possession of a file, not an account |
| `none:unattributed` | The daemon could not establish an account: `SO_PEERCRED` failed, returned no usable pid, or reported the overflow uid because the peer is not representable in this daemon's namespaces. The connection is handled at `Observer` and the row admits attribution failed rather than naming `nobody` |

### Layer 4 — One-time approval receipt (sysknife-daemon)

Every mutating action requires a preview→approve→execute round-trip:

1. The client requests a preview; the daemon records the action + canonical
   params and returns a transaction ID.
2. The user approves. MCP users run `sysknife approve <transaction-id>` in a
   real terminal, which reloads the daemon-authoritative preview before asking
   for confirmation and requires the exact action name for high-risk work.
3. The daemon derives a domain-separated Ed25519 receipt from the transaction
   ID and request hash, then stores only its SHA-256 commitment. That commitment
   is part of the immutable signed transaction row.
4. Execute must present the transaction ID, exact action and params, and the
   receipt. The daemon atomically consumes the receipt before running anything.

A receipt cannot be replayed and expires with its queued preview after 15
minutes. MCP exposes no tool that can mint a receipt, so an agent cannot turn
its own plan into an executable request without the separate terminal step.

This boundary protects against an untrusted MCP agent, not against arbitrary
malware already running as the same Linux user. A same-user process that can
connect directly to the daemon IPC endpoint can invoke the approval request;
Unix permissions, role groups, and host security remain part of the trust
model.

### Layer 5 — Atomic execution claim (sysknife-daemon)

Concurrent execute requests for the same transaction are blocked by an
database transaction that verifies the receipt digest, changes the queued
transaction to running, and marks the receipt consumed. Only the first request
wins; concurrent or replayed requests get `stale_approval`.

Receipt digests are 256-bit commitments to 512-bit Ed25519 signatures. The
atomic claim compares the digest inside the database transaction; SQL engines
do not promise constant-time string comparison, but the high-entropy,
single-use, 15-minute bearer value makes timing recovery impractical. The
daemon uses constant-time comparison when validating the signed commitment
before issuing a receipt.

### vsock transport authentication — threat model and residual risk

Over a Unix socket the caller's identity is attested by the kernel
(`SO_PEERCRED`) and cannot be forged or replayed. Over **vsock** (the daemon in
a VM) there is no equivalent: the client authenticates with a **pre-shared
bearer token** sent as the first frame, and possession of the token — a file,
not an account — is the whole of the proof (`token:vsock` in the principal
table above).

This has a residual risk that cannot be fully closed at the application layer
([#152](https://github.com/lacs-project/sysknife/issues/152)):

- **The token is a replayable bearer credential over an unencrypted channel.**
  An adjacent party that can observe one legitimate vsock connection (a
  co-located guest that can see the traffic, a compromised hypervisor path, a
  vsock proxy) reads the token from the first frame and can open its own
  connection, authenticate as the configured role (`SYSKNIFE_TOKEN_ROLE`,
  default `Dev`), and from there mint a fresh one-time approval receipt. The
  approval-receipt and atomic-claim layers above stop *replay of a captured
  request*, but not an attacker who holds the token and constructs their own.

- **Why it is inherent.** A bearer token over a channel with no confidentiality
  or peer authentication is, by construction, replayable by anyone who can read
  the channel. Closing it fully requires either confidentiality + peer
  authentication under the vsock (TLS or a WireGuard underlay), or a
  per-connection challenge so the token is never sent in the clear (a
  nonce/HMAC handshake, which defeats a *passive* observer but still not an
  active man-in-the-middle). Both are larger changes tracked on #152.

**Operator guidance (do this until the deeper mitigation lands):**

- Treat the vsock token as a secret with the blast radius of `SYSKNIFE_TOKEN_ROLE`.
  Prefer the lowest role that works; do not give the vsock path `admin`.
- Run the daemon only where the vsock namespace is **isolated**: a single
  trusted host↔guest pair on a hypervisor you control, not a multi-tenant host
  where other guests share the vsock namespace.
- Rotate the token file on any suspicion of exposure; the daemon reloads it.
- For anything crossing an untrusted boundary, forward the daemon's **Unix**
  socket over an authenticated, encrypted transport (`ssh -L`) instead of
  exposing vsock directly — SSH gives the confidentiality and peer
  authentication vsock does not.

---

## Deployment — User and Group Setup

The daemon socket lives at `/run/sysknife/daemon.sock` in a directory owned
`sysknife:sysknife 0750`. A user needs two group memberships to use SysKnife:

1. **`sysknife` group** — grants access to the socket directory. Without
   this the connection is refused before any authentication happens.
2. **A role group** — determines what the user can do once connected.
   Omitting this falls back to `Observer` (read-only queries only).

```sh
# Grant a user read-only access:
sudo usermod -aG sysknife,sysknife-observer alice

# Grant a user medium-risk access (services, containers, SSH keys, flatpaks):
sudo usermod -aG sysknife,sysknife-dev alice

# Grant a user full access (rpm-ostree, reboot, kernel arguments):
sudo usermod -aG sysknife,sysknife-admin alice
```

Group changes take effect on next login. To apply without logging out:

```sh
exec newgrp sysknife
```

Members of the `wheel` group are automatically treated as `sysknife-admin`
by the daemon — no explicit `sysknife-admin` membership is needed for
existing `sudo` users. They still need the `sysknife` group to reach the
socket.

The four role groups (`sysknife-observer`, `sysknife-dev`, `sysknife-admin`,
`sysknife-boot`) are created at install time by `systemd-sysusers` via
`packaging/sysknife-sysusers.conf`.

## Audit Trail

### Safety fence log

Every plan rejected by the brain's safety fence (unknown action name,
bad risk level, etc.) is appended as a JSON line to:

```text
$XDG_DATA_HOME/sysknife/safety-audit.jsonl
~/.local/share/sysknife/safety-audit.jsonl  (fallback)
```

Each entry contains `timestamp`, `event`, `intent`, `reason`, and
`raw_plan`.

### Transaction log

Every daemon execution — previewed, approved, running, succeeded, failed, or
rolled back — is recorded in the configured transaction database. SQLite is
the default at `SYSKNIFE_DATABASE_PATH` (packaged default:
`/var/lib/sysknife/daemon.sqlite`); PostgreSQL is available for centralized,
off-host durability. Both backends store the same signed hash-chain fields.

The transaction database is authoritative. Query it with `sysknife history`
and verify its chain with `sysknife audit verify`. See
[`docs/storage-cloud.md`](docs/storage-cloud.md) for backup, restore, and
PostgreSQL migration operations.

### Journald and syslog forwarding

On systemd hosts, every safety fence rejection is also forwarded to the
systemd journal as a structured log entry with these fields:

```text
SYSKNIFE_EVENT=safety_fence_rejection
SYSKNIFE_INTENT=<the user's original intent>
SYSKNIFE_REASON=<why the fence triggered>
SYSKNIFE_TIMESTAMP=<RFC 3339 UTC timestamp matching the JSONL entry>
PRIORITY=4   (LOG_WARNING)
SYSLOG_IDENTIFIER=sysknife-brain
```

Query live:

```sh
journalctl -f SYSKNIFE_EVENT=safety_fence_rejection
journalctl SYSLOG_IDENTIFIER=sysknife-brain --since today
```

The daemon also emits an audit-chain watermark to journald after transaction
writes and can forward transaction events as RFC 5424 syslog over UDP. These
paths are best effort: UDP may lose, reorder, or duplicate events, and neither
path replaces the transaction database or its backups.

### Enabling tamper-evident sealing (recommended for production)

systemd's Forward Secure Sealing (FSS) signs each journal entry with a
key that rotates forward — retrospective forgery is computationally
infeasible, and modification of any entry is detectable offline.

Enable FSS once at deployment time:

```sh
sudo journalctl --setup-keys
```

Verify log integrity at any time:

```sh
sudo journalctl --verify
```

Without FSS enabled, journald entries are still useful for querying
but are not tamper-evident. The JSONL file on disk is never
cryptographically protected regardless of FSS status.

---

## Release Artefact Trust

`npx sysknife-setup` downloads `sysknife`, `sysknife-daemon` and
`sha256sums-linux-<arch>.txt` from the GitHub release over TLS, then verifies
each binary against that checksum file. Be precise about what that does and does
not establish:

- **It does** detect corruption in transit, a truncated download, and a swapped
  or mismatched asset within the release.
- **It does not** prove the release itself is authentic. The binaries and the
  checksum file share one trust root — whoever can publish a release can publish
  a malicious daemon together with a matching checksum. The daemon holds broad
  passwordless `sudo` grants, so that is the consequential case.

Two controls exist today:

1. **Signed tags.** Release tags are SSH-signed from `v0.2.15` onward, so the
   commit a release was built from can be verified independently of the release
   assets:
   ```sh
   git verify-tag v0.2.15
   ```
2. **Out-of-band digest pinning.** Point `SYSKNIFE_PINNED_SHA256SUMS` at a
   checksum file you obtained independently — from a signed tag, an internal
   mirror, or config management — and the installer requires every asset to match
   both it and the release's own sums:
   ```sh
   SYSKNIFE_PINNED_SHA256SUMS=/etc/sysknife/trusted-sums.txt npx sysknife-setup
   ```
   An unreadable or malformed pin aborts the install. A security control that
   silently degrades to a no-op is worse than none.

Publisher-signed release manifests with a pinned key embedded in the installer
are the remaining step; that needs key-custody decisions and is not yet in place.

## Audit Anchoring in the Default Deployment

The signed chain detects modification of any row. It does **not**, on its own,
detect removal of the newest rows: the retained prefix still chains, and
verification walks it from an empty expected predecessor, so a truncated chain
reports as intact.

Detecting truncation requires a previously anchored signed tip in a store the
host attacker does not control. That is opt-in via `SYSKNIFE_CHECKPOINT_DB`, and
the packaged unit does not configure it, so **the default system deployment
cannot detect tail truncation.** `sysknife audit verify` now says so beside its
verdict rather than letting `OK` be read as "nothing was removed".

For a deployment that claims tamper-evident retention:

```sh
# An independent, append-only Postgres database — not the SysKnife store.
sudo systemctl edit sysknife-daemon
# [Service]
# Environment="SYSKNIFE_CHECKPOINT_DB=postgres://sysknife@anchor-host/anchors"
```

Grant the role only `INSERT` and `SELECT` on `audit_checkpoints` and `REVOKE
UPDATE, DELETE`. Append-only permissions do not stop a database superuser; the
signature is what makes tampering detectable, and the independence is what makes
removal detectable.

## Known Limitations

These are acknowledged gaps tracked as open issues. They do not
represent exploitable vulnerabilities in normal use — the downstream
enforcement layers cap their blast radius — but they are relevant for
security certification work.

| Gap | Issue | Notes |
|---|---|---|
| Tool output injection | [#98](https://github.com/lacs-project/sysknife/issues/98) | `query_*` results re-enter the LLM context unsanitized. A crafted service description or package name could attempt prompt injection. Impact is bounded by Layer 2–5. |
| Action param validation | — | Action params are typed per-handler but not validated at a shared schema boundary. A compromised LLM could propose valid action + malicious params (e.g. `AddAuthorizedKey` with an attacker-controlled key). |
| UDP audit forwarding | — | External RFC 5424 forwarding is best effort and provides no delivery acknowledgement. Use the transaction database and tested backups as the durable record. |
| Caller attribution strength | — | Rows written under `chain_version = 3` name the account (`uid:<n>`), but a uid is only as meaningful as account hygiene on the host: shared logins, `su` into a service account, or a uid reused after a user is deleted all weaken the claim. vsock callers are recorded as `token:vsock` because a pre-shared secret proves possession of a file, not a person. Rows written before the upgrade remain role-only by design, since backfilling them would rewrite what was signed. |
| Unattributed callers verify as intact | — | A row whose principal is `none:unattributed` is authentic and verifiable, but names no account, and a chain composed entirely of such rows still reports `Intact`. That verdict is about tampering only. `sysknife audit verify` reports `unattributed_rows` alongside it, and the daemon logs a warning per occurrence, but an operator who reads only the verdict will overestimate what the trail can attribute. Rows signed before `chain_version = 3` are counted separately as `rows_without_principal`, because they name nobody for a different reason and cannot be repaired. Every count is `null` rather than `0` when the store could not be read at all, so a database nobody could open cannot read as an empty one that opened fine. |
| `caller_principal` is unsigned on pre-v3 rows | — | The column enters the signed message only under `chain_version = 3`. On a v1 or v2 row it is unsigned free space: anyone who can write to the transaction table can populate it, and the chain still verifies as `Intact`, because no signature covers it. `sysknife audit verify` therefore buckets by the encoding rather than by the column, counts such a value as `rows_unattested`, and never as an account. Losing attribution is a gap; inventing it would be a lie, so the census refuses the second even at the cost of reporting less. |
| An action that cannot be stopped is reported, not hidden | [#140](https://github.com/lacs-project/sysknife/issues/140), [#142](https://github.com/lacs-project/sysknife/issues/142) | Actions run in their own process group and the timeout signals the group, which stops non-privileged commands. An unprivileged daemon cannot signal a root child, so a `sudo` action's real work cannot be force-killed; the timeout detects this (the group probe returns `EPERM`, meaning members remain but are unsignalable) and returns `ActionNotStopped` rather than a false success. On that verdict the daemon skips the automatic rollback and holds the exclusion slot, so no second mutating action can race the first: starting `rpm-ostree rollback` over a transaction that may still be live is worse than leaving it. An operator seeing that error should inspect the host before retrying; a daemon restart clears the held slot. Forcible termination of a root child is follow-up work (#142). |
| Attribution counts on a broken chain are claims | — | The census spans every row read while verification stops at the first break, so when the chain verdict is not `intact` `rows_censused` can exceed `rows_checked`, and the surplus is the part of the trail this command did not vouch for. Not every surplus row is forged: deleting or reordering one breaks the link while leaving later signatures valid, and an aggregate count cannot say which is which. The counts carry that caveat in words, `rows_censused` makes the gap measurable, and the MCP report exposes `chain_status` because the top-level `status` is the worst of three checks. A reader who takes `attributed_rows` from a chain that did not verify as established attribution is reading an unchecked claim. |
