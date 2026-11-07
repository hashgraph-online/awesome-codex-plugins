# Deep Review Pass — Methodology

The Deep Review pass is a per-IC comparison of actual usage against
datasheet requirements, with findings recorded durably in
`analysis/deep_review.json` and checked by the evidence gate: cited
components, nets and pins must exist in the run's analyzer JSON, and each
datasheet quote must appear on its page. A finding the gate could not check in
full is kept with `evidence_checked: partial`; treat that part of its evidence
as unverified. This guide holds the depth the SKILL.md loop points to:
comparison heuristics per part class, interacting-pair patterns,
helper-script conventions, evidence quality, and fan-out for big
BOMs. Checks are DERIVED from each part's datasheet — the lists
below are starting points, not ceilings.

`<skill-path>` is the installed kicad skill directory. Run the
commands below from the hardware project directory.

## Comparison heuristics by part class

**Regulators (LDO / buck / boost / SMPS controllers)**
- Vin range vs the actual input rail (worst case, not nominal —
  include supply tolerance and transients).
- Vout set point: recompute the FB divider (target = Vref × (1 +
  Rtop/Rbot)); compare against the rail name and downstream parts.
- Required externals vs datasheet minimums: inductance floor,
  input/output capacitance (and its effective value after DC bias
  derating), bootstrap caps, feed-forward caps.
- Enable pin: threshold vs the driving voltage; strap resistors vs
  leakage.
- Power-good: pull-up present? Voltage domain of the pull-up?
- Thermal: P_diss ≈ (Vin−Vout)×Iout for linears; compare Rθ_JA ×
  P_diss + T_amb against Tj_max (the thermal analyzer's assessment
  is the starting fact).
- Soft-start / sequencing requirements against the power tree.

**MCUs / SoCs**
- Supply range and per-domain decoupling vs datasheet placement
  requirements (per-pin caps, bulk).
- Reset circuit vs required RC / supervisor thresholds.
- Crystal: load capacitance math (CL = (C1×C2)/(C1+C2) + Cstray)
  vs the crystal's spec; drive level.
- USB: series resistors, required external pull-ups per speed, VBUS
  tolerance of the PHY pins.
- Boot straps: pull direction vs the intended boot source.
- 5 V tolerance: any pin fed from a higher domain than its supply.

**Op-amps / comparators**
- Supply vs input common-mode range at the actual input voltages
  (rail-to-rail in? out?).
- Output swing vs load and what the downstream stage needs.
- Stability: capacitive load vs datasheet limit; missing isolation
  resistor or compensation.

**Interface / level shifters / transceivers**
- Direction and voltage of each side vs the connected domains.
- Bus speed vs part rating; termination and idle-state biasing
  (RS-485 fail-safe, CAN split termination).

**MOSFETs / power switches / drivers**
- Vgs(th) and Rds(on)-at-Vgs vs the actual gate drive voltage
  (logic-level gate vs 10 V spec is the classic catch).
- Vds/Id margins vs rail + load, including inductive spikes.
- Gate resistor + driver current vs switching frequency.

**Diodes / LEDs / protection**
- If/Vf at operating current; reverse rating vs the blocked rail.
- TVS working voltage vs the protected rail's normal high; clamping
  voltage vs the protected pin's absolute max.

**Connectors** — current per pin vs load (cross_analysis CC-001 is
the fact source), mating cycles, keying/pinout vs the mating side.

## Interacting-pair checks

After the per-IC loop, look between parts:
- **Shared rails:** sum the worst-case loads vs the regulator's
  rating; check any sequencing requirements one IC imposes on
  another (core-before-IO, PG chaining).
- **Bus partners:** for each bus (I2C/SPI/UART/CAN/USB), check both
  ends' logic thresholds against the shared rail (VIH of the reader
  vs VOH of the driver), pull-up ownership and net value (parallel
  pull-ups!), and speed compatibility.
- **Thermal neighbors:** hot parts adjacent on the board (thermal
  analyzer proximity facts) whose combined dissipation invalidates
  each other's single-part Rθ assumptions.

## Helper-script conventions

Write disposable, design-specific scripts under `analysis/helpers/`:
- Name them `check_<topic>.py`; stdlib-only.
- Read facts from the analyzer JSON (pass paths on argv) — don't
  re-parse KiCad files.
- Print human-readable result lines with the numbers in them; the
  key line goes verbatim into `evidence.computation.result`.
- Keep the scripts (do not delete after use) — they are cited
  evidence and must resolve when the gate re-runs.

## Recording and evidence quality

