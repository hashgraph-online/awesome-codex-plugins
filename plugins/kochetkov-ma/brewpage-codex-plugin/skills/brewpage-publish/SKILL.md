---
name: brewpage-publish
description: "Prepare BrewPage drafts, publish supplied content or a new page, and update a specific BrewPage publication. Supports HTML, Markdown, JSON, files, built sites, and forms with saved visitor answers. Keeps the private owner key of an anonymous publication so its owner can edit or delete it later: saves it to the workspace file brewpage-history.md, recovers it from a local receipt, and reconciles an interrupted create. Its bundled runner talks only to brewpage.app. Use for BrewPage, share this as a link, publish site, RSVP, poll, черновик BrewPage, опубликуй, обнови страницу."
homepage: https://brewpage.app
user-invocable: true
license: MIT
---

## Prompt contract

Use the owner’s free-form RU/EN prompt. Keep supplied material intact and resolve selected paths against the workspace.

Resolve the requested effect before matching keywords. An explicit no-publish or local-only instruction overrides mode words and defaults. Negated, quoted, instructional and incidental publishing words authorize no write. Explanation-only requests, like drafts, make zero BrewPage calls or tool discovery requests.

| Mode | EN keywords | RU keywords | Mutates? |
|---|---|---|---|
| `draft` | prepare a draft, preview, local only | подготовь черновик, предпросмотр, только локально | local only |
| `publish` | publish this, share as a link, upload this | опубликуй это, поделись ссылкой, загрузи этот файл | yes |
| `compose-and-publish` | create and publish, build and host | создай и опубликуй, сделай и размести | yes |
| `update` | update this publication, replace the page, edit in place | обнови публикацию, замени страницу, исправь на месте | yes |

1. Mode: separate flags from the request. An affirmatively requested explicit mode wins. Otherwise score distinct whole-word keywords only within the requested action. A tie with `draft` stays local. For two writing modes, use the first matched keyword. A direct invocation with supplied content defaults to `publish` only without a contrary instruction. An empty or ambiguous request needs scope before any write.
2. Scope: extract the material, exact requested text, target, changes and options. “Publish this draft” supplies material for a create. “Draft this for BrewPage” requests preparation only. A request to revise an existing local file does not identify a live publication.
3. Ask: ask once (up to four scope questions) for scope choices that change the work. Ask only for missing material, a missing exact update target, or an unresolved consequential choice. Drafts need no ownership or visibility questions.

Print once before the first action. Redact credentials, private management links and password values.

```text
PLAN — brewpage-publish
INPUT:  <request, or (empty)>
MODE:   <mode> — <explicit | matched keyword: X | default>
SCOPE:  <artifact or target and requested options>
DO:     <2–5 actions>
RESULT: <local artifact or confirmed publication outcome>
```

## Perform the requested work

1. **Draft:** prepare the requested local files or inline artifact. For a form, pair HTML with its Page data declaration from the [offline recipe](references/page-data.md). Return the artifact and how to use it. Stop here. Make zero BrewPage calls, tool discovery requests, owner lookups or domain changes.
2. **Publish or compose and publish:** preserve supplied content and exact requested text, including punctuation (`Ready.` → `<p>Ready.</p>`), unless edits were requested. MCP: explicitly public/listed publication → `namespace:"public"`; ordinary link-only → omit `namespace`. Receipts confirm listing eligibility; public input URLs alone request no listing. Use [publishing](references/publishing.md) for local input or other access choices and the [REST runner](references/rest-runner.md) for REST. Plain inline MCP HTML needs no publishing reference. Read [Page data](references/page-data.md) for requested visitor storage and [custom domains](references/custom-domain.md) for a requested owned hostname.
3. **Update:** use the exact target and selected owner; inventory only for unknown targets. MCP: a title-only rename of known HTML `notes/Agenda0001` calls `publication_settings({kind:"html",namespace:"notes",id:"Agenda0001",title:"New agenda"})` directly; hostname `domains(action=attach)`; saved entries `read_page_data` (private `manageUrl` alone or owner proof + target; collection if known). Use the supplied source or recover it through a permitted read of that item. Change only the requested fields or content. A full site replacement needs the complete desired file set and verified existing entry unless an entry change was requested; pass that entry explicitly to MCP. Leave replacement pending if it cannot be resolved. A content-only update keeps the address and existing visitor entries. A missing or read-only target requires a separate user decision before any new publication.

