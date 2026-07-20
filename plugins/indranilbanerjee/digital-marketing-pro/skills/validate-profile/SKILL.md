---
name: validate-profile
description: "Validate a brand profile end-to-end — required fields, voice/audience completeness, connector reachability, credentials health, and compliance prerequisites — without exposing credential values. Run after any credential change or brand-profile edit."
user-invocable: true
triggers:
  - validate brand profile
  - check brand profile health
  - is the brand setup correct
  - check connector credentials
  - profile sanity check
  - validate profile
allowed-tools: Read Bash Glob Grep
---

# /digital-marketing-pro:validate-profile — Brand Profile + Credential Health Check

This skill is the canonical "is this brand ready to ship work?" gate. It validates a brand profile is complete enough for production use AND that every credential/connector referenced by the profile is actually reachable — **without ever printing credential values**.

Use this skill:

- After **`/digital-marketing-pro:brand-setup`** (or `/digital-marketing-pro:client-onboarding`) to confirm the new profile is production-ready.
- After **rotating any API key** (Slack, HubSpot, Stripe, Ahrefs, GA4 service account, etc.) so connectivity is re-confirmed without exposing the new value in logs.
- After **importing brand guidelines** (`/digital-marketing-pro:import-guidelines`) to confirm the merge succeeded.
- As the **prerequisite check** before `/digital-marketing-pro:engagement`, `/digital-marketing-pro:campaign-plan`, or `/digital-marketing-pro:launch-campaign`.

## Why this skill exists

For agencies running 50–200 client brands, brand profiles and credentials drift constantly: a junior changes a Slack channel, an API key rotates, a brand voice gets edited. The cost of running a 60-minute engagement on a broken profile is hours of rework. This skill catches those drift cases in under 60 seconds.

The skill is **read-only** — it inspects state, never modifies it. It also **never prints credential values** — connector checks emit pass / fail / error-class without echoing the secret.

## Validation dimensions

| Dimension | What's checked | Severity |
|---|---|---|
| **Required identity** | `brand_name`, `industry`, `target_jurisdictions` non-empty | BLOCKER |
| **Voice profile** | `voice.tone`, `voice.formality`, `voice.energy` populated | BLOCKER for content work |
| **Audience profile** | `target_audience.primary_persona` with `role` + `reading_level` | WARNING |
| **Guardrails** | `guardrails.prohibited_terms` + `guardrails.prohibited_claims` non-empty | BLOCKER for regulated industries (pharma, BFSI, healthcare, legal) |
| **Compliance jurisdictions** | Each declared jurisdiction has a matching rules entry in `skills/context-engine/compliance-rules.md` | BLOCKER |
| **Connector config present** | Every connector named in `tracking.backend`, `integrations.*`, `analytics.*` has its env vars / `.mcp.json` entry present (local check; live reachability comes from the MCP/curl probe below) | BLOCKER per unconfigured connector |
| **MCP server health** | Every entry in `.mcp.json` (if present) responds to a tools/list ping | WARNING |
| **Credential storage** | `~/.claude-marketing/{brand}/credentials.json` (or env vars) present for every backend referenced | BLOCKER |
| **Output paths writeable** | `~/.claude-marketing/{brand}/` is writeable; the user-visible publish dir (`$DIGITAL_MARKETING_PRO_PUBLISH_DIR` or `~/Documents/DigitalMarketingPro/`) is writeable | BLOCKER |
| **Model curator currency** | `scripts/resolve_model.py --registry-age` returns < 90 days | WARNING |

A **BLOCKER** means "do not let the user run engagement / campaign-plan / launch-campaign until this is fixed." A **WARNING** is surfaced but does not gate.

## Process

### Step 0 — Resolve the brand to validate

If `--brand <slug>` was passed, use it. Otherwise read the active brand from `~/.claude-marketing/active-brand` (set by `/digital-marketing-pro:switch-brand`). If neither is available, error: `"--brand <slug> required, or run /digital-marketing-pro:switch-brand first."` Do NOT validate "everything" — validation is per-brand by design.

### Step 1 — Load the brand profile

