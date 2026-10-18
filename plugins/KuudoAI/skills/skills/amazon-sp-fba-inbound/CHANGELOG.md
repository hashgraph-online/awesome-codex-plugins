# Changelog

All notable changes to this skill are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com). Versions are semver and must
match `metadata.version` in SKILL.md.

Bump rules:

- **patch:** non-behavioral changes (typos, formatting, reference-only
  edits).
- **minor:** behavioral additions (new sections, rules, triggers).
- **major:** contract changes (response shape, output format, scope).

Every bump also updates the `evals/evals.json` `skill_version`.

## [0.2.1] - 2026-10-17

### Changed

- Replaced Unicode ellipses with ASCII `...` in SKILL.md. Security scanners normalize Unicode and read the changed text as obfuscation; wording and behavior are unchanged.

## [0.2.0] - 2026-10-17

### Added

- **Data, not instructions.** A new first guardrail treats every API
  response and error as data: plan and shipment names, option and carrier
  text, addresses, `operationProblems[]` messages, error strings,
  eligibility, prep, and compliance reasons, and `list_identities` labels.
  It also covers box files the seller uploads. An embedded instruction never
  picks an option, counts as a yes or `CONFIRM`, or decides the next call;
  the skill flags it to the seller instead.
- **Show, then yes.** Before `createInboundPlan`, `confirmPackingOption`,
  `setPackingInformation`, `updateShipmentTrackingDetails`,
  `updateShipmentSourceAddress`, `setPrepDetails`,
  `updateItemComplianceDetails`, and the two rename calls, the skill shows
  the exact call, including the merchant ID, and waits for an explicit yes
  in the seller's next message. A pick from options shown in full counts as
  the yes for `confirmDeliveryWindowOptions` and
  `scheduleSelfShipAppointment`. `cancelSelfShipAppointment` gets its own
  ask.
- **Retry rule.** A retry that changes anything (option ID, amount,
  selection, box or address data) needs a fresh yes or `CONFIRM`. After a
  5xx, the skill reads the plan before retrying.
- Evals 5 (single fee-free packing option plus box data stop for a yes),
  6 (an instruction in a plan name is flagged and ignored), and 7 (a
  `CONFIRM` sent before the restatement doesn't count).

### Changed

- **Gate table.** The catch-all row "Everything else (creates, sets,
  generates, reads) | Reversible, no fee, or read-only | Proceed" is replaced
  by a per-call classification. Only the `generate*` calls,
  `createMarketplaceItemLabels`, and reads run without asking. Server
  selection calls run only for the seller the user named.
- **Single fee-free packing option.** It is no longer confirmed with a
  notice; the skill shows it and waits for a yes. This and the gate table
  resolve a contradiction between the description ("Pauses at every
  fee-charging or irreversible step") and the body, which proceeded on
  writes it called permanent (box data, compliance details). The safer
  description wins.
- **`CONFIRM` timing.** The typed `CONFIRM` must come in a later message
  than the restatement. One in the original request doesn't count.
- **Server authority.** Tool descriptions and `get_schema` are authoritative
  only for tool names and argument names, types, and shapes. They never
  relax a gate (tool-access.md, SKILL.md section 1, request-shapes.md).
- **Failed writes.** Fixes after a `FAILED` operation or a rejected confirm
  come from the seller's data, not from the error text
  (operations-and-limits.md, tool-access.md, carriers-and-shipping.md).
- Eval 0 now expects a preview and a stop before `createInboundPlan`; the
  original request is not the yes. Its pack-first and status-check
  assertions moved to eval 5.

## [0.1.0] - 2026-09-24

### Added

- First KuudoAI release. Adapted from the Amazon Selling Partner
  `fba-inbound-management` skill (Apache-2.0) and substantially rewritten to
  work with a code-mode SP-API MCP server. The rewrite was verified against the
  Fulfillment Inbound v2024-03-20 OpenAPI model and Amazon's use-case guides.

### Changed (compared with the upstream skill)

- **Tool resolution.** The skill now resolves tools by `operationId` through
  server discovery, instead of hard-coding the `fbaInbound_*` names. On a
  code-mode server the names are `fba-inbound_<operationId>` and
  `fulfillment-inbound-v0_<operationId>`.
- **No `entityId`.** The skill no longer asks for or passes `entityId`. The
  seller comes from the server's active identity, and the marketplace is
  passed only where an operation takes one.
- **Pack-first order.** Corrected to: generate and confirm the packing
  option, then `setPackingInformation(packingGroupId)`, then placement.
- **Transport quotes before placement.** Transportation is quoted for a
  candidate placement *before* placement is confirmed, following Amazon's
  documented flow. The seller sees the placement fee and the carrier quote
  together.
- **Transportation inputs.** Corrected to `readyToShipWindow.start`, plus
  contact, pallets, and freight info where needed. There is no ship-from
  field.
- **Delivery windows.** The decision now keys off each option's
  `preconditions` (`CONFIRMED_DELIVERY_WINDOW`) rather than a program
  enrollment.
- **Fees.** Now net `fees[]` minus `discounts[]`, in the returned currency,
  instead of "dollars".
- **Void windows.** Now read from `quote.voidableUntil` instead of hard-coded
  hours.
- **Pack Later.** Corrected to `setPackingInformation(shipmentId)` after
  placement, with any content source (`MANUAL_PROCESS` carries a fee).
- **Self-ship appointments.** Documented beyond India (MX, BR, EG, SA, AE).
- **Polling.** Now sized for code mode: chain the write, one status check,
  and the follow-up reads in one `execute` block. Re-check across calls, cap
  at about five checks, and read `operationProblems[]`.

### Removed

- The non-existent `updateBoxIdentifiers` operation.
- The 500K-units-per-SKU limit. The real limits are 1,500 SKUs and 10,000
  units per SKU per plan.
- The claim that `setPrepDetails` sets owners. It sets prep category and
  types.
- Non-spec frontmatter: the top-level `version` key and list-valued
  `metadata`.

### Validated live

- Validated read-only against a live SP-API MCP server. The code-mode
  specifics now match it: three meta-tools with no `tags`;
  a required `set_active_identity`; plain-string errors; `entityId` silently
  ignored; 403 when a seller lacks inbound access; AWD plans in
  `listInboundPlans`; `get_schema` needs `detail="full"`.

### Fixed after live smoke testing

- **Plan status overviews** now read `SHIPPED`-status plans as well as
  `ACTIVE`. Once shipments leave, the plan moves to SHIPPED, so an
  ACTIVE-only overview missed everything in transit or being received.

### Fixed from PR review

- **`MANUAL_PROCESS` gate.** `setPackingInformation` with a
  `MANUAL_PROCESS` box now requires a typed `CONFIRM`, because Amazon
  charges a manual-processing fee. The skill offers `BARCODE_2D` and
  `BOX_CONTENT_PROVIDED` as fee-free alternatives.

### Also added

- Request shapes for every write.
- A tool-access guide.
- `getBillOfLading` for partnered pallet shipments.
- Status enums and rate limits.
- Content-update limits.
