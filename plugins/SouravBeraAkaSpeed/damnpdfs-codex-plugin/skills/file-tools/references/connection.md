# Connection, privacy and recovery

The local Node.js MCP bridge sends requests only to `https://api.damnpdfs.com`. It uses the same browser-owned execution bridge as the website's optional native WebMCP tools. Native WebMCP is feature detected; the HTTPS pairing path works without experimental browser flags.

Installation does not need an OpenAI API account, OpenAI API key, identity verification or a paid DamnPDFs account. Node.js 22+ must be installed and the browser must support the live DamnPDFs website.

1. Open https://damnpdfs.com/ in a normal, controlled browser tab.
2. Choose **Agent access**, create a single-use code, then call `connect_browser`.
3. Inspect the workspace and operate only on the requested files. One browser operation can run at a time.

Pairing codes expire after five minutes. Sessions initially last two hours. The connected tab's auto-renewal setting can extend a still-active session; this does not extend document retention. Closing/suspending the tab can interrupt access. Expired or revoked sessions require a new code. The bridge never stores credentials on disk, reads Codex authentication files, creates accounts, or changes a user's MCP configuration.

Browser workspaces may retain up to 100 MB for at most four hours. Temporary cloud files expire within one hour or are removed when their job/export is acknowledged or cleared. Downloaded files remain under the user's control. Native tools, and local-file imports through the bridge, transfer selected content to DamnPDFs. Website uploads for browser-only tools can avoid the bridge's cloud import. External AI sends selected content to the provider configured by the user. Review https://damnpdfs.com/privacy and https://damnpdfs.com/terms for current details.

If the browser is unavailable, reopen the same tab and inspect status before rerunning. If an operation is still running, inspect/cancel it deliberately; do not start duplicates. If a request times out, it may still be executing in the browser. If a credential is expired, request a new code. Do not retry invalid/revoked tokens indefinitely or weaken authorization.

The installed catalog is a reviewed snapshot. Run `catalog_check` to compare live names and schemas without uploading documents. Updating the plugin release is required when that check reports drift; discovery does not by itself prove execution.
