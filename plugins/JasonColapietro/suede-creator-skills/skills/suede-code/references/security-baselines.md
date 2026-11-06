# Security Baselines

The security baseline the review scores against, per OWASP category, with what counts as a finding in each. Last checked against the official lists in October 2026.

Run the web baseline automatically on `auth/`, `api/`, `middleware/`, `routes/`,
`pages/api/`, or code importing crypto, session, or payment modules. Cite the
exact standard and category in each finding. Use the current official lists;
do not remap a finding to an older category number.

### OWASP Top 10 (2025)

- **A01 Broken Access Control:** enforce object, function, tenant, and admin
  authorization server-side; default deny and prevent horizontal escalation.
- **A02 Security Misconfiguration:** safe production defaults, least-exposed
  services, hardened headers, no debug output, and reviewed cloud/runtime config.
- **A03 Software Supply Chain Failures:** lock and verify dependencies and build
  inputs; protect CI/CD, registries, provenance, and update paths.
- **A04 Cryptographic Failures:** approved algorithms and key management; protect
  sensitive data in transit and at rest; never place secrets in source.
- **A05 Injection:** parameterize commands and queries, validate untrusted input,
  and contextually encode output.
- **A06 Insecure Design:** threat-model trust boundaries, abuse cases, rate
  limits, and fail-closed behavior before implementation.
- **A07 Authentication Failures:** resist enumeration and brute force; use secure
  recovery, MFA where warranted, rotation, expiry, and session invalidation.
- **A08 Software or Data Integrity Failures:** verify signatures and provenance,
  validate deserialized data, and prevent untrusted update or plugin execution.
- **A09 Security Logging and Alerting Failures:** record and protect meaningful
  security events, detect abuse, alert operators, and avoid sensitive log data.
- **A10 Mishandling of Exceptional Conditions:** handle errors, timeouts,
  resource exhaustion, partial failure, and cleanup without failing open.

Official list: https://owasp.org/Top10/2025/

### OWASP API Security Top 10 (2023)

For APIs, explicitly check **API1 Broken Object Level Authorization**, **API2
Broken Authentication**, **API3 Broken Object Property Level Authorization**,
**API4 Unrestricted Resource Consumption**, **API5 Broken Function Level
Authorization**, **API6 Unrestricted Access to Sensitive Business Flows**,
**API7 Server Side Request Forgery**, **API8 Security Misconfiguration**, **API9
Improper Inventory Management**, and **API10 Unsafe Consumption of APIs**.
Trace each request through object/property/function authorization, quotas and
cost bounds, business-flow abuse controls, outbound URL policy, versioned API
inventory, and validation of third-party responses.

Official list: https://owasp.org/API-Security/editions/2023/en/0x10-api-security-risks/

### OWASP MASVS v2.1+ Mobile Baseline

For native or hybrid mobile changes, map findings to **MASVS-STORAGE**,
**MASVS-CRYPTO**, **MASVS-AUTH**, **MASVS-NETWORK**, **MASVS-PLATFORM**,
**MASVS-CODE**, **MASVS-RESILIENCE**, or **MASVS-PRIVACY**. Check local data and
backup exposure, key handling, authentication/session flows, TLS and endpoint
trust, IPC/deep links/web views, update/runtime safety, tamper resistance where
the threat model requires it, and privacy-minimized collection/disclosure.

Official standard: https://mas.owasp.org/MASVS/
