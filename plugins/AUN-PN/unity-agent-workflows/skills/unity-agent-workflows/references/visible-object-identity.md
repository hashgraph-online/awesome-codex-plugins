# Visible Object Identity

Use before Unity visual, model, sprite, source asset, prefab, or animation integration when the visible target may differ from the feature name, source asset, factory, semantic module, or first search result.

## Visible Object Identity Lock

Before editing, prove:

```text
user-visible target:
screen/scene/surface:
exact runtime GameObject name:
scene/prefab/runtime creator:
owner presenter/controller/component:
writer/update method:
asset/model/factory dependency:
nearby semantic owner candidates:
rejected candidates and reason:
validation:
```

If the user-visible target and semantic feature name disagree, stop before patching. Continue single-agent investigation only if you can reject competing owners with file-backed proof, or ask the user to approve read-only sub-agent discovery.

Example failure mode: the request mentions a gameplay unit, but the visible object is a menu preview object. Do not patch gameplay factories or contracts until the menu/runtime object, creator, writer, and factory dependency chain are proven.

## Single-Agent Anti-Anchoring Guard

Use before patching a visible/runtime Unity target when naming is ambiguous.

Required when:

- feature name, asset name, scene object, and visible surface do not point to the same owner.
- the first candidate is a factory/helper/registry/bridge/global selector.
- search results show both scene/prefab objects and feature code owners.
- the requested object appears in multiple UI surfaces.

Required output before edit:

```text
primary candidate:
competing candidates:
why primary is runtime-visible:
why rejected candidates are not owners:
proof still missing:
```

If competing candidates cannot be rejected with file-backed proof, do not patch. Ask to continue single-agent investigation or to use read-only sub-agent discovery.
