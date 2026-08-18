# Client Application Security Review

| Field | Value |
| --- | --- |
| Client / platform(s) | <browser/native; versions> |
| Trust boundary | <client hints vs server-enforced decisions> |
| Client sinks | <sink: neutralization> |
| Credential boundary | <embedded reusable credential prohibited; short-lived token or device-bound/non-exportable key; server-side enforcement> |
| Local storage | <data class: protected storage; exportability; lifetime; deletion> |
| Transport trust | <TLS; pinning decision; rotation/recovery> |
| Entry points | <deep links / schemes / intents / web views: validation> |
| Tamper posture | <defense-in-depth only> |
| Negative tests | <injection, malicious deep link, downgrade, tampered build> |
| Residual risk | <risk, compensating control, owner, expiry> |
