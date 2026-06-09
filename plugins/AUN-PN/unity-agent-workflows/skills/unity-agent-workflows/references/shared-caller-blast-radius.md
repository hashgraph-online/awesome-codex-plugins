# Shared Caller Blast Radius

Use before editing any shared factory, helper, registry, bridge, global method, sprite/model selector, theme/style utility, localization provider, or reusable presenter dependency for one requested surface.

## Factory Is Not Owner Rule

Factories, builders, layout helpers, font/style helpers, localization providers, theme utilities, shared gameplay factories, sprite/model factories, registries, bridges, and shared UI primitives are dependencies by default.

Treat them as owners only after proving the visible runtime callsite uses them:

```text
visible target
-> owner presenter/controller/component
-> creator/update method
-> helper/factory callsite
-> helper output used by the visible object
```

If only the helper/factory is found, stay read-only or continue tracing callsites. Do not patch shared helpers to fix a single visible target until the target owner chain proves the helper participates in that runtime object.

## Shared Caller Blast Radius Gate

Required proof before editing:

```text
requested surface/object:
allowed runtime caller(s):
shared method/helper/factory:
all direct callers:
serialized/resource callers checked:
callers outside target surface:
existing behavior that would change:
surface-local API/adapter/branch plan:
validation:
```

If callers outside the requested surface exist, changing the shared method's existing behavior is a FAIL unless the user explicitly broadened scope. Prefer a surface-local API, adapter, option, or callsite patch that leaves existing callers unchanged.

For Unity, caller search must include direct C# references plus likely serialized/resource paths when relevant: scene YAML, prefab YAML, ScriptableObject references, `Resources.Load`, Addressables keys, runtime registrations, service locators, animation events, and UnityEvent bindings.

Closeout must state:

```text
Allowed runtime caller(s):
Callers outside target:
Shared behavior changed: yes/no
Why non-target surfaces are unchanged:
```
