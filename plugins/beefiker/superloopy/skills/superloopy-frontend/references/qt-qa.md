# Qt QA

Apply this evidence gate to Qt Widgets, Qt Quick/QML, and mixed work, including their WebAssembly routes when selected. Define the **validation scope** from the changed claims, affected journey, adjacent regression surface, and consequence risk. A successful build is necessary for executable changes but does not by itself prove real-target rendering or interaction.

## Commands

Record the repository's exact commands with the candidate revision and build directory identifiable. An implementation must run and pass all applicable commands; a plan must name the intended commands and clearly mark them as not yet run.

Every implementation or release-proof plan must explicitly classify the configure/build, Qt Test/ctest, and repository lint/static gates. An executable Qt UI change requires a real configure/build. A docs-only or otherwise non-executable contract change may mark configure/build `not applicable` with a reason. Run affected existing tests and add focused automated coverage for changed behavior where the repository supports it. Missing required build infrastructure is a blocker for an executable claim. Missing test infrastructure is a disclosed gap, not an automatic blocker for every narrow change; it becomes a blocker when the changed risk cannot be covered truthfully by another reproducible behavioral check or when release criteria require that test layer.

Before returning a plan, include a **Repository gates** block:

- **Configure/build:** the applicable command and result, `BLOCKED` when required infrastructure is missing, or `N/A with reason` for a docs-only/non-executable change.
- **Qt Test/ctest:** the affected command and result; otherwise `GAP with evidence`, or `BLOCKED` when an unverified high-consequence behavior or release criterion requires it.
- **Lint/static:** the applicable command that must run and pass, or `N/A with evidence` that no relevant repository check exists.

Never use `N/A` for a required executable build, and never turn an unverified changed behavior into a pass.

- **Project configure/build:** the existing CMake, qmake, preset, or wrapper command for the real UI target.
- **Qt Test/ctest:** the affected Qt Test executable or focused `ctest` invocation, followed by the project's required suite.
- **Repository lint/static checks:** the existing formatter, compiler-warning, static-analysis, or other repository-defined command for the changed C++/UI scope. Add module-aware `qmllint` when QML is present; when no relevant check exists, record the evidenced `N/A` instead of silently omitting the gate.
- **Module-aware qmllint:** the QML module's generated lint target or `qmllint` with its real import paths and type information; an isolated file with unresolved imports is not a valid pass.
- **Quick Test:** the project's Qt Quick Test executable or its registered test invocation, using the same QML modules and target configuration as the application.

Keep the command output as evidence. Use official [`qmllint`](https://doc.qt.io/qt-6/qtqml-tooling-qmllint.html), [Qt Quick Test](https://doc.qt.io/qt-6/qtquicktest-index.html), and [Qt Test best practices](https://doc.qt.io/qt-6/qttest-best-practices.html) as the command and test-design references.

## State matrix

Build the state matrix from the applicable changed journey and adjacent regression risk. Exercise every selected row with behavior checks; add visual inspection for a changed visual claim or an interaction with a visible-state/layout consequence.

| Surface/state | Required coverage |
| --- | --- |
| Core control | Normal, hover when supported, pressed, focused, selected/checked, disabled, and inactive |
| Transient/data | Popups/editors and empty, loading, and error states |
| Environment | Applicable localization including CJK/RTL/long text, target window classes or orientations, and representative supported DPR/display transitions |

Record a reason for every non-applicable state. Test keyboard, pointer, touch, pen, switch, and assistive-technology actions when supported against the same semantic outcome; interrupt motion and asynchronous state changes before also checking their settled state.

## Deterministic branded gallery

For a custom-painted or multi-identity Widgets surface with broad reusable presentation changes, add a deterministic client-pixel gallery; do not impose it on an ordinary native-adaptive change. Pin stable fixtures, component/window dimensions, Qt version, base style, locale, DPR, graphics backend, applicable states, themes or identities, and stable filenames. Generate the declared component-by-identity-by-state matrix, check its expected artifact count, and fail on clipping, overflow, or an unexpected scrollbar; retain the gallery as a CI artifact when CI supports it.

Keep Qt Test behavior and accessibility checks beside the gallery. An offscreen gallery is not native or accessibility evidence and cannot replace the real-target capture below. Exact pixel equality in a frozen equivalent environment may prove unchanged pixels; it does not prove visual quality, interaction correctness, or cross-platform parity.

## Capture contract

When a visual claim changes, or an interaction claim has a visible-state or layout consequence, capture the real target application built from the candidate revision in the named platform, style, theme, graphics backend, locale, and DPR. Wait for fonts, data, layout, transitions, and scene-graph presentation to settle, then show the exercised state rather than a replica or isolated mock. A narrow nonvisual change still needs real-target behavioral evidence for the affected claim, but it may do so without a decorative screenshot.

Use an OS-level capture for native window chrome, platform dialogs, IME/candidate UI, native menus, and separate-window popups. A `QQuickWidget::grabFramebuffer()`, `QQuickWindow`/client grab, offscreen renderer, virtual display, or headless image is functional evidence for the pixels it contains; **offscreen capture is not native evidence** and cannot verify surfaces outside that client/framebuffer boundary. If OS capture of a required target is unavailable, list that surface as unverified rather than substituting a browser or synthetic frame.

## `VISUAL_QA.md` fields

Create `VISUAL_QA.md` under the active evidence root for a visual claim or an interaction claim with a visible-state or layout consequence. For a narrow nonvisual change, record `VISUAL_QA.md: not applicable` with the reason in the run receipt and retain behavioral, accessibility, and regression evidence instead. When the file is required, fill every applicable field and mark unsupported fields not applicable with a reason:

```markdown
Platform:
Qt version:
Style:
DPR:
Locale:
Theme:
Graphics backend:
Capture method:
Window size:
Exercised states:
Findings/fixes:
Unverified surfaces:
```

For each artifact, identify the application surface and state it proves. Do not mark a finding fixed until the matching behavior check and recapture both pass.

## Screenshot interpretation

Compare screenshots only when platform, Qt version, style, theme, locale, DPR, graphics backend, capture boundary, and window dimensions are equivalent. A dimension mismatch is non-comparable, not a failed similarity score.

Pixel diffs and ranked hotspots are **screenshot guidance, never a verdict**. They direct human review toward clipping, stale state, palette drift, focus errors, or rendering changes; they do not decide pass/fail, excuse a visible defect, or prove interaction and accessibility. Record the human finding and confirm its cause in the running application.

## Qt exclusions

Lighthouse is not Qt proof. React Doctor, CSS compliance, and a browser viewport matrix do not prove Qt build, QML behavior, or renderer semantics. Use them only for the separately scoped Web owner of an embedded client or Qt WebAssembly target; never substitute them for Qt build/tests, Qt-owned interaction/renderer proof, or applicable native capture.

The Qt gate passes only when the applicable commands succeed, selected states are exercised, visual findings are fixed and recaptured when relevant, and every claimed but unverified target surface is disclosed.
