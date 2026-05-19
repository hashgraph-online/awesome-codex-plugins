# Unity Validation

Use the smallest useful check. Validation should match the edited surface and risk.

## Validation Ladder

1. Text/metadata:
   - `git diff --check -- <files>`
   - Parse changed JSON/YAML/TOML when applicable.

2. C# compile:
   - Prefer Unity-generated Bee `.rsp` files matching the touched asmdef.
   - If `dotnet` is unavailable, use Unity-bundled Roslyn.
   - If Bee `.rsp` files are stale after moves, copy to `Temp/`, rewrite only stale paths for the check, and report that Unity must regenerate durable artifacts.

3. Graph/architecture:
   - Refresh or inspect graph when code changed and architecture proof depends on it.
   - Report God Node, edge gate, and largest touched `.cs` status for structural edits.

4. Runtime-owner:
   - For visible behavior, prove scene/prefab/component/mutator/override chain.
   - For runtime-built UI, validate the builder/presenter path, not only scene YAML.

5. Runtime visual:
   - Use Game view, Device Simulator, Play mode, captured visual output, or device build only when the task/risk justifies it.
   - State clearly when visual runtime validation was not run.
   - For repeated visible-output failures, include runtime numeric proof for source bounds, converted rect, and final drawn rect before another patch. `git diff --check`, C# compile, source inspection, and sub-agent review do not satisfy this proof.
   - For multi-surface visible behavior, validate every requested surface separately; preview/transition proof does not validate gameplay/runtime.
   - For sprite/model/animation state fixes, validate active asset/sprite/model name, selector/factory result, and fallback path.

## AI-Generated Unity Code Gate

Use this when reviewing or accepting Unity code written by an AI agent, especially new runtime behavior, generated helpers, lifecycle methods, input, physics, UI layout, scene loading, asset loading, or serialized fields.

Before closeout, check the code against the live project instead of generic Unity examples:

- Unity version and package APIs: avoid deprecated or version-mismatched APIs when a current API exists.
- Project input stack: do not mix legacy `Input.*` with the New Input System unless the repo already does.
- 2D vs 3D API: use `Rigidbody2D`, `Collider2D`, `Physics2D`, and 2D callbacks for 2D gameplay.
- Lifecycle phase: place initialization, subscription, physics, camera follow, UI layout reads, and teardown in the correct project/runtime phase.
- Runtime owner path: prefer the existing service, presenter, state owner, navigation owner, registry, or content definition over a new global lookup.
- Serialized fields: preserve field names when possible; use `FormerlySerializedAs` for safe renames; check prefab/scene overrides that may beat code defaults.
- Performance-sensitive loops: avoid repeated `Camera.main`, broad `Find*`, allocations, layout rebuild triggers, or Resources scans in hot paths unless the repo already proves it is acceptable.
- Asset/loading pattern: do not introduce `Resources.Load`, direct scene loads, or hardcoded paths when the project uses Addressables, registries, ScriptableObjects, gateways, or navigation services.

If the code compiles but any item above is unverified, report the missing proof instead of claiming the Unity behavior is validated.

## Common Commands

```bash
git diff --check -- <files>
rg --files Library/Bee | rg '\\.rsp$'
rg -n "error CS|warning CS" <log-file>
```

## Roslyn/Bee Pattern

1. Find `.rsp` files:

```bash
rg --files Library/Bee | rg '\\.rsp$'
```

2. Pick the response file matching the touched assembly, such as a feature/module/system asmdef.
3. Locate Unity Roslyn under the installed Unity editor.
4. Run the compiler from the repo root with the response file.
5. Report only actionable errors. Separate analyzer warnings or unrelated dirty-file failures from requested changes.

## Batchmode Guardrails

- Another open Unity editor can block batchmode. Report it as an environment blocker.
- Do not chase unrelated compile errors unless they block the requested proof.
- Do not edit `Library/`, Bee output, generated `.csproj`, or `.sln` as durable source fixes.

## Unity MCP Operational Checks

Use this when validation, hierarchy inspection, scene edits, prefab edits, or Play Mode proof depends on Unity MCP or another editor-assisted tool.

Before trusting MCP output:

- Confirm Unity Editor is open, the intended project is loaded, and the MCP server/listener is connected.
- If MCP fails, report the exact connection, timeout, or tool error. Do not replace MCP proof with guessed scene data.
- Confirm the active scene, loaded additive scenes, and current stage: normal scene, Prefab Mode, prefab asset, or prefab instance.
- Refresh or re-query the hierarchy before choosing object ownership, especially after entering Play Mode, loading scenes, spawning runtime clones, or changing prefabs.
- Distinguish Edit Mode object state from Play Mode runtime state. MCP hierarchy proof is not visual/runtime proof by itself.
- For visible fixes, validate the Game view, Play Mode, captured visual output, Device Simulator, or device build when the task risk requires it.
- For repeated captured-output failures, Play Mode, Game view, Device Simulator, Unity MCP/runtime query, or temporary runtime logs must provide concrete numeric values before another coordinate/focus/layout patch.
- For scene/prefab mutation, confirm the edit persisted to the intended asset or scene file and was not only a transient editor object change.
- If MCP is unavailable, narrow the task to file/source inspection or ask for an editor/session retry when runtime proof is required.

## Visible Output Checker Failures

Checkers must return FAIL for repeated visible-output patches when any of these are true:

- runtime numeric values for source bounds, converted min/max, and final drawn rect are missing
- cross-canvas or cross-root output lacks source canvas/root/camera/scaleFactor and destination canvas/root/camera/scaleFactor
- overlay/dim/mask/blocker output rects are used as source bounds without an explicit marker proof
- a multi-surface request proves only one surface or treats preview/transition proof as gameplay/runtime proof
- a sprite/model/animation change lacks active asset/sprite/model name, selector/factory result, or fallback proof

## Final Validation Report

Include:

- Command run.
- Pass/fail.
- Exact error text if failed.
- Whether failures are related to touched files.
- Residual risk if Play mode/Game view/device was skipped.
- For repeated visible-output fixes: whether runtime numeric proof was captured, and which values were missing if not.
- For multi-surface fixes: each requested surface and its validation result.
- For sprite/model/animation fixes: active asset/sprite/model name and fallback path.
