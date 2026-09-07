# Security policy

Please report suspected vulnerabilities privately to `zack@codetruss.com` with
the subject `CodeTruss security report`. Include the affected wrapper or CLI
version, reproduction steps, impact, and whether public disclosure is already
planned. Do not include third-party source code, credentials, or unredacted
receipts unless requested through a mutually agreed secure channel.

We will acknowledge a report within two business days, provide a preliminary
triage within five business days when reproducible, and coordinate disclosure
after a fix or mitigation is available. Availability and timelines may change
for reports that cannot be reproduced or concern unsupported versions.

The MIT wrapper repository contains skill instructions and manifests only. CLI
implementation reports belong in the public CLI issue tracker unless they are
security-sensitive. Deterministic CLI operation is local; optional provider
review sends the reviewed diff directly to the selected provider, and explicit
sync sends a privacy-minimized receipt to CodeTruss but never the patch.
