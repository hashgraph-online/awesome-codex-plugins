# Dependencies & support matrix

## Install
```bash
npm install @cometchat/chat-uikit-angular@^5 @cometchat/chat-sdk-javascript@^4 @cometchat/cards-angular@^1 dompurify@^3
```
Calls (optional): `npm install @cometchat/calls-sdk-javascript@^5`

## Peer dependencies — verified against the published 5.1.0
| Package | Range | Notes |
| --- | --- | --- |
| `@angular/core` | `>=17.0.0 <22.0.0` | 22 fails to install — see below |
| `@angular/common` | `>=17.0.0 <22.0.0` | |
| `@cometchat/chat-sdk-javascript` | `^4.1.13` | required |
| `@cometchat/cards-angular` | `^1.0.0` | **required** — added in 5.1.0 |
| `dompurify` | `^3.0.0` | required |
| `@cometchat/calls-sdk-javascript` | `^5.0.3` | optional — calls only |

> `@cometchat/cards-angular` was added between 5.0.3 and 5.1.0. Omitting it produces an incomplete install.

## Angular version support
| Angular | Status |
| --- | --- |
| 17 | Works (within the peer range) but undocumented |
| 18 – 21 | Supported and documented |
| 22 | **Install fails** — `ERESOLVE`, peer range excludes it |

> **Divergence from the docs.** `{DOCS_BASE}/ui-kit/angular/overview.md` lists Angular "v18, v19, v20, v21, v22" as supported. That is wrong against the published 5.1.0 package: the peer range is `>=17.0.0 <22.0.0` (so 22 hard-fails `ERESOLVE`). The table above is verified against npm — **trust it over the guide**. Do not scaffold Angular 22 because the docs say it is supported, and never `--force` past the install failure. (The version range needs a kit release; `@cometchat/cards-angular` as a required peer was corrected upstream and now appears in the overview's peer list — verified against cometchat/docs, 2026-09-09.)

CometChat's stated policy is 18 through latest, so the range is expected to widen in a future kit release. Until that ships, 22 does not install. Scaffold new apps with:
```bash
npx -y @angular/cli@21 new my-app
```

## Stylesheet + icon assets — BOTH are required
`angular.json` → `projects.<app>.architect.build.options`:

`styles`:
```json
"node_modules/@cometchat/chat-uikit-angular/styles/css-variables.css"
```
The package-specifier `@import` form does not work — the `exports` map does not expose it.

`assets` (282 SVG icons ship under `src/lib/assets`):
```json
{ "glob": "**/*", "input": "node_modules/@cometchat/chat-uikit-angular/src/lib/assets", "output": "assets" }
```
Missing this leaves icons broken across every component with no error — the most commonly missed Angular setup step. Verify after `ng serve`: send/attach/emoji buttons in the composer should render as icons, not blank space.

## Versions this skill was verified against
`@cometchat/chat-uikit-angular@5.1.0` · `@cometchat/chat-sdk-javascript@4.1.13`

## Production build: budgets + the CommonJS bailout

A stock CLI app budgets the initial bundle at 500 kB warning / 1 MB error. The kit plus the Chat SDK is ~4.2 MB, so the DEFAULT `ng build` (which is the production config) exits non-zero:
```
✘ [ERROR] bundle initial exceeded maximum budget. Budget 1.00 MB was not met by 3.21 MB with a total of 4.21 MB.
```
`ng serve` is unaffected, so this only bites at ship time. Under `configurations.production`:
```json
"budgets": [{ "type": "initial", "maximumWarning": "5mb", "maximumError": "6mb" }]
```
Also silence the CommonJS bailout warning (the Chat SDK is not ESM) under `build.options`:
```json
"allowedCommonJsDependencies": ["@cometchat/chat-sdk-javascript"]
```
