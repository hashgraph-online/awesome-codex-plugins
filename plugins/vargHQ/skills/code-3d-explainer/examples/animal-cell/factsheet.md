# Fact sheet: an animal cell, built one organelle at a time

Subject: a generic mammalian (animal) cell in interphase, ~20 s, no narration.
Model units: 1 unit = 1 µm. Written 2026-11-10 before any 3D work; revised the same day after the
critic's pass 1 (log at the end). Status: **approved for build**.

## On-screen claims

Every string the film shows must appear in the "On screen" column, word for word.
`scripts/check_facts.ts` compares this table with what the render really showed.

| ID | Part | On screen | Claim checked | Source |
|---|---|---|---|---|
| F0 | title | The animal cell | (title, no claim) | — |
| F0b | title | Built one part at a time | (title, no claim) | — |
| F1 | membrane | Plasma membrane | name | Wikipedia "Cell membrane" ("also known as the plasma membrane"), https://en.wikipedia.org/wiki/Cell_membrane |
| F1a | membrane | A lipid bilayer about 5 nm thick | the bilayer is ~4–5 nm thick (whole membrane with proteins 4–10 nm) | BioNumbers, "What is the thickness of the cell membrane?", https://book.bionumbers.org/what-is-the-thickness-of-the-cell-membrane/ ; Alberts, Molecular Biology of the Cell (MBoC) 4th ed., ch. 10 ("about 5 nm thick"; NCBI pages were behind a captcha for the critic) |
| F2 | nucleus | Nucleus | name | Wikipedia "Cell nucleus", https://en.wikipedia.org/wiki/Cell_nucleus |
| F2a | nucleus | Holds nearly all the cell's DNA | the nucleus holds nearly all of the genome (mitochondria keep a small genome of their own) | Wikipedia "Cell nucleus" ("nearly all of the cell's genome") |
| F3 | nucleolus | Nucleolus | name | Wikipedia "Nucleolus", https://en.wikipedia.org/wiki/Nucleolus |
| F3a | nucleolus | Assembles ribosome subunits | ribosome subunits form in the nucleolus (they finish maturing in the cytoplasm) | Wikipedia "Nucleolus"; OpenStax Biology 2e 4.3 ("to assemble the ribosomal subunits"), https://openstax.org/books/biology-2e/pages/4-3-eukaryotic-cells |
| F4 | er | Rough ER | name (rough endoplasmic reticulum) | Wikipedia "Endoplasmic reticulum", https://en.wikipedia.org/wiki/Endoplasmic_reticulum |
| F4a | er | Ribosome-studded sheets joined to the nucleus | rough ER is flattened sheets carrying ribosomes; its membrane is continuous with the outer nuclear membrane | Wikipedia "Endoplasmic reticulum" ("large double-membrane sheets … continuous with the outer layer of the nuclear envelope") |
| F5 | golgi | Golgi apparatus | name | Wikipedia "Golgi apparatus", https://en.wikipedia.org/wiki/Golgi_apparatus |
| F5a | golgi | Modifies, sorts and ships proteins | the Golgi modifies (e.g. glycosylates), sorts and packages proteins into vesicles | Wikipedia "Golgi apparatus"; OpenStax Biology 2e 4.4 |
| F6 | mito | Mitochondria | name | Wikipedia "Mitochondrion", https://en.wikipedia.org/wiki/Mitochondrion |
| F6a | mito | Make ATP by aerobic respiration | mitochondria use aerobic respiration to generate ATP | Wikipedia "Mitochondrion" (lead: "use aerobic respiration to generate adenosine triphosphate (ATP)") |
| F7 | ribo | Ribosomes | name | Wikipedia "Eukaryotic ribosome", https://en.wikipedia.org/wiki/Eukaryotic_ribosome |
| F7a | ribo | Build proteins · real ones are 25–30 nm | ribosomes translate mRNA into protein; eukaryotic ribosomes are 25–30 nm (250–300 Å) across | Wikipedia "Eukaryotic ribosome" |
| F8 | lyso | Lysosomes | name | Wikipedia "Lysosome", https://en.wikipedia.org/wiki/Lysosome |
| F8a | lyso | Break down waste in an acidic interior | lysosomes hold >60 hydrolases that work in an acidic lumen (pH ~4.5–5.0) and break down and recycle waste | Wikipedia "Lysosome"; OpenStax Biology 2e 4.4 |
| F9 | cyto | Cytoskeleton | name | Wikipedia "Cytoskeleton", https://en.wikipedia.org/wiki/Cytoskeleton |
| F9a | cyto | Protein filaments for shape and transport | a network of protein filaments that gives shape and carries cargo; in interphase microtubules radiate from one centrosome near the nucleus and the Golgi | Wikipedia "Cytoskeleton"; Wikipedia "Microtubule organizing center" |
| F10 | end | One animal cell, ~20 µm across | our model cell is 20 µm; eukaryotic cells are 10–100 µm; a HeLa cell is ~2,000 µm³ (500–4,000), a ~16 µm sphere | OpenStax Biology 2e 4.2; Milo & Phillips, Cell Biology by the Numbers, "How big is a human cell?", https://book.bionumbers.org/how-big-is-a-human-cell/ |
| F11 | end | Simplified: far fewer parts, colours invented | summary of S1 and S3 | this sheet |
| F11b | end | Small parts drawn larger than real | summary of S2 | this sheet |
| SB | scale bar | `<n> µm` / `<n> nm` | computed from the camera at the look-at depth, so it is true for the drawn geometry there; **hidden for the whole ribosome label window** (12.35–15.95 s) where the drawn ribosomes are 4–5× too big | computed (`lib/explainer.js` `scaleBar`) |
| IX | label index | `<n>` | the build order of the nine parts, 01–09 (UI, no claim) | — |

