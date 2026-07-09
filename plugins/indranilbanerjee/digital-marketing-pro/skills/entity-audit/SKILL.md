---
name: entity-audit
description: "Audit brand entity consistency. Use when: checking Wikidata, Knowledge Panel, or directory discrepancies."
---

# /digital-marketing-pro:entity-audit

## Purpose

Audit brand entity data consistency across the platforms that AI engines use as knowledge sources. Check Wikidata entries, Google Knowledge Panel accuracy, Wikipedia presence and notability, and industry directory listings for consistency. Inconsistent entity data degrades AI engine trust and visibility — when knowledge sources disagree about basic facts like the official website, founding date, headquarters location, or industry classification, AI engines either omit the brand entirely or present conflicting information. This command provides a systematic, platform-by-platform audit with specific discrepancies flagged and a prioritized fix plan ordered by impact on AI visibility.

## Input Required

The user must provide (or will be prompted for):

- **Brand/entity name**: The exact name of the brand, organization, person, or product to audit — must match the entity as it should appear in knowledge sources. If the brand has known aliases or former names, include those for cross-referencing
- **Entity type**: `Organization`, `Person`, `Product`, or `Brand` — determines which properties are checked and which directory types are relevant. Organizations check founding date, headquarters, industry; Products check manufacturer, launch date, category; Persons check role, affiliation, notable works
- **Key properties to verify**: Official website URL, founding date, headquarters location, social media profiles (LinkedIn, Twitter/X, Facebook, Instagram), industry classification, key people (CEO, founders), parent organization, number of employees, and any entity-specific properties the user considers critical. Properties from the brand profile are used as the source of truth
- **Directories to check (optional)**: Industry-specific directories (e.g., G2, Capterra, Clutch for SaaS; Yelp, TripAdvisor for hospitality), professional associations, and business registries relevant to the brand's industry. If not provided, the command will suggest directories based on the brand's industry classification from the profile

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Extract the authoritative values for all entity properties — official name, website, founding date, headquarters, social profiles, industry, key people, and description. These become the source of truth against which all platforms are compared. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with user-provided values.
2. **Check Wikidata**: Search for the entity on Wikidata by name and aliases. If found, verify each property — official website (P856), social media profiles (P2002, P2003, P2013, P4264), founding date (P571), headquarters (P159), industry (P452), key people (P169, P112), instance of (P31), and description. Record each property as matching, mismatched (with both values), outdated, or missing. If no Wikidata entry exists, record as absent and assess whether the entity meets notability criteria for creation.
3. **Check Google Knowledge Panel**: Verify Knowledge Panel existence for the brand name query. If present, check whether the panel is claimed or unclaimed, whether displayed information (website, address, social links, description, category) matches the brand profile, and whether images and logos are current. Record each element as accurate, inaccurate (with discrepancy details), outdated, or missing. Note the panel source attribution.
4. **Assess Wikipedia presence**: Search for the entity on Wikipedia. If an article exists, verify accuracy of key facts — founding date, headquarters, description, key people, products/services, and any claims that could be outdated or incorrect. Check for citation quality and recency. If no article exists, assess notability criteria — significant coverage in reliable independent sources, demonstrated importance in the field, and verifiable claims. Record as present-and-accurate, present-with-issues (list issues), or absent with notability assessment (likely notable, borderline, or unlikely notable).
5. **Check industry directories**: For each relevant directory, verify the listing exists and check data consistency — business name spelling, address, phone number, website URL, business description, category classification, and any directory-specific fields. Record each listing as consistent, inconsistent (with specific discrepancies), incomplete (missing fields), or absent. Flag NAP (Name, Address, Phone) inconsistencies specifically, as these have outsized impact on entity resolution by AI engines.
6. **Record findings**: Store each entity finding via geo-tracker's `entity-check` action (`--platform` takes an entity platform: `wikidata`, `google-kp`, `wikipedia`, or `directory`; `--status` takes `present`, `absent`, `inconsistent`, or `outdated`):
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/geo-tracker.py" \
       --brand {slug} --action entity-check \
       --platform wikidata \
       --entity-name "Acme Corp" \
       --status inconsistent \
       --details "Founding date P571 shows 2015; brand profile says 2014"
   ```
   Run once per platform × property finding, recording expected vs. actual value and severity in `--details`.
7. **Generate inconsistency report**: Compile all discrepancies across platforms into a single report — grouped by property (see all platforms that disagree about the founding date, for example) and by platform (see all issues on Wikidata, for example). Calculate an overall entity consistency score based on the proportion of properties that match across all platforms.
8. **Create prioritized action plan**: Rank fixes by impact on AI visibility — Wikidata property corrections first (direct knowledge graph impact), Knowledge Panel claims and corrections second (Google AI Overview impact), Wikipedia accuracy fixes third (broad citation impact), and directory consistency fixes fourth (reinforcing entity signals). Include specific instructions for each fix: what to change, where to change it, and any process requirements (Wikipedia's reliable source requirements, Knowledge Panel claim verification, Wikidata citation needs).

## Output

A comprehensive entity consistency audit containing:

- **Entity consistency scorecard**: Per-platform status — present/absent, consistent/inconsistent/outdated — with an overall consistency percentage and letter grade
- **Specific discrepancies list**: Every property mismatch across every platform, showing expected value (from brand profile), actual value found, and severity (critical for NAP/website mismatches, high for founding date/industry errors, medium for missing social profiles, low for minor description differences)
- **Wikidata action items**: Properties to create, update, or correct on Wikidata, with required citation sources and step-by-step editing guidance
- **Knowledge Panel action items**: Claim status and process, information corrections to submit, image/logo updates needed, and category adjustments
- **Wikipedia notability assessment**: If no article exists — assessment of notability criteria with specific reliable sources identified, recommendation on whether to pursue article creation, and draft outline if notable. If article exists — accuracy issues to address with talk page discussion guidance
- **Directory listing audit**: Per-directory status with specific fields to update, missing listings to create, and NAP consistency issues to resolve
- **Prioritized fix plan**: All action items ranked by AI visibility impact, with effort estimate (quick fix, moderate effort, significant project) and expected impact on entity consistency score
- **Execution log entry**: Timestamped record with platform count, consistency score, critical discrepancy count, and key flags for audit trail

## Agents Used

- **seo-specialist** — Entity analysis across Wikidata, Knowledge Panel, Wikipedia, and directories, knowledge graph optimization strategy, Wikidata property verification and edit guidance, Wikipedia notability assessment with reliable source identification, NAP consistency analysis, entity resolution impact assessment, and prioritized fix recommendations ranked by AI visibility impact
- **execution-coordinator** — Directory update coordination across multiple platforms, Google Knowledge Panel claim process guidance, structured action plan creation with effort estimates and sequencing, and execution tracking for multi-step entity fix workflows