```bash
BRAND_DIR="$HOME/.claude-marketing/{brand}"
test -d "$BRAND_DIR" || { echo "Brand directory not found at $BRAND_DIR — run /digital-marketing-pro:brand-setup first."; exit 1; }
PROFILE="$BRAND_DIR/brand-profile.json"
test -f "$PROFILE" || { echo "brand-profile.json missing under $BRAND_DIR — run /digital-marketing-pro:brand-setup."; exit 1; }
```

Parse the profile JSON and capture: `brand_name`, `industry`, `target_jurisdictions`, `voice.*`, `target_audience.*`, `guardrails.*`, `tracking.backend`, `integrations.*`, `analytics.*`.

### Step 2 — Required-field checks

Walk the checklist in the **Validation dimensions** table above. For each field, record one of: `OK` / `WARN: <reason>` / `BLOCK: <reason>`. Do NOT short-circuit — collect every issue so the user sees the full picture in one pass.

For regulated industries (`industry` matches any of `pharma`, `pharmaceuticals`, `bfsi`, `banking`, `insurance`, `healthcare`, `legal`, `medical-devices`), upgrade guardrails issues from WARNING to BLOCKER.

### Step 3 — Compliance-jurisdiction cross-check

For every entry in `target_jurisdictions`, confirm `skills/context-engine/compliance-rules.md` contains a matching section header (e.g. `### 1.11 India — DPDPA`). If a jurisdiction is declared but not covered, BLOCK with: `"Jurisdiction {X} declared in profile but no compliance rules for it — engagement will produce non-compliant deliverables."`

### Step 4 — Connector reachability (credential-safe)

For each backend referenced in `tracking.backend`, `integrations.crm`, `integrations.email`, `integrations.cms`, `integrations.analytics`, `integrations.social`, run the matching health probe via `scripts/connector-status.py`:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/connector-status.py" \
    --action status \
    --brand "{brand}" \
    --connectors "{comma-separated list inferred from profile}" \
    --probe-only --no-secrets
```

`connector-status.py --probe-only` runs a **local** readiness check: it verifies that the required environment variables / `.mcp.json` entry for each connector are present and non-empty. It does NOT open a live network connection or make a `whoami` call — so it reports a **config-level** class (CONFIGURED / MISSING_ENV / NOT_IN_MCP), not a live HTTP status. `--no-secrets` guarantees it never echoes, logs, or writes a credential value. For an actual liveness check, use the connector's MCP `tools/list` endpoint or the HTTP curl probe below.

For MCP servers in `.mcp.json` (if present at the brand or project level), run a `tools/list` ping against each via `mcp__connector__*` if the connector is loaded, or invoke a 5-second curl HEAD against the configured `url` for HTTP MCPs:

```bash
for url in $(jq -r '.mcpServers[] | select(.type=="http") | .url' .mcp.json); do
    code=$(curl -sS -o /dev/null -w "%{http_code}" -m 5 "$url" || echo "000")
    echo "$url -> HTTP $code"
done
```

HTTP `200`, `204`, `401` (auth required for GET — POST will work), and `405` (method not allowed for GET — POST will work) all count as "reachable". `404`, `000` (DNS / timeout), `5xx` count as BLOCK.

### Step 5 — Output-path writeability

```bash
test -w "$HOME/.claude-marketing/{brand}/" || echo "BLOCK: brand directory is not writeable"
# User-visible publish dir (dual-copy pattern)
if [ -n "$DIGITAL_MARKETING_PRO_PUBLISH_DIR" ]; then
    test -w "$DIGITAL_MARKETING_PRO_PUBLISH_DIR" || echo "WARN: DIGITAL_MARKETING_PRO_PUBLISH_DIR ($DIGITAL_MARKETING_PRO_PUBLISH_DIR) is not writeable"
elif [ -d "$HOME/Documents" ]; then
    test -w "$HOME/Documents" || echo "WARN: ~/Documents is not writeable — the user-visible publish copy will fail"
fi
```

### Step 6 — Model-curator currency

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/resolve_model.py" --registry-age
```

