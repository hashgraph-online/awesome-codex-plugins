---
name: region-config
description: "Configure regional settings. Use when: setting timezone, language, compliance rules, currency, or local preferences."
---

# /digital-marketing-pro:region-config

## Purpose

Configure regional and market-specific settings for a brand. Sets the timezone for scheduled content delivery, primary language for content generation, applicable compliance and privacy regulations, preferred local platforms, currency for budget and performance reporting, and business hours for communication scheduling. These settings propagate to all downstream commands so that campaigns, content, and reporting automatically respect regional requirements without manual adjustment each time.

This is a setup/configuration command. It writes persistent configuration files that other commands consume. Once a region is configured, commands like `/digital-marketing-pro:content-calendar`, `/digital-marketing-pro:email-sequence`, `/digital-marketing-pro:paid-advertising`, and `/digital-marketing-pro:performance-report` automatically inherit the region's timezone, language, compliance rules, and platform preferences.

Supports both single-market configurations (e.g., "Japan") and broad regional groupings (e.g., "APAC") depending on how granular the brand's market segmentation needs to be.

## Input Required

The user must provide (or will be prompted for):

- **Region name**: The market being configured — broad region (North America, Europe, APAC, LATAM, MENA) or specific market (Japan, Germany, Brazil, United Kingdom, Australia). Determines which compliance rules, platforms, and defaults apply
- **Timezone**: IANA timezone identifier — e.g., `America/New_York`, `Europe/London`, `Asia/Tokyo`. Used for content scheduling, reporting windows, and business hours calculations
- **Primary language**: The main language for content generation and audience communication in this region — e.g., English (US), English (UK), Japanese, German, Portuguese (BR)
- **Secondary languages** (optional): Additional languages used in the market for multilingual campaigns — e.g., French and German for Switzerland, English and Mandarin for Singapore
- **Currency**: ISO 4217 currency code for budget and performance reporting — e.g., USD, EUR, GBP, JPY, BRL. All financial metrics for this region render in this currency
- **Local platforms** (optional): Region-specific platforms to prioritize — e.g., LINE and Yahoo Japan for Japan, Kakao for South Korea, VK for Russia, WeChat for China, Mercado Libre for LATAM. Overrides global platform defaults for this market
- **Business hours** (optional): Operating hours for the region in local time — e.g., "09:00-18:00 Mon-Fri". Used to constrain SMS sends, chat responses, and notification timing. Defaults to standard business hours for the timezone if not specified
- **Holiday calendar** (optional): Region-specific public holidays and observances that affect scheduling — e.g., Golden Week (Japan), Diwali (India), Carnival (Brazil). If omitted, common holidays for the region are applied automatically
- **Data residency requirements** (optional): Whether data must remain within specific geographic boundaries — relevant for EU, China, Russia, and other jurisdictions with data localization laws
- **Industry-specific regulations** (optional): Sector-level compliance beyond general privacy laws — e.g., HIPAA for US healthcare, FCA for UK financial services, TGA for Australian therapeutic goods. Adds industry constraints on top of regional compliance rules
- **Set as default** (optional): Whether this region should become the brand's default region — used when no region is explicitly specified in other commands. Only one region can be the default at a time

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Check existing regional configs**: Look for existing region configuration files at `~/.claude-marketing/brands/{slug}/regions/`. If the specified region already exists, load it and show current settings — then ask whether to update or replace. If this is a new region, proceed with creation. List all currently configured regions for context.
3. **Apply compliance rules for the region**: Consult `skills/context-engine/compliance-rules.md` and map applicable regulations — GDPR for EU/EEA/UK markets, CCPA/CPRA for California, PDPA for Singapore and Southeast Asia, LGPD for Brazil, PIPA for South Korea, APPI for Japan, PIPEDA for Canada, and DPDPA (Digital Personal Data Protection Act) for India. For any EU/EEA market, also flag **EU AI Act Article 50** AI-content transparency obligations (applicable 2 August 2026): AI-generated marketing assets must carry machine-readable provenance (see `skills/c2pa-metadata/SKILL.md`) and, for deepfakes or public-interest text, a visible disclosure. Record all applicable regulations with their key requirements (consent mechanisms, data retention limits, opt-out requirements, age restrictions, cookie consent banners, AI-content disclosure). Layer any industry-specific regulations on top.
4. **Set platform preferences**: Consult `skills/context-engine/team-roles-framework.md` for regional platform recommendations. Merge user-provided local platforms with defaults for the region. Set platform priority order — which platforms receive content first, which are secondary, and which are excluded in this market. Note any platform-specific API or account requirements for the region (e.g., separate WeChat Official Account for China, LINE Business Account for Japan).
5. **Configure timezone-aware scheduling rules**: Set content publishing to occur in the region's local timezone. Define quiet hours for SMS and push notifications (typically 21:00-08:00 local time). Set email send windows optimized for the region's typical engagement patterns. Map DST transition dates and adjust scheduling logic to prevent missed or double-sent content during clock changes. Define weekend days for the region (Friday-Saturday for MENA markets, Saturday-Sunday for most others).
6. **Set language and localization preferences**: Record primary language with locale variant (en-US vs. en-GB vs. en-AU), secondary languages with priority order, translation review requirements, and any terminology or spelling preferences specific to the market (e.g., "colour" for UK, "optimization" vs. "optimisation"). Set date format (MM/DD/YYYY vs. DD/MM/YYYY), measurement units (imperial vs. metric), and address format conventions.
7. **Configure currency and financial reporting**: Set the region's reporting currency with exchange rate source and update frequency. Define budget thresholds in local currency. Set number formatting conventions (decimal separator, thousands separator, currency symbol placement — prefix vs. suffix). If the brand operates in multiple currencies, define the base currency for cross-region comparison.
8. **Apply holiday calendar and observances**: Load region-specific public holidays — either from user input or from default holiday sets for the region. Mark these dates as scheduling blackout or reduced-activity periods. Flag cultural observances that may affect content tone or campaign timing (e.g., Ramadan, Lunar New Year, national mourning periods). Set recurring annual reminders to review and update the calendar.
9. **Set data residency and storage rules**: If data residency requirements were specified, record which data types must remain in-region (PII, analytics, email lists, CRM records), which cloud regions or data centers are approved, and any cross-border transfer mechanisms needed (Standard Contractual Clauses for EU, adequacy decisions). Flag any connected MCPs or tools that may not comply with the residency requirement.
10. **Save region configuration**: Write the complete region config to `~/.claude-marketing/brands/{slug}/regions/{region-slug}.json` containing all settings — timezone, languages, compliance rules, industry regulations, platforms, currency, business hours, scheduling rules, holiday calendar, data residency flags, and metadata (created date, last modified, created by).
11. **Update brand profile**: Add the new region to the brand profile's active regions list at `~/.claude-marketing/brands/{slug}/profile.json`. If this is the first region configured, set it as the default region. Update the brand's compliance summary to include the new region's regulations.
12. **Generate compliance checklist**: Produce a practical compliance checklist for the marketing team operating in this region — required disclaimers, consent collection points, data handling procedures, content restrictions, and advertising disclosure requirements. This checklist is saved alongside the region config for quick reference during campaign creation.
13. **Validate and confirm**: Display the complete region configuration for user review. Highlight any compliance requirements that will affect existing campaigns or content. Flag any potential conflicts with other configured regions (overlapping timezones, conflicting platform priorities, currency conversion needs). Summarize what downstream commands will now inherit from this configuration.

