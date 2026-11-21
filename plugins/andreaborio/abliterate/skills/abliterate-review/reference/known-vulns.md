# Known vulnerabilities

Two ways to anticipate a bug from vulnerabilities that are already known:
1. **Dependencies**: a package version with a published advisory.
2. **Variants**: code that repeats a pattern some fix already removed, here or upstream.

## Dependencies: `abliterate deps --changed --base REF`

For each resolved package version from the lockfiles, the engine queries OSV and adds:
- the CISA KEV flag (exploited in the wild);
- the EPSS probability;
- a reachability verdict per advisory.

| `reachability.verdict` | Meaning | What to do |
| --- | --- | --- |
| `symbol-used` | The package is imported and a function the advisory names is called | Open each `symbolUses` location. Trace the arguments: is the attacker-controlled part of the call the one the advisory describes? If yes → `confirmed`, `source: "deps"`. |
| `imported-symbol-not-seen` | Import observed, no matching call seen in the inspected files | Check dynamic access, re-exports and wrappers. If the path remains unresolved, record the missing evidence. |
| `imported` | Imported; the advisory names no function | Read the advisory to identify the vulnerable feature, then search for it. Unresolved → `needs-evidence`. |
| `not-imported` | No matching import observed in the inspected files | Check indirect imports, transitive dependencies and build or deploy tooling before determining reachability. |
| `unknown` | Ecosystem without import mapping | Search manually. |

Rules:
- **Priority:** KEV first, then EPSS (higher = more likely to be exploited soon), then advisory severity.
- **Introduced vs pre-existing:** `introduced: true` means the change added or bumped the package. A vulnerable version present before the change is `pre-existing` unless the change starts calling the vulnerable function.
- **The fix:** the minimal upgrade to `fixed`. If the fixed version is a major bump, say so, and propose the smallest safe range.
- **Never confirm from the version alone:** the advisory must apply to how the code uses the package.
- **Incomplete runs:** if `complete` is false or there are network notes, say which packages went unchecked.

findings.json entry for a dependency:

```json
{ "source": "deps", "location": { "path": "package-lock.json", "startLine": 12 },
  "advisory": { "id": "GHSA-35jh-r3h4-6jhm", "aliases": ["CVE-2021-23337"], "ecosystem": "npm", "package": "lodash", "version": "4.17.20", "fixed": "4.17.21", "kev": false, "epss": 0.2 },
  "trace": [{ "path": "src/render.js", "startLine": 5, "note": "_.template called with request-controlled options" }] }
```

## Variants: `abliterate variants`

| Seed | Command | Use when |
| --- | --- | --- |
| This repo's history | `variants --history --base REF` | Every review: past security fixes reveal the patterns this codebase gets wrong |
| A fix you just confirmed | `variants --from <fixing-commit-sha>` | After a fix: find its siblings before calling it done |
| An advisory | `variants --from GHSA-…` or `CVE-…` | The user names a CVE, or a dependency advisory describes a misuse pattern |
| An upstream fix | `variants --from https://github.com/o/r/commit/<sha>` | A similar project fixed a bug in code you copied or mirror |

What a seed contains:
- the rule the removed code violated;
- the guard calls the fix introduced (`escape`, `safe_join`, a scoped query).

Each variant is a place where that rule fires without that guard. Then:
1. Confirm the variant reaches attacker-controlled data. Shape seeds (`rule: shape:…`) are weaker: read them critically.
2. `changedIn` set → introduced by this change. `null` → pre-existing sibling of a past fix, which is still worth reporting separately: it is the bug the earlier fix missed.
3. Use the original fix to identify the relevant data contract. Check that the sibling receives user-controlled data and that the omitted guard matters on its path. A shared contract can establish this for multiple callers. If the contract or caller is missing, record the specific evidence needed.
4. When an advisory's fix is internal to a library, the engine falls back to its CWE class. That sweep finds the same class of bug in application code; it does not prove the library flaw is reachable.
