# Ownership and receipts

## Select the owner before the write

- Reuse the owner already chosen for this BrewPage origin, workspace and target. Prefer an appropriate connected account when the user did not select another owner. A connected account belongs to the MCP client. Keep OAuth tokens, browser sessions and code exchange in that client.
- For explicit account intent, use a compatible MCP connection and `requireAccount: true`. An unavailable or unapproved connection leaves the account operation pending. Present the host's Connect instructions or first-party consent when offered. A finished anonymous publication is never replayed or claimed during connection. An explicit new anonymous owner needs a route with neither bearer nor previously selected token.
- Reuse a workspace's one selected protected anonymous owner when the route supports it. If legacy history has several owners, ask once using nonsecret labels and select the requested record. Keep legacy rows and previous publications. Use proof only at the matching first-party API origin. An owner token can create more publications and manage those it owns. A private management link reaches its own item. An ordinary reader link provides reader reach.
- Keep verified legacy owner proof even when its reader is a first-party subdomain and its update endpoint is unavailable. Resolve unproven or ambiguous history before writing. A custom reader address alone does not establish a first-party owner API endpoint.
- For a targeted edit, use the exact `kind`, `namespace` and `id` from a private receipt or authorized inventory, or the recorded owner API endpoint. Pass a full management URL privately only to a tool that accepts it for this target. Never open it through a web reader, reconstruct it from a public link, or try alternate owners after a denied request. If proof is unavailable, request the original private receipt or equivalent owner authorization.

## Prepare for a new anonymous owner

Before an anonymous MCP create, verify the host's owner-only tool-result boundary or protected private handoff: the response can contain a reusable `ownerToken` and bearer `manageUrl` in tool text. Saving them to a protected file afterward does not protect a shared transcript. An established owner-only conversation can satisfy this check; use known context without repeating a settled privacy question. Without that boundary, select authorized REST with protected receipt handling before any write, or leave MCP-only intent pending. Keep the separate new-key storage and recovery requirements below.

Use an existing authorized private storage preference. Otherwise offer to save the new key before creating the publication. Name the BrewPage origin, this workspace, the actual vault or resolved private file location, who can read it, and what one owner token can do. Use the installed runner's protected store or a private delivery channel because a new key may be issued only once.

For example, in an owner-only interaction: “Save the new brewpage.app owner key for this workspace in `<resolved protected destination>`? Only `<authorized reader>` can read it. It lets you manage this owner's publications and publish more under the same owner.” For Claude plugin and generic POSIX stores, resolve the workspace's `.claude/brewpage-history.md`; its fallback receipt is `.claude/brewpage-recovery.json`. For OpenClaw resolve the working directory's `brewpage-history.md` and sibling `brewpage-recovery.json`. These are protected owner-only regular files with mode `0600`, ignored before the write. Use the host's actual destination and access rules.

If workspace history is declined, agree on a protected receipt file before the create. The REST runner takes `--no-save --receipt-dir '{receipt_directory}'` and writes `brewpage-recovery.json` with mode `0600`. Use an existing owner-only directory with mode `0700` outside the workspace and any Git repository. Pick a new location if the file already exists. Keep credential paths, raw token values, password values, and management URLs out of shared tool transcripts, content and logs. Use only a host-supported protected field or private file for supplied proof.

For an MCP receipt, use the authorized host vault or import the new owner key into the runner's workspace store. Import only when the host can put the actual key in an owner-only `0600` file without exposing it to shared output or shell arguments. Use the installed `{runner}` and single-quoted slots from the [REST runner](rest-runner.md). Pass the exact reader link and the official owner endpoint from the verified receipt identity.

```bash
bash {runner} owner-store --target '{owner_api_url}' --reader '{reader_url}' --owner-token-file '{owner_token_file}'
```

This command stores and reads back the local key without contacting BrewPage. A linked account or foreign deduplication winner supplies no new anonymous proof to import.

An owner-only runner recovery JSON is also accepted by `--owner-token-file`. Keep its exact proof, origin, target and reader identity together; `owner-store` verifies the matching target and reader. Only the exact validated protected local fallback can implicitly reconcile its operation. External proof imports leave pending unchanged; use explicit `owner-reconcile` below with the independently verified finding to close a missing-response operation.

After a confirmed write whose history save failed, use this read-only command through a verified owner-only channel. It reports the owner API target and reader link from the fixed protected workspace receipt.

```bash
bash {runner} owner-recovery --private-output
```

An unresolved fallback blocks another saved write. Restore protected history storage, then pass the actual fallback path as `--owner-token-file` to `owner-store`. Use the reported target and reader link. The runner consumes the matching workspace fallback after verified history readback. For a receipt written outside the workspace, supply that file directly with `--owner-token-file` on a future update or import it with `owner-store`.

## Reconcile an uncertain create

Use this advanced path only for a pending local create whose result is unresolved. Keep the write blocked while its outcome or ownership is unknown. If the matching protected fallback is available, use `owner-recovery` and `owner-store` above instead. These commands require a verified owner-only output channel.

