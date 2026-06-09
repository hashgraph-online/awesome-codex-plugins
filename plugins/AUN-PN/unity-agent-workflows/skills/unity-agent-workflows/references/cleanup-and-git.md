# Cleanup And Git

## Source vs Generated

Source control should contain:

- source code
- scenes and prefabs intentionally edited
- source assets and `.meta` files
- asmdefs and project settings
- architecture docs

Usually exclude:

- `Library/`
- `Temp/`
- `Obj/`
- build output
- logs
- user settings
- generated `.csproj` and `.sln`
- editor/Bee cache output

Do not stage generated/cache churn with gameplay, architecture, or UI changes.

## Deletion Proof

Before removing files, prove unused status through:

- `rg` code references
- Unity YAML GUID references
- `.meta` GUID checks
- `Resources.Load` paths
- addressable/resource catalog paths
- prefab/scene references
- runtime factory/registry reachability
- graph evidence as supporting data only

An isolated graph node is not deletion proof by itself.

## Safe Cleanup Shape

Only run cache/source-control cleanup when Unity is closed and source/scene edits are separated.

```bash
git status --short
git rm -r --cached Library Temp Obj Builds Logs UserSettings 2>/dev/null || true
git rm --cached '*.csproj' '*.sln' 2>/dev/null || true
git status --short
```

Review the result before committing. If source files, scenes, prefabs, or `.meta` files appear unexpectedly, stop.

## Commit/Push Hygiene

- Check branch and remote before pushing.
- Do not include unrelated dirty files.
- Stage only the skill/project files you changed.
- If creating a GitHub repo from extracted lessons, default to private unless the user asks for public.
- Avoid copying proprietary project source or raw chat into a public skill. Convert lessons into generic workflows.
- After push, report branch, repo URL, commit hash, and any private/public status.
