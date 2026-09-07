# Qt Quick/QML route

Apply [`qt.md`](qt.md) first. Preserve the repository's QML-module boundaries, selected Qt Quick Controls style, and style-selection mechanism. Start with standard Controls; replace a control or create a custom item only when the product requirement cannot be met through the selected style's supported surface.

## Select one Controls style route

Record one route before loading the application UI. Runtime and compile-time selection are different deployment contracts; do not mix them casually or change the project's route as an incidental visual edit.

| Route | Selection contract | Consequence |
| --- | --- | --- |
| Runtime | Import `QtQuick.Controls`. Apply `QQuickStyle::setStyle()`, the command-line option, environment, or configuration file **before loading any QML that imports Qt Quick Controls**. | One binary may support multiple styles; preserve user/deployment selection and its precedence. |
| Compile-time | Explicitly import the chosen `QtQuick.Controls.<Style>` before any other Controls import and omit the generic runtime import from owned QML. | The QML compiler sees the concrete style; each executable has one compiled style, and a custom style declares its fallback. |

If repository ownership or static-build requirements are unknown, the selection must remain unresolved without listing alternatives. Once those facts are known, select exactly one repository-owned runtime channel, or the compile-time route when required; never invent a provisional channel or add a second channel. Document override precedence only when the repository already supports it deliberately.

Before returning a custom-style plan when those facts were not inspected, write `Style-selection channel: unresolved pending repository ownership and static-build inspection`; do not name, recommend, or exemplify any runtime or compile-time channel. After inspection, replace that unresolved line with the one selected route.