## Select one write route

Before dispatching MCP that can return an owner key or bearer management link, verify that the tool result reaches only the requesting owner or an authorized private handoff. Anonymous creates can include `ownerToken` and `manageUrl` in tool text; a protected file alone does not make that transcript private. Known owner-only host context can establish this boundary without another privacy question. Otherwise select authorized REST with protected receipt handling **before** writing, or leave an MCP-only request pending. New-owner storage or private recovery is still required.

- Prefer a BrewPage tool already exposed to this host session. If the host discovers tools on demand, use that interface once. Verify the BrewPage binding, actual tool schema, input and options, and the selected authority. Use compact `publish` or `update_publication` when supported. An advertised legacy operation is usable within its original schema. Supplied HTML requiring exact source needs preservation support; a legacy shape without it requires another authorized route selected before writing. For an ordinary inline HTML publish, call the suitable tool directly. A similarly named tool, a package install and an endpoint probe cannot establish a usable binding.
- Before serializing local files into tool arguments or a request, use the packaged local checks in [publishing](references/publishing.md) and the [REST runner](references/rest-runner.md). A local path is never a remote source URL. For unrepresentable bytes, missing MCP capability or absent BrewPage binding, select authorized direct REST **before** any write when the host and the same owner proof permit it. Explicit MCP-only intent requires a capable binding. If there is no authorized route, return the local result and the specific remaining step.
- Prefer a suitable already connected account when no other owner is chosen. For explicit account publishing, use `requireAccount: true` on the compatible MCP tool and follow the client’s first-party authorization flow. If unavailable or cancelled, leave the write pending. The MCP client alone handles OAuth. Use REST only if it supports the selected owner proof or the requested unsigned operation. Explicit fresh anonymity needs a route with neither bearer nor saved owner token. Setting `requireAccount` to false does not select that route.
- Honor host restrictions, denials, missing scope and rejected credentials. After a sent write times out, reconcile through the selected owner's inventory or receipt. Never switch transports or owners to repeat a sent or refused write. Use bundled recipes as data. Without a specialized path, compose locally and explain the missing capability. Fetch only a needed first-party guide or template for an authorized hosted workflow.

For the bundled runner, substitute this installed path for `{runner}` in the REST runner reference. Use the host shell tool only when permitted.

```text
{baseDir}/scripts/brewpage-run.sh
```

Runner commands: `probe`, `limits`, `stage`, `preflight`, `publish`, `update`, `cleanup`, and owner-key upkeep `owner-store`, `owner-recovery`, `owner-pending`, `owner-reconcile` ([ownership](references/ownership.md)). It sends HTTPS requests only to `https://brewpage.app/api/`, keeps working copies in a private `$TMPDIR/brewpage.*` run directory removed when the run ends or by `cleanup`, and writes only `brewpage-history.md`, `brewpage-recovery.json` (both mode 0600) and their `.gitignore` entries in the workspace. If the owner declines workspace history, it writes only `brewpage-recovery.json` (mode 0600) in the owner-chosen `--receipt-dir` instead. It needs `bash`, `curl`, `jq` and `python3`; local file and site checks add `node`, `zip` and `unzip`. Inline MCP publishing needs none of them.

The runner uses `brewpage-codex/0.2.2 (+https://brewpage.app)` for direct REST requests.

## Return the actual result

Before a first anonymous create, arrange authorized private storage or owner-only delivery of its key. Refer to [ownership and receipts](references/ownership.md) for owner selection, storage and recovery. Report the exact returned reader link, effective access and any consequential notice. Deliver the private management link and owner instructions only through a protected channel. An account-owned result goes to the account’s publications. For anonymous ownership, say “saved” only after private readback. A shared destination receives reader-facing details only. Report a live publication or update only from a confirmed receipt.
