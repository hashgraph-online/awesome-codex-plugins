# Security policy

## Supported environment

Rekall is intended for a single-user workstation running the Codex VS Code extension on Windows, macOS, or Linux. The extension version and platform verification limits are listed in [README.md](README.md#compatibility-and-extension-updates). Shared machines and multi-tenant hosts are outside the supported deployment model. Security fixes target the latest version on `master`; older versions do not have a separate maintenance branch.

Standalone Codex CLI sessions and the Codex desktop app are unsupported. Rekall's adapter requires the VS Code extension's IPC owner and conversation events; the presence of a thread ID or a successful MCP installation is insufficient to control a session owned by another host.

## Trust boundary

Rekall connects to the extension's existing local named pipe on Windows or Unix socket on macOS and Linux. It does not create or administer that endpoint, configure its access control, or add a separate authentication layer. On macOS and Linux it checks the current UID, rejects symlinks at the IPC directory and socket paths, and requires both to have no group/other permissions. It uses only `$CODEX_HOME/ipc/ipc.sock` (default `~/.codex/ipc/ipc.sock`), with no legacy shared-socket fallback. These filesystem checks do not authenticate another process running under the same account. Any local process that can connect to the endpoint can participate in the extension's IPC protocol, subject to the extension's own checks. Thread IDs and owner IDs are routing and consistency checks, not credentials. Do not expose or forward this endpoint over a network.

The operating-system account, the Codex extension, the installed Rekall code, and processes with access to that account's files and IPC endpoint belong to the trusted computing base. Rekall's schema, owner, thread, user-input, and handoff checks reduce accidental misrouting and unintended continuation; they do not isolate mutually untrusted local processes.

Handoff SHA-256 detects a changed handoff relative to the recorded journal. It is not a signature: a process that can rewrite both the handoff and its journal can also replace the recorded checksum. Handoffs and journals are stored unencrypted under the user's Codex directory, with filesystem permissions inherited from that environment. Treat their contents as private and restrict access to the account and its files.

Rekall does not use an extension-version allowlist. It checks extension identity, public schema, runtime layout, owner/thread binding, and IPC protocol compatibility regardless of version. These checks do not authenticate the pipe or guarantee compatibility with future protocol changes.

## Linux socket isolation

The Linux adapter uses the private per-user Codex IPC directory and verifies directory/socket ownership and permissions before each connection. It rejects symlinks at those two paths and does not fall back to a globally shared `/tmp` socket. Peer-process authentication is not implemented; processes running under the same account remain trusted as described above. Cross-user socket isolation was the subject of [upstream issue #8965](https://github.com/openai/codex/issues/8965); that historical report is not a claim about the current extension's behavior. Passing Linux tests with a synthetic socket does not establish a secure live Linux deployment.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/DitriXNew/rekall/security/advisories/new) for security defects. Include the Rekall version or commit, operating system, extension version, expected trust boundary, and a minimal reproduction using synthetic data.

Do not post credentials, raw handoffs, transcripts, job journals, real thread/owner/job/turn IDs, or personal filesystem paths in public issues. Redact these from probe output too. For an ordinary extension compatibility failure, use the [new extension version issue template](https://github.com/DitriXNew/rekall/issues/new?template=new-extension-version.yml).
