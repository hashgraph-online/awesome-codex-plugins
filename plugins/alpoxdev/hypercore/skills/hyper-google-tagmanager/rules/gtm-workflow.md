# GTM Workflow

**Purpose**: Pick one mode, run its phases in order, and chain into verification so no install or container change ends unproven.

## 1. Mode Selection

Choose the mode from the requested output, then confirm it with the script output from phase 1.

| Mode | Requested output | Ends with |
|---|---|---|
| `audit` | Findings about what a site, repository, or container export loads and what is wrong | Report only; no edits |
| `install` | GTM loading on the site, with dataLayer, consent defaults, SPA page views, and CSP handled | `verify` |
| `configure` | Container items created or changed in a workspace draft or an import JSON | `verify`, then the publish gate |
| `verify` | Proof that named tags fire with the right data and consent state | Verification table |
| `diagnose` | A missing, duplicate, or wrong signal found, fixed, and re-verified | Before-and-after evidence |
| `analyze` | Container health metrics or destination data checked against the event plan | Report only; no edits |

- A request that names several outputs runs the modes in this order: `audit` -> `install` -> `configure` -> `verify`. `diagnose` replaces `verify` when a check fails.
- "점검만", "audit only", "고치지 말고", "do not change" keep the run in `audit` or `analyze` even when findings are fixable; fixes are listed as proposals.
- An `install` on a site that already loads GTM becomes `audit` first: report the existing container and ask once whether to keep it, replace it, or add the requested tags to it. Recommend keeping the existing container.

## 2. Phases Per Mode

### `audit`

1. Run `scripts/gtm-detect.sh --root <repo>` when a repository is in scope.
2. Run `scripts/gtm-site-check.sh --url <url> --check-loader` for each named URL; run it on at least the home page and one deep page.
3. Run `scripts/gtm-container-audit.sh --file <export.json>` when the user supplied an export or the API returned a container version.
4. When a rendered browser is available, load the page, record requests to `googletagmanager.com` and `/g/collect`, and read `window.dataLayer` and `window.google_tag_manager` keys (`references/verification.md`).
5. Classify each finding as `error`, `warn`, or `info` with its evidence, and propose the fix with the mode that would apply it.

### `install`

1. Decide the tag strategy with `references/install-recipes.md` §1: GTM, or a direct Google tag for a single product with few changes. Do not install both for one ID.
2. Write the event plan table (`references/container-design.md` §1) before any code.
3. Get the snippet from the container's Install dialog or the API `snippet` method; otherwise use the current form in `references/install-recipes.md` §2 and record which form was used.
4. Place the consent default (`references/consent.md` §2) and any page-level dataLayer pushes above the snippet.
5. Apply the framework recipe (`references/install-recipes.md` §3), the SPA rule (§4), and the CSP rule (§5).
6. Run `gtm-detect.sh` again and confirm one container, one loader, and no direct Google tag for the same ID.
7. Continue with `verify`.

### `configure`

1. Read the current container: the export, or `accounts.containers.versions.live` and the workspace through the API (`references/api-and-analysis.md` §1).
2. Run `gtm-container-audit.sh` on it, so the change starts from known debt.
3. Write each change as an event plan row, then as a workspace item or an import JSON with the naming rules in `references/container-design.md` §7.
4. Set the consent settings of every new tag (`references/consent.md` §3).
5. Open Preview (Tag Assistant) or `quick_preview` and continue with `verify`.
6. Stop at the publish gate in `rules/safety-gates.md` §1.

### `verify`

1. Use a non-production environment or Preview first (`references/verification.md` §1-§2).
2. For each tag in the plan, record the trigger event, whether the tag fired, the request it sent, its key parameters, and the consent state.
3. Run `gtm-site-check.sh` against the page that now carries the change.
4. Report each tag as `verified`, `failed`, or `not verified` with the reason. Standard reports are not proof; a request or a debug event is.

### `diagnose`

Narrow in this order and stop at the first layer that explains the symptom:

1. Loading: is the container in the served or rendered page, once, with the right ID, and does `gtm.js` return a non-empty container (`references/verification.md` §4)?
2. Blocking: CSP violations, ad blockers, a deny-all `gtag('policy')`, `gtm.blocklist`, or a firewall.
3. Order: consent default and dataLayer pushes before the snippet; no `dataLayer = []` after load.
4. Trigger: did the event reach the dataLayer, and did the trigger condition match it?
5. Consent: did the tag wait for or skip consent as its settings say?
6. Destination: did the request leave the browser, and did it arrive (DebugView, Realtime, the vendor's debugger)?

Change one thing per attempt, re-run the same check, and record before and after. Three failed attempts on one root cause end as `exhausted`.

### `analyze`

1. Run `gtm-container-audit.sh` and report counts, tag types, and findings.
2. Compare the container's tags with the event plan or the user's list: planned but missing, present but unplanned.
3. When the user wants data checked and a read credential exists, compare events seen in a realtime or recent-days report against the plan (`references/api-and-analysis.md` §5). State the data latency and any sampling or thresholding.

## 3. Target Line

Print one Korean line before phase 2:

```text
대상: <site or repo> / 컨테이너: <GTM-ID or 없음> / 환경: <Preview|<env name>|Live> / 근거: <script and finding that showed the current state>
```

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Preview and Tag Assistant as the pre-publish check | <https://support.google.com/tagmanager/answer/6107056> |
| Standard reports lag; requests and DebugView are the immediate check | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| The diagnosis layers (loading, blocking, order, trigger, consent, destination) | this package's design over `references/verification.md` |

### Evidence grade

`LOCAL` - the mode order and the diagnosis order are this package's design, not a validated optimum.
