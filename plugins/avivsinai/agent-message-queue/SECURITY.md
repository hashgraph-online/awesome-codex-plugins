# Security Policy

## Security Model

AMQ's core queue is for local communication between agents that run under
the same user account and share filesystem access. It is not an isolation
boundary between mutually untrusted agents or users. Optional cross-host
delivery uses the [bridge's separate authentication and routing contract](docs/adr-bridge-protocol.md).

### Threat Model

The queue uses these controls:

- Writers sync a temporary file before publishing it into an inbox. Readers
  do not read a partially written message from that publication path.
- Handle and message-ID validation rejects path separators and invalid names.
- Queue directories use mode `0700` and files use mode `0600` on Unix.
- Session and root checks reject conflicting routing contexts before mutation.

A process with the same user's filesystem access can read or change queue
files directly. AMQ does not defend against that process or provide a
multi-user access-control service.

### Rooted Delivery Boundary

After `send` or `reply` authorizes a source and destination tree, AMQ opens each
tree once with Go's `os.Root` and performs mailbox delivery, directory sync,
presence touch, and outbox writes relative to that pinned directory capability.
Replacing the authorized path or one of its ancestors with a symlink cannot
redirect those writes outside the opened tree. Relative symlinks that remain
inside the tree continue to work; symlinks that escape it are refused.

This boundary does not defend against filesystem namespace changes below an
already opened root, including privileged bind mounts, or against writing to
pre-existing device files. Those cases require separate mount and file-type
hardening and remain outside the rooted-delivery guarantee.

### Accepted limits

The local trust model does not defend against:

- **Untrusted-ancestor / TOCTOU alias swaps.** A different-euid local attacker
  who can retarget an ancestor symlink between commands (cross-command alias
  retarget for `--project`/`--session` routes; ABA swaps of config or message
  files) is out of scope. Legitimate in-tree symlinks continue to work.
- **Bind mounts and device files below an opened root** (as noted above).

Native Windows does not provide the Unix cross-tree identity and `.amqrc`
authority-hardening guarantees; those checks use legacy lexical behavior.
See the [platform limits](INSTALL.md#platform-capability-matrix).

### Known Risks

#### TIOCSTI Terminal Injection (`amq wake`)

`amq wake` can inject terminal input through TIOCSTI or an explicitly configured
transport. Hardened Linux kernels can disable TIOCSTI.

Input injection can activate an approval dialog or submit a partially typed
prompt. Removing Enter is not a safety boundary: some dialogs accept a single
key. Input-quiet checks reduce typing collisions but do not detect modal dialogs.
The input doorbell is fixed text, not a message body; that does not remove the
dialog risk. External injectors are operator-selected local executables and
can have their own side effects.

Use `amq wake --inject-mode none` when zero synthetic terminal input is
required, or `amq coop exec --require-wake --wake-inject-mode none <agent>`
for a managed launch. This mode refuses external injectors. See
[wake operations](docs/wake-operations.md) before changing an existing wake.

## Reporting a Vulnerability

Use private vulnerability reporting from the repository's
[Security tab](https://github.com/avivsinai/agent-message-queue/security)
when it is available. Otherwise, open an issue asking for a private contact
channel without disclosing the vulnerability. Do not include credentials,
private messages, or exploit details in a public issue.

We will acknowledge receipt as soon as possible and work to provide a fix or mitigation.
