---
name: clinical-trials-biotech-leads
description: >-
  Extract recruiting Industry Biotech, Pharma, and MedTech clinical trials from
  ClinicalTrials.gov API v2 with direct corporate sponsor emails, Principal
  Investigators (PIs), and deduplicated site contacts ($0 proxy cost).
---

# ClinicalTrials.gov Biotech & PI Email Leads (`ttyan0111/clinical-trials-biotech-leads`)

- **Actor ID:** `eFcbJHonnspdvgqIy` (`ttyan0111/clinical-trials-biotech-leads` — staged private pending daily Apify Store publication slot)
- **Dedicated MCP URL (when public):** `https://mcp.apify.com?actors=ttyan0111/clinical-trials-biotech-leads`
- **Pricing:** `$0.006` start + `$2.50/1k` trial leads + `$1.50/1k` site contacts enriched. Zero proxies needed (`256 MB` RAM).

## Example Input

```json
{
  "queries": ["oncology", "immunotherapy"],
  "location": "United States",
  "statuses": ["RECRUITING", "NOT_YET_RECRUITING"],
  "sponsorClass": "INDUSTRY",
  "phases": ["PHASE1", "PHASE2", "PHASE3"],
  "onlyWithEmail": true,
  "includeSiteContacts": true,
  "maxSiteContactsPerTrial": 10,
  "maxTrials": 20
}
```

## AI-Agent Workflow

- Read Key-Value Store **`RUN_SUMMARY`** first (`totalTrialsScraped`, `trialsWithCentralEmailCount`, `totalUniqueEmailsFound`, `byPhase`, `topBiotechLeads`)—compressing megabytes of raw ClinicalTrials.gov JSON by `~96%`.
- Project item fields: `nctId,briefTitle,leadSponsorName,leadSponsorClass,phasesText,overallStatus,enrollmentCount,primaryEmail,primaryContactName,primaryPhone,corporateSponsorDomain,leadPiSummary,siteContactsCount,studyUrl,agentSummary`.
