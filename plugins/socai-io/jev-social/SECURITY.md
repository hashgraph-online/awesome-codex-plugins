# Security policy

## Supported versions

Security fixes target the latest release and the current `main` branch.

## Report a vulnerability

Please use [GitHub's private vulnerability reporting](https://github.com/socai-io/jev-social/security/advisories/new). Do not open a public issue for a suspected vulnerability.

Include the affected version, reproduction steps, impact, and a minimal proof of concept when possible. Remove API keys, cookies, browser profiles, captured social data, and other personal information before submitting.

Jev Social starts a loopback-only local server and launches the socai CLI. Reports involving command construction, local file access, secret exposure, unsafe remote-browser routing, or untrusted media rendering are especially useful.

## Data flow, credentials, and retention

Jev Social runs locally, but it is not an offline application.

### Network data

- Onboarding can send the OpenRouter key to `https://openrouter.ai/api/v1/auth/key` for validation.
- Jev decisions send the research goal, requested platform, bounded action labels, observed source URLs, previous action summaries, and up to 400 characters of visible title, caption, text, or name for each captured item to OpenRouter's Decisions API. This content may contain public or personal social-media data. The request does not intentionally include raw socai JSON, downloaded media, browser cookies, or local filesystem paths.
- When `JEV_SOCIAL_SYSTEM_ONE_URL` is configured, the same bounded decision payload is sent instead to an explicit loopback-only TypeSafe-compatible endpoint such as Kev. Only plain HTTP on `localhost`, `127.0.0.1`, or `::1` with the exact `/v1/systemone` path is accepted. Redirects, URL credentials, query strings, fragments, non-loopback hosts, oversized responses, and malformed typed answers fail closed. The OpenRouter key is never attached to this local request.
- Evidence-report synthesis is enabled by default and makes a second OpenRouter model call after collection. Its compact, bounded user payload is at most 48,000 characters and contains the research goal, selected platform, run status and stop reason, coverage counts, and at most 40 sanitized records: source URLs, titles, up to 1,000 characters of each author claim, up to five 300-character comment excerpts, observed engagement metadata, and capture depth. Set `OPENROUTER_REPORT_MODEL=off` to keep report generation deterministic and prevent this synthesis call. The synthesizer receives no browser or shell tools.
- Provider-side storage and retention are governed by OpenRouter and the selected model provider, not this repository.
- A local decision server has its own model, log, and retention behavior. Jev Social neither starts nor downloads that server automatically. Set `OPENROUTER_REPORT_MODEL=off` if an OpenRouter key remains configured but the report must stay on the deterministic local path.
- The installed socai CLI and Chrome connect to the selected social platform. Their browser and network behavior is maintained by [socai](https://github.com/socai-io/socai), outside the Jev Social process.

### socai CLI telemetry

Jev Social does not proxy OpenRouter traffic through a Jev Social or socai server and does not operate an analytics endpoint of its own. Its OpenRouter requests go directly to OpenRouter. It launches `socai` with an explicit environment allowlist that excludes `OPENROUTER_API_KEY`, `TYPESAFE_API_KEY`, `SOCAI_API_KEY`, and session-token variables.

The installed `socai CLI` has a separate telemetry contract. Jev Social sets `SOCAI_TELEMETRY=0` when it is absent, so its spawned CLI processes do not emit socai telemetry by default. This privacy default applies to capability probes and browser actions and works when the CLI reuses an existing daemon. Set `SOCAI_TELEMETRY=1` in the launching environment or project `.env` only to opt in explicitly.

For the audited `socai v0.6.1` release, explicitly enabled telemetry has these boundaries:

- Structured CLI events go to `https://socai.io/v1/events`, then the first-party proxy forwards every client-supplied scalar field to the third-party observability provider Axiom. The public client does not contact Axiom directly.
- Events include a stable install ID, process-session and request IDs, app/platform/device context, command status and timing, and search query text by default. Shared enrichment code can also add the authenticated cloud account's full phone number, point balance, Pro expiry, and subscription status when that account snapshot is available.
- Every non-`query` command argument is summarized into event metadata. Depending on the selected action, that can include Instagram or LinkedIn profile/company URLs and TikTok author handles or URLs. `SOCAI_TELEMETRY_QUERY_TEXT=off` omits the dedicated search-query text but does not remove those targets or other metadata. Only the master `SOCAI_TELEMETRY=0` setting prevents the CLI event upload.
- Ordinary tool results do not include captured post/comment bodies, downloaded media, cookies, browser storage, raw output, or model output. A bounded unexpected-page OCR diagnostic is a documented exception. socai applies pattern-based secret scrubbing to event text, but it is not a guarantee for arbitrary secret formats pasted into a query, target, error, or other field. Independently, Jev Social prevents its configured OpenRouter and socai credentials from entering the child environment at all.
- `SOCAI_TELEMETRY_CHAT_TEXT=off` controls conversation content and note summaries in agent run traces. Jev Social forwards it, but Jev Social invokes plain CLI tool commands, which emit events rather than uploading traces. The TUI may write `trace.json` locally without uploading it. Only the separately launched desktop app uploads content-bearing run traces, and an already-running desktop process is unaffected by Jev Social's child environment; configure or restart that desktop process with its own `SOCAI_TELEMETRY=off` setting.
- The public `v0.6.1` telemetry contract does not specify a server-side deletion or retention period. Do not assume one. Local Jev Social and socai artifacts still follow the separate manual-retention rules below.

Jev Social does not pin the installed socai executable: onboarding resolves the current official release, and `SOCAI_BIN` can select another build. The statements above are the audited `v0.6.1` behavior, not a promise about another version. Check the version shown by Jev Social and review that release's telemetry contract when it differs.

See the immutable [`socai v0.6.1` telemetry schema](https://github.com/socai-io/socai/blob/v0.6.1/docs/telemetry-schema.md) for the field-level contract and source references.

### Keys and browser sessions

- A key entered interactively during `onboard` is saved in `config.json` with file mode `0600`. If `OPENROUTER_API_KEY` is already present in the environment, onboarding can use it without writing a second copy to the config file.
- The OpenRouter key is filtered out of the environment passed to the socai subprocess.
- Chrome cookies and login state remain in the Chrome or socai profile selected by the installed socai CLI. Jev Social does not read or copy the browser cookie store directly. Use a separate browser profile or test account when the research target is sensitive.

### Local artifacts

- `JEV_SOCIAL_HOME` controls Jev Social's local state root; the default is `~/.jev-social`.
- `config.json` and `runs/<run-id>.json` are written with file mode `0600`, inside directories created with mode `0700`. A saved run contains the goal, decisions, command strings, captured evidence, source URLs, report, and captured socai output. It can therefore contain personal or sensitive social content even though API keys and cookies are not part of the run object.
- socai keeps its own run artifacts in its configured run directory. Depending on the command, those artifacts can include downloaded media and other browser evidence. Jev Social exposes an eligible media file only through an opaque loopback URL and expires that in-memory URL after one hour; expiry does not delete the underlying file.
- No automatic retention or cleanup schedule is applied to either store. After stopping Jev Social, inspect and remove only the specific run JSON files and specific socai run directories you no longer need. Do not use a broad recursive deletion against either configured state root.

### External effects and recovery

- Supported platform operations do not change remote social state, but they still make network requests and write local run files. Jev Social exposes a TikTok action containing `--download-media` only when the user's goal explicitly asks to download, save, archive, capture, record, or keep an offline copy of media. That authorization is recorded as `downloadMedia: true` on the selected action in run history; there is no second confirmation after the explicit request.
- Jev and platform requests can incur provider or network costs. `--max-steps` bounds decision-loop work, and cancellation terminates the active socai process tree.
- Access gates, low-confidence decisions, failed operations, and step exhaustion produce partial or failed runs instead of changing remote social state. Recovery consists of stopping the run, reviewing the saved evidence, and removing only the unwanted local artifacts described above.