## Real sizes used in the model (1 unit = 1 µm)

| Part | Real | Model | Source |
|---|---|---|---|
| Cell | eukaryotic 10–100 µm; HeLa ~2,000 µm³ (~16 µm sphere) | 20 µm lumpy sphere (4,190 µm³) | OpenStax; BioNumbers "How big is a human cell?" |
| Nucleus | ~6 µm in human cells (Wikipedia); 2–10 µm (BioNumbers); often ~10% of cell volume | 8.6 µm (8% of the model's volume) | Wikipedia "Cell nucleus"; BioNumbers "How big are nuclei?" |
| Nucleolus | not sourced (visual only, no claim on screen) | 2.2 µm, one | — |
| Nuclear pore complex | ~120 nm; ~2,000–4,000 per nucleus | 0.26 µm rings (~2.2× too big), 140 | Wikipedia "Nuclear pore complex", "Cell nucleus" |
| Mitochondrion | ~1 µm diameter, ~2 µm long; 10³–10⁴ per mammalian cell; often a connected network; 10–20% of cell volume | 0.7 µm wide, 1.6–2.8 µm long, 18 separate beans (~0.3% of volume) | BioNumbers "How big are mitochondria?", https://book.bionumbers.org/how-big-are-mitochondria/ |
| Golgi | 4–8 cisternae per stack; 40–100 stacks joined in a ribbon beside the nucleus and centrosome | one stack of 5 cisternae (size not sourced) at the centrosome | Wikipedia "Golgi apparatus" |
| Lysosome | 0.1–1.2 µm; hundreds per cell | 0.5–0.84 µm, 12 | Wikipedia "Lysosome" |
| Ribosome | 25–30 nm; millions per cell | 120 nm spheres (4–5× too big), ~2,800 free, on the ER and on the outer nuclear membrane, one polysome | Wikipedia "Eukaryotic ribosome" |
| Microtubule | ~25 nm wide (23–27), radiating from the centrosome | 0.08 µm lines (~3× too thick), 36 | Wikipedia "Microtubule"; BioNumbers |
| Lipid bilayer | ~4–5 nm | glowing rim; at the cut a double line ~0.2 µm (~40× too thick) | BioNumbers |

## Simplifications on purpose

| ID | What we change | Why |
|---|---|---|
| S1 | Counts: 18 mitochondria (real 10³–10⁴, often one connected network, 10–20% of the volume; ours ~0.3%), ~2,800 ribosomes (real: millions), 12 lysosomes (real: hundreds), 140 nuclear pores (real ~2,000–4,000), 36 microtubules, one Golgi stack (real 40–100 in a ribbon), one nucleolus (real often 1–2, up to ~10) | legibility; a true count is a solid fog |
| S2 | Ribosomes 4–5× too big, nuclear pores ~2× too big, microtubules ~3× too thick, the bilayer at the cut ~40× too thick, Golgi vesicles (~0.2–0.3 µm vs ~50–100 nm) and cisternae (~0.15–0.25 µm thick vs tens of nm) several times too big | otherwise invisible at whole-cell scale; the ribosome label states the real size; the end card says "Small parts drawn larger than real"; the scale bar is hidden in the ribosome close-up |
| S3 | Colours are invented: organelles are mostly colourless; micrographs are grey or stained | colour codes the parts |
| S4 | Cytoplasm drawn nearly empty; the real cytosol is packed with protein (macromolecular crowding) | so the parts can be seen |
| S5 | ER shown as four sheets around the nucleus; the real ER is a network of sheets and tubules reaching much of the cytoplasm. No smooth ER, peroxisomes, endosomes, actin cortex or intermediate filaments; no vesicle traffic between organelles (only a few vesicles at the Golgi) | one beat per part; the film says "Simplified" |
| S6 | Everything is still; mitochondria shown as separate beans; real organelles move, fuse, divide and often form networks | 20 s film, build metaphor |
| S7 | The cell is a lumpy sphere; real cells take many shapes (flat, spread on a surface) | a readable whole |

## Claims we deliberately do NOT make

- No "power plant" metaphor and no "most of the cell's ATP" (true for typical aerobic cells, but the critic found no source we could load that says "most"; glycolysis also makes ATP).
- No count presented as real (S1); no colour presented as real (S3).
- No claim that the nucleus is in the centre (it is often off-centre; we put it off-centre).
- No size for the nucleolus or the Golgi on screen (not sourced).

## Critic log

Pass 1, 2026-11-10, a fresh general-purpose subagent with web access, prompt from
`references/critic-prompt.md`. Verdict, verbatim (table condensed to the rows that changed something):

> VERDICT: PASS WITH FIXES
>
> | ID | Verdict | Problem | Replacement |
> |---|---|---|---|
> | F1a | FIX (source only) | The cited URL NBK21054 is the front page of the MBoC 4th ed. book, not ch. 10. Other sources give a bilayer of ~4 nm and 4–10 nm for the whole membrane with its proteins, so "about 5 nm" is fine for the bilayer. | keep the text; fix the URL |
> | F2a | FIX | "Holds the DNA" overclaims: mitochondria have their own DNA, and the film shows mitochondria. Wikipedia says "nearly all of the cell's genome". The 10% figure varies a lot by cell type. Milo & Phillips' vignette is "How big are nuclei?" and does NOT give 10%. | Holds nearly all DNA · often ~10% of cell volume |
> | F4a | FIX | "Folds" is the wrong word: rough ER is flattened sheets (cisternae). | Ribosome-studded sheets joined to the nucleus |
> | F6a | FAIL (source) | The cited quote is not in the current Wikipedia article. The lead now says only "use aerobic respiration to generate ATP", with no "most". | Make ATP by aerobic respiration |
> | F8a | FIX | Wrong mechanism wording: the enzymes are not acids. They are hydrolases that work in an acidic lumen (pH ~4.5–5). | Break down waste in an acidic interior |
> | F10 | FIX (source only) | Milo & Phillips ("How big is a human cell?") give HeLa as 2,000 µm³ (range 500–4,000), a sphere of ~16 µm. "10–30 µm" has no source. | keep the text |
> | F11 | FIX | Over 50 characters and incomplete: microtubules (3×), nuclear pores (~2×) and the bilayer (30×) are enlarged too, and the cytoplasm is emptied. | Simplified: far fewer parts, colours invented / Small parts drawn larger than real |
> | SB | FIX | The bar is true for the drawing, but the drawing has enlarged parts. In the ribosome close-up the bar will measure a 120 nm ribosome while the text says 25–30 nm. It is also only true at one depth. | Hide the bar during those beats, or add a caveat |
> | R-nucleolus | FAIL (source) | Wikipedia "Nucleolus" gives no size, so "~1–5 µm" has no source. | — |
> | R-pore | FIX | Model rings are 0.26 µm, so pores are ~2.2× too big, and S2 does not list this. | — |
> | R-mito | FAIL (source) | Wikipedia gives "0.75 and 3 µm² in cross section", an AREA. Use BioNumbers: ~1 µm diameter, ~2 µm long, 10³–10⁴ per mammalian cell, often a connected network. | — |
> | R-golgi | FIX | Mammalian cells have 40–100 stacks joined into a ribbon, so one stack is an unlisted simplification. "2.6 µm across" has no source. | — |
> | R-mt | FIX | The 36 microtubules are not in the S1 counts. | — |
>
> - Mitochondrial volume: 18 × ~0.76 µm³ ≈ 14 µm³, about 0.3% of the model cell. Real cells are ~10–20% mitochondria. Separate beans are also not how mitochondria look in most cells, where they form a network. Add both to S1 and S6.
> - S1 and S2 are missing items (36 microtubules, one Golgi stack, one nucleolus, pores ~2× too big). S5 says "no vesicle traffic", but cell.js draws Golgi vesicles budding.
> - Citations are misquoted throughout (wrong Milo & Phillips titles, non-verbatim Wikipedia quotes, Wikipedia cited for numbers it does not contain).
> - I could not check any MBoC (NCBI Bookshelf) page: all five returned a reCAPTCHA. A human should load the MBoC pages before citing them.
> - Ribosome placement and mechanisms are right. One gap a specialist would raise: there are no ribosomes on the outer nuclear membrane (optional).

What we changed: every FIX and FAIL above (on-screen texts F2a, F4a, F6a, F8a, F11 → F11 + F11b; the
scale bar hides in the ribosome close-up; S1, S2, S5, S6 extended; sources corrected; unsourced sizes
marked "not sourced, no claim on screen"); we also added ribosomes on the outer nuclear membrane. For
F2a we dropped the "~10%" half rather than hedge it, since it varies by cell type.

Pass 2, frames vs sheet, a second fresh subagent (the first attempt was cut off by a network outage).
Verdict on the first full render: **FIX FIRST**. Its findings, condensed:

> | Time (s) | Problem | Fix |
> |---|---|---|
> | 10.90–11.37 | "Golgi apparatus" stays at full opacity over a shot that shows only mitochondria; viewers read the red beans as "Golgi" | fade the label as soon as the anchor leaves the frame |
> | 16.4–17.9 | the Cytoskeleton dot lands on a mitochondrion | anchor to a microtubule point nothing hides, near the aster |
> | 12.9–14.1 | the Ribosomes leader points at empty space beside the mRNA | anchor to one polysome ribosome |
> | 14.30–14.77 | the 500 nm scale bar is back while "real ones are 25–30 nm" is still on screen | hide the bar for the whole ribosome label window |
> | 18.9–21.0 | the end-card Lysosomes leader passes through the Golgi dot; its target is faint | re-anchor or reorder |
> | 1.1–18.2 | the orange step numerals 01–09 are on-screen text not tracked by check_facts | add a row and track them |
> | 18.4–21.0 | the caveat lines are 34 px (~7 px on a phone), the second one dim | ≥ 44 px, high contrast |
>
> - Every label, title and caveat string matches the sheet word for word; sizes against the scale bar agree with the model.
> - Unlisted enlargements under a visible bar: Golgi vesicles (~0.33 µm) and cisternae thickness. Add to S2.
> - Lower priority: the ER-to-envelope joins are not visible in the ER shot; lysosome granules look like ribosomes; cristae are surface stripes; the nucleolus looks faceted.

What we changed: label text now lingers ≤ 0.25 s after its anchor leaves the frame (the camera holds grew to
keep reading time); the cytoskeleton anchor sits on a microtubule near the centrosome facing the camera; the
ribosome anchor is the 5th ribosome of the polysome; the scale bar hides 12.35–15.95 s; the end-card
lysosome tag was removed (no clearly visible lysosome outside the nucleus face from that angle); the
step numerals are tracked (row IX, `ui` in labels.json); the caveat is 44 px, near-white; S2 lists the
Golgi enlargements; lysosome granules are now brown, not ribosome cream; the nucleolus is smoother.
Not changed (listed as limits): visible ER-envelope joins in the ER shot, cristae as inner folds.
After the fixes `check_labels.ts` and `check_facts.ts` pass on the final render; the frames were not
re-reviewed by a third critic.
