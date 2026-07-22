# Deployment Eligibility Gate

Apply this gate before cloud-native readiness scoring. Eligibility answers whether a
deployment unit belongs on the target cloud platform; the 0-12 readiness score only
measures how well an eligible unit follows cloud-native practices.

## Decision Contract

Classify the requested repository or directory with exactly one status:

| Status | Meaning | Required action |
|--------|---------|-----------------|
| `eligible` | A supported headless workload or static web build is identifiable | Continue to readiness scoring |
| `ineligible` | The target is outside the deploy skill's scope | Report evidence and STOP |
| `needs_review` | Evidence is insufficient, conflicting, or belongs to multiple units | Inspect manually; continue only after explicitly proving the requested root eligible |

The gate is fail-closed. Dockerfiles, Compose files, published images, a readiness
score, or user willingness to proceed do not override an `ineligible` decision.
`needs_review` also blocks downstream phases until the review records an explicit
`eligible` or `ineligible` result.

A mixed repository remains blocked in this workflow even when one nested unit looks
deployable. Do not select or deploy that nested unit as part of this gate.

Keep the decision in the active run context and user-facing report. Do not create a
new project artifact for deployment eligibility.

Every eligible decision must identify a supported workload at the requested root.
Ineligible decisions expose no deployable candidates. A `remote_desktop` decision
can become eligible only after explicit review.

## Eligible Workload Types

- `web_service` — a headless web application, API, gateway, or network service with
  a clear non-interactive start command
- `static_web` — a frontend with a reproducible production build whose output can be
  served by Nginx, Caddy, or another standard static server
- `worker` — a long-running, non-interactive queue consumer or background processor
  with a clear start command; an inbound HTTP port is not required
- `scheduled_job` — a non-interactive batch or scheduled task with bounded execution
  and an explicit command
- `remote_desktop` — only when the repository already defines an intentional
  headless, browser-accessible runtime such as noVNC, Xvfb, Selkies, or WebRTC;
  ordinary desktop source code does not qualify

## Ineligible Workload Types

- `desktop_gui` — Electron, Tauri, Qt, GTK, native macOS/Windows GUI, or similar
  desktop-only applications without an independently runnable cloud unit
- `mobile_client` — Android, iOS, React Native, Expo, or Flutter client code without
  an independently runnable backend or web target
- `cli` — interactive or short-lived command-line tools that are not intentional
  scheduled jobs
- `library` — libraries, frameworks, SDKs, plugins, and source packages without an
  application entry point
- `browser_extension` — browser extensions without an independently runnable backend
- `hardware_dependent` — firmware, embedded, driver, or local-hardware-dependent code
- `unknown` — no supported deployment unit or executable build/run contract can be
  established after review

## Repository and Unit Rules

1. Classify runnable workloads, not repository labels.
2. If the repository contains multiple runnable units, or mixes desktop/mobile code
   with a cloud workload, return `needs_review`, list the evidence, and STOP. This
   gate does not select and deploy a nested unit from a mixed repository.
3. Do not classify a renderer bundled inside an Electron/Tauri app as `static_web`
   unless the repository documents and builds it as an independent web target.
4. Do not require an HTTP listener from workers or scheduled jobs. Require a clear,
   non-interactive runtime contract instead.
5. Treat an existing browser/VNC container contract as `needs_review` until its
   headless entry point and remote access path are confirmed.

## Evidence

Record concise, repository-relative evidence for every decision. Prefer multiple
signals when rejecting a unit.

Examples:

- desktop: Electron dependency plus `BrowserWindow`/`ipcMain`, Tauri config, Qt/GTK
  imports, desktop packaging scripts
- mobile: Android/iOS project layout, React Native/Expo dependencies, Flutter mobile
  targets
- web service: server framework plus listener/start command, or an existing runtime
  container exposing the service
- static web: frontend framework plus production build script and documented output
- worker/job: queue or scheduler integration plus a dedicated non-interactive command
- CLI/library: package `bin`/console-script metadata, library exports, and absence of
  a supported application entry point

Dependency presence alone is not enough to reject a mixed repository. Evidence must
show that the selected unit itself is outside the supported workload types.
