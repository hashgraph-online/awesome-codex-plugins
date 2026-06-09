# Architectural Depth — Lens for Roasting

Architectural lens inspired by John Ousterhout's "A Philosophy of Software Design" and Michael Feathers' notion of *seam*. Use during a roast when the task involves **architecture, refactoring, testability, module depth**.

**When to apply**: roasts of a project / module suffering from "many small files doing little", "hard-to-write tests", "repeated bugs that don't concentrate in one place", "code that changes in 8 files for one fix".

**When NOT**: roasts focused on style/naming/tooling — use a different lens.

## Glossary (use these terms exactly)

This is the spine of the feedback. Use these terms in the roast — don't drift into "component", "service", "generic API", "boundary".

- **Module** — anything with an interface and an implementation (function, class, package, cross-cutting slice). Scale-agnostic.
  *Avoid*: unit, component, service.

- **Interface** — everything a caller must know to use the module correctly. Types, invariants, ordering, error modes, required configuration, performance characteristics.
  *Avoid*: API, signature (too narrow — they refer only to the type-level surface).

- **Implementation** — the body of code inside the module. Distinct from *Adapter*: a thing can be a small adapter with a large implementation (a Postgres repo) or a large adapter with a small implementation (an in-memory fake).

- **Depth** — leverage at the interface: the amount of behavior a caller (or test) can exercise per unit of interface they have to learn. A module is **deep** when a large amount of behavior sits behind a small interface. **Shallow** = interface nearly as complex as the implementation.

- **Seam** *(Michael Feathers)* — a place where you can alter behavior without editing in that place. *The location at which a module's interface lives.* Choosing where to put the seam is its own design decision, distinct from what goes behind it.
  *Avoid*: boundary (overloaded with DDD's bounded context).

- **Adapter** — a concrete thing that satisfies an interface at a seam. Describes *role* (which slot it fills), not substance (what's inside).

- **Leverage** — what callers get from depth. More capability per unit of interface they have to learn. One implementation pays back across N call sites and M tests.

- **Locality** — what maintainers get from depth. Change, bugs, knowledge, and verification concentrate in one place rather than spreading across callers. Fix once, fixed everywhere.

## Diagnostic principles (use in the roast)

### The deletion test
Imagine deleting the module. If complexity vanishes, the module was a pass-through (it wasn't earning its cost). If complexity reappears across N callers, the module was earning its keep.

**How to apply during a roast**: for each "suspiciously shallow" module (interface complexity ~ implementation complexity), hypothesize deleting it. If callers absorb complexity, leave it alone — it's a weak but real seam. If complexity vanishes, it's a useless pass-through to inline.

### The interface is the test surface
Callers and tests cross the same seam. If you want to test *past* the interface (private methods, internal state), the module is probably the wrong shape.

**Roast signal**: tests that mock internal dependencies, tests that inspect private state, tests that break after a refactor that didn't change behavior — interface too narrow or seam in the wrong place.

### One adapter = hypothetical, two adapters = real
Don't introduce a seam unless something actually varies across it. A seam with only one implementation is speculation, not leverage.

**Roast signal**: an interface + 1 implementation, no fake/mock/alt-impl, no concrete roadmap for a second — drop the interface, use the concrete type.

### Depth is a property of the interface, not the implementation
A deep module can be internally composed of small, swappable, mockable parts — they just aren't part of the interface. A module can have **internal seams** (private to its implementation, used by its own tests) as well as the **external seam** at its interface.

## Friction signals (what to look for in the codebase)

Explore the codebase organically. Note where you feel friction:

- Understanding one concept requires **bouncing between many small modules**? → modules too shallow, decomposition wrong.
- **Shallow** modules: interface nearly as complex as implementation? → candidates for deepening or inlining.
- Pure functions extracted just for testability, but real bugs hide in **how they're called** (no locality)? → seam in the wrong place.
- Coupled modules **leaking past their seam** (callers must know internal facts)? → the interface is not the real seam.
- Parts of the codebase **untested or hard to test** through the current interface? → wrong depth/shape.

For each, apply the **deletion test**: would deleting the module concentrate complexity (signal "keep, deepen") or scatter it (signal "inline")?

## Roast output (format)

For each architectural candidate presented:

- **Files** — modules/files involved.
- **Problem** — why the current architecture causes friction (use the glossary above).
- **Diagnosis** — current depth, where the real seam lives, why it's shallow / mis-placed.
- **Refactor direction** — what would change (plain English, not implementation). How much leverage and locality is gained.
- **Tests that would improve** — tests that are hard today and would become natural.

**Do not propose concrete interface signatures at this stage.** That comes later, in refactor planning. Here you only *flag the friction* so the owner decides which candidate to explore.

## Rejected framings (do not use)

- **Depth as ratio of implementation-lines to interface-lines** (Ousterhout's original): rewards padding the implementation. Use **depth-as-leverage**.
- **"Interface" as the TypeScript `interface` keyword or a class's public methods**: too narrow. Interface here includes every fact a caller must know.
- **"Boundary"**: overloaded with DDD's bounded context. Say **seam** or **interface**.

## Cross-link

- Designing new interfaces (Design It Twice): `brainstorming/references/design-it-twice.md`.
- TDD through the public interface: `create-test/references/tdd-workflow.md`.
