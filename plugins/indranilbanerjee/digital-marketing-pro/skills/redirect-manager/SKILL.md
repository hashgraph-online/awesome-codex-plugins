---
name: redirect-manager
description: "Manage URL redirects. Use when: creating 301/302 redirects, auditing chains, fixing loops, or deploying via CMS MCP."
disable-model-invocation: false
argument-hint: "[URL or action]"
---

# /digital-marketing-pro:redirect-manager

## Purpose

Manage URL redirects across the website. Create new 301/302 redirects, audit existing redirects for chains and loops, fix broken redirect paths, and deploy changes via connected CMS MCP. Covers site migrations, URL restructuring, and ongoing redirect maintenance. Redirect mismanagement is one of the most common causes of SEO traffic loss — chains dilute link equity, loops create crawl errors, and broken redirects return 404s for previously indexed URLs. This command provides systematic redirect lifecycle management from creation through auditing and repair.

## Execution gate (MANDATORY — cannot be skipped)

1. Present the full preview — every redirect to be created/updated/removed with current-vs-proposed state and site-wide blast radius — as an **Execution Summary** before touching any live rule.
2. The user must type `yes` (or an equivalent explicit approval). ANY other input — ambiguous, implied, partial, or absent approval — cancels the run.
3. Never proceed on ambiguous input. Never auto-retry a failed execution; a failure needs human review before any re-run.
4. Record the approval with `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action create-approval --data '{"risk_level":"<tier>","summary":"..."}'` **before** executing, then `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action mark-executed --id {approval_id}` after the platform confirms success.

## Input Required

The user must provide (or will be prompted for):

- **Redirect action**: The operation to perform — `create` (set up new redirects), `audit` (scan all existing redirects for issues), `fix` (resolve chains, loops, and broken targets found during audit), or `bulk-import` (import a redirect map from CSV or Google Sheet for migrations). Multiple actions can be chained (e.g., audit then fix)
- **Source URL(s)**: For create and bulk-import — the URL(s) that should redirect. Can be exact URLs, URL patterns with wildcards (e.g., `/old-blog/*` to `/blog/*`), or regex patterns for complex matching. For audit and fix, source URLs are discovered automatically from the CMS
- **Target URL(s)**: For create and bulk-import — the destination URL(s) that users and search engines should be sent to. Must be live, accessible URLs returning 200 status codes. For bulk-import, provided as source-target pairs in the import file
- **Redirect type**: `301` (permanent — use for permanent URL changes, domain migrations, HTTPS upgrades, and URL restructuring) or `302` (temporary — use for A/B tests, seasonal content, maintenance pages, or geo-redirects). Default is 301 if not specified
- **CMS platform**: `wordpress` or `webflow` — must have the corresponding CMS MCP server connected. For WordPress, specify the redirect management method: Redirection plugin, RankMath redirects, Yoast Premium redirects, or `.htaccess` direct. For Webflow, the native redirect API is used

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **For create: validate source and target URLs**: Confirm the source URL exists or was previously indexed (check GSC for historical data), verify the target URL is live and returns a 200 status code, check for any existing redirect already set for the source URL to avoid duplicates, and check whether the proposed redirect would create a chain (source redirects to an intermediate URL that itself redirects elsewhere). For bulk-import, validate every source-target pair in the import file and flag any issues before proceeding.
3. **For audit: crawl all existing redirects**: Query the CMS API to retrieve every configured redirect rule. For each redirect, test the full redirect path by following it to its final destination. Detect chains (more than 1 hop — e.g., A redirects to B redirects to C), loops (A redirects to B redirects to A, or longer circular paths), redirects pointing to 4xx or 5xx error pages, redirect-to-redirect patterns that waste crawl budget, mixed protocol redirects (HTTP to HTTPS to HTTP), and redirects with excessive query parameter handling.
4. **For fix: resolve detected issues**: For chains — update the first redirect to point directly to the final destination URL, eliminating intermediate hops. For loops — break the cycle by identifying the correct final destination and updating or removing the looping rule. For broken targets — identify the correct live destination (check for URL changes, archived content, or replacement pages) and update the redirect, or flag for manual review if no clear target exists. For duplicates — remove redundant rules, keeping the most recently created or most specific match.
5. **Create approval gate**: Present all proposed redirect changes with current state and proposed state — new redirects to be created (source, target, type), chain fixes (current path vs. simplified path with hop reduction count), loop resolutions (broken cycle with new target), and broken target updates (old dead target vs. new live target). Assess risk: `medium` for individual redirect creation or small fixes (under 10 changes), `high` for bulk imports, migration-scale changes (over 10 redirects), or any deletion of existing redirect rules.
6. **Execute via CMS MCP**: On approval, deploy redirect changes through the connected CMS MCP. For WordPress: create or update rules via the Redirection plugin REST API (preferred for logging and monitoring), RankMath redirect module, Yoast Premium redirect manager, or direct `.htaccess` modification (last resort, with backup). For Webflow: use the native 301 redirect API with bulk support for migrations. Handle CMS-specific constraints — Webflow's 301-only limitation, WordPress plugin-specific rule formats, and pattern-matching syntax differences.
7. **Verify post-deployment**: Test every created or modified redirect by sending HTTP requests to the source URLs and confirming the response code (301 or 302) and final destination match the specification. For chain fixes, verify the redirect now resolves in a single hop. For loop fixes, verify the redirect reaches a 200 page. Report any verification failures for immediate investigation.
8. **Log all changes via seo-executor.py**: Record every redirect change with timestamp, action type (create, update, delete), source URL, target URL, redirect type, previous state (for updates and fixes), CMS platform and method used, verification result, and rollback instructions. Store the complete pre-change redirect state for bulk operations to enable full rollback if needed.

## Output

A structured redirect management report containing:

- **Redirect change confirmation**: Every redirect created, updated, or removed — showing source URL, target URL, redirect type (301/302), action taken (new, chain-fixed, loop-resolved, target-updated), and before/after state for modifications
- **Audit report**: Total redirects scanned, chains found (with hop count and full path), loops found (with cycle path), broken targets found (with HTTP status codes), duplicates found, and overall redirect health score as a percentage of clean single-hop redirects
- **Verification results**: HTTP response testing for every deployed redirect — confirmed source URL, response code received (301/302), final destination URL reached, hop count, and pass/fail status. Any failures are highlighted with diagnostic details
- **Execution log entry**: Timestamped record with full redirect change metadata, CMS API responses, pre-change state snapshot for rollback capability, approval reference, and verification results for audit trail

## Agents Used

- **seo-specialist** — Redirect analysis including chain detection, loop identification, and broken target diagnosis, URL validation against GSC historical data and live status checks, migration planning for bulk redirect operations, redirect type recommendations (301 vs. 302) based on use case, and link equity preservation strategy for redirect consolidation
- **execution-coordinator** — CMS MCP execution for WordPress (Redirection plugin API, RankMath redirects, Yoast Premium redirects, .htaccess management) and Webflow (native redirect API with bulk support), approval workflow with risk assessment scaled to redirect volume and change type, pre-change state capture for rollback capability, HTTP verification testing, and execution logging with full audit trail
