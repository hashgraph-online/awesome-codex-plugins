---
name: tokenchronicle-feedback
description: Help a user review, save, export, or explicitly submit TokenChronicle product feedback without including private Codex conversations.
---

# TokenChronicle Feedback

Resolve the plugin root and prefer its exact matching signed executable under
`bin/<platform>/tokenchronicle/`;
if an installed plugin has no matching executable, report that the platform client has not been
published and stop. Never download or substitute a binary.

Run the read-only `readiness` command first. If TokenChronicle is not initialized, switch to guided
setup before opening or configuring feedback. Never describe feedback activation as product or daily
archive activation.

1. Direct the user to the Feedback tab in the local TokenChronicle viewer.
2. Confirm that the preview contains only product version, source page, category, optional rating, message, and timestamp.
3. Do not attach conversation content, timelines, thread identifiers, project paths, memory content, or credentials.
4. Save a local draft or export its JSON after the user reviews the preview.
5. Network submission is allowed only when an HTTPS receiver and a private installation credential are
   configured and the user confirms that individual payload.
6. Activate with a one-time invitation file or configure a token file. Never place either secret on the
   command line, print it, copy it into a report, or store it in the plugin directory.
7. Never enable background submission, reuse an earlier confirmation, or attach context automatically.
