---
name: superloopy-frontend
description: Use only after explicit Codex `$superloopy:superloopy-frontend` or Claude Code `/superloopy:superloopy-frontend` invocation for supported screen-based application UI across browser-hosted Web, interactive deployed content-led Web, desktop, mobile/tablet, embedded/hybrid, Qt, custom-rendered, or mixed targets, such a task started with a leading `loopy` or `루피`, or an active Superloopy loop explicitly routing it here. Do not activate from UI, frontend, desktop, mobile, or framework vocabulary alone, or for TV, wearable, XR, automotive, game UI, TUI, static media/document artifacts, or non-UI work.
---

# Superloopy Frontend

## Activation

Open your reply with `SUPERLOOPY FRONTEND ENABLED`. If another active Superloopy mode mandates its own first line, print that first and this marker on the next line.

**Explicit activation only.** Engage when the user invokes `$superloopy:superloopy-frontend` in Codex or `/superloopy:superloopy-frontend` in Claude Code for a supported screen-based application UI task, begins such a task with a leading `loopy` or `루피`, or an already-active Superloopy loop explicitly routes that task here. Interactive deployed content-led Web such as a campaign, publication, or landing experience is supported when navigation, forms, consent, localization, or another user journey is being built or validated; a static image, video, slide deck, document, or other non-interactive artifact is not. A plain mention of UI, frontend, desktop, mobile, SwiftUI, Tauri, Flutter, Qt, QML, Widgets, or a visible symptom is not authorization to activate this workflow. TV, wearable, XR, automotive, game UI, TUI, static media/document artifacts, and backend, API, data, concurrency, or infrastructure work stay with their primary workflows.

## Inspect and route

Resolve the facts that determine ownership and proof before choosing references:

- affected users, job, and outcome, marking each as evidence, assumption, or unknown with confidence;
- deployed OS, device, desktop environment, and session;
- public, authenticated, private/internal, installed, embedded, native-control, custom-rendered, or mixed composition;
- renderer and its semantic and accessibility model;
- client, shell, service, document, and state ownership;
- framework, runtime, provider, backend, and supported version;
- package, sandbox, update or distribution channel, and persistence boundary; and
- supported input, locale, accessibility services, and target validation capability.

For a Qt route, also resolve the minimum Qt version. Inspect repository evidence first. Ask the minimum necessary questions only when material unknowns would change the route or result; batch independent unknowns when more than one must be answered. Load the smallest applicable union:

