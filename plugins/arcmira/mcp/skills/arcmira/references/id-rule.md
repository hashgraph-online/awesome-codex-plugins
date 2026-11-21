# The ID rule

ID RULE. Filters take verbatim ids only: entity ids look like ent_14, channel ids like UC-DRzaGnL_vtBUpCFH5M0tg (UC plus 22 characters), video ids are 11 characters or a YouTube URL. A name where an id belongs throws id_required before any network call. Resolve the name first, then pass its id:

```javascript
const r = await arcmira.resolve("Sam", { context: "the My First Million co-host" });
const e = r.best ?? r.suggested;          // a show: resolve with { type: "channel" }, use e.youtube_channel_id
if (!e) return { ask: r.ask };            // r.ask.options: [{ id, name, type, label }]
```

RESOLVE ANSWERS ONE OF THREE. best: the name means that row; use it and name it. suggested: no row is certain but one stands out (suggested.reason, suggested.evidence); use it and tell the user you assumed it, quoting the evidence ("Sam Altman, assuming the most mentioned Sam: 4,399 appearances, 11x the next"). ask: several rows fit and none stands out; return ask.options for the user to pick and stop, or check every option id against the data in one program (occurrences or momentum with all the ids) and answer per row, naming each. Resolve the exact name the user said ("ICE", "Mercury"), not a paraphrase, and always pass context with the user's own words about the name when they gave any ("Sam, the My First Million co-host" is resolve("Sam", { context: "the My First Million co-host" })). Context is only words from the user's message, never your own guess: a bare "Theo" is resolve("Theo") with no context, never "Theo Von" or context "the comedian", and its ask goes back to the user. Omit type for a brand (the catalog types some companies as product). A name that resolves to nothing (no best, suggested or ask) is not in the Arcmira index: say so and ask for another spelling or a link; never answer for a different entity without saying so. Always say in the answer which entity you used.
