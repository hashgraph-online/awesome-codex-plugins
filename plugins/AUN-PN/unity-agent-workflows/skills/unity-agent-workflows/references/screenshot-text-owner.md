# Screenshot Text Owner

Use when a screenshot, user wording, OCR, visible UI label, HUD text, menu text, tutorial text, localized string, TMP text, or runtime text styling points to a visible text target.

Do not patch by nearby class names, shared factories, style helpers, localization utilities, semantic UI guesses, or the first file that mentions a similar concept.

## Screenshot Text Owner Gate

Before editing, prove:

```text
visible screenshot/user text
-> exact visible string / localization key / text setter searched
-> active UI text object name
-> scene/prefab/runtime source
-> creator method
-> refresh/update writer
-> owning presenter/controller/component
-> serialized/runtime override
-> validation method
```

If the exact text/key is not searchable, inspect candidate UI builders and report candidates first. Missing creator or refresh/update writer is a FAIL for visible text edits.

Closeout for visible text fixes must include:

```text
Why this owner is runtime-visible:
Why nearby candidates are not owners:
Exact text/key searched:
Refresh writer checked:
Factory/helper touched? yes/no, with proven callsite:
```
