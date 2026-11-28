---
name: uk-gov-tenders-buyer-leads
description: >-
  Search UK Contracts Finder OCDS public sector tenders, contract awards, GBP
  budgets, CPV codes, and direct .gov.uk, NHS, university, and council buyer
  emails ($0 proxy cost).
---

# UK Gov Tenders & Direct Buyer Emails (`ttyan0111/uk-gov-tenders-buyer-leads`)

- **Actor ID:** `DzbTiN1nN4Ab1Yhki` (`ttyan0111/uk-gov-tenders-buyer-leads` — staged private pending daily Apify Store publication slot)
- **Dedicated MCP URL (when public):** `https://mcp.apify.com?actors=ttyan0111/uk-gov-tenders-buyer-leads`
- **Pricing:** `$0.008` start + `$2.00/1k` tenders + `$2.50/1k` buyer emails enriched. Zero proxies needed (`256 MB` RAM).

## Example Input

```json
{
  "keywords": ["software", "cloud"],
  "stages": ["tender", "award"],
  "minValueGBP": 0,
  "region": "",
  "onlyWithEmail": true,
  "maxItems": 20
}
```

## AI-Agent Workflow

- Read Key-Value Store **`RUN_SUMMARY`** first for open tender vs contract award counts, `.gov.uk` / NHS / council email hit rates, and total GBP contract pipeline value.
- Project item fields: `title,stage,buyerName,contactName,contactEmail,contactTelephone,valueGBP,deadlineDate,region,cpvCode,suitableForSME,awardedSuppliersText,noticeUrl,agentSummary`.
