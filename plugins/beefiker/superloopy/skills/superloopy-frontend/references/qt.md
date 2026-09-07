# Qt common route

Load this contract before the Qt Widgets, Qt Quick/QML, or mixed route. This is a target-neutral Qt 6 common contract: compose it with `references/desktop.md` for a desktop target, `references/mobile.md` for a mobile/tablet target, or `references/web.md` plus `references/renderer.md` for Qt Widgets, Qt Quick/QML, or mixed Qt WebAssembly. Preserve the repository's architecture and use the Qt route's target-native evidence gates for Qt-owned non-Web pixels. A Qt WebEngine or embedded HTML client still composes `references/web.md` and `references/hybrid.md` with the target platform route; Qt build, interaction, or capture never substitutes for that client's browser, accessibility, lifecycle, and client-shell boundary proof.

## Establish the repository and target facts

Before editing UI code, record:

- whether the build uses CMake, qmake, or both, and which targets own the UI;
- whether the surface is Widgets, QML, or mixed, including each technology boundary;
- the declared **minimum Qt version**, taken from repository configuration rather than the locally installed SDK;
- every target OS, device/window class, and supported input; on desktop, include the desktop environment and display server when they affect behavior;
- the selected Qt style, where it is selected, and whether users or deployment can change it;
- existing unit, interaction, accessibility, and visual tests; and
- the command and real target environment available for behavioral validation and, when a visual claim changes, capture.

Do not infer an unknown fact from the development machine. Ask the minimum necessary questions when unknowns would change the implementation strategy, and batch independent unknowns when more than one answer is required; otherwise disclose them and constrain the claim.

## Authority and ownership

Existing architecture and the project's authoritative design source own app-defined product decisions, but they cannot override required target behavior or accessibility. Use version-matched Qt documentation for API and toolkit facts, the target platform's HIG for platform conventions, and optional visual inspiration only to refine decisions inside those boundaries.

The project's existing design source of truth remains authoritative. Use `DESIGN.md` as that owner only when the repository already establishes it. Otherwise, use `DESIGN.md` only as a scoped mapping/receipt when the repository has no equivalent or when it links every changed app-defined semantic back to, and stays synchronized with, the authoritative source. Never create a competing token source. A repository without a formal design-system document is not blocked: preserve its working Qt style, theme, palette, component, and platform conventions and document only the affected visual decisions. A narrow nonvisual change may record `Design impact: unchanged` and `Visual evidence: not applicable` with behavioral, accessibility, and regression evidence instead of creating design artifacts.