```bash
bash {runner} owner-pending --private-output
```

The local result is `{"pending":[{"operationId":...,"request":...,"recordedAt":...,"localBinding":...,"receiptAvailable":...}]}`. A recorded `request` contains the exact official endpoint, method, API kind, namespace and `payloadSha256`, plus actual `passwordProtected` and `deliveryMode`, `uploadName` for files, and `stateSha256` when sent separately. Copy the entire request object without editing it. It contains no source content, credential or local file path. Treat its operation details as private.

`payloadSha256` fingerprints the submitted HTML/JSON envelope file, raw upload bytes or ZIP, not the rendered page or persisted server source. A site's separately submitted Page data declaration has its own hash; its entry remains in the exact endpoint. The local `operationId` is not sent to BrewPage and is not a server idempotency key. A reader link, raw owner key, current owner inventory or matching page appearance alone cannot identify the original lost attempt.

Proceed only after an operator actually verifies a first-party finding matched to that attempt. The helper makes no external lookup and cannot authenticate the finding: it records an explicit operator attestation, its reference and input digest. Never invent evidence, assert verification from this local record alone, or infer `no-write` because a publication was not found.

Through an already authorized private mechanism, place the resolution in an absolute, owned, non-symlink regular file named `brewpage-reconciliation.json`, mode `0600`. In a workspace repository, the selected file must be untracked and effectively ignored by Git. This reserved input cannot be uploaded. If protected input or actual external verification is unavailable, leave the operation pending.

| Resolution field | Required value |
|---|---|
| `schema` | `"brewpage-reconciliation-v1"` |
| `operationId` | Exact pending operation selected above |
| `outcome` | `"no-write"` for an actually verified absence of the write, or `"publication-owned"` for the verified completed write with recoverable owner proof |
| `request` | Entire exact request object for this operation; equality with its recorded local witness is mandatory |
| `evidence` | `{"source":"owner-verified-first-party","verifiedByOperator":true,"reference":"<actual bounded first-party finding reference>"}` only after that verification occurred |
| `receipt` | Required only for `publication-owned`: full actual receipt with `origin:"https://brewpage.app"`, official `ownerApi`, exact `readerUrl`, reusable `ownerToken`, typed `identity`, and `manageUrl` when present. If it includes `operationId`, it must match. Omit the receipt for `no-write`. |

Retain the request's original API kind and namespace. The only supported kind transition is a documented `POST /api/files` result published as an HTML page: for that independently verified `publication-owned` finding, add top-level `"routing":"files-to-html"`. Keep the exact original files request fingerprint and namespace, and supply the actual final HTML owner endpoint, identity and proof. Other routing values or kind mismatches are rejected.

```bash
bash {runner} owner-reconcile --operation '{operation_id}' --resolution-file '{resolution_file}' --private-output
```

An older opaque marker may have `request:null` and `localBinding:"unavailable"`. Only an independently verified operator match can resolve it: supply the actual externally established request, add top-level `"binding":"external-only"` to the same resolution schema, and append `--external-only` to the command. The result explicitly states that no local request witness existed. This records external attestation; it does not recreate a missing local witness. Do not use that flag for a recorded request.

Reconciliation sends no HTTP request, retry or create. After protected atomic journal/receipt readback, it clears only the selected marker and preserves other pending operations and owner history. Unknown outcomes, lost keys without recoverable proof, reader-only links, a raw key alone, and unverified or mismatched resolutions cannot clear the pending operation. Recording an attestation is not a server receipt and never replays the original write.

## Render the actual result

1. On a confirmed create or update, say what was done and give the exact reader `link`. Include the effective access, any applied Page data or domain result, and relevant notices regardless of credential storage status. For an unlisted page without a password, anyone with the link can open it. Use the response's actual listing and access information, including the runner's `VISIBILITY:` line, before calling it listed or password-protected. For an unknown outcome, reconcile that operation using the selected owner's receipt or inventory before trying again. An unrelated success does not resolve it.
2. In a private receipt, provide the actual `manageUrl` if authorized to display it. Label it private and explain it manages this publication. For signed ownership, say it is in the verified account's publications and give the returned private account management link when present. Signed ownership requires no anonymous key save.
3. For newly issued anonymous proof that was saved, confirm private readback before saying “saved” and name the protected destination in the private receipt. For verified reuse, say the existing owner key was used. Keep its value private and skip a new save prompt. Missing `ownerToken` on an update or a deduplicated response does not erase existing proof.
4. If a create succeeded while history was declined or could not be saved, say both facts. Confirm protected recovery when the runner reports `OWNER RECOVERY SAVED`. The JSON file retains the owner proof, private management link and exact publication identity. The runner keeps those capabilities out of stdout even with `--private-output`. Use the same file for recovery and keep the publication link. When a foreign deduplication winner lacks owner reach, provide the reader link and say management access was unavailable.

For an eligible hidden public publication, listing is a separate requested owner action. A private namespace needs a separately authorized public copy, with its previous link and visitor entries kept private. Password removal requires its own explicit decision. A shared receipt contains only authorized reader-facing details.
