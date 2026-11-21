# Cloud, hosting and domains

## Hosting a project

1. **Free tier first, and read its terms.** Static sites, small APIs and side projects usually fit
   in a free tier (Cloudflare, Vercel, Netlify, GitHub Pages, Google Cloud always-free). Some hobby
   tiers forbid commercial use: check before putting a business on one.
2. **A small VPS beats a hyperscaler for steady small workloads.** A 4 to 6 USD VPS with a
   self-hosted PaaS (Coolify, Dokku, CapRover) often replaces 50+ USD of managed services. The catch
   is that the user maintains it.
3. **Egress is the hidden bill.** Serving large files or media from S3-style storage can cost more
   than everything else. Storage with zero egress fees, or a CDN in front, fixes it.
4. **Scale to zero** for anything idle most of the day (serverless, scheduled shutdown of dev
   environments, autoscaling minimum 0 where safe).
5. **Commit only to steady usage.** Savings plans and committed-use discounts pay off only on the
   baseline you are sure about; leave spikes on demand or spot.
6. **Spot or preemptible** for batch work, CI and anything that can restart.
7. **Budgets and alerts on day one.** Set a budget alert at the expected monthly cost; it is free
   on every major cloud and catches runaway bills.
8. **Estimate before creating resources** (for example `infracost` for Terraform) and state the
   monthly number.
9. **New account credits** and startup programs (see [../programs/startups.md](../programs/startups.md)).

## Domains

- Compare the **renewal** price, not the first-year price. Cheap first years on some TLDs renew at
  5 to 10 times the price.
- At-cost registrars charge only the registry fee; others add margin and upsells (privacy, email,
  SSL) that should be free.
- WHOIS privacy and TLS certificates should cost nothing.
- Pick the TLD for the brand, not because a tutorial or a free-first-year offer pushed it.
- For a domain the user will keep for years, prepaying several years before an announced price
  increase locks the lower price.
- Email on a custom domain: free forwarding (several registrars and Cloudflare offer it) may be
  enough; paid mailboxes only for people who actually send from them.

## Reference data

### Prices and levers (checked 2026-10-29, re-verify before quoting)

