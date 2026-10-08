# Choose by the failure, not a fixed model ranking

Read live tool schemas for current availability, reference limits, aspect ratios, resolution and pricing. The observations below are dated evidence, not current model defaults or a market benchmark.

In the [September 10, 2026 AURORA editing runs](https://github.com/magichourhq/skills/tree/main/examples/aurora-edits), all five attempts used the same synthetic product reference through the signed-in web app:

| Observation | Practical response | What it does not prove |
| --- | --- | --- |
| Two Flux 2 Klein attempts requested square but returned 640×384 | Check downloaded dimensions. If the full product cannot survive a square crop, try a live-supported alternative within budget | That Flux always ignores aspect ratios |
| Qwen Edit with the same guided prompt returned 640×640 and a usable centered catalog composition | A model change can address an observed constraint failure without making the prompt longer | A general Qwen quality advantage or exact color preservation |
| Two Qwen vertical edits returned 360×640 but placed the cap above the required midpoint | Stop treating exact geometry as a prompt-only problem; compose an accepted source in a bounded panel if the brief permits | That the outputs passed the original strict placement requirement |
| A longer Flux prompt changed the bottle more than the simple baseline | Compare against the original after every edit; revert rather than inheriting drift | That more instructions reliably improve quality |

For a new task, choose a currently supported route that fits the input and required operation. Inspect one authorized output before expanding a batch. If it fails, name the failed criterion and change one relevant variable when practical: model for unsupported behavior, source for identity problems, compositor for coordinates. Count every failed attempt toward budget and cost-to-accepted-output.

We have not tested these observations through an installed agent's authenticated creation MCP, or established portrait, cleanup, long-video, premium-model, or customer-revenue results. Keep untested routes provisional; do not generalize one product example into a quality guarantee.
