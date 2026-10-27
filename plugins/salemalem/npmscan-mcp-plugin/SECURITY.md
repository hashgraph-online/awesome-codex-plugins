# Security policy

## Reporting a vulnerability

Email **shyngys@blockhacks.io** with "SECURITY" in the subject line. Please
include what you found, how to reproduce it, and which part is affected.

Please don't open a public GitHub issue for a security problem. We reply within
3 business days and aim to ship a fix or mitigation within 30 days. We credit
reporters in the changelog unless you'd rather stay anonymous.

## Scope

- This repository: plugin manifests, skills and install docs.
- The hosted MCP server at `https://npmscan.com/api/mcp` that the plugin
  connects to.

Reports about a malicious or vulnerable npm package itself should go to the
package's maintainers or to npm (`npm report`). You can also look the package
up on [npmscan.com](https://npmscan.com).

## How the plugin works

- The plugin contains no code that runs on your machine. It is skills
  (Markdown) plus a connection to a remote MCP server.
- All MCP tools are read-only lookups of public npm, OSV.dev, GitHub Security
  Advisories and NIST NVD data. They never install, remove or change packages.
- No API key, account or credentials are needed, and the plugin stores none.

## Supported versions

Only the latest release on the `main` branch is supported.
