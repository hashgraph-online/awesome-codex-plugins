# Security policy

## Supported versions

Security fixes are applied to the latest version on the `main` branch.

## Reporting a vulnerability

Please report vulnerabilities privately by emailing `jose@skillnet.es`. Include the affected
version, reproduction steps, impact, and any suggested mitigation. Do not open a public issue until
the report has been reviewed. You can expect an acknowledgement within seven days.

## Local file access

`mcp-md-reader` runs with the filesystem permissions of the process that starts it. Its tools accept
Markdown file or vault paths supplied by the MCP client, so a client can request any readable
Markdown file on that machine. Run the server only with trusted MCP clients and under an operating
system account whose file access matches your intended boundary.

Parsed content is cached under the operating system temporary directory in
`mcp-md-reader-cache`. The cache has a seven-day TTL and can be removed by deleting that directory
after the server stops.
