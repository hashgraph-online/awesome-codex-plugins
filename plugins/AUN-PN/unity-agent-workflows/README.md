# Unity Game Agent Workflows

[![Publish](https://github.com/AUN-PN/unity-agent-workflows/actions/workflows/publish.yml/badge.svg)](https://github.com/AUN-PN/unity-agent-workflows/actions/workflows/publish.yml)
[![npm](https://img.shields.io/npm/v/unity-agent-workflows.svg)](https://www.npmjs.com/package/unity-agent-workflows)
[![Codex Plugin](https://img.shields.io/badge/Codex%20Plugin-Unity%20Workflows-10A37F)](#install-as-a-codex-plugin)

[ภาษาไทย](README.th.md)

Codex plugin, Codex skill, and `npx` installer for AI-assisted Unity 2D game work.

Use it when an agent needs to touch real Unity project files but must first prove the path that actually controls what the player sees: local rules, project structure, scene/prefab references, runtime owner, mutation path, and validation.

| Surface                   | Name                    |
| ------------------------- | ----------------------- |
| npm package               | `unity-agent-workflows` |
| Codex plugin display name | `Unity Workflows`       |
| Skill name                | `unity-agent-workflows` |
| Skill title               | `Unity Agent Workflows` |

The core rule:

```text
No proof, no edit.
```

## Why Use It

Unity agents often fail in the same practical ways: they edit the nearest script, trust scene YAML that gets overwritten in Play Mode, pick the wrong duplicated object name, grow a large controller, or call a change "validated" after only checking syntax.

This plugin gives the agent a stricter workflow for Unity 2D projects:

- read project-local instructions before touching files
- preserve unrelated dirty work
- derive folders, namespaces, assemblies, scenes, prefabs, and content paths from the live repo
- prove runtime-visible owner chains before UI, HUD, scene, prefab, or gameplay edits
- route new C# responsibility to existing project owners instead of broad folders
- keep UI/safe-area/TMP/coordinate-space work tied to the real runtime hierarchy
- load deep reference files only when the current task needs them
- ask before spawning sub-agents unless the user already requested them in the same turn
- validate with the smallest useful check and report residual risk honestly
- require reference proof before cleanup or deletion

`runtime-owner proof` is this project's workflow heuristic, not a Unity API term. It is grounded in Unity's GameObject/Component model, serialized fields, prefab overrides, and runtime instantiation behavior.

## Workflow Steps

The plugin starts from the user's input, routes the task, then loops on proof until it is safe to patch or close out.

```mermaid
flowchart TD
    input["1. User input<br/>Unity task, screenshot, stack trace, or repo request"]
    invoke["2. Skill trigger<br/>explicit $unity-agent-workflows or implicit Unity workflow match"]
    context["3. Read context<br/>AGENTS.md, git status, structure maps, relevant docs"]
    classify["4. Classify task<br/>visible output, state flow, content, architecture, cleanup, validation"]
    refs["5. Load required references<br/>only the docs needed for this task"]
    prove{"6. Proof complete?"}
    inspect["Inspect deeper / probe runtime<br/>owner chain, source bounds, state steps, duplicate objects"]
    scope["7. Lock scope<br/>Routing Card, files allowed, files not touched, worker ownership"]
    patch["8. Patch smallest safe set"]
    validate{"9. Validation pass?"}
    fixloop["Fix validation issue<br/>or return probe plan if proof is still missing"]
    close["10. Close out<br/>changed files, proof, validation, residual risk"]

    input --> invoke --> context --> classify --> refs --> prove
    prove -- "no" --> inspect --> classify
    prove -- "yes" --> scope --> patch --> validate
    validate -- "no" --> fixloop --> prove
    validate -- "yes" --> close

    classDef step fill:#eef2ff,stroke:#7c3aed,color:#111827;
    classDef decision fill:#fef9c3,stroke:#ca8a04,color:#111827;
    class input,invoke,context,classify,refs,inspect,scope,patch,fixloop,close step;
    class prove,validate decision;
```

Step details:

1. **User input**: a Unity task, screenshot, stack trace, feature request, cleanup request, or validation request enters the agent.
2. **Skill trigger**: the skill runs from an explicit `$unity-agent-workflows` prompt or an implicit Unity 2D repo task that needs editing, validation, routing, runtime proof, state proof, asmdef/module safety, cleanup, or multi-agent coordination.
3. **Read context**: the agent reads `AGENTS.md` if present, `git status --short`, existing `UNITY_STRUCTURE.md` plus only the focused map that matches the task, and only relevant docs.
4. **Classify task**: the request is routed as visible output, state flow, content, architecture, cleanup, or validation.
5. **Load references**: `SKILL.md` selects the required reference files instead of loading every rule. `unity-validation.md` and `workflow-recipes.md` are deferred until validation/recipe context needs them.
6. **Proof loop**: if owner chain, overlay/dim source-bound proof, runtime numeric proof, or guided state-flow proof is missing, the agent loops back to inspect or probe runtime data.
7. **Lock scope**: the main agent names `Files allowed to touch`, `Files explicitly not touched`, and multi-agent ownership before workers patch. Sub-agents are not spawned until the user approves, unless the user already asked for them in the same turn.
8. **Patch**: edit the smallest safe file set only after proof is complete.
9. **Validation loop**: failed validation returns to proof/patch; missing runtime proof returns a probe plan instead of another guess.
10. **Close out**: report changed files, proof, validation, and residual risk.

## Install As A Codex Plugin

In Codex, open Plugins, choose Add marketplace, then use:

```text
Source:
https://github.com/AUN-PN/unity-agent-workflows.git

Git ref:
main

Sparse paths:
```

Leave `Sparse paths` empty.

The Codex marketplace metadata lives at:

```text
.agents/plugins/marketplace.json
.codex-plugin/plugin.json
plugins/unity-agent-workflows/.codex-plugin/plugin.json
plugins/unity-agent-workflows/skills/unity-agent-workflows/SKILL.md
```

After adding the marketplace, install or enable `Unity Workflows` from the Codex Plugins list.

## Install As A Local Skill

Install the skill payload with `npx`:

```bash
npx unity-agent-workflows
```

Install to both Codex and Claude-style skill folders:

```bash
npx unity-agent-workflows --target both
```

Preview without writing files:

```bash
npx unity-agent-workflows --dry-run
```

By default, the installer writes to:

```text
~/.codex/skills/unity-agent-workflows
```

If the target folder already exists, the installer backs it up with a timestamp before replacing it. The `npx` installer installs only the local skill payload; it does not add the Codex plugin marketplace entry.

Supported installer options:

```text
--target codex|claude|both
--codex
--claude
--all, --both
--dest <path>
--dry-run
--no-backup
--help
--version
-h
-v
```

### Optional skills.sh Discovery

The public skill listing can be inspected with:

```bash
npx skills add AUN-PN/unity-agent-workflows --list
```

Install the skill through `skills` for Codex with:

```bash
npx skills add AUN-PN/unity-agent-workflows -a codex -y
```

## Quick Start

Inside a Unity 2D repo, invoke the skill:

```text
$unity-agent-workflows. Teach
```

`Teach` is a Codex skill instruction, not an npm CLI command. Use it when onboarding a new Unity project, when `UNITY_STRUCTURE*` maps are missing or stale, or when the user explicitly requests a structure refresh. When the agent follows it, it creates or refreshes a short structure index and focused maps only where useful:

```text
UNITY_STRUCTURE.md
UNITY_STRUCTURE.ui.md
UNITY_STRUCTURE.runtime.md
UNITY_STRUCTURE.content.md
UNITY_STRUCTURE.assemblies.md
UNITY_STRUCTURE.cleanup.md
```

Because `Teach` writes files, ask for a read-only pass first when you only want analysis:

```text
Use $unity-agent-workflows.
Do not edit yet. Inspect the project structure and report the proposed UNITY_STRUCTURE map plan.
```

Later tasks should read only `UNITY_STRUCTURE.md` plus the focused map that matches the work. They should not run `Teach` again unless a needed map is missing or stale.

| Task                                                                 | Read                                                  |
| -------------------------------------------------------------------- | ----------------------------------------------------- |
| UI, HUD, menu, safe area, TMP, visible target                        | `UNITY_STRUCTURE.md`, `UNITY_STRUCTURE.ui.md`         |
| Runtime behavior, scene objects, interactions, abilities, objectives | `UNITY_STRUCTURE.md`, `UNITY_STRUCTURE.runtime.md`    |
| Balance, localization, ScriptableObjects, config                     | `UNITY_STRUCTURE.md`, `UNITY_STRUCTURE.content.md`    |
| New files, refactor, asmdef, namespace, dependency                   | `UNITY_STRUCTURE.md`, `UNITY_STRUCTURE.assemblies.md` |
| Deletion, cleanup, generated files, Resources/addressables           | `UNITY_STRUCTURE.md`, `UNITY_STRUCTURE.cleanup.md`    |

### Example Case: FTUE Sentinel Install Focus

The visible bug was a repeated FTUE Stage 5 Sentinel install focus mismatch. A normal non-plugin pass showed the Sentinel install tutorial text, but the focus ring stayed on the ship area instead of the live `ADD` button. The `Unity Workflows` pass forced main-agent scope lock, read-only sub-agents, runtime numeric proof requirements, and checker criteria before patching.

**Before using the plugin: the focus is still on the bottom Satellite/Sentinel navigation tab.**

![Before command: Sentinel menu tutorial text](assets/case-ftue-sentinel-before-plugin.png)

**Fix with `Unity Workflows`: the focus moves to the real Sentinel `ADD` button.**

![After Unity Workflows: ADD button focus](assets/case-ftue-sentinel-after-plugin.png)

**Attempt without plugin rules: the Sentinel install tutorial text appears, but the focus lands around the ship position instead of `ADD`.**

![Without plugin rules: wrong ship-area focus](assets/case-ftue-sentinel-without-plugin.png)

What the plugin changed:

- Treat the issue as a repeated visible-output failure.
- Ask before spawning sub-agents unless the user already requested them in the same turn.
- Keep sub-agents read-only until the main agent locks scope.
- Require runtime numeric proof before another focus/position patch.
- Check that the final focus target is the visible `ADD` button, not the ship area.

Example request:

```text
Use $unity-agent-workflows.
Fix the FTUE Stage 5 Sentinel ADD focus mismatch.
Main: lock scope, patch only after proof.
Sub-agent A: read-only state flow proof.
Sub-agent B: read-only ADD focus bounds proof.
Checker: verify ADD focus, state steps, and PASS/FAIL criteria.
Do not include private paths or session IDs.
```

## Workflow

The skill routes work through this sequence:

```text
1. Read local rules
2. Check repo state
3. Derive live project structure
4. Classify the task
5. Prove owner or route
6. Name the file boundary
7. Patch the smallest safe file set
8. Run useful validation
9. Close out with proof, validation, and residual risk
```

For visible Unity behavior, the proof chain is:

```text
visible object -> scene/prefab/reference -> script/component -> mutating method -> serialized/runtime override
```

If that chain is incomplete, the agent should inspect deeper or ask one focused question before editing.

## What It Covers

| Area                      | What the skill enforces                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Runtime-visible bugs      | prove the object, owner, mutator, and override path                                                           |
| UI/HUD                    | inspect hierarchy, anchors, safe area, `CanvasScaler`, TMP, and runtime builders                              |
| Visible targets           | resolve runtime bounds instead of guessing hardcoded coordinates                                              |
| Repeated visible mismatch | require runtime numeric proof before another coordinate, focus, layout, marker, or fallback patch             |
| Overlay/dim source bounds | reject overlay, mask, blocker, or spotlight surfaces as source bounds unless an explicit marker proves target |
| Coordinate conversion     | keep world, local, screen, viewport, canvas, camera, and safe-area spaces explicit                            |
| Guided state flows        | separate shown/clicked/opened/selected/equipped/claimed/completed/persisted before marking completion        |
| Multi-agent work          | ask before spawning, then lock Routing Card, file ownership, runtime proof, and checker gates before patches  |
| C# routing                | derive folders, namespaces, `.asmdef` files, dependency direction, and owner modules                          |
| Content changes           | prefer existing data/config surfaces when the project has them                                                |
| Validation                | use the smallest useful check and report exact command output                                                 |
| Cleanup                   | prove unused status through code refs, YAML/GUID refs, Resources/addressables paths, and runtime reachability |

## Reference Files

The main [SKILL.md](SKILL.md) stays short. Deeper workflow rules live in `references/` and are loaded only when the task needs them. This table is a catalog, not a preload list; agents should follow `SKILL.md` Required References and each reference file's own `Read` / `Load Extra Detail` guidance.

| File                                                                                   | Purpose                                                                      |
| -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| [references/ai-workflows.md](references/ai-workflows.md)                               | universal workflow, Routing Card, closeout shape                             |
| [references/project-structure-discovery.md](references/project-structure-discovery.md) | live Unity structure discovery and `UNITY_STRUCTURE.md` maps                 |
| [references/runtime-owner-proof.md](references/runtime-owner-proof.md)                 | core runtime-visible owner chain and lazy proof router                       |
| [references/visible-object-identity.md](references/visible-object-identity.md)         | competing visible owners and anti-anchoring checks                           |
| [references/multi-surface-visible.md](references/multi-surface-visible.md)             | menu/gameplay/preview/runtime surface proof                                  |
| [references/asset-source-lock.md](references/asset-source-lock.md)                     | asset variants, source IDs, and fallback locks                               |
| [references/screenshot-text-owner.md](references/screenshot-text-owner.md)             | visible text, TMP, and localization owner proof                              |
| [references/shared-caller-blast-radius.md](references/shared-caller-blast-radius.md)   | shared helper/factory caller blast-radius proof                              |
| [references/runtime-visible-output.md](references/runtime-visible-output.md)           | output hard stops and hardcoded layout guard                                 |
| [references/runtime-numeric-proof.md](references/runtime-numeric-proof.md)             | repeated visible mismatch numeric proof                                      |
| [references/serialized-persistence.md](references/serialized-persistence.md)           | scene/prefab serialized persistence proof                                    |
| [references/runtime-visible-targets.md](references/runtime-visible-targets.md)         | focus, highlight, click target, marker, and fallback rules                   |
| [references/target-bounds-catalog.md](references/target-bounds-catalog.md)             | UI, 2D world, VFX, safe-area, and TMP bounds choices                         |
| [references/coordinate-space-conversion.md](references/coordinate-space-conversion.md) | world/local/screen/viewport/canvas/camera/safe-area/RenderTexture conversion |
| [references/modular-architecture.md](references/modular-architecture.md)               | project-derived module boundaries, asmdef safety, hub gates                  |
| [references/unity-validation.md](references/unity-validation.md)                       | validation ladder, Unity/Bee/Roslyn notes, MCP checks                        |
| [references/ui-and-visual-assets.md](references/ui-and-visual-assets.md)               | UI layout, mobile readability, safe area, localization, visual asset gates   |
| [references/content-and-systems.md](references/content-and-systems.md)                 | data-first content and runtime system readiness                              |
| [references/cleanup-and-git.md](references/cleanup-and-git.md)                         | deletion proof, generated files, commit/push hygiene                         |
| [references/session-mining.md](references/session-mining.md)                           | turning old agent lessons into durable rules                                 |
| [references/workflow-recipes.md](references/workflow-recipes.md)                       | optional named recipes for common work patterns                              |

## Validate This Package

For this repository:

```bash
npm run sync:mcpmarket
npm run validate
npm run pack:dry-run
```

`npm run sync:mcpmarket` mirrors `SKILL.md`, `references/`, and `agents/` into:

```text
.claude/skills/unity-agent-workflows/
skills/unity-agent-workflows/
plugins/unity-agent-workflows/skills/unity-agent-workflows/
```

`npm run validate` checks package metadata, plugin manifests, mirrored skill payloads, README workflow coverage, reference links, JavaScript syntax, runtime numeric proof triggers, overlay/dim source-bound gates, guided state-flow gates, and multi-agent scope triggers.

For Unity projects using the skill, Unity Editor, Play Mode, Game view, device tests, batchmode builds, and project logs remain the authoritative validation path. Bee `.rsp` or direct Unity-bundled Roslyn checks are best-effort local compile smoke tests and can be stale after Unity regenerates project artifacts.

## Mathematical & Physics Invariants (World-Class Precision)

Heuristic guessing causes AI agents to fail in precision tasks. The workflow enforces closed-form mathematical equations and quantitative physics models grounded in international standards (ISO/IEC 25010, IEEE 29119, IEEE 754, Pascal VOC/COCO, ACM SIGGRAPH, AIAA):

1. **Perspective Projection Singularity ($w \le 0$) & Screen Border Clamp**:
   - Problem: Objects behind camera ($z_{\text{view}} \le 0$) flip screen coordinates $180^\circ$ backwards under standard `WorldToScreenPoint`.
   - Analytical Solution: Homogeneous coordinate clipping and ray-box border clamping to guarantee offscreen pointers/HUD arrows point towards the true target.
2. **Optical Axis Singularity Degeneracy Guard**:
   - Problem: Targets directly on the optical axis behind the camera ($x_v = 0, y_v = 0, z_v \le 0$) create zero-magnitude rays causing `NaN` in floating-point division.
   - Analytical Solution: Degeneracy guard assigns the canonical up vector $\mathbf{d} = (0, 1)^T$, clamping safely to top screen margin without `NaN`.
3. **Frustum Near-Plane 3D Bounding Box Parametric Clipping**:
   - Problem: Projecting 3D bounds when some vertices are behind $z_{\text{near}}$ causes perspective divide by negative numbers, exploding screen bounding boxes.
   - Analytical Solution: Parametrically clip 3D edges crossing $z = z_{\text{near}}$ ($t_{\text{clip}} = \frac{z_{\text{near}} - A_z}{B_z - A_z}$) before projecting (Blinn & Newell, Sutherland-Hodgman).
4. **CanvasScaler Logarithmic Scaling**:
   - $\text{scaleFactor} = (W_{\text{actual}} / W_{\text{ref}})^{1-m} \cdot (H_{\text{actual}} / H_{\text{ref}})^m$
   - Prevents 5%–15% layout drift across wide/ultrawide screens compared to naive linear interpolation.
5. **RectTransform Anchor Span Invariants**:
   - Stretched anchors require $\text{sizeDelta} = \text{targetSize} - \text{parentSpan}$, preventing UI dimension explosion.
6. **Kinematic Closed-Form Predictive Lead Intercept**:
   - Solves $(|\mathbf{v}_t|^2 - v_p^2) t^2 + 2(\mathbf{r} \cdot \mathbf{v}_t) t + |\mathbf{r}|^2 = 0$ for moving target turret/laser aiming with zero heuristic nudging.
7. **Intercept Degeneracy Fallback & Closest Point of Approach (CPA)**:
   - When target moves faster than projectile or $\Delta < 0$, computes CPA time $t_{\text{cpa}} = \max(0, -\frac{\mathbf{r} \cdot \mathbf{v}_{\text{rel}}}{\|\mathbf{v}_{\text{rel}}\|^2})$ to aim at closest pass point.
8. **True Proportional Navigation (TPN Guidance Law)**:
   - Command acceleration $\mathbf{a}_{\text{cmd}} = N \cdot V_c \cdot \boldsymbol{\omega}_{\text{LOS}}$ ($N \in [3, 5]$) for maneuvering targets (Zarchan, AIAA).
9. **Ballistic Trajectories Under Gravity**:
   - Exact elevation angle $\tan \theta = \frac{v_0^2 \pm \sqrt{v_0^4 - g(g x^2 + 2 y v_0^2)}}{g x}$ for low/high trajectory arcs.
10. **Ballistic Trajectories with Aerodynamic Linear Drag (Unity Rigidbody Damping)**:
    - Stokes drag $\frac{d\mathbf{v}}{dt} = \mathbf{g} - k\mathbf{v}$ with finite horizontal range limit $x_{\max} = \frac{v_{0x}}{k}$. Fails impossible shots before firing.
11. **Continuous Collision Detection (CCD)**:
    - Tunneling detection bound $\|\mathbf{v}\| \cdot \Delta t > D_{\min}$ and swept raycast/circlecast volumes.
12. **Quaternion Antipodal Shortest-Path Slerp (Anti-Flip Guarantee)**:
    - Checks $\mathbf{q}_1 \cdot \mathbf{q}_2 < 0 \implies \mathbf{q}_2 \gets -\mathbf{q}_2$ before interpolation, preventing violent $360^\circ$ inversion spins (Shoemake, SIGGRAPH 1985).
13. **Quaternion Small-Angle Nlerp Stability Threshold**:
    - When $\cos\Omega > 0.9995$, transitions from Slerp to Nlerp to avoid $\sin\Omega \approx 0$ division instability.
14. **Symplectic Euler Energy Conservation vs Explicit Euler Divergence**:
    - Semi-implicit Euler ($\mathbf{v}_{t+\Delta t} = \mathbf{v}_t + \mathbf{a}_t\Delta t, \mathbf{x}_{t+\Delta t} = \mathbf{x}_t + \mathbf{v}_{t+\Delta t}\Delta t$) used in PhysX preserves bounded Hamiltonian energy, avoiding the exponential explosion of explicit Euler.
15. **Quantitative Spatial Verification (IoU Metric)**:
    - Evaluates overlays against the Pascal VOC / COCO benchmark standard: $\text{IoU} \ge 0.95$ for pixel-perfect UI, and center offset $\le 1.0\text{ px}$.
16. **Unity 2D Orthographic Camera Viewport & World Projection Bounds**:
    - Orthographic camera projection with parallel lines ($w = 1$), half-height $S = \text{orthographicSize}$, and half-width $S \times \text{aspect}$. Exact screen-to-world mapping with zero perspective distortion.
17. **Camera.main.ScreenToWorldPoint 2D z-Distance Plane Invariant**:
    - Invariant: $\text{screenPoint.z} = z_{\text{target\_plane}} - z_{\text{camera}}$. Eliminates the 10-unit offset trap where raw $z=0$ puts world points on the camera plane ($z=-10$) rather than the gameplay plane ($z=0$).
18. **2D Pixel-Perfect PPU Snapping & Sub-Pixel Shimmering Elimination**:
    - Texel grid snapping $x_{\text{snap}} = \text{round}(x \times \text{PPU}) / \text{PPU}$ eliminates sub-pixel rendering jitter and sprite shimmering in retro/pixel art games.
19. **Box2D & Rigidbody2D Linear & Angular Drag Damping Dynamics**:
    - Discrete damping velocity dissipation $v_{t+\Delta t} = v_t \times \max(0, 1 - \Delta t \cdot d_{\text{linear}})$ under Symplectic Euler integration with exact finite stopping distance $S_{\text{stop}} = \frac{v_0 (1 - \Delta t \cdot d_{\text{linear}})}{d_{\text{linear}}}$ and unreachable target drag range barrier.
20. **2D Kinematic Predictive Lead Intercept in XY Plane**:
    - Closed-form 2D quadratic lead equation for moving targets with linear degeneracy guard ($A \approx 0$ when projectile speed matches target speed), solving exact intercept time $t^*$ and firing angle.
21. **2D Continuous Collision Detection (CCD) & Raycast2D Tunneling Bound**:
    - Solves the bullet-through-paper tunneling problem when $\|\mathbf{v}\|\Delta t > T_{\text{col}}$ via swept parametric raycast intersection $t_{\text{hit}} \le \Delta t$.
22. **2D Platformer Parabolic Jump Kinematic Apex and Landing Timing**:
    - Closed-form kinematic derivation of gravity $g = \frac{2h}{t_{\text{apex}}^2}$ and jump velocity $v_{y0} = \frac{2h}{t_{\text{apex}}}$ from designer height $h$ and time to apex $t_{\text{apex}}$, guaranteeing exact apex height and landing timing.
23. **2D Steering & True Proportional Navigation (TPN) in XY Plane**:
    - Commanded lateral acceleration $\mathbf{a}_{\text{cmd}} = N \cdot V_c \cdot \dot{\lambda} \cdot (-\sin\lambda, \cos\lambda)^T$ with signed line-of-sight angular rate providing restoring steering feedback for both CCW and CW rotations.
24. **2D Tilemap Grid-to-World Center Pivot Offset Invariant**:
    - World-to-cell floor mapping and $+0.5$ half-tile center pivot offset, preventing 1-tile off-by-one errors and collider snagging during A* pathfinding and tile queries.
25. **2D Separating Axis Theorem (SAT) Minimum Translation Vector (MTV)**:
    - Minimum overlap axis $\hat{\mathbf{n}}_{\text{mtv}}$ and penetration depth $\delta_{\min}$ across all candidate edge normals for rotated 2D OBBs and polygon colliders, resolving penetration with zero jitter.
26. **Unity 2D RectTransform in Canvas: Screen Space - Overlay vs World Space PPU Scale Invariant**:
    - Enforces `camera = null` in `ScreenPointToLocalPointInRectangle` for Screen Space - Overlay to prevent projection inversion errors, and enforces $\text{localScale} = (1/\text{PPU}, 1/\text{PPU}, 1)$ for World Space Canvases to prevent 100x layout blowout.

Run the physics and math precision benchmark:
```bash
npm run benchmark:physics
```


## Repository Layout

```text
unity-agent-workflows/
├── .agents/plugins/marketplace.json
├── .codex-plugin/plugin.json
├── .claude/skills/unity-agent-workflows/
├── plugins/unity-agent-workflows/
├── skills/unity-agent-workflows/
├── SKILL.md
├── README.md
├── README.th.md
├── package.json
├── agents/openai.yaml
├── assets/unity-workflows.png
├── bin/unity-agent-workflows.js
├── evals/skill-trigger-cases.json
├── references/
└── scripts/
```

## Limits

- Built for Unity 2D game projects.
- Does not replace Unity Play Mode, device testing, build validation, code review, or project-local `AGENTS.md`.
- Does not assume a fixed project structure.
- Does not make `runtime-owner proof` an official Unity concept; it is a guardrail workflow.
- Does not install the Codex plugin marketplace entry through `npx`.
- Public reuse and external contribution are allowed under the MIT License; see [LICENSE](LICENSE).

## Support

Report issues at:

```text
https://github.com/AUN-PN/unity-agent-workflows/issues
```

## License

MIT License.
