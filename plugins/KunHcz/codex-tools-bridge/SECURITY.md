# Security and privacy

This bridge gives an authorized ChatGPT conversation access to real local tools. Use it only on a machine and workspace you control. Do not expose it as a shared public remote-computer service.

## Threat model

Treat retrieved webpages, repository files, emails, documents, and third-party tool output as untrusted data that may contain prompt injection. Tool discovery and transport encryption do not make instructions inside those sources trustworthy.

Default to configured native permissions. `--tool-access all` is an explicit broad grant, not a security feature. A shell with broad permissions can access files outside the bridge's direct file-helper paths or invoke other programs. Known model-starting/recursive tool filters preserve the intended architecture; they are not a comprehensive defense against malicious code.

Keep runtime state outside the public repository. Never commit runtime keys, browser cookies, auth.json, private SSH material, native task transcripts, logs, actual chat URLs, or populated tunnel profiles. Do not share the localhost provider's randomized route. The release checker is a heuristic hygiene check, not a security audit or proof that no secret exists.

## What data moves

Tool execution happens locally. Requested files, command output, images, and other returned tool data are sent back to ChatGPT through the connection. Tool implementations can also contact their own services and retain their own logs. Native Codex task history may retain execution context. This is not an offline or zero-retention product.

A chat identity hash is used for routing, not user authentication. Different local tasks may share files, OS credentials, applications, and the physical desktop. Use separate OS users or stronger isolation for different trust boundaries; that deployment is outside the guarantees of this release.

## Safety defaults

The new installer does not alter global default model/provider/approval settings. It only adds an owned named provider block to an explicitly selected registry, refuses existing private state and user-owned workspace configuration, and creates a workspace-write/on-request native task. The local protocol server binds to loopback. Missing native hosts fail rather than switching to a different model provider.

Never assume a timed-out write, command, or UI action did not execute. Inspect state before retrying. Operating-system lock protections and physical-input pauses must be resolved by the user through normal host controls; the bridge does not bypass them.

## Reporting

Do not post credentials or private tool output in a public issue. Use the repository's private vulnerability reporting feature when available. If unavailable, open an issue containing only a request for a private reporting channel, without exploit details or sensitive data. Include minimal sanitized reproduction steps and component versions through the private channel.

Only the current experimental release is maintained. There is no security-support SLA.
