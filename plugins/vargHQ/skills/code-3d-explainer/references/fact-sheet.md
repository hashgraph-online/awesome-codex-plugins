# The fact sheet

Write it before any 3D work. It is the contract between the film and reality: every word the film shows
comes from it, every size the model uses is in it, and every lie the film tells on purpose is listed in
it. A critic checks it before the build (`critic-prompt.md`) and `scripts/check_facts.ts` checks the
render against it after.

Worked example: `examples/animal-cell/factsheet.md` (24 rows, 7 simplifications, the critic's verdict).

## Template

```markdown
# Fact sheet: <subject>

Subject: <what exactly: which cell type / isotope / engine / object>, <length>, <narration or not>.
Model units: 1 unit = <1 µm | 1 nm | 1 Å | 1 m>. Written <date> before any 3D work.
Status: **approved for build**            <- only after the critic's pass 1 and your fixes

## On-screen claims

| ID | Part | On screen | Claim checked | Source |
|---|---|---|---|---|
| F0 | title | <exact title text> | (title, no claim) | — |
| F1 | <part> | <exact label name> | name | <URL> |
| F1a | <part> | <exact one-line fact, ≤ 45 characters> | <what is actually true, with numbers> | <URL + the sentence that says it> |
| SB | scale bar | `<n> µm` / `<n> nm` | computed from the camera at the look-at depth; hidden where parts are enlarged | computed |

## Real sizes used in the model

| Part | Real (with range) | Model | Source |

## Simplifications on purpose

| ID | What we change | Why |

## Claims we deliberately do NOT make

## Critic log
```

## Rules

- **Word for word.** The "On screen" cell is the exact string, including the `·` and the dash. The check
  script compares the render's real text with this column, so a typo fails the build.
- **One claim per row, one source per claim**, and the source must *say it*. The critic found four rows
  in our first cell sheet whose source did not contain the number we quoted (Wikipedia gives mitochondria
  as an *area*, 0.75–3 µm²; a book chapter title was misquoted). Quote the sentence when you can.
- **Primary or reference sources**: a textbook (Alberts MBoC, OpenStax), a review, Wikipedia with the
  sentence quoted, BioNumbers / *Cell Biology by the Numbers* for sizes and counts, the PDB / RCSB for
  molecular structure, NIST / CODATA for physical constants, NASA / ESA for astronomy, the manufacturer's
  datasheet for a machine. A blog or a viral post is never a source.
- **Mechanism rows.** If the film explains *why* something happens, the why is its own row with its own
  source. This is where viral explainers fail (see the Zeno example in `critic-prompt.md`).
- **Real sizes even when you change them.** Write the real value and the model value side by side. Model
  ratios must be consistent with each other (the critic computed our nucleus volume fraction from the
  diameters: 8%, matching the sheet).
- **Every simplification a viewer could mistake for a fact is listed**: counts (we show 18 mitochondria,
  a cell has 10³–10⁴), enlargements (ribosomes 4–5× too big), invented colours, emptied space, missing
  parts, a still world. Then put a short caveat on screen ("Simplified: far fewer parts, colours
  invented" / "Small parts drawn larger than real") for at least 1.6 s.
- **Prefer hedged truth to confident error**: "Holds nearly all the cell's DNA" (mitochondria have DNA
  too), "Make ATP by aerobic respiration" (no unsourced "most"), "Break down waste in an acidic interior"
  (the enzymes are not acids).
- **Unsourced numbers stay off screen.** Mark them "not sourced, visual only" in the sizes table.
- **Short on-screen lines.** Name 1–3 words; fact ≤ 45 characters, 4–7 words, so it can be read in the
  ~2 s a label stays up (`labels.md`).

## Where real data exists, use it

| Subject | Data | How |
|---|---|---|
| Proteins, viruses, DNA, ribosomes | RCSB PDB (`https://files.rcsb.org/download/<ID>.pdb` or `.cif`) | parse ATOM lines → instanced spheres per atom or per residue (Cα trace as a tube); keep the PDB ID on screen in small type |
| Small molecules | PubChem 3D conformers (SDF) | atoms + bonds as spheres and cylinders |
| Orbitals, atoms | analytic hydrogen wavefunctions | sample ψ² as a point cloud; say "probability cloud", never "orbit" |
| Planets, orbits | NASA JPL Horizons, published radii | real ratios, then say what you scaled |
| Machines | manufacturer drawings, published dimensions | real proportions, labelled parts |
| Maths | the formula itself | compute it; never hand-draw a curve you could compute |

Cache downloaded data in the project (`data/`), never fetch at render time.