| Requested surface | Load |
| --- | --- |
| Browser-hosted DOM/document Web | [`references/ux.md`](references/ux.md) + [`references/web.md`](references/web.md) |
| Browser-hosted canvas/custom-rendered Web | [`references/ux.md`](references/ux.md) + [`references/web.md`](references/web.md) + [`references/renderer.md`](references/renderer.md) |
| Installed PWA or browser extension | [`references/ux.md`](references/ux.md) + [`references/web.md`](references/web.md) |
| Embedded HTML on desktop | [`references/ux.md`](references/ux.md) + [`references/web.md`](references/web.md) + [`references/desktop.md`](references/desktop.md) + [`references/hybrid.md`](references/hybrid.md) |
| Embedded HTML on mobile | [`references/ux.md`](references/ux.md) + [`references/web.md`](references/web.md) + [`references/mobile.md`](references/mobile.md) + [`references/hybrid.md`](references/hybrid.md) |
| Native/custom desktop | [`references/ux.md`](references/ux.md) + [`references/desktop.md`](references/desktop.md) |
| Qt Widgets on desktop | [`references/ux.md`](references/ux.md) + [`references/desktop.md`](references/desktop.md) + [`references/qt.md`](references/qt.md) + [`references/qt-widgets.md`](references/qt-widgets.md) + [`references/qt-qa.md`](references/qt-qa.md) |
| Qt Widgets on mobile or tablet | [`references/ux.md`](references/ux.md) + [`references/mobile.md`](references/mobile.md) + [`references/qt.md`](references/qt.md) + [`references/qt-widgets.md`](references/qt-widgets.md) + [`references/qt-qa.md`](references/qt-qa.md) |
| Qt Quick/QML on desktop | [`references/ux.md`](references/ux.md) + [`references/desktop.md`](references/desktop.md) + [`references/qt.md`](references/qt.md) + [`references/qt-quick.md`](references/qt-quick.md) + [`references/qt-qa.md`](references/qt-qa.md) |
| Qt Quick/QML on mobile or tablet | [`references/ux.md`](references/ux.md) + [`references/mobile.md`](references/mobile.md) + [`references/qt.md`](references/qt.md) + [`references/qt-quick.md`](references/qt-quick.md) + [`references/qt-qa.md`](references/qt-qa.md) |
| Qt Widgets on WebAssembly | [`references/ux.md`](references/ux.md) + [`references/web.md`](references/web.md) + [`references/renderer.md`](references/renderer.md) + [`references/qt.md`](references/qt.md) + [`references/qt-widgets.md`](references/qt-widgets.md) + [`references/qt-qa.md`](references/qt-qa.md) |
| Qt Quick/QML on WebAssembly | [`references/ux.md`](references/ux.md) + [`references/web.md`](references/web.md) + [`references/renderer.md`](references/renderer.md) + [`references/qt.md`](references/qt.md) + [`references/qt-quick.md`](references/qt-quick.md) + [`references/qt-qa.md`](references/qt-qa.md) |
| Mixed Qt Widgets + Qt Quick on WebAssembly | [`references/ux.md`](references/ux.md) + [`references/web.md`](references/web.md) + [`references/renderer.md`](references/renderer.md) + [`references/qt.md`](references/qt.md) + [`references/qt-widgets.md`](references/qt-widgets.md) + [`references/qt-quick.md`](references/qt-quick.md) + [`references/qt-qa.md`](references/qt-qa.md) |
| Mixed Qt Widgets + Qt Quick on desktop | [`references/ux.md`](references/ux.md) + [`references/desktop.md`](references/desktop.md) + [`references/qt.md`](references/qt.md) + [`references/qt-widgets.md`](references/qt-widgets.md) + [`references/qt-quick.md`](references/qt-quick.md) + [`references/qt-qa.md`](references/qt-qa.md) |
| Mixed Qt Widgets + Qt Quick on mobile or tablet | [`references/ux.md`](references/ux.md) + [`references/mobile.md`](references/mobile.md) + [`references/qt.md`](references/qt.md) + [`references/qt-widgets.md`](references/qt-widgets.md) + [`references/qt-quick.md`](references/qt-quick.md) + [`references/qt-qa.md`](references/qt-qa.md) |
| Native/cross-platform mobile or tablet | [`references/ux.md`](references/ux.md) + [`references/mobile.md`](references/mobile.md) |
| Mixed or multi-target | Union of the applicable references above, beginning with [`references/ux.md`](references/ux.md) |

### Claim-triggered cross-cutting quality overlays

After selecting the target route, add only the references selected by the changed claim. These overlays are independent of target classification and do not expand a narrow task merely because every interface has layout or may contain animation:

- When information hierarchy, content exposure, or disclosure changes spatial presentation, or when placement, region topology, sizing, scroll, overflow, reflow, or adaptation changes, add [`references/layout.md`](references/layout.md). Behavioral-only label or purpose cleanup remains in shared UX and does not select layout when geometry and traversal stay unchanged; neither do other geometry-neutral copy, color, data, accessible-name, or behavior changes.
- When motion, transition, gesture progress, animated continuity, or haptic feedback changes, add [`references/motion-core.md`](references/motion-core.md). A Web implementation may additionally load the Web-only `references/motion.md`; native, Qt, and other routes do not inherit its React, browser, or animation-library rules.
- When a materially changed visual claim uses a generated, captured, sketched, or supplied reference, add [`references/image-first.md`](references/image-first.md) and classify its authority. Do not require an image for an existing-system delta that the authoritative product source already resolves.
- When the delivery is marketing, editorial, campaign, or an explicitly new visual direction, add [`references/anti-slop.md`](references/anti-slop.md) as the visual-direction check. It stays unselected for authenticated, internal, or convention-preserving product UI.
- High-impact decisions, task-based usability evidence, and accepted UX debt remain proportional sections of `references/ux.md`; they do not create separate project artifacts for every change.

`references/redesign.md` is a Web-only living-site specialization and is selected from the Web route. A native or embedded-shell redesign uses `ux.md` plus claim-selected `layout.md` and `image-first.md`, then its platform, renderer, and composition references; it does not inherit browser, SEO, or real-browser completion rules.

`layout.md` and `motion-core.md` are skill references, not mandatory output filenames. Keep the smallest applicable union and write into the existing receipt or proportional `UX_CONTRACT.md` unless the target repository already owns a more suitable artifact.

