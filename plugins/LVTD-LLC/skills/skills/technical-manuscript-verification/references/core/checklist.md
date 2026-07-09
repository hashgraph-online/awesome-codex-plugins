# Technical Manuscript Verification Checklist

Use this checklist for a technical accuracy pass.

## Scope

- [ ] Verification scope is defined by chapter, artifact type, or risk area.
- [ ] Supported environments are named.
- [ ] Unsafe-to-test items are identified.
- [ ] Current-info dependencies are identified.

## Commands And Code

- [ ] Commands are complete and copyable only when safe.
- [ ] Destructive commands have warnings and context.
- [ ] Code snippets compile, parse, lint, or are marked illustrative.
- [ ] Config files are syntactically valid.
- [ ] Placeholders are consistent and explained.
- [ ] Expected outputs are included.

## Prerequisites And Environment

- [ ] Required tools, versions, accounts, domains, hardware, and permissions are stated.
- [ ] Secrets and credentials are handled safely.
- [ ] OS or provider variants are marked.
- [ ] Network, firewall, DNS, and port assumptions are explicit.

## Links And Current Info

- [ ] Links resolve.
- [ ] Primary-source links are preferred for volatile details.
- [ ] Pricing, policies, package names, UI flows, and APIs are current or flagged.
- [ ] Deep links are avoided when likely to rot.

## Reader Safety

- [ ] Data-loss risks are warned before the action.
- [ ] Public exposure and security posture changes are explicit.
- [ ] Rollback or cleanup exists where needed.
- [ ] Cost, quota, or irreversible account changes are called out.

## Visuals And Layout

- [ ] Screenshots match surrounding text.
- [ ] Diagrams match current terminology.
- [ ] Code blocks and terminal output remain readable in final format.
- [ ] PDF or print layout does not clip commands, URLs, or screenshots.

## Output

- [ ] Findings are ordered by reader risk.
- [ ] Each finding includes evidence and fix.
- [ ] Untested items are not implied to be verified.
- [ ] Items needing expert or beta-reader checks are separated.

## Red Flags

- "Works on my machine" is the only evidence.
- The manuscript assumes prior local state.
- Screenshots are the only verification.
- A security-sensitive instruction lacks rollback.
- A reader can follow all steps and still not know whether they succeeded.