Compile-time imports override runtime selection. If third-party QML forces both routes, document that boundary and make the explicit style import first so fonts and palettes remain coherent; otherwise use one route throughout. Check static-build and minimum-version requirements against the repository. See [Styling Qt Quick Controls](https://doc.qt.io/qt-6/qtquickcontrols-styles.html).

## Customize without replacing the architecture

Prefer a narrow, supported customization of the selected standard Control. When the application owns a full custom style, each implemented control file must root itself in the corresponding `QtQuick.Templates` type and live in an importable QML module with a `qmldir`. Choose exactly one fallback mechanism consistent with the selected style route: a compile-time or static fallback is the style's qmldir import; a dynamic runtime fallback may be selected only when no static qmldir fallback exists. Never configure both. The fallback must supply every control the custom style omits. Do not import `QtQuick.Controls` inside a style implementation or derive a control from itself. Preserve the repository's existing fallback rather than silently changing its metrics or behavior. Follow [Qt's customization contract](https://doc.qt.io/qt-6/qtquickcontrols-customize.html).

Reuse the project's existing theme or design module. App-owned semantic color, spacing, type, and motion tokens may be exposed through one registered, typed singleton in that QML module when they genuinely need shared access. Use a declared QML singleton or `QML_SINGLETON` plus `QML_ELEMENT`, so `qmllint` and other tooling retain type information; do not replace it with an untyped context property or global JavaScript object. A singleton is only for **app-owned tokens**, not a cache for the live system palette, platform font, native metrics, Controls style, or accessibility preferences. See [Singletons in QML](https://doc.qt.io/qt-6/qml-singleton.html).

## Keep geometry and state ownership singular

A layout owns the `x`, `y`, `width`, `height`, and anchors of its immediate children. Give those children truthful implicit sizes and `Layout.*` constraints; do not also anchor them or bind their owned geometry. Anchors or explicit dimensions may size a top-level layout against its non-layout parent. This ownership rule follows [Qt Quick best practices](https://doc.qt.io/qt-6/qtquick-bestpractices.html) and the [Layouts overview](https://doc.qt.io/qt-6/qtquicklayouts-overview.html).

Drive appearance from semantic model/control states such as enabled, pressed, checked, focused, selected, loading, and error. Put the final property values in the state or its bindings; a `Transition` only interpolates between those truths. Make reverse paths explicit or reversible where required, and test interruption by changing state mid-motion: the component must settle on the newest state's final values without relying on `onStopped`, animation order, or stale event callbacks. See [states and transitions](https://doc.qt.io/qt-6/qtquick-statesanimations-topic.html) and the [`Transition` contract](https://doc.qt.io/qt-6/qml-qtquick-transition.html).

## Preserve interaction and accessibility

Use a standard Control when it supplies the required behavior. A custom interactive item is complete only when every target-supported pointer, touch, keyboard, switch, and assistive-technology action invokes the same semantic command; unsupported input modes are not invented. Documented `Accessible` attached properties provide accessibility metadata, supported state flags, relationships, and actions; they do not replace ordinary properties required by a role.

For value roles, expose the declared-version-supported ordinary properties `value`, `minimumValue`, `maximumValue`, and `stepSize`. Availability derives from the item's `enabled` property. Keep supported attached metadata and state such as role, name, checked, and selected synchronized with the same visual/model truth, and wire each supported accessibility or input action to the same command. If required semantics are unavailable at the declared minimum version, use a standard Control that exposes them or a validated custom accessibility-interface path. Verify target-applicable focus traversal, visible focus, cancellation, action parity, and change notifications. Follow [Accessibility for Qt Quick](https://doc.qt.io/qt-6/qml-qtquick-accessible.html).

Treat popup presentation as part of the component contract. Test the actual supported `Popup.Item`, `Popup.Window`, or `Popup.Native` path and its documented fallback; a separate or platform-native popup is not part of the parent scene's pixels. Guard `popupType` or any other newer API at the declared minimum Qt version. See the [Popup type](https://doc.qt.io/qt-6/qml-qtquick-controls-popup.html).

## Tooling and behavior checks

Use repository commands and module metadata rather than linting an isolated file without its imports:

- run the configured formatter or [`qmlformat`](https://doc.qt.io/qt-6/qtqml-tooling-qmlformat.html) only on the changed QML scope, preserving the required style-import order;
- run module-aware [`qmllint`](https://doc.qt.io/qt-6/qtqml-tooling-qmllint.html), including generated type information and project import paths or the CMake module's lint target;
- run affected C++/Qt tests and [Qt Quick Test](https://doc.qt.io/qt-6/qtquicktest-index.html) cases; and
- inspect startup and scene-graph warnings on the named graphics backend.

Exercise long translations, CJK and emoji fallback, RTL and mixed direction, enlarged text, supported keyboard and IME input, target-applicable minimum and expanded window classes, representative DPRs, affected popup/editor paths, and selected scene-graph initialization/failure handling. Add live resizing and mixed-DPR screen moves only when the named desktop/windowing target exposes them; on mobile/tablet, use the current-window, orientation, posture, inset, and display-transition cases selected by `mobile.md` instead of importing desktop-only behavior. Profile an observed problem with the QML Profiler before rewriting bindings, delegates, loaders, or animations; speculative performance rewrites are not evidence. Follow Qt's [performance guidance](https://doc.qt.io/qt-6/qtquick-performance.html).

## `QQuickWidget` mixed boundary

Use this branch only when QML is embedded in a Widgets hierarchy, and apply [`qt-widgets.md`](qt-widgets.md) to the host. `QQuickWidget` adds a render pass into an offscreen buffer and disables the threaded render loop on every platform; do not assume `Animator` or vsync-driven behavior matches a `QQuickWindow`. Accept that cost explicitly against alternatives, avoid turning the widget into a native window with `winId()`, and never show its offscreen `quickWindow()`.

Validate the boundary on the real target:

- exercise bidirectional focus traversal between Widgets and QML when the named target supports hardware keyboard focus; on touch-only or switch-driven targets, prove the corresponding touch and assistive action crosses the boundary with the same result. Exercise text selection, CJK composition/preedit, candidate placement, and input-method dismissal when editable text is supported; synthetic key events are not IME proof;
- exercise continuous resize and mixed-DPR screen movement on desktop/windowing targets only when the named target exposes them. On mobile/tablet, use the selected current-window, orientation, posture, inset, and display-transition cases instead, checking target-applicable geometry, input coordinates, text/icon sharpness, and scene-graph recovery;
- compare active, inactive, disabled, light/dark, and runtime palette changes across the widget and QML sides only when the selected style and named target expose or claim those states, rather than assuming a custom token bridge follows `QPalette`;
- open the in-scene, separate-window, or native popup forms actually used by the affected journey, checking target-applicable focus, modality, placement, stacking, and fallback; and
- treat `grabFramebuffer()` as an expensive readback of the Quick scene only. An offscreen/client grab cannot prove native widget chrome, platform dialogs, IME UI, or separate/native popups; capture those through the OS under [`qt-qa.md`](qt-qa.md).

These constraints come from the official [`QQuickWidget` documentation](https://doc.qt.io/qt-6/qquickwidget.html). Do not claim native parity until both the embedded scene and every surface outside its framebuffer have real-target evidence.
