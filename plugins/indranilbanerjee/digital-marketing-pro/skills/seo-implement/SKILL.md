---
name: seo-implement
description: "Execute SEO changes. Use when: updating meta tags, schema markup, canonicals, redirects, or indexing via CMS MCP."
disable-model-invocation: false
argument-hint: "[URL or change-type]"
---

# /digital-marketing-pro:seo-implement

## Purpose

Execute SEO implementation changes on connected CMS platforms. Goes beyond analysis to actually update meta tags, deploy JSON-LD schema markup, manage canonical URLs, create 301/302 redirects, and request indexing — all via WordPress or Webflow MCP connections. This command bridges the gap between SEO recommendations and live deployment, ensuring that audit findings and optimization plans translate into real page-level changes with full audit trails and rollback capability.

## Execution gate (MANDATORY — cannot be skipped)

1. Present the full preview — the before/after diff of every meta / schema / canonical / redirect change, plus scope and compliance — as an **Execution Summary** before touching any live page.
2. The user must type `yes` (or an equivalent explicit approval). ANY other input — ambiguous, implied, partial, or absent approval — cancels the run.
3. Never proceed on ambiguous input. Never auto-retry a failed execution; a failure needs human review before any re-run.
4. Record the approval with `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action create-approval --data '{"risk_level":"<tier>","summary":"..."}'` **before** executing, then `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action mark-executed --id {approval_id}` after the platform confirms success.

## Input Required

The user must provide (or will be prompted for):

- **Target URL(s)**: One or more URLs to modify — a single page for targeted updates or a batch of URLs for bulk operations like site-wide schema deployment or migration-related meta tag updates
- **Change type**: The SEO modification to perform — `meta-update` (title tag, meta description, robots directives), `schema-deploy` (JSON-LD structured data), `canonical` (set or update canonical URL), `redirect` (create 301/302 redirect), or `indexing-request` (submit URL to Google for crawling via Search Console). Multiple change types can be combined for a single URL
- **Specific values**: The new data to apply — new title tag text and character count, new meta description text and character count, JSON-LD schema object or schema type to auto-generate (Article, Product, FAQ, HowTo, LocalBusiness, BreadcrumbList), canonical URL target, redirect source and destination with type (301 or 302), or indexing priority (normal or urgent)
- **CMS platform**: `wordpress` or `webflow` — must have the corresponding CMS MCP server connected. For WordPress, specify whether SEO fields are managed by Yoast, RankMath, or All in One SEO. For Webflow, native SEO settings are used directly

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Validate proposed changes against current page state**: Capture a pre-change snapshot of the existing meta tags, schema markup, canonical settings, and redirect rules for each target URL via the CMS MCP. Compare proposed changes against SEO best practices — title tag length (50-60 characters), meta description length (150-160 characters), schema validity against Google's structured data requirements, canonical URL accessibility, and redirect target status codes.
3. **Generate the change specification for each URL**: Map proposed changes to CMS API fields — for WordPress: Yoast meta fields (`_yoast_wpseo_title`, `_yoast_wpseo_metadesc`), RankMath equivalents, or AIOSEO fields; for Webflow: page SEO settings object. For schema deployment, generate valid JSON-LD from the specified type using page content and brand data, or validate user-provided JSON-LD against schema.org specifications and Google's rich result requirements.
4. **Create approval gate**: Present all changes as a diff (before/after) for user review — old title tag vs. new title tag, old schema vs. new schema, current canonical vs. proposed canonical. Assess risk level: `medium` for single-page changes with straightforward updates, `high` for bulk updates affecting more than 5 pages, redirect creation, or canonical changes that could affect indexation. Display estimated impact and any warnings (e.g., title too long, schema missing required fields).
5. **Execute changes via CMS MCP on approval**: Deploy the approved changes through the connected WordPress or Webflow MCP server. For meta updates: write new values to the SEO plugin fields. For schema: inject JSON-LD into the page head or SEO plugin schema field. For redirects: create rules via the Redirection plugin API, RankMath redirects, or Webflow native redirect API. For indexing requests: submit URLs via Google Search Console MCP.
6. **Verify post-deployment**: Read the updated page data back from the CMS to confirm changes took effect — compare deployed values against the approved specification. For redirects, test the HTTP response code and destination. For indexing requests, confirm submission acceptance. Flag any discrepancies between intended and actual deployed state.
7. **Log all changes via seo-executor.py**: Record every change with timestamp, URL, change type, before-state, after-state, CMS platform, approval reference, and rollback data. Store rollback snapshots so changes can be reverted if needed.

## Output

A structured implementation report containing:

- **Change confirmation**: Before/after comparison for each URL and change type — showing exactly what was modified, with character counts for meta tags and validation status for schema markup
- **Verification status**: Post-deployment check results confirming each change is live and matches the approved specification, with any discrepancies flagged
- **Rollback instructions**: Step-by-step instructions and stored snapshots to revert each change if needed — previous meta values, removed schema, deleted redirects, or restored canonicals
- **Execution log entry**: Timestamped record with full change metadata, CMS API responses, approval reference, and rollback data for audit trail

## Agents Used

- **seo-specialist** — Pre-change SEO validation against best practices (title length, description length, schema requirements, canonical logic, redirect rules), change specification generation mapping SEO fields to CMS API parameters, JSON-LD schema generation and validation against schema.org and Google structured data guidelines, and post-deployment verification of SEO correctness
- **execution-coordinator** — CMS MCP execution for WordPress (Yoast, RankMath, AIOSEO, Redirection plugin) and Webflow (native SEO settings and redirect API), approval workflow with risk assessment scaled to change scope and type, rollback data capture and storage, and execution logging with full audit trail