Map app-defined semantic roles for color, spacing, type, and motion at component boundaries and keep runtime-owned values live: do not freeze the **system palette, platform font, native metrics, focus geometry, or accessibility preferences** into product tokens. Use [QGuiApplication](https://doc.qt.io/qt-6/qguiapplication.html) palette and font only as application defaults, not as substitutes for the effective values after component inheritance or overrides.

- **Widgets** use the effective [QPalette](https://doc.qt.io/qt-6/qpalette.html) of the widget or style option and the current [QStyle](https://doc.qt.io/qt-6/qstyle.html) for style-owned geometry and metrics.
- **Quick** resolves each live value at the type that owns it: palette comes from the effective [Item](https://doc.qt.io/qt-6/qml-qtquick-item.html#palette-prop), [Window](https://doc.qt.io/qt-6/qml-qtquick-window.html#palette-prop), [Control](https://doc.qt.io/qt-6/qml-qtquick-controls-control.html), or [ApplicationWindow](https://doc.qt.io/qt-6/qml-qtquick-controls-applicationwindow.html), while font comes from a concrete font-owning `Control`, `ApplicationWindow`, or [Text](https://doc.qt.io/qt-6/qml-qtquick-text.html) type. Combine those effective values with the selected Controls style, truthful [implicit sizes](https://doc.qt.io/qt-6/qml-qtquick-item.html#implicitWidth-prop), and [`Layout.*`](https://doc.qt.io/qt-6/qtquicklayouts-overview.html) constraints. A generic `Item` or `Window` must not be assumed to expose a font property.
- A **pure Quick** route must not add a Qt Widgets dependency or consult `QStyle` for style metrics. Keep Quick geometry and metrics inside the selected Controls style, implicit-size, and Qt Quick Layout contracts.

Read only properties actually exposed by [QStyleHints](https://doc.qt.io/qt-6/qstylehints.html) for supported platform and accessibility hints; check each one against the declared minimum Qt version and provide a guarded fallback before use. Product accents and internal rhythm may be deterministic, but user and platform settings remain authoritative unless the product requirement explicitly owns them; follow Qt's [accessibility guidance](https://doc.qt.io/qt-6/accessible.html).

## Version and fallback contract

Check every referenced API and style behavior against the declared minimum Qt version. For an API introduced later, add the appropriate build/runtime guard and a named fallback before using it. Keep the fallback behind the same component boundary, preserve the existing or native behavior, and never silently raise the minimum version or drop keyboard/accessibility semantics. Platform support is a capability to verify, not a promise inferred from a newer documentation page.

## Common behavior contract

- **Supported input and focus:** Enumerate the target-supported input modes, including pointer, keyboard, touch, pen, switch, and assistive actions where applicable. Preserve a logical focus chain, visible focus, standard activation, and parity across every supported way to invoke the same action. Do not impose hover, desktop mnemonics, or hardware-keyboard traversal on a touch-only target; do not omit them where the supported target requires them. Derive available platform timing, hover, activation, and focus behavior from [QStyleHints](https://doc.qt.io/qt-6/qstylehints.html) instead of hard-coded desktop assumptions.
- **Accessibility:** Prefer controls with built-in accessibility. Every custom interactive element must expose its role, name, state, value, and available action, and must notify assistive technology when those change. Color, sound, animation, or pointer input cannot be the only carrier of meaning; see Qt's [accessibility guidance](https://doc.qt.io/qt-6/accessible.html).
- **Text and direction:** Layouts must survive CJK line breaking, RTL and mixed-direction text, emoji, font fallback, translations longer than the source, and enlarged text. Use logical alignment and locale direction; do not encode left/right assumptions or fixed text boxes. Follow Qt's [internationalization guidance](https://doc.qt.io/qt-6/internationalization.html).
- **High DPI and display transitions:** Keep UI geometry in device-independent coordinates, provide suitable image/icon representations, and test each target-supported DPR and display transition. Exercise mixed-density multi-screen movement only on targets that support it; exercise orientation, window-class, or external-display changes when those are the actual target transitions. Follow Qt's [High DPI model](https://doc.qt.io/qt-6/highdpi.html).
- **Motion and native chrome:** Motion must not carry required state and must honor the platform's available motion/accessibility preference; an older-version fallback removes nonessential motion. Keep target-native system chrome, system bars, top-level window chrome, and platform dialogs native by default as applicable. A deliberate custom replacement must retain the target's required move, resize, insets, system-menu, focus, input, accessibility, and lifecycle behavior.

## Disclosed boundaries

This reference does not silently generalize across Qt editions or targets:

- **Qt 5:** use its archived, version-matched documentation and audit every Qt 6 assumption and guard;
- **language bindings:** verify binding names, ownership/lifetime, threading, and packaging in that binding's official documentation;
- **desktop:** load `references/desktop.md` and apply its window, chrome, desktop input, session, distribution, and packaged-lifecycle rules only where the named desktop target supports them;
- **mobile/tablet:** load `references/mobile.md`; its mobile guidance replaces desktop-specific input, window, display, chrome, lifecycle, and package checks while this common Qt ownership, version, accessibility, text, and rendering contract remains active;
- **WebAssembly:** load `references/web.md` and `references/renderer.md`; prove the production browser journey, Qt-owned renderer/semantics boundary, browser accessibility and input integration, loading/failure behavior, and supported browser matrix independently. Do not claim native shell, package, or platform-dialog behavior unless a separately named host owns and proves it;
- **Qt for MCUs:** use the product's constrained-device requirements and real-device evidence rather than borrowing desktop or general mobile assumptions;
- **unknown Linux desktop:** identify desktop environment, style/theme, display server, scale, and input method before claiming native behavior. If they remain unknown, test stated representative combinations and mark the rest unverified.

## Qt pre-flight

For Qt-owned non-Web pixels, this checklist replaces the Web anti-slop, browser-breakpoint, and Lighthouse checklist. It does not replace the Web + hybrid proof retained by a Qt WebEngine or embedded HTML client:

- [ ] Build system, surface type, minimum Qt version, targets, selected style, tests, and capture path are recorded.
- [ ] One appearance owner is selected for each surface, with mixed Widgets/QML boundaries explicit.
- [ ] Newer APIs have guards, a fallback, and a testable boundary.
- [ ] The existing design source remains authoritative; any `DESIGN.md` is either that established source or a synchronized scoped mapping, and app semantics do not freeze the system palette, platform font, native metrics, or accessibility preferences.
- [ ] Every supported input path (pointer, keyboard, touch, pen, switch, or assistive action as applicable) reaches the same truthful semantic outcome.
- [ ] User-visible strings pass through `tr()`/`qsTr()` with a translation setup when the target implies more than one locale; a mismatched shipped language records its locale decision.
- [ ] CJK, RTL, emoji/font fallback, long translations, and enlarged text remain usable.
- [ ] High-DPI geometry and assets are correct across each target-supported DPR and display transition; unsupported transitions are recorded as not applicable.
- [ ] Motion preferences and target-native system chrome are preserved or an explicit replacement is fully verified.
- [ ] Validation runs on the named target style/platform and produces behavioral evidence; a changed visual claim or interaction with a visible-state/layout consequence also produces the applicable real-target capture.
