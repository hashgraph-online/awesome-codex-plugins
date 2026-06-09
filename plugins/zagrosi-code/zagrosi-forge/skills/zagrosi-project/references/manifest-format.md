# Project Manifest Format

`project-manifest.md` must start with this exact parseable block:

```markdown
<!-- SPLIT_MANIFEST
01-foundation
02-authentication
03-dashboard
END_MANIFEST -->
```

Rules:

- one split per line
- format: `NN-kebab-case`
- numbers start at `01` and are sequential
- lowercase letters, digits, and hyphens only
- keep the block before all prose

After the block, include:

- overview of the split strategy
- dependency graph or ordered list
- parallelization notes
- shared decisions and cross-cutting constraints
- exact next command for each split, for example:
  `Use $zagrosi-forge:zagrosi-plan on @planning/01-authentication/spec.md`
