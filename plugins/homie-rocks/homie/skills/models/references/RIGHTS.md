# Rights for models and generated art

What the providers' own terms say about the files this skill makes or brings in, with the date each page was
read. Terms change: before anything commercial is published, read the live page again, and update the date here
and in `@homie-rocks/studio`'s `lib/asset-manifest.mjs` (`PROVIDER_TERMS`), which writes every game's RIGHTS.md.

## Generated on the person's own account

- **fal** (https://fal.ai/terms, read 2026-10-02, "Last Updated: September 8, 2026"): "Customer owns and retains
  all right, title, and interest in and to the Customer Input." There is no matching clause assigning the
  Output to the customer; fal "does not represent, warrant, or covenant that any Output Content will be original,
  will not infringe rights of any third party … or otherwise entitle Company to any intellectual property rights
  in any Output Content". Third-party model outputs may not be used to train models that compete with them. The
  endpoints in `models.json` carry fal's "Commercial use" label.
- **Tripo** through fal (developer terms, https://developers.tripo3d.ai/en/terms, read 2026-10-02, last updated
  2025-07-11): "you may use Outputs for lawful commercial or non-commercial purposes". Calls through fal are paid
  calls. Tripo's FREE plan makes outputs public under CC BY 4.0 (credit Tripo); this skill never uses a free plan.
- **Copyright in purely AI-made files** may be thin, so a licence on them may not bind whoever copies those
  files. RIGHTS.md says so plainly and never claims more than the terms above.

## The starter library (CC0 only)

- **Kenney** (https://kenney.nl/support; each pack's License.txt): "Creative Commons Zero, CC0": personal,
  educational and commercial use; credit "is not a requirement".
- **KayKit** (each repository's licence file): CC0 1.0, no attribution required (a request not to resell
  unmodified copies is a request, not a term; Homie never sells them).
- **Poly Haven** (https://polyhaven.com/license): CC0; redistribution allowed; no credit needed for downloaded or
  mirrored files (only the live API inside a product needs a visible credit, and Homie never proxies it).
- **ambientCG** (https://docs.ambientcg.com/license/): CC0 1.0; "You can include the raw files in your project,
  for example a video game".

Never in the library or a public game's repository: Quaternius (its site licence of 2026-08-28 forbids
redistribution as an asset pack or template; reference only until written permission), Mixamo, Synty, Fab,
Unity Asset Store, TurboSquid (forbids three.js `.glb` outright), Sketchfab Standard, three.js example models,
anything trained on or made from non-commercial data (AMASS, SMPL, GVHMR, the Bandai Namco dataset).

## What may be handed on

A game serves its files to its players and to nobody else. A file leaves a studio only inside a part the studio
chose to share (the `parts` skill), and only when its licence lets the file itself be handed on.

| Licence | In a shared part |
| --- | --- |
| CC0, CC BY (credit kept), the studio's own, generated | yes |
| Quaternius (QAL) | no |
| Mixamo, a store EULA, a bought listing, "other" | no |
