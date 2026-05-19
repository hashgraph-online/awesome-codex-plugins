---
name: archive
description: Use at ship time to merge the spec into the living documentation, delete the staging spec and plan, and ask how to finish.
---
# living documentation

- `README.md` : project overview, what it is, who it's for, how to use it. Links to the technical specification.
- `docs/tech-spec.md` : main technical specification.
- `docs/specs/*.md` : created by splitting out details from the main spec if they are too bulky or complex. Reference by path from the main spec.

technical specification is declarations only (no narrative), with facts only, no interpretation or plans.

# Archive

`<gate>`Before proceeding: (1) verify `tdd`/`subagents` have completed all tasks listed in the plan; (2) confirm the user has provided explicit written approval.`</gate>`

1. **Create** or **Merge**  the living documentation file with `docs/staging/specs/YYYY-MM-DD-<topic>.md`'s content. Not simple copy-paste — merge the new spec content into the existing living spec, preserving the living spec's structure and any existing content that is still relevant. The new spec's content should be integrated into the living spec in a way that maintains coherence and readability.

`<gate>`  confirm the merged content with the user before delete staging spec and plan. ` </gate>`

2. **Delete** `docs/staging/specs/YYYY-MM-DD-<topic>.md` — content absorbed; Git has the history.
3. **Delete** `docs/staging/plans/YYYY-MM-DD-<topic>.md` — plans don't belong on `main`.
