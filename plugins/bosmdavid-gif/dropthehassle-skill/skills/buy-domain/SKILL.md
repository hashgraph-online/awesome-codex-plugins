---
name: buy-domain
description: Finds a free domain name for the user's website and hands them a payment link to buy it, with DropTheHassle. Use when the user wants to buy a domain, find a domain name, check if a .com is available, "get a .com" or "my own domain" for a site. Checks real availability and price with search_domain or the DropTheHassle domain search API, suggests a short list, and after a yes returns a checkout.stripe.com link the human pays. The site goes live on the name with HTTPS and no DNS. The agent never pays.
license: MIT
compatibility: Needs network access to dropthehassle.com. Searching needs no account. Buying needs the site on the user's DropTheHassle account (hosted MCP https://dropthehassle.com/mcp with sign_in, or DTH_TOKEN for npx -y dropthehassle-mcp@latest).
metadata:
  author: DropTheHassle
  homepage: https://dropthehassle.com/guides/buy-domain-with-ai
  version: "1.0.0"
---

# Buy a domain name (the human pays)

DropTheHassle sells .com, .org and .net at €19 / $19 a year (including VAT in the EU, the same every
year), .nl and .eu at €12 / $12 and .app at €25 / $25. It does not sell .co, .shop, .studio, .io or .ai.
A name bought here goes live on the user's DropTheHassle site with HTTPS and no DNS editing.
Always quote the price from a search answer in this session, not from this page.

## The one rule

You never pay and never open, fill in or pay a payment link. A DropTheHassle payment link is always on
`checkout.stripe.com`. Create one only after the user said yes to that exact name.

## Steps

1. **Suggest 3 to 8 short names** from the project (brand, package.json name, page title).
2. **Check them** (free, read-only, about 30 lookups per 10 minutes):
   - MCP: `search_domain` with `name` (a bare name such as `studiomaple` checks .com, .nl and .app).
   - No MCP:
     ```bash
     curl -s "https://dropthehassle.com/api/v1/domains/search?q=studiomaple.com"
     ```
     Call a name available only when `"available": true`. If `"verified": false`, say it is confirmed
     at checkout.
3. **Show only checked results**, e.g.
   `studiomaple.com: available, EUR 19/year incl. VAT in the EU, or USD 19 elsewhere, the same every year.`
   Optional: `check_trademark` for a quick look at EU and US word marks (not legal advice).
4. **Ask which one they want.** Stop here until they answer.
5. **Make sure the site is on their account.** No site yet? Publish it first
   (`npx -y dropthehassle@latest deploy ./dist`, or the `dropthehassle-publish` skill). Anonymous site?
   Sign in (`sign_in` on the hosted MCP) and `claim_site` with the claim link.
6. **Get the payment link**: `get_checkout_link` with `site` and `name`. Give the link, amount and
   expiry to the human. The human pays it.
7. **After they pay**, check `site_status` until the domain is active, then `check_live`.
   Offer a mailbox on the name (see the `domain-email` skill). Don't create that link unasked.

Site already runs on another host (Vercel, ChatGPT Sites, ...)? They can still buy the name here and
keep the site where it is: link its HTTPS address with `set_backend` (or the Backend card in the
dashboard), e.g. `https://myapp.vercel.app`. DropTheHassle serves the domain and passes every request
to that host, so no DNS records are needed, and email on the domain still works. There is no raw DNS
record editor; to manage DNS themselves, transfer-out gives them the transfer code for another registrar.

Already own the name somewhere else? Use the `custom-domain` skill instead.
