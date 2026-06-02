---
name: express-tracking
description: Query shipment progress when a user provides a tracking number, wants the latest courier updates from Kuaidi100, needs a Chinese summary plus recent events, or wants another skill such as MSI repair status to enrich a shipment number into live logistics progress.
---

# Express Tracking

Use `scripts/run.mjs` for Kuaidi100-backed shipment tracking.

## Workflow

1. Install the bundle into the target project.
2. Put Kuaidi100 credentials in the current shell or the target project's `.env.local`, not in the skill directory.
3. Run:
   - `node .codex/skills/express-tracking/scripts/run.mjs --number="<tracking-number>"`
   - Optional carrier override: `--carrier="<kuaidi100-company-code>"`
   - Optional recent-events limit: `--recent-limit="<count>"`
   - Optional machine output: `--json`
4. Prefer automatic carrier detection first when the credential supports it.
5. If auto detection is unavailable or not enabled, fall back to a narrow local heuristic for obvious prefixes such as JD shipment numbers.
6. If neither auto detection nor heuristic can determine the carrier, ask the user for an explicit Kuaidi100 company code and rerun with `--carrier`.
7. Report the result in Chinese:
   - tracking number
   - carrier code and how it was determined
   - current logistics state
   - latest event time and message
   - a short recent-events list
8. In `--json` mode, return a stable object with:
   - `provider`
   - `number`
   - `carrier.code`
   - `carrier.source`
   - `state.code`
   - `state.label`
   - `status.code`
   - `status.message`
   - `latestEvent`
   - `recentEvents`

## Required Configuration

- Secrets must come from the current shell or the project-local `.env.local`.
- Supported keys:
  - `EXPRESS_TRACKING_KUAIDI100_KEY`
  - `EXPRESS_TRACKING_KUAIDI100_CUSTOMER`
  - `EXPRESS_TRACKING_KUAIDI100_QUERY_URL`
  - `EXPRESS_TRACKING_KUAIDI100_AUTO_URL`
  - `EXPRESS_TRACKING_DEFAULT_RECENT_LIMIT`

## Guardrails

- Do not pass credentials on the command line.
- Keep the published skill bundle public-safe. Ship only `.env.example`, never live credentials.
- Treat auto carrier detection as optional capability. Some Kuaidi100 accounts do not have it enabled.
- If auto detection fails and the local heuristic is not confident, stop and ask for `--carrier` instead of guessing broadly.
- If Kuaidi100 returns a business error, surface the returned message clearly instead of masking it.
- If another skill calls this one, prefer `--json` so the caller can consume a stable machine-readable result.

## Notes

- The realtime query uses Kuaidi100 `customer + sign + param`.
- The `sign` is the uppercase MD5 of `param + key + customer`.
- The shipped bundle is self-contained under `skills/express-tracking/` and does not depend on repository-root files after installation.

## References

- Read `references/kuaidi100.md` when you need the request shape, config behavior, or state-code mapping.
