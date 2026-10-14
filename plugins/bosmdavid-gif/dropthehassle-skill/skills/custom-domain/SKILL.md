---
name: custom-domain
description: Connects a domain the user already owns (bought at another registrar) to their DropTheHassle site, free, with one A record. Use when the user says "use my own domain", "connect my domain", "add a custom domain", "point my domain to my site" or already has a .com at GoDaddy, Namecheap, Cloudflare or similar. Gets the A record from DropTheHassle, shows it to the human to set at their registrar, then checks HTTPS is live. Never edits DNS at the registrar for them. For a name they don't own yet, use buy-domain.
license: MIT
compatibility: Needs network access to dropthehassle.com and a site published with DropTheHassle (npx -y dropthehassle@latest deploy, or the MCP at https://dropthehassle.com/mcp).
metadata:
  author: DropTheHassle
  homepage: https://dropthehassle.com/guides/domain-without-dns
  version: "1.0.0"
---

# Connect a domain the user already owns

Connecting an existing domain to a DropTheHassle site is free and needs no transfer: one A record
at the user's registrar. HTTPS follows by itself.

## Steps

1. **Have a published site.** If not, publish first:
   `npx -y dropthehassle@latest deploy ./dist` (answer gives the live link and claim link).
2. **Ask for the exact name** (`example.com` or `www.example.com`). Don't guess it.
3. **Get the A record**, one of:
   - Folder published with the CLI: read `site_id` and `site_token` from that folder's
     `.dropthehassle.json`, then
     ```bash
     curl -s -X POST "https://dropthehassle.com/api/v1/sites/<site_id>/connect" \
       -H "Authorization: Bearer <site_token>" -H "Content-Type: application/json" \
       -d '{"name":"example.com"}'
     ```
     The answer says which A record to set. Don't print the site token back to the user.
   - Claimed site: the human opens the site in the dashboard, presses **Point it here** and enters the
     name. The dashboard shows the address.
4. **Show the human the record** (type A, host `@` or the subdomain, value from the answer). They set
   it at their registrar. Don't log in to their registrar or change DNS for them.
5. **Check it**: after they set it, the human presses **Check now** in the dashboard, or run
   `npx -y dropthehassle@latest status <site>`. DNS can take minutes to hours. Then open
   `https://example.com` and confirm it serves the site.

## Notes

- `point_domain` (MCP, account token) only moves a domain that is already on the DropTheHassle
  account to another of their sites. It does not connect outside domains.
- Moving the registration itself (a transfer) is a human step in the dashboard.
- Want email on that name too? See the `domain-email` skill (needs the domain on DropTheHassle).
