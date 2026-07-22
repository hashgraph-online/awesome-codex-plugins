# Qt Widgets route

Apply [`qt.md`](qt.md) with the actual desktop or mobile/tablet target contract, or with the Web plus renderer contracts for Qt Widgets WebAssembly, then choose exactly one appearance strategy for each affected widget subtree. Preserve the repository's existing strategy unless the task explicitly changes ownership. Desktop window, menu, multi-screen, pointer, keyboard, shortcut, and mnemonic obligations apply only when the named target and supported inputs expose them; the mobile contract owns system bars, insets, lifecycle, orientation/posture, and touch behavior on mobile/tablet. WebAssembly keeps browser loading, input, accessibility integration, renderer, and supported-browser proof and does not inherit native-shell behavior.

## Strategy quick reference

| Strategy | Use when | Owns appearance |
| --- | --- | --- |
| Native-adaptive | The product is a platform-native app | current `QStyle`, semantic `QPalette`, narrow `QProxyStyle` overrides |
| Branded-deterministic | The app intentionally owns consistent chrome | explicit base style, controlled proxy/delegates/custom paint |
| QSS-led | An existing subtree already uses documented QSS | QSS properties, states, and subcontrols without a custom-style collision |

Write the chosen strategy and its subtree boundary before implementation. One affected subtree has one appearance owner: never make QSS and a custom `QStyle`/`QProxyStyle` co-own the same widget subtree. [Qt explicitly warns that style sheets are unsupported for custom `QStyle` subclasses](https://doc.qt.io/qt-6/qstyle.html#creating-a-custom-style); keep a QSS-led boundary in the documented [Qt Style Sheets](https://doc.qt.io/qt-6/stylesheet.html) surface and use its [property/state/subcontrol reference](https://doc.qt.io/qt-6/stylesheet-reference.html). A native-adaptive proxy stays narrow and delegates everything else to its base [QProxyStyle](https://doc.qt.io/qt-6/qproxystyle.html); a branded-deterministic route names its explicit base style and tests it on every target.

## Branded and multi-identity systems

Apply this section only when the product explicitly owns a branded, custom-painted, or switchable visual identity. An ordinary native-adaptive surface must not acquire a skin manager, renderer family, replacement view, or deterministic gallery merely because this section exists.

Write an **identity constitution** before implementation: signature or metaphor; hierarchy driver; typography and density; geometry and edge/corner grammar; depth or material strategy; state grammar; prohibited treatments; and the rule for extending new components. If two named identities differ only by palette, they are themes, not distinct identities; either name them as themes or introduce multiple meaningful differences across non-color categories such as hierarchy, geometry, typography/density, depth/material, state grammar, or component structure. Light/dark token sets are variants of one identity unless the product defines a different structural language.

Within the chosen ownership boundary, route presentation by capability. Use QSS for supported stock widget chrome and documented states only where it has no custom-`QStyle`/`QProxyStyle` collision. Use a `QStyledItemDelegate` for model/view rows; the shared delegate may own `sizeHint()`, editing, and `editorEvent()` or hit behavior. Use a widget's `paintEvent()` with `QPainter` for non-item custom or data geometry. Use custom `QWidget`/view factories only when structure genuinely differs and a delegate cannot express it. These layers may coexist only with explicit, non-overlapping responsibilities; the QSS/custom-style prohibition above still applies.

Shared models, controllers, host widgets, and delegates retain their existing behavior boundaries: models and controllers own data, commands, and serialization; hosts and delegates own input and hit testing, keyboard behavior, editing, and accessibility actions. Identity-specific presentation receives resolved semantic state and device-independent geometry and owns styling, painting, or a structure-specific view; it must not duplicate per-identity behavior or domain logic.

New presentation hooks default to no-op or legacy-equivalent output, and a frozen equivalent environment must prove the existing/default identity remains visually unchanged. Runtime switching must be idempotent and preserve focus, selection, active editors, scroll state, model/action identity, and accessibility semantics. Repolish and repaint when only paint changes; when typography, density, style metrics, or geometry changes, call `updateGeometry()` and invalidate affected layouts before repainting. When structure genuinely changes, rebuild or rebind only the affected subtree and restore those states instead of assuming repaint can change structure.

## Layout and state

Use layouts, truthful `sizeHint()`/`minimumSizeHint()`, and `QSizePolicy` to negotiate geometry. Do not position responsive content with fixed rectangles or compensate for a style by hard-coding its current metrics. Let [layout management](https://doc.qt.io/qt-6/layout.html), [size policies](https://doc.qt.io/qt-6/qsizepolicy.html), and the selected [QStyle](https://doc.qt.io/qt-6/qstyle.html) determine usable sizes; verify minimum, preferred, expanded, translated, and enlarged-font cases.

Consume semantic [QPalette](https://doc.qt.io/qt-6/qpalette.html) roles from the effective widget/style palette. Handle and test the `Active`, `Inactive`, and `Disabled` color groups that the selected style and named target expose or that the product claims, rather than painting one literal "normal" state; record unsupported groups as not applicable with a reason. Do not assume every native style paints every palette brush; inspect the rendered target when product color ownership is required.

## Interaction and geometry

Initialize the correct `QStyleOption` from the widget or delegate and carry its enabled, active, selected, pressed, direction, and focus state into style drawing. Ask [QStyle](https://doc.qt.io/qt-6/qstyle.html) for metrics, content sizes, sub-element rectangles, and subcontrol rectangles rather than duplicating native geometry.

A custom or composite control must have one semantic part model: the same part identifiers and rectangles drive **paint, event hit-testing, supported-input focus/activation, and accessibility**. A part that is only painted or invocable through one supported input is incomplete. Use `QStyleOption` state for visible focus and preserve standard keyboard activation when hardware keyboard input is supported. For a `QStyle::ComplexControl`, make painting and `hitTestComplexControl()` agree; for an ordinary custom widget, use the same geometry in its applicable pointer, touch, or pen-event hit testing. Verify every supported path at each selected target scale and layout direction.

For dynamic model/view rows, keep data in the model and implement appearance, `sizeHint()`, editing, and hit behavior with [QStyledItemDelegate](https://doc.qt.io/qt-6/qstyleditemdelegate.html). Do not create a persistent child-widget tree per row merely to style repeated content. Initialize and use the supplied style option so selection, focus, enabled state, palette, direction, and the current style remain coherent.

## Native and inclusive behavior

Keep target-native top-level chrome or system bars, standard dialogs, focus conventions, and platform actions by default as applicable; brand the content area inside that boundary. Desktop menus, window movement/resizing, system controls, system shortcuts, and multi-screen behavior are required only on named targets that expose those capabilities. If a custom replacement is explicit, verify the target-applicable window or inset behavior, modality, supported input, system actions, lifecycle, and assistive technology on every named target.

Stock widgets already expose accessibility semantics. Custom widgets and virtual subparts must provide the corresponding `QAccessibleInterface` roles, names, states, values, relationships, and actions, then emit the appropriate accessibility event after state changes. Keep the accessible tree and bounds aligned with the shared paint/hit-test geometry; follow [Accessibility for QWidget Applications](https://doc.qt.io/qt-6/accessible-qwidget.html).

Keep geometry and custom painting device-independent and provide high-density raster/icon assets rather than scaling raw device-pixel assumptions. Layout and paint with font metrics so platform font fallback, CJK, RTL/mirroring, emoji, long translations, and enlarged text can change both width and height without clipping.

## Behavior checks

Use [Qt Test](https://doc.qt.io/qt-6/qtest-overview.html) to exercise behavior, not screenshots alone:

- every supported pointer, touch, pen, keyboard, switch, or assistive action path triggers the same action exactly once;
- focus traversal, visible focus, shortcuts/mnemonics, enabled/disabled behavior, and cancellation work where the named target and supported inputs expose or require them;
- paint and hit-test boundaries agree in applicable LTR and RTL layouts at target-selected scale factors;
- each target-applicable `Active`, `Inactive`, and `Disabled` palette group remains legible under the selected supported style/theme;
- dynamic rows preserve selection, focus, editing, accessibility, and size hints with long/CJK/emoji text; and
- custom accessibility state/value changes emit the expected events.

Complete the common Qt pre-flight and the Qt QA route on a real named target before claiming native or branded parity.
