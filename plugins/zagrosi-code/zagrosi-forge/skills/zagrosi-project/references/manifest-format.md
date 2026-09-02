# Manifest format

Start with sequential names:

```markdown
<!-- SPLIT_MANIFEST
01-foundation
02-dashboard
END_MANIFEST -->
```

Then use one table:

| Split | REQ | Depends on | Owns/boundary | Next command |
|---|---|---|---|---|

Each `REQ-*` has one owner. After the table, state execution order, safe
parallel groups, and shared sequencing once. Omit strategy prose. Command:

```text
Use $zagrosi-forge:zagrosi-plan on @{planning_dir}/01-foundation/spec.md
```
