# Goal-Design Packet Input

Use this when `/discovery` receives `.agents/goal-design/<slug>` or any directory
containing `intent.md` and `driver.md`.

1. Run `scripts/check-goal-design-packet.sh <packet-dir>` before any research,
   planning, or pre-mortem work. A failing checker blocks Discovery.
2. Extract `intent.objective`, `why_it_matters`, `boundaries`, `bdd.scenarios`,
   `evidence_for_done`, and `hard_rules` into the six density fields.
3. Use `driver.candidate_beads[]` as candidate slice seeds for `/plan`.
4. Preserve scenario ids and names exactly (`S1`, `S2`, etc.); do not paraphrase
   them away in summaries or execution packets.
5. Record `intent.md`, `driver.md`, and the checker command under artifacts and
   evidence. The raw packet remains the source of truth.

The packet is an input to Discovery, not a replacement for `/plan`; Discovery
still crosses the `plan_slices` port with dense context and artifact links.
