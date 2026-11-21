# Security

## Reporting a vulnerability

Please do not open a public GitHub issue for a suspected vulnerability.

Send the report to [feedback@bestprice.gr](mailto:feedback@bestprice.gr), or use
the [BestPrice contact page](https://www.bestprice.gr/contact). Put "MCP
security report" in the subject when using email, and include:

- the affected URL, tool, or file in this repository;
- clear reproduction steps;
- the impact you observed;
- any request IDs that the service returned;
- a safe way to contact you.

Do not include credentials, payment-card data, personal data that is not needed
for the report, or live exploit traffic against other users.

## What happens next

BestPrice acknowledges reports within five business days and keeps you informed
while the issue is investigated and fixed. We ask for up to 90 days of
coordinated disclosure from the acknowledgement; if a fix ships sooner, we will
agree an earlier publication date with you. We credit reporters who want to be
credited.

## Scope

In scope:

- the hosted MCP service at `https://mcp.bestprice.gr/mcp` and its server card;
- the WebMCP tools registered on `https://www.bestprice.gr/` pages;
- the code in this repository: the stdio bridge (`stdio.mjs`, `src/`), the
  Docker image built from it, and the WebMCP layer in `webmcp/`;
- the client manifests in this repository, if one of them could point a client
  somewhere other than the public endpoint.

Out of scope: the third-party AI clients, directories, and marketplaces that
list or connect to the service, and social engineering of BestPrice staff.

## Good-faith research

Testing the public endpoint with your own requests is welcome as long as you
avoid degrading the service for others (no volumetric or automated flooding),
do not access data that is not yours, and stop and report as soon as you find
an issue. BestPrice will not pursue action against research conducted in this
spirit.

## Supported version

The hosted service is continuously updated; only its current production
version is supported. The manifests in this repository describe that hosted
service, and the stdio bridge is supported at its latest tagged release.

The canonical machine-readable security contact is published at
[`https://www.bestprice.gr/.well-known/security.txt`](https://www.bestprice.gr/.well-known/security.txt).
