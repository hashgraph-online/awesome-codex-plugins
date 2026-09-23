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
- Provider-side storage and retention are governed by OpenRouter and the selected model provider, not this repository.
- The installed socai CLI and Chrome connect to the selected social platform. Their browser and network behavior is maintained by [socai](https://github.com/socai-io/socai), outside the Jev Social process.

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
