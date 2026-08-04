# Threat-focused review checklist

Use relevant sections rather than reporting every item.

## Identity and authorization

- Session and token validation
- Resource-level and tenant-level authorization
- Privilege escalation and confused-deputy paths
- Account recovery, invitation, and impersonation flows

## Injection and execution

- SQL, NoSQL, template, shell, expression, and log injection
- Unsafe deserialization or dynamic evaluation
- Path traversal, archive extraction, and file upload handling
- XSS and unsafe HTML or URL handling

## Network boundaries

- SSRF and internal service access
- Redirect validation
- Webhook authenticity and replay
- TLS and certificate assumptions

## Data protection

- Secret, token, personal, financial, and health data exposure
- Logging, analytics, caching, backups, and error messages
- Encryption and key lifecycle according to repository policy
- Cross-tenant caching or object references

## Browser and API

- CSRF and origin assumptions
- CORS and credential configuration
- Rate limits and abuse controls
- Mass assignment and over-broad response fields

## Supply chain and operations

- Untrusted CI execution with privileged tokens
- Dependency and action provenance
- Container and runtime privileges
- Cloud IAM expansion
- Secret injection into builds or artifacts

For a dependency, lockfile, base-image, or CI-action change:

1. Identify the direct change and unexpected transitive lockfile churn.
2. Verify the package, image, publisher, source, version, checksum, signature, or
   commit pin using repository-approved authoritative metadata.
3. Treat advisory and scanner results as leads; confirm the affected version,
   vulnerable behavior, and whether the dependency is reachable in this system.
4. Check install/build scripts, generated artifacts, credential exposure, and
   whether untrusted pull-request code can reach privileged automation.
5. Prefer the smallest compatible patched version or removal, then run focused
   behavior and build verification.
6. Record unresolved transitive risk, compensating controls, and update owner.

Do not execute an untrusted package merely to inspect it, and do not suppress an
advisory solely because the current test suite passes.

## Severity questions

- Can an external or low-privilege actor reach it?
- What asset is affected?
- Is user interaction required?
- Is impact contained to one tenant or broad?
- Do existing controls materially reduce exploitability?
