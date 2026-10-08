# Choose role and source route

Role and route are separate decisions. The role follows the requested
deliverable; the route follows where the evidence lives and which access mode
the user selected. Check the pair against the sibling `routes.json` in this
skill's `references/` directory.

## Choose a role

| Requested result | Role |
| --- | --- |
| Inspect a bounded source for defects or review concerns | `reviewer` — review branch |
| Check stated claims, requirements, or acceptance criteria | `reviewer` — verification branch |
| Answer an analysis question | `advisor` — reasoning branch |
| Produce an ordered course of action | `advisor` — planning branch |
| Revise prose or document content | `editor` |
| Change software behavior or source code | `implementer` |

Read only `references/roles/<role>.md` for the selected role.

## Choose a source route

| Evidence and access | Route | Load |
| --- | --- | --- |
| User-supplied files or frozen evidence | `packet.inspect` | `references/packet.md` |
| Current workspace using default ZIP mode | `packet.inspect` | `references/packet.md` |
| Current workspace using explicitly chosen MCP | `local.review` for reviewer; `local.plan` for advisor; `local.implement` for editor/implementer | `references/local-tasks.md` when a grant or MCP mutation is needed |
| Exact GitHub repository, ref, or PR | `github.review` for reviewer/advisor; `github.implement` for editor/implementer | `references/github-routes.md` |

The role and route together determine the work. Do not infer permission from
the role name: the selected route and any required task grant determine what
can be written or run.

## Local access

ZIP is the default for local files. Codex builds a narrow packet, sends it to
ChatGPT, and applies any returned patch locally. ZIP needs no Connector, does
not start MCP, and never falls back to MCP. Read `references/browser.md` only
when the packet must be uploaded or the reply captured through the Codex
in-app browser.

Use MCP only when the user explicitly chooses it or asks for Connector
setup/update. Read-only workspace access does not authorize mutations. Follow
`references/local-tasks.md` for artifact writes, source writes, or named
validation.

Do not switch access modes automatically after an error. An
`alternative_route` in `routes.json` is only an option to present; use it only
after the user chooses it.

## GitHub

Pin the requested repository state to an exact commit. Keep GitHub
authorization and state separate from local workspace access. Do not combine
the sources, fetch between them, or synchronize changes implicitly.
