# Security policy

## Scope

This policy covers:

- the hosted MCP server at `https://mcp.maqami.co/`, and
- the `maqami-travel` npm package (the stdio bridge in this repository).

## Reporting a vulnerability

Please don't report security issues in public issues, discussions or pull requests.

Report them privately in one of these ways:

- GitHub private vulnerability reporting: open the [Security tab](https://github.com/negm17111995/mcp-server/security) of this repository and choose **Report a vulnerability**.
- Email [info@maqami.co](mailto:info@maqami.co) with the subject "Security report".

Please include:

- what you found and where (endpoint, tool name or file),
- steps to reproduce, and
- the impact you expect.

Please don't include real guest or payment data in a report. Don't make real bookings, access other people's bookings or run load tests against the hosted endpoint while testing.

We will acknowledge your report, keep you informed while we investigate, and credit you when a fix is released if you'd like.

## Supported versions

| Component | Supported |
| --- | --- |
| Hosted endpoint `https://mcp.maqami.co/` | Yes |
| `maqami-travel` npm package, latest release | Yes |
| Older npm releases | No. Please upgrade to the latest version. |
