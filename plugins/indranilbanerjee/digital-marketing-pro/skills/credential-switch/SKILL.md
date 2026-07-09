---
name: credential-switch
description: "Switch brand credentials. Use when: activating the correct API keys for MCP servers in multi-client workflows."
disable-model-invocation: false
argument-hint: "[brand-slug]"
---

# /digital-marketing-pro:credential-switch

## Purpose

Switch the active credential profile to a different brand for multi-client agency management. Validates all platform connections and reports which services are available for the target brand. Ensures the correct API keys, tokens, and environment variables are active before executing any platform operations — preventing cross-client data leakage, misrouted ad spend, or accidental operations on the wrong account.

## Execution gate (MANDATORY — cannot be skipped)

1. Present the validation summary — target brand, per-platform credential status, and any warnings — as an **Execution Summary**.
2. If validation is clean **and only one** client credential profile is configured, the switch may proceed automatically. If **more than one** client profile exists, or any warning / missing / expiring credential is present, the user must type `yes` (or an equivalent explicit approval) — ANY other input cancels.
3. Never proceed on ambiguous input. Never auto-retry a failed switch.
4. When confirmation is required, record it with `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action create-approval --data '{"risk_level":"medium","summary":"credential switch to {slug}"}'` **before** switching, then `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action mark-executed --id {approval_id}` after the switch verifies.

## Input Required

The user must provide (or will be prompted for):

- **Target brand slug**: The brand slug to switch credentials to — must match a configured brand in `~/.claude-marketing/brands/` with a corresponding credential profile in `~/.claude-marketing/credentials/`
- **Validation depth (optional)**: One of:
  - Quick: Check that env vars exist and are non-empty — fast, no API calls
  - Full: Test live API connectivity and token validity for each configured platform — slower but confirms actual access
  - Defaults to quick for faster switching
- **Force switch (optional)**: If the target profile has missing or expired credentials, whether to switch anyway with warnings or abort entirely — defaults to abort on missing critical credentials (ad platforms, analytics)
- **Reason (optional)**: Brief note for the switch log — helps with audit trail when multiple team members share the system (e.g., "Starting monthly reporting for Acme Corp")
- **Platforms to validate (optional)**: Specific platforms to validate instead of all — useful when you only need certain integrations for the current task (e.g., "google-ads, google-analytics" for a paid media session)

## Process

1. **Check current context**: Read `~/.claude-marketing/brands/_active-brand.json` to identify the currently active brand, and `~/.claude-marketing/credentials/_active-profile.json` for the current credential profile. Display current state before switching.
2. **Verify target brand exists**: Confirm the target brand slug has a configured profile at `~/.claude-marketing/brands/{slug}/profile.json`. If not found, list all available brands from `~/.claude-marketing/brands/` and suggest `/digital-marketing-pro:brand-setup` for new brands or `/digital-marketing-pro:client-onboarding` for new client setup
3. **Check credential profile exists**: Run `credential-manager.py --action get-profile --id {slug}` to verify a credential profile exists for the target brand. If missing, explain how to create one with the required platform credentials and abort with setup instructions
4. **Validate credential profile**: Run `credential-manager.py --action validate-profile --id {slug}` to check each platform's credentials — verify API keys are present and non-empty, OAuth tokens are not expired, and required environment variables are set for all MCP servers configured in `.mcp.json`
5. **Present validation summary**: Display a platform-by-platform validation report — for each configured service:
   - Platform name and type (ad platform, analytics, CRM, social, email)
   - Credential status: configured / not configured / expired
   - Required env vars: set or missing (with specific variable names)
   - Token expiry date if applicable
   - Last successful connection timestamp if available
6. **Check for recent operations**: Before switching, scan `python "${CLAUDE_PLUGIN_ROOT}/scripts/execution-tracker.py" --brand {slug} --action get-history --limit 20` for recently logged executions and deliveries under the current profile that a context switch could affect. The tracker records completed runs (success/failure) — there is no live "in-progress" feed, so treat the most recent entries as potentially still settling and warn with specific operation details if any look active
7. **Confirm switch intent**: If validation passed cleanly, proceed automatically. If warnings exist (missing non-critical credentials, expiring tokens within 7 days), present the warnings and ask for confirmation. If critical credentials are missing and force is not set, abort with specific guidance on what needs to be configured
8. **Execute credential switch**: Run `credential-manager.py --action switch-profile --id {slug}` to activate the target brand's credential profile. This updates the active profile reference and loads the corresponding environment variables for all MCP servers
9. **Switch active brand**: Update `~/.claude-marketing/brands/_active-brand.json` to set the target brand as the active brand context — ensuring brand profile and credentials are aligned so all subsequent commands use the correct client
10. **Verify switch success**: Re-read both `_active-brand.json` and `_active-profile.json` to confirm the switch completed successfully. If full validation was requested, run a quick connectivity test on critical platforms (Google Ads, Analytics, CRM) to confirm live access works
11. **Log the switch**: Record the switch event with timestamp, previous brand, new brand, validation result, any warnings, and reason (if provided) in `~/.claude-marketing/credentials/switch-log.json` for audit trail purposes
12. **Report new active context**: Display the new active brand name, slug, industry, business model, configured platforms with their validation status, and any warnings for missing or expiring credentials. Suggest relevant next steps based on common post-switch workflows

## Output

A credential switch confirmation containing:

- **Previous context**: Brand name, slug, and credential profile that was active before the switch — so the user can verify what they switched away from and return if needed
- **New active context**: Brand name, slug, industry, business model, primary marketing channels, engagement type, and contract status now active
- **Platform validation report**: Per-platform status table — platform name, configured (yes/no), env vars (set/missing with specific var names listed), token status (valid/expired/N/A with expiry date if applicable), and connectivity result (verified/not tested/failed with error detail)
- **Missing credential warnings**: Any platforms configured in the brand profile but missing API keys or tokens, with specific instructions for adding them — which env var to set, where to obtain the credential, and whether the platform is critical or optional for current workflows
- **Expiring credential alerts**: Any tokens or keys approaching expiration within 7 days, with renewal instructions, urgency level (informational/action-needed/critical), and impact if not renewed
- **Active operations check**: Confirmation that no in-progress operations were disrupted, or detailed warnings listing any operations that may need attention after the switch
- **Switch log entry**: Timestamp, previous brand, new brand, validation summary, warnings count, and reason — recorded for audit and troubleshooting purposes
- **Next steps**: Confirmation message — "All operations will now use [brand_name]'s credentials. Configured platforms: [list]. Use `/digital-marketing-pro:agency-dashboard` to see this client's status, `/digital-marketing-pro:client-report` to generate a performance report, or `/digital-marketing-pro:credential-switch` again to return to the previous brand."

## Agents Used

- **agency-operations** — Credential profile management, platform validation logic, active operations safety check, switch execution, context alignment verification, audit logging, and post-switch recommendation engine