Record findings in `analysis/deep_review.json` per
`<skill-path>/review/schemas/deep_review.schema.json`:
- `category` is free-form but reuse a small stable vocabulary within
  a project (e.g. `power_input`, `power_sequencing`, `bus_levels`,
  `thermal`, `protection`, `required_externals`) — the diff and the
  summary group by it.
- Datasheet quotes must be verbatim text from the cited page — the
  gate greps the page via pdftotext; paraphrases quarantine. If the PDF is not
  found, `pdftotext` is not installed, cannot run, or exits with an error
  other than a missing page, the quote is not checked and the finding is
  `partial`. A cited page below 1, or past the
  last page of the PDF, quarantines the finding. Mid-quote
  elision (`...` or `…`) is fine for trimming a long quote down to the
  relevant clauses — each segment on either side must still appear on
  the page, in order.
- Page numbers are PDF page indexes (what pdftotext counts), not the
  printed page footer.
- Computations cite the helper script path and paste its result line. The
  gate checks that the script exists but does not run it, so a finding with a
  computation is recorded as `evidence_checked: partial`. `full` means every
  cited datasheet quote was found on its page and nothing else was cited
  unchecked.
- A cited net passes the gate if it exists anywhere in the run's analyzer
  JSON under any of its identities: schematic name, `display_name`, or
  PCB net name (case-insensitive).
- A cited pin is `REF.PIN` by pin number or pin name (`U3.7`, `U3.VIN`,
  case-insensitive). It passes if that component has that pin in the run's
  analyzer JSON; a floating pin counts. Names match exactly: when an
  alternate pin function is selected the analyzer lists the alternate's name,
  so cite such pins by number.
  A pin of a component whose pins the analyzer JSON does not list (a part
  listed without pins, a PCB-only footprint with a pad on no net), or a pin
  name on a part listed by number only, is not checked and makes the
  finding `partial`.
- The gate finds the run folder from `analysis/manifest.json` and the
  run id inside `--analysis-dir` (`--run` picks another), so a moved or
  copied analysis folder still gates; no absolute path is stored.
- Severity and confidence are yours to assign — the trust story is
  the evidence, not a cap.

Gate, then deal with the fallout:

    python3 <skill-path>/review/scripts/deep_review_gate.py \
        analysis/deep_review.json --analysis-dir analysis/

`--project-dir` (for resolving `evidence.computation.script` paths)
defaults to `--analysis-dir`'s parent, and `--datasheets-dir` defaults to
`<project-dir>/datasheets` — pass `--project-dir` explicitly only when
the gate runs from outside the normal `<project>/analysis/` layout:

    python3 <skill-path>/review/scripts/deep_review_gate.py \
        /path/to/project/analysis/deep_review.json \
        --analysis-dir /path/to/project/analysis/ \
        --project-dir /path/to/project/

Quarantined entries are visible in the file with reasons. Fix the
citation (or drop the claim) and re-run — the gate re-evaluates
quarantined entries and promotes corrected ones. Anything left
quarantined renders in the report as an unverified claim.

## Re-review protocol

1. `cp analysis/deep_review.json analysis/deep_review.prev.json`
2. Run the pass fresh; gate it.
3. `python3 <skill-path>/scripts/diff_analysis.py analysis/deep_review.prev.json analysis/deep_review.json --text`
4. Report fixed / still-open / new. Treat `reworded_candidates` as
   advisory — confirm by reading, then report as still-open.

## Fan-out for big BOMs

Main-loop is the default. When the design is too big to hold (rough
threshold: >20 review-worthy ICs, or context pressure mid-pass):
- Chunk by subsystem (power tree, then digital core, then I/O) and
  run the loop per chunk yourself; or
- Dispatch one subagent per IC-group. Each subagent gets: the
  analyzer JSON paths, its IC list, the datasheet locations, and
  this guide; it returns a JSON array of findings (schema shape,
  no finding_id — the gate stamps ids). Concatenate the arrays into
  `findings[]`, then gate once, centrally.
- `analysis/design_context.json` (optional input) steers priorities:
  automotive → derating and temperature attention up; battery →
  quiescent current; RF → supply noise on analog rails.

## Degradation (never silent)

| Situation | Do this |
|---|---|
| No datasheets at all | Topology-only pass; per-IC "not verified against datasheet" gap lines in the report |
| Cache miss, PDF on disk | Read the PDF directly |
| No PDF, no API | Write "X unverified — no datasheet available" in the review text; it is not a `deep_review.json` finding |
| Extraction exists, low quality | It comes back with `quality.trusted: false` — decide: trust, or re-read the PDF |
| Gate failure | Finding sits in `quarantined[]` with a reason; report as unverified claim |
| Prior deep_review.json missing/old schema | Fresh review; say why in the delta section |
