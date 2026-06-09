# SPF, DKIM, DMARC, and alignment

Three DNS-based mechanisms decide whether mail is authenticated. All are published as DNS TXT records on the sending domain.

## SPF (Sender Policy Framework)

- One TXT record at the domain root authorizing who may send for it.
- Shape: `v=spf1 include:<provider-include> ~all`
  - `include:` pulls in a provider's authorized servers. Use the exact include SenderKit gives you (do not invent it).
  - `~all` = softfail (recommended while stabilizing). `-all` = hardfail (stricter). `+all` is never correct.
- **Exactly one** `v=spf1` record per domain. Two SPF records = both ignored. Merge multiple `include:` into a single record.
- **10-DNS-lookup limit:** every `include`, `a`, `mx`, `ptr`, `exists`, and `redirect` counts. Exceeding 10 makes SPF `permerror`. Flatten or remove unused includes.
- Check: `dig +short TXT <domain>`

## DKIM (DomainKeys Identified Mail)

- A cryptographic signature; the public key is published as a TXT record at `<selector>._domainkey.<domain>`.
- Shape: `v=DKIM1; k=rsa; p=<base64 public key>`
- The **selector** and key are issued by the sender (SenderKit). Obtain the exact record from the SenderKit dashboard; do not guess the selector.
- Check: `dig +short TXT <selector>._domainkey.<domain>`

## DMARC (Domain-based Message Authentication, Reporting & Conformance)

- One TXT record at `_dmarc.<domain>` telling receivers what to do when SPF/DKIM fail, and where to send reports.
- Shape: `v=DMARC1; p=none; rua=mailto:dmarc@<domain>; adkim=s; aspf=s`
  - `p=none` → monitor only. `p=quarantine` → spam folder. `p=reject` → block. Start at `none`, watch `rua` reports, then escalate.
  - `rua=` is the aggregate-report mailbox.
  - `adkim`/`aspf`: `r` = relaxed (default), `s` = strict alignment.
- Check: `dig +short TXT _dmarc.<domain>`

## Alignment

DMARC passes only if SPF or DKIM **aligns** with the visible `From:` domain:

- SPF alignment: the `MAIL FROM`/Return-Path domain matches the `From:` domain (relaxed = same organizational domain; strict = exact).
- DKIM alignment: the signature `d=` domain matches the `From:` domain.
- A message can pass raw SPF/DKIM yet fail DMARC if neither aligns. When a provider sends with its own Return-Path, rely on aligned DKIM.

## BIMI (optional, brand logo)

- TXT at `default._bimi.<domain>` pointing to an SVG logo; **requires DMARC at `quarantine` or `reject`** first. Note it only after enforcement is in place.
