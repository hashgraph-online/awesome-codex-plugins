# Adding DNS records on common hosts

You add TXT records wherever the domain's **authoritative DNS** lives — often the registrar, sometimes a separate DNS host (Cloudflare, Route 53). Find it with:

```bash
dig +short NS <domain>
```

General rules for all hosts:

- **Type:** TXT (MX for mail servers).
- **Name/Host:** the part **before** the domain. For a record at `example.com`, many UIs want `@` or blank. For `selector._domainkey.example.com`, enter `selector._domainkey` (the UI appends the domain). For `_dmarc.example.com`, enter `_dmarc`.
- **Value:** paste exactly, including `v=spf1`/`v=DKIM1`/`v=DMARC1`. Do not add surrounding quotes unless the UI requires them; never wrap/split the value yourself.
- **TTL:** default (e.g. 3600) is fine.
- Some UIs auto-append the domain to the Name — do not double it (avoid `_dmarc.example.com.example.com`).

Host-specific notes (verify against the host's current docs; UIs change):

- **Cloudflare:** DNS → Records → Add record. For root SPF/DMARC use `@` / `_dmarc`. Set proxy status to DNS-only (grey cloud); TXT is not proxied anyway.
- **AWS Route 53:** Hosted zones → Create record → TXT. Enter the full subdomain in *Record name*; wrap each value in double quotes.
- **GoDaddy / Namecheap:** DNS management → Add → TXT. Host = `@`, `_dmarc`, or `selector._domainkey`.
- **Google Domains / Squarespace, Vercel, Netlify:** add TXT under the domain's DNS section with the same Name/Value rules.

After adding, confirm with `dig +short TXT <name>` (see verification in SKILL.md). Propagation is typically minutes but can take hours.
