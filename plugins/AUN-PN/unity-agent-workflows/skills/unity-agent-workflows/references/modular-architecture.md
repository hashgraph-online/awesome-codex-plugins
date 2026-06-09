# Modular Architecture

## Project-Derived Shape

Do not force a fixed `Core/Systems/Features` layout onto every Unity repo. First read `references/project-structure-discovery.md` and derive the user's live folders, namespaces, assemblies, scenes, prefabs, bootstraps, and content paths.

Use the repo's own structure as the target shape. If the repo already has architecture docs or `.asmdef` boundaries, those are the initial routing map unless live code proves they are stale.

## Sample Shape

This pattern is only a fallback/example for projects that already resemble it or when the user explicitly wants a migration target:

```text
Assets/Scripts
├── Core
├── Systems
│   └── <SystemName>
│       └── Contracts
└── Features
    └── <ModuleName>
```

Sample dependency direction:

```text
Core
  <- Contracts
  <- Systems
  <- Feature Modules
```

Sample rules:

- `Core` references no Systems, Features, or `Assembly-CSharp`.
- Contracts are implementation-free.
- Systems may reference Core, contracts, and lower-level acyclic systems.
- Systems must not reference Features.
- Features may reference Core, contracts, and documented implementation systems.
- Features must not reference sibling Features.
- Bootstrap/composition roots initialize through interfaces, contracts, or gateways.

## Placement Matrix

Translate this matrix into the repo's own names. For example, "feature" may be `Modules`, `Gameplay`, `Screens`, `Presentation`, or another project-local boundary.

| Change | Place | Avoid |
| --- | --- | --- |
| One module's runtime behavior | `Features/<ModuleName>` | `Core`, unrelated systems, sibling features |
| Reusable runtime service | Repo-local service/system/runtime owner path | Unrelated feature/module folders |
| Cross-feature interface/event/DTO | Repo-local contract/event/gateway boundary | Feature/module implementation folders |
| Generic primitive/utility | `Core` | Feature/system folders with runtime/content knowledge |
| Content/balance/progression data | ScriptableObject, content definition, config | Hardcoded branches inside hubs |
| Menu/lobby UI construction | Owning UI feature | Gameplay systems |
| Runtime UI/display | Owner feature/system that owns the runtime facts | Unrelated menu feature |
| App/screen/session state | State contracts plus thin owner publisher | Global polling manager |
| Analytics/telemetry | Analytics contracts/service plus shared storage | Feature-local file writer |
| Visual source asset | Asset workflow first | Procedural fallback in random code |

## Hub Stop Gate

Before closing any C# edit that adds or moves responsibility, check touched runtime owners.

Stop and split unless the user approves temporary debt when:

- A new `.cs` file is over 500 lines.
- A touched controller/manager/presenter/service is over 500 lines and the edit adds responsibility.
- A new/touched class appears as a God Node in the graph.
- A new/touched class has more than 80 graph edges.
- A controller owns multiple major responsibility groups:
  - spawn/registration/active list
  - tick/lifecycle
  - phase/state machine
  - action/ability scheduling
  - hit/damage/death resolution
  - visual creation/animation
  - resource loading/fallback art
  - UI/status text
  - audio/camera/presentation feedback
  - cross-system bridge calls

## Collaborator Choices

| Responsibility | Collaborator |
| --- | --- |
| Runtime state bucket | `<Feature>RuntimeState` |
| Action/ability timing | `<Feature>ActionScheduler` |
| Visual creation/fallback art | `<Feature>VisualFactory` / `<Feature>SpriteCatalog` |
| UI formatting | `<Feature>Formatter` / `<Feature>Presenter` |
| Spawn selection/budget | `<Feature>Spawner` / `<Feature>ActiveObjectBudget` |
| Active object list | `ActiveRuntimeSet<T>` or registry |
| Tuning numbers | profile, content definition, config, `[SerializeField]` settings |
| Cross-system call | contract, gateway, bridge, event payload |

## Asmdef Readiness

Before adding or tightening asmdefs:

- Match real `.asmdef` names and references from the repo.
- No direct sibling feature imports.
- No dependency on `Assembly-CSharp`.
- No system-to-feature reference.
- Contract assemblies have no implementation references.
- Feature modules reference only Core, contracts, and approved acyclic implementation systems.
- Unity serialized fields and `.meta` GUIDs stay stable after moves.
- Machine-readable dependency rules match real `.asmdef` files when the repo has them.

Useful check pattern:

```bash
rg -n "using .*\\.Modules\\.|ProjectName\\.Modules\\." Assets/Scripts
rg --files Assets/Scripts | rg '\\.asmdef$'
```

## Refactor Proof

A refactor is complete only when at least one proof exists:

- Removed dependency edge.
- Replaced direct module reference with contract/event/bridge/registry/service.
- Moved logic out of a hub into a focused collaborator with changed callsites.
- Reduced callsite coupling or global static reach.
- Tightened an asmdef boundary without breaking Unity serialization.
- Updated architecture docs to match actual dependency graph.
