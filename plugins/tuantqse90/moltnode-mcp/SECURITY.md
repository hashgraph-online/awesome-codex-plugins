# Security policy

## Reporting a vulnerability

Please report security issues privately through GitHub's "Report a vulnerability" (Security tab of this repository), or open
an issue with only a request for a private contact if that is not available. Do not post exploit details in public issues.

We aim to acknowledge reports within 3 days and to ship a fix or mitigation for confirmed issues as fast as their severity
requires.

## Scope

- This repository: the stdio bridge (`index.mjs`), the plugin and extension manifests, and the skills under `skills/`.
- The hosted servers it points to: `https://moltnode.ag/mcp` (MoltNode) and `https://api.getchord.xyz/v1/mcp` (Chord).

## Design notes

- No secrets: nothing in this repository needs or stores an API key. The servers are keyless for reading; an optional free
  Chord key only raises rate limits.
- Non-custodial: the tools return unsigned transactions. They never ask for, receive or store a private key or seed phrase;
  signing happens in the user's own wallet.