Add `references/renderer.md` to native/custom or cross-platform routes when an engine or custom renderer owns pixels, semantics, text, or input. Route framework names by deployed facts, not by brand. Tauri and pywebview follow the actual desktop or mobile target and embedded client ownership. Electron is a desktop hybrid with bundled Chromium, not an OS WebView. CustomTkinter follows native/custom desktop. Flutter and Compose add renderer and semantics proof where their engine owns pixels or accessibility. React Native follows the actual provider and target. MAUI Hybrid combines a native host with an embedded client. Qt uses the matching desktop, mobile/tablet, or WebAssembly row above. Qt Widgets on WebAssembly, Qt Quick/QML on WebAssembly, and mixed Qt WebAssembly all keep browser and renderer proof; they must not borrow native-shell proof or be routed as desktop merely because Qt built them. For HTML embedded in a Qt-owned shell, compose the Web + target platform + hybrid route, then add `qt.md`, `qt-qa.md`, and only the actual shell specialization (`qt-widgets.md`, `qt-quick.md`, or both). Qt preflight replaces browser gates only for Qt-owned non-Web pixels; it never removes Web proof for an embedded HTML client. Mac Catalyst is UIKit-on-desktop with AppKit augmentation; iPadOS stays on the mobile route with a desktop-capabilities overlay rather than inheriting macOS wholesale.

Treat framework capability claims as versioned facts: compare the repository-pinned version with current official documentation, record the provider and target, and keep unknown or unavailable capabilities unverified rather than inferring them from a brand name.

For every new scoped `surfaceEvidence` row—single, mixed, or multi-target—record `target: { id, platform, environment }`, one affected `owner`, non-empty `claims`, and `scopeReason`; use the [Gate Notes claim-shaped evidence table](../../docs/superloopy-gate-notes.md#claim-shaped-surface-evidence) to select compatible artifact kinds and proof minimums. For mixed or multi-target work, load shared UX once, then create one evidence row per target and affected owner and require independent, attributable proof. Ambiguous free-text such as `Web + iOS` does not establish a native owner; name `native iOS app`, the framework, or a separate owner row. One surface cannot substitute for another.

## Shared UX and design gate

Apply [`references/ux.md`](references/ux.md) before platform checklists. The project's existing design source of truth remains authoritative. Use `DESIGN.md` only as a scoped mapping/receipt when the repository has no equivalent or when it links each changed app-defined visual semantic back to that authoritative source; never create a competing token source. `UX_CONTRACT.md` owns expanded journeys and high-consequence behavioral claims when the proportional UX contract requires it. Preserve the project's architecture and existing styling infrastructure. A narrow nonvisual change may record `Design impact: unchanged` with its reason instead of creating design artifacts. Before adding an app-defined visual value that the existing contract lacks, add and synchronize its token in the project's design source of truth. Platform runtime values remain authoritative when native.

## Build, dispatch, and evidence

Preserve the existing stack. Resolve and announce `FRONTEND_SKILL_DIR` as the absolute directory containing this loaded `SKILL.md`; packaged helper scripts live there, never under the target project's working directory. For parallel work, dispatch self-contained crew slices with the relevant requirements and tokens inline, then judge each lane by delivered evidence. Use the portable `YYYYMMDDTHHMMSSZ-<slug>` run ID created by `$FRONTEND_SKILL_DIR/scripts/evidence-root.mjs`; its slug is 1-48 lowercase ASCII letters or digits joined by single hyphens, so the same path works across supported shells and filesystems. Store the run under `.superloopy/evidence/frontend/<run-id>/` in the target project. Capture real rendered-surface evidence and write `VISUAL_QA.md` when a visual claim changed, or when an interaction claim has a visible-state or layout consequence; a purely behavioral interaction uses behavioral evidence. Match functional, accessibility, usability, renderer, shell, package, and target evidence to each claim. A static policy check proves only that the contract is packaged.

With an active Superloopy loop, run `superloopy loop guide --json` and record each artifact against the returned goal and criterion; never omit their identifiers from `loop evidence`. Without an active Superloopy loop, keep the run-scoped receipts and finish with `SUPERLOOPY_EVIDENCE: <path>` instead of inventing loop state.

## Completion

Apply only the selected shared, platform, composition, and specialization checklists. Truthful interaction states, claim-shaped evidence, disclosed limitations, and no weakened UX are mandatory. Require design, UX, visual, accessibility, package, or real-target artifacts only when the affected claims and risk call for them. Promote simulated work capability by capability only after new real-target evidence.