## Output

A structured region configuration summary containing:

- **Region overview**: Region name, slug, timezone, UTC offset, and status (new or updated) with creation or modification timestamp
- **Language settings**: Primary language with locale, secondary languages in priority order, and localization preferences — spelling conventions, terminology, date format, measurement units, and address format
- **Compliance rules applied**: List of all applicable regulations (regional and industry-specific) with key requirements — consent mechanisms needed, data retention limits, opt-out/unsubscribe requirements, age verification needs, cookie consent type, and advertising disclosure rules
- **Data residency summary**: If applicable, documented data storage constraints — approved cloud regions, cross-border transfer mechanisms, affected data types, and any MCP compliance flags
- **Platform preferences**: Ordered list of platforms for this region — primary, secondary, and excluded — with rationale for region-specific platforms, API or account requirements, and any content format differences from global defaults
- **Currency and financial settings**: Reporting currency, symbol placement, exchange rate source, base currency for cross-region comparison, number formatting conventions, and budget threshold displays in local currency
- **Business hours and scheduling rules**: Operating hours in local time, weekend days, quiet hours for messaging channels, optimal send windows for email by day of week, and scheduling blackout periods around holidays
- **Holiday calendar**: List of public holidays and cultural observances for the region with dates, scheduling impact (blackout vs. reduced activity), and content tone considerations
- **Timezone configuration**: IANA timezone, UTC offset, DST transition dates with scheduling adjustment logic, and impact on cross-region coordination if multiple regions are configured
- **Cross-region considerations**: If other regions are already configured, a summary of how this region interacts — overlapping business hours for team coordination, currency conversion requirements, content localization dependencies, and shared compliance obligations
- **Downstream impact summary**: Which existing commands and workflows will now inherit these regional settings — content scheduling, budget reporting, compliance checks, platform targeting, and language defaults
- **Active regions list**: Updated list of all configured regions for this brand showing region name, timezone, primary language, currency, and compliance framework — confirming where this new region fits in the overall market footprint
- **Compliance checklist**: Practical checklist for the marketing team — required disclaimers, consent points, data handling rules, content restrictions, and advertising disclosures specific to this region and industry
- **Configuration file path**: The saved config location for reference and manual editing if needed
- **Next steps**: Recommended follow-up actions — configure additional regions, run `/digital-marketing-pro:content-calendar` with the new region settings, or update existing campaigns to comply with newly configured rules
- **Audit trail**: Record of who created or modified the region config, when, and what changed — useful for multi-team environments where configuration changes need accountability

## Agents Used

- **agency-operations** — Regional configuration management, compliance rule mapping, platform preference alignment, timezone scheduling logic, holiday calendar application, data residency assessment, and cross-region coordination