| Name | Who qualifies | What you get | Official URL | Status | Verified |
|---|---|---|---|---|---|
| AWS Free Tier (credit-based) | New AWS accounts (legacy 12-month tier no longer offered to new sign-ups) | $100 credits at sign-up + up to $100 more for completing activities. Free plan: no charges, limited service list, ends after 6 months or when credits run out (account then closes unless upgraded). Paid plan: all services, credits still apply. 30+ always-free services on both. | https://aws.amazon.com/free/ | changed - credits replaced 12-month tier (July 2025) | 2026-10-29 |
| Google Cloud Free Trial + Free Tier | New GCP customers (trial); everyone (Free Tier) | $300 credit for 90 days. Always free monthly: 1 e2-micro VM in us-west1/us-central1/us-east1 + 30 GB standard disk, 5 GB Cloud Storage (US regions), Cloud Run 2M requests, BigQuery 1 TiB query + 10 GiB storage, Cloud Run functions 2M invocations. | https://cloud.google.com/free | active | 2026-10-29 |
| Azure free account | New Azure customers (not direct PAYG in China/India) | $200 credit for 30 days, 20+ popular services free for 12 months, 65+ always-free services. Must switch to pay-as-you-go within 30 days to keep the 12-month offers. | https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account | active | 2026-10-29 |
| Oracle Cloud Free Tier (Always Free) | Anyone, one account per person | $300 credit for 30 days. Always Free: Ampere A1 1,500 OCPU-h + 9,000 GB-h/month (= 2 OCPU, 12 GB RAM), 2 AMD micro VMs, 200 GB block storage, 20 GB object storage, 2 Autonomous DBs, 10 TB/month egress. Idle instances (<20% for 7 days) may be reclaimed. | https://www.oracle.com/cloud/free/ | changed - A1 halved June 2026 | 2026-10-29 |
| Cloudflare R2 object storage | Anyone with a Cloudflare account | Zero egress fees. Standard $0.015/GB-month, Class A $4.50/M, Class B $0.36/M. Free monthly: 10 GB-month storage, 1M Class A, 10M Class B. Infrequent Access $0.01/GB-month (30-day minimum, $0.01/GB retrieval). | https://developers.cloudflare.com/r2/pricing/ | active | 2026-10-29 |
| Cloudflare Workers Free / Paid | Anyone | Free: 100,000 requests/day, 10 ms CPU per invocation, KV 100k reads/day + 1 GB, D1 5M rows read/day + 5 GB, SQLite Durable Objects 100k requests/day. Paid: $5/month incl. 10M requests + 30M CPU ms. | https://developers.cloudflare.com/workers/platform/pricing/ | active | 2026-10-29 |
| Cloudflare Pages Free | Anyone | 500 builds/month, 1 concurrent build (20 min timeout), 20,000 files per site, 25 MiB max file, 100 custom domains per project, 100 projects per account (Workers static assets for more). | https://developers.cloudflare.com/pages/platform/limits/ | active | 2026-10-29 |
| Hetzner Cloud | Anyone (identity checks apply) | Still far below hyperscalers: CX23 (2 vCPU, 4 GB, 40 GB NVMe, 20 TB EU traffic) EUR 5.49/month (product page shows 5.99), extra traffic EUR 1/TB. But 15 June 2026 repricing for new orders/rescales: CPX22 7.99 to 19.49, CCX13 15.99 to 42.99. Cost-optimized line showed "currently unavailable". | https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/ | changed - big 2026 price increases | 2026-10-29 |
| OVHcloud VPS | Anyone | VPS-1: 2 vCores, 4 GB RAM, 40 GB NVMe, unlimited traffic at 500 Mbps, from $4.54/month; VPS-4: 8 vCores, 24 GB, 200 GB, 3 Gbps, from $23.37. Daily backup included. Now cheaper than Hetzner entry plans. | https://www.ovhcloud.com/en/vps/ | active | 2026-10-29 |
| AWS Savings Plans | Any AWS account with steady usage | Up to 72% off On-Demand. Compute SP up to 66% (1 or 3 yr), EC2 Instance SP up to 72% (1 or 3 yr), SageMaker SP up to 64%, Database Savings Plans up to 35% (1-year only). | https://aws.amazon.com/savingsplans/faq/ | changed - Database Savings Plans added | 2026-10-29 |
| AWS EC2 Spot Instances | Any AWS account; interruptible workloads | Up to 90% off On-Demand; capacity can be reclaimed by AWS with short notice. | https://aws.amazon.com/ec2/spot/ | active | 2026-10-29 |
| Google Cloud CUDs + Spot VMs | Any GCP account | Resource-based CUDs up to 55% (70% memory-optimized). Flexible (spend-based) CUDs up to 28% (1 yr) and up to 63% (3 yr, M-series). Spot VMs up to 91% off, configurable preemption notice (120 s recommended). | https://docs.cloud.google.com/compute/docs/instances/committed-use-discounts-overview | active | 2026-10-29 |
| Cloudflare Registrar | Cloudflare account holders (domain uses Cloudflare nameservers) | At-cost registration, renewal and transfer (registry + ICANN fee, no markup), free WHOIS redaction and DNSSEC, 430+ TLDs incl. .ai (added March 2025). | https://www.cloudflare.com/products/registrar/ | active | 2026-10-29 |
| Porkbun | Anyone | Low flat pricing: .com $11.08 reg/renew. Free WHOIS privacy, Let's Encrypt SSL, URL forwarding, 20 email forwards. First-year sales (.xyz $2.04, .dev/.app $8.75, .io $28.12) renew at full price. | https://porkbun.com/products/domains | active | 2026-10-29 |
| .io renewal trap | Anyone buying .io | Promo first year (e.g. Porkbun $28.12) renews at $51.80/yr. Registry reportedly raising .io wholesale from $50 to $56 on 19 Jan 2027 (trade press, not registry page). Prepay multi-year renewals before increases. | https://porkbun.com/products/domains | changed - wholesale rise announced | 2026-10-29 (Porkbun price); wholesale rise unverified |
| .ai renewal trap | Anyone buying .ai | 2-year minimum for registration AND every renewal (registry rule). Porkbun $82.70/yr, so about $165 per renewal; transfer $165.09 includes 2 years. Registry (Identity Digital since Jan 2025) reportedly raised wholesale March 2026; watch $50 first-year promos that renew near $160. | https://porkbun.com/tld/ai | changed - higher prices, 2-yr minimum | 2026-10-29 (Porkbun page); registry increase unverified |
| Domain price comparison (TLD-List, domcomp, tldes) | Anyone | Free tables of cheapest registration, renewal, transfer and "best 3 year value" per TLD across registrars (TLD-List: about 3,500 TLDs, 55 registrars, user-reported). Compare renewal, not first-year price. | https://tld-list.com/ | unverified - sites block automated fetch (403) | unverified |
| Vendr (now part of Vertice) | Anyone can view marketplace; paid plans for companies | Free public pages with median price paid per SaaS vendor (e.g. Slack median $57,031/yr from 1,508 purchases, 12% avg savings). Paid SaaS Purchasing from $40,000/yr with contractually guaranteed savings; AI negotiation agent. | https://www.vendr.com/marketplace | changed - acquired by Vertice June 2026 | 2026-10-29 |
| Tropic / Spendflo | Mid-market and enterprise buyers | Buy-side SaaS and AI procurement with pricing benchmarks and negotiation services. Tropic claims 21% average savings; Spendflo offers a free savings analysis. No self-serve free tier; demo-gated. | https://www.tropicapp.io/ , https://www.spendflo.com/ | active | 2026-10-29 |

Changes vs 2024:
- AWS no longer gives new accounts 12 months of free t2/t3.micro; it is $100 + up to $100 credits, and the Free plan account closes after 6 months unless upgraded.
- Oracle quietly halved the famous Always Free Ampere A1 allowance in June 2026: 2 OCPU / 12 GB instead of 4 OCPU / 24 GB (free-only accounts over the limit get shut down).
- Hetzner repriced in 2026 (new orders from 15 June 2026: dedicated-vCPU CCX about 2.7x, CPX about 2.4x, CX/CAX about 1.3-1.4x) and entry plans were showing unavailable; OVHcloud VPS-1 at $4.54 with unlimited traffic is now the cheaper EU default.
- Domain traps got worse: .ai has a hard 2-year minimum and higher wholesale under Identity Digital; .io wholesale reportedly rises to $56 in January 2027.
- Vendr was acquired by Vertice (June 2026) but its free per-vendor median-price pages still work; AWS added Database Savings Plans (up to 35%, 1-year).
