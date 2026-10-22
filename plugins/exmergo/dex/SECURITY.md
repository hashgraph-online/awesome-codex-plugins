# Security Policy

dex connects to data warehouses, discovers credentials, and writes to your
repository, so security is a first-class concern and several guarantees are
enforced in the engine itself: read-only against your data, writes confined to
reviewable diffs, dev-target-only builds, cost surfaced before any spend, and
credentials and raw rows kept out of agent context. Repository confinement runs
in both directions: a path dex reads a semantic-layer document from, and a path
it writes one to, must resolve inside the repository, so an absolute path, a `..`
that walks out, and a symlink resolving out are each refused rather than
followed. If you find a way to violate any of these, we want to hear about it.

## Reporting a vulnerability

Please report security issues privately. Do not open a public GitHub issue for a
vulnerability.

- Preferred: open a private report through GitHub's security advisories at
  https://github.com/exmergo/dex/security/advisories/new
- Or email security@exmergo.com.

Include the affected version, a description of the issue, and the steps to
reproduce it. Please do not include real credentials or raw warehouse data in
your report; a sanitized reproduction is enough.

## What to expect

- We aim to acknowledge your report within 3 business days.
- We will confirm the issue, share our assessment and a remediation timeline,
  and keep you updated as we work on a fix.
- We will credit you in the release notes when the fix ships, unless you prefer
  to remain anonymous.

## Supported versions

Security fixes are applied to the latest published version only. 
Pin to a released version and upgrade promptly when a security release is announced.
