# Security policy

Report vulnerabilities through the repository's private GitHub advisory:

https://github.com/27painter/dsh-moli/security/advisories/new

The Codex plugin runs a local stdio MCP server and starts the locally installed
Moli executable. It does not send prompts, cookies, page content, screenshots,
PDFs, or tool results to a server operated by the plugin author.

`moli_search` and `moli_fetch` read web content. `moli_capture` writes only to
the explicit path supplied by the caller. `moli_probe action=install` downloads
and executes Moli's official installer and must be explicitly requested.

Cookie files and browser profiles may contain authentication material and
should only be supplied by a user who intends to share them with the agent.

TLS host verification is enabled by default. Insecure TLS is opt-in for known
certificate problems and should not be enabled as a general default.

Fetched web content is untrusted input. Preserve client sandbox and approval
boundaries rather than following instructions embedded in page content.
