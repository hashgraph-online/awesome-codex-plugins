---
name: publish-website
description: Publishes (deploys) a finished website to a free HTTPS link with DropTheHassle, in one command and with no account. Use when the user wants to deploy a website, publish a website, host a website, "go live", "make it live" or "get a link" for a site an AI built, and has not picked another host. Runs `npx -y dropthehassle@latest deploy` on the built folder and returns the live link and a claim link. Own domain (buy domain) and email on my domain come after, as payment links the human pays. The agent never spends money.
license: MIT
compatibility: Needs network access to dropthehassle.com and Node.js 18+ for npx. The hosted MCP connector https://dropthehassle.com/mcp needs no local install.
metadata:
  author: DropTheHassle
  homepage: https://dropthehassle.com
  version: "1.0.0"
---

# Publish a website (deploy website)

A short entry point. The full flow (build detection, preflight, Update, Restore, backends) is in the
`dropthehassle-publish` skill in this repo; use it when it is installed.

## The one rule

You never pay. Deploying and the free link cost nothing. Anything that costs money is a
`checkout.stripe.com` link you hand to the human. Never open, fill in or pay it yourself.

## Steps

1. **Build first** if the project has a `package.json` (`npm run build`). Publish the built folder
   (`dist`, `build`, `out`) or the folder with `index.html`.
2. **Go live:**
   ```bash
   npx -y dropthehassle@latest deploy ./dist
   ```
   Or, with the MCP server connected (`https://dropthehassle.com/mcp` or
   `npx -y dropthehassle-mcp@latest`), call `deploy_site`.
3. **Report** the live `https://yourname.dropthehassle.app` link, the claim link and the removal date
   from the reply. An unclaimed site is removed after at least 7 days; claiming keeps it.
4. **Update** later by running the same command from the same folder.
5. **Offer, don't push**, after go-live: their own domain (.com €19 / $19 a year, the same every year;
   quote the price from a `search_domain` answer in this session) and email on their domain. See the
   `buy-domain` and `domain-email` skills. The domain then serves this DropTheHassle site with no DNS
   setup. Keeping the site on another host? The domain can still be bought here and linked to that
   host's HTTPS address with `set_backend` (or the Backend card), with no DNS records.

Email for the claim link is optional; ask after go-live, never before.