If the registry is more than **90 days** old, WARN: `"model_registry.json is {N} days old — frontier models change every ~6 weeks. Run scripts/refresh_models.py to check drift."` (Do not block — the curator auto-falls-forward on deprecated ids, so an older registry is degraded, not broken.)

### Step 7 — Report

Print a structured report. ALWAYS show every check (don't only print failures — agencies need positive confirmation for the rest):

```
🔎 Brand profile validation — {brand_name}
   Slug: {brand} · Industry: {industry} · Jurisdictions: {list}

✅ Required identity      brand_name, industry, target_jurisdictions all set
✅ Voice profile          tone={tone} · formality={formality} · energy={energy}
⚠️  Audience profile       primary_persona.role set, reading_level MISSING
✅ Guardrails             {N} prohibited_terms, {M} prohibited_claims (industry={industry})
✅ Compliance jurisdictions  EU-GDPR ✓ · IN-DPDPA ✓ · US-CCPA ✓
🛑 Connector — Slack       MISSING_ENV (SLACK_* env not set — add via /digital-marketing-pro:add-integration slack)
✅ Connector — HubSpot     OK (workspace acme-corp, 1247 contacts)
✅ Connector — Stripe      OK
✅ MCP — gmailmcp.googleapis.com  HTTP 405 (alive)
✅ Output paths            ~/.claude-marketing/{brand}/ writeable; ~/Documents/DigitalMarketingPro/ writeable
⚠️  Model curator           registry is 102 days old — consider scripts/refresh_models.py

Decision: 🛑 BLOCKED — Slack connector not configured. Fix before running:
  • /digital-marketing-pro:engagement
  • /digital-marketing-pro:campaign-plan
  • /digital-marketing-pro:launch-campaign

Re-run /digital-marketing-pro:validate-profile after fixing.
```

Also emit a machine-readable JSON summary so it can be consumed by `/digital-marketing-pro:check`, `/digital-marketing-pro:status`, or downstream automation:

```json
{
  "brand": "{slug}",
  "decision": "blocked | passed | passed_with_warnings",
  "blockers": [{"check": "connector_slack", "reason": "..."}],
  "warnings": [{"check": "audience_persona", "reason": "reading_level missing"}],
  "passed": ["required_identity", "voice_profile", ...]
}
```

## Behaviour rules

1. **Never print credential values.** Connector probes use `--no-secrets`; if a probe accidentally returns a credential in its error string, redact before printing. The skill output goes to logs and clipboards — assume it leaks.
2. **Read-only.** Never modify the brand profile, credentials, MCP config, or any persistent state. This is a checker, not a fixer. Hand back actionable next commands instead.
3. **Don't short-circuit.** Run every check even after the first BLOCKER — agencies want the full punch list in one pass.
4. **Don't validate cross-brand.** Per-brand only, by design. Looping across all brands is a separate workflow (`/digital-marketing-pro:agency-dashboard --health`).
5. **Idempotent.** Running this skill twice in a row produces identical output (modulo timestamps). No retries inside the skill — retries are the user's call.

## Arguments

```
/digital-marketing-pro:validate-profile [--brand <slug>] [--json] [--connectors <list>] [--quick]
```

- `--brand <slug>` — brand to validate (else uses active brand)
- `--json` — emit only the JSON summary, no human report (useful for chaining)
- `--connectors <list>` — comma-separated subset to probe instead of every connector in the profile (useful when only Slack rotated)
- `--quick` — skip the connector reachability probes (run only the field-level checks)

## Related skills + commands

- [`brand-setup`](../brand-setup/SKILL.md) — interactive brand creation
- [`import-guidelines`](../import-guidelines/SKILL.md) — bulk-load existing brand guidelines into the profile
- [`status`](../status/SKILL.md) — unified read-only snapshot of the active brand
- [`check`](../check/SKILL.md) — pre-publish content quality gate
- [`switch-brand`](../switch-brand/SKILL.md) — set the active brand
- `scripts/connector-status.py` — the underlying connector health probe
- `scripts/resolve_model.py` — model curator (used for currency check)
