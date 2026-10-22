---
name: domain-email
description: Sets up email on the user's own domain, such as hello@yourdomain.com, a real mailbox that sends and receives, with DropTheHassle. Use when the user wants domain email, a professional email address, an inbox like info@ or hello@ on their domain, or asks "can I get email on my domain". Checks the domain is active with site_status, then hands the human a checkout.stripe.com payment link from get_email_checkout_link (main inbox €5 / $5 a month). The agent never pays and never reads the mail.
license: MIT
compatibility: Needs a domain already on the user's DropTheHassle account and an account token (hosted MCP https://dropthehassle.com/mcp with sign_in, or DTH_TOKEN for npx -y dropthehassle-mcp@latest). The CLI `npx -y dropthehassle@latest email` shows the current state.
metadata:
  author: DropTheHassle
  homepage: https://dropthehassle.com
  version: "1.0.0"
---

# Email on your own domain

DropTheHassle turns on a mailbox for a domain on the user's DropTheHassle site: it sends and
receives (not forwarding only). Read and send in the DropTheHassle webmail, or in any mail app over
IMAP/SMTP with the settings shown in the dashboard. The main inbox is €5 / $5 a month, including VAT
in the EU. The price is shown and confirmed before anything is enabled.

## The one rule

You never pay. Give every payment link (`checkout.stripe.com`) to the human. You cannot read their
mail or see the mailbox password, and you don't need to.

## Steps

1. **The domain has to be on DropTheHassle.** No domain yet? Use the `buy-domain` skill first.
   A domain at another registrar must be on the DropTheHassle account first (a transfer, done by the
   human in the dashboard).
2. **Sign in.** Hosted MCP: `sign_in`, the user opens the link. Local server: `DTH_TOKEN` set.
3. **Check the domain is active**: `site_status` with `site`. It lists domains and any email already
   on. From a linked folder, `npx -y dropthehassle@latest email` shows the same.
4. **Ask which address** they want (e.g. `hello`, `info`, their name). Don't pick it for them.
5. **Get the payment link**: `get_email_checkout_link` with `site` and `address`. Give the link and
   price to the human. The human pays.
6. **After they pay**, the mailbox and its DNS records are set up. Check `site_status`, then tell them
   to open the webmail in the dashboard or add the IMAP/SMTP settings shown there to their mail app.

## Not available to an AI

Extra addresses (€3 / $3 a month each) and changing where the main inbox delivers: the human does
those in the dashboard.
