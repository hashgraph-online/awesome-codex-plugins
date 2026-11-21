# Security reports

Report vulnerabilities privately to the maintainer at **axegggl@gmail.com**. Do not open a public issue containing credentials, exploit instructions or private conversation data.

Include the plugin and Codex versions, a reproduction with synthetic data, and the affected behavior. Send no bot token, API key or original transcript. The maintainer will coordinate investigation and disclosure by email.

## Access boundary

Pairing grants access to a Codex session with full filesystem access and no approval prompts. Roles identify participants; they do not provide filesystem isolation. Supported setup/access commands require the matching request entered in the owner's local Codex terminal, or an interactive owner command outside Codex. Telegram input cannot authorize those commands. The CLI conversation and model receive a token pasted into the configure skill. Keep the state directory private to that operating-system user; the checks on supported commands do not create a sandbox against arbitrary same-account filesystem access.
