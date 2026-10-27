---
name: 13c-metabolic-flux
description: Estimates intracellular metabolic fluxes from steady-state carbon-13 isotope-tracing measurements using validated atom maps, mfapy isotope simulation, constrained multistart fitting, and flux-profile diagnostics. Use for 13C-MFA, carbon tracing, mass isotopomer distributions (MDVs/MIDs), positional isotopomers, parallel tracer experiments, and determining whether labeling data constrain a pathway flux. Distinguishes measured-label inference from COBRA flux balance analysis and flags experiments requiring nonstationary MFA.
license: MIT
compatibility: Python 3.11 with uv and Git for installation. Tested with mfapy 0.6.3 at a10433af16682386548b360297e2476152d46ede, NumPy 2.4.6, SciPy 1.17.1, and NLopt 2.11.0. Network access is needed only to install public dependencies. Inference runs locally without credentials; inputs are JSON.
metadata:
  version: '1.0'
  category: life-sciences
  maintainer: Kalaris Labs
  last-reviewed: '2026-09-29'
  tags: 13C-MFA, metabolic flux analysis, isotope tracing, metabolomics, systems biology
---

# Carbon-13 metabolic flux inference

Turn reviewed carbon maps, explicit tracer mixtures, and corrected labeling measurements
into feasible flux estimates and evidence about which fluxes the experiment constrains.
Use the bundled solver rather than reconstructing isotope balances or fitting each
reaction independently. It runs mfapy's EMU forward simulator and fits fluxes in the
mass-balanced feasible space with SciPy. It does not use an FBA objective.

## Scope and required evidence

This implementation supports **metabolic and isotopic steady state**, a single shared
flux state across one or more tracer experiments, nonnegative one-way reaction fluxes,
and carbon-subset mass distributions. Reversible reactions are two separately mapped
directions. Measurement error is Gaussian with a supplied covariance or a disclosed
diagonal approximation.

Before fitting, obtain:

- The carbon network and the source of each atom assignment. Stoichiometry alone does
  not specify where labeled atoms go. Record compartments as separate metabolite IDs.
- Evidence for both steady-state assumptions. Stable metabolite abundance does not
  establish isotopic steady state. Time-course labeling requires INST-MFA with pool
  sizes and initial labeling; do not average it into this solver.
- Every carbon input's positional isotopomer distribution, including unlabeled
  supplements, bicarbonate/CO2 when assimilated, and tracer impurity.
- Fragment carbon assignments, natural-abundance correction history, and uncertainty
  of the **reported mean**. Raw peak intensities, derivatized spectra, and MS/MS
  transitions require validated preprocessing before these inputs can be constructed.
- Flux units, extracellular rate measurements or a stated relative-flux reference,
  and biologically justified bounds. Label fractions alone cannot set an absolute rate.

If necessary information is missing, name it and prepare the input template; do not
invent a fragment assignment, atom map, isotope correction, or measurement error.
Read [references/input-contract.md](references/input-contract.md) when preparing inputs.
Read [references/inference.md](references/inference.md) before interpreting an actual fit.

## Install the tested engine

Run in the user's analysis directory. Set `SKILL_DIR` to this skill's installed directory,
using the actual resolved path. Keep environments and generated results outside the skill.

```bash
uv venv --python 3.11 .venv-mfa
uv pip install --python .venv-mfa/bin/python -r "$SKILL_DIR/assets/requirements.txt"
```

The following commands use `.venv-mfa/bin/python`; on Windows use the environment's
`Scripts/python.exe`. mfapy is installed from an immutable Git revision because it is
not distributed on PyPI. Installation executes dependency build code; model inputs
are data, not user-supplied Python. The adapter restricts identifiers and atom-map
syntax before they reach mfapy's internally generated numerical functions.

## Workflow

1. **Prepare explicit inputs.** Copy a relevant model asset into the analysis directory,
   then replace its scientific content only from reviewed evidence. The bundled models
   are demonstrations, not validated organism-specific reconstructions. Use a separate
   dataset for each biological condition; jointly fit tracer replicates only when their
   biological flux state is defensibly shared.
2. **Check the contract and feasibility.**

   ```bash
   .venv-mfa/bin/python "$SKILL_DIR/scripts/mfa.py" check \
     --model model.json --data measurements.json --output input-check.json
   ```

   This checks atom counts and conservation, fragments, tracer sums, uncertainty
   matrices, bounds, and steady-state mass-balance feasibility. It cannot verify that a
   chemically consistent atom map is biologically correct or that a sample reached steady state.
3. **Exercise the forward model.** Supply one mass-balanced flux vector in the declared
   units. Compare predicted labeling with a reference or independently derived limits.

   ```bash
   .venv-mfa/bin/python "$SKILL_DIR/scripts/mfa.py" simulate \
     --model model.json --data measurements.json --fluxes fluxes.json \
     --output simulated-mdvs.json
   ```

4. **Fit and profile the fluxes relevant to the question.**

   ```bash
   .venv-mfa/bin/python "$SKILL_DIR/scripts/mfa.py" fit \
     --model model.json --data measurements.json --starts 12 --seed 2026 \
     --profile v3 --profile v7 --profile-points 31 --profile-starts 6 \
     --output fit.json
   ```

   Replace `v3` and `v7` with actual reaction IDs. Each profile point fixes that reaction
   and reoptimizes nuisance fluxes. For nonlinear networks, repeat with a different seed
   and more starts before interpreting a profile. A small residual is not an
   identifiability result.
5. **Inspect the evidence.** Check failed starts, residual patterns, mass balance,
   active bounds, local sensitivity rank, and profile status. Report threshold-crossing
   brackets at their actual grid resolution. Refine the grid if they are too coarse.
   If a profile finds a better solution than the baseline, rerun the fit; do not publish
   the stale intervals. A failed profile point is unknown, not excluded by the data.
6. **Deliver a bounded scientific result.** Include model and data hashes, package
   versions, source/correction provenance, units and reference flux, fitted predictions,
   residual diagnostics, profile plots or a table, and the unresolved flux combinations.
   Retain the JSON artifact. Separate point estimates supported by the data from arbitrary
   optimizer choices along a flat direction. Suggest additional measurements only after
   testing that their predicted labeling changes along that direction.

## Worked examples

These executable examples use synthetic, tracer-only data. There is no hidden natural-
abundance correction, and the tracer proportions already include unlabeled material.

### Recover a pathway split; then remove the informative measurement

The analytical two-route model sends a two-carbon substrate through either a
carbon-preserving or a carbon-swapping route. Uptake is fixed to 100. An 80% carbon-1
labeled feed and a carbon-1 fragment with M+1 = 0.56 determine the preserving route
as 70 and the swapping route as 30.

```bash
.venv-mfa/bin/python "$SKILL_DIR/scripts/mfa.py" fit \
  --model "$SKILL_DIR/assets/branch-model.json" \
  --data "$SKILL_DIR/assets/branch-identifiable.json" \
  --profile straight --profile-points 41 --output branch-fit.json

.venv-mfa/bin/python "$SKILL_DIR/scripts/mfa.py" fit \
  --model "$SKILL_DIR/assets/branch-model.json" \
  --data "$SKILL_DIR/assets/branch-unresolved.json" \
  --profile straight --output unresolved-fit.json
```

The first fit recovers approximately 70/30. Under its declared Gaussian error model,
the analytical 95% interval for `straight` is about 67.55–72.45; the script reports
grid brackets enclosing the threshold crossings. The second fit has only the whole-
molecule distribution, which is identical for the two routes. Expect local rank zero
and `unresolved_within_bounds`; its returned split is an arbitrary optimum.

`assets/branch-fluxes.json` supplies the 70/30 forward-simulation vector.

### Reproduce a published cyclic-network calculation

```bash
.venv-mfa/bin/python "$SKILL_DIR/scripts/mfa.py" simulate \
  --model "$SKILL_DIR/assets/tca-model.json" \
  --data "$SKILL_DIR/assets/tca-tracer.json" \
  --fluxes "$SKILL_DIR/assets/tca-fluxes.json" --output tca-simulation.json

.venv-mfa/bin/python "$SKILL_DIR/scripts/mfa.py" fit \
  --model "$SKILL_DIR/assets/tca-model.json" \
  --data "$SKILL_DIR/assets/tca-reference-mdv.json" \
  --profile v3 --profile v7 --output tca-fit.json
```

The first command reproduces the published rounded glutamate MDV
`[0.3464, 0.2695, 0.2708, 0.0807, 0.0286, 0.0039]`.
The second uses synthetic reference measurements to recover the glutamate branch
flux near 50, while recognizing that this labeling does not resolve the
fumarate/oxaloacetate exchange. A constraint-induced upper edge is not evidence of
a measurement-determined exchange interval.

## Interpretation boundaries

- A positional isotopomer string runs **carbon 1 to carbon N from left to right**.
  `"100000"` means carbon-1 labeled glucose. A mass distribution alone cannot specify
  that positional mixture. The adapter handles mfapy's reversed integer-bit ordering.
- Natural-abundance correction and tracer-purity correction are different operations.
  Inputs must be in the documented tracer-only basis, with tracer impurity represented
  consistently in source mixtures. Do not correct the same contribution twice.
- An N-carbon mass distribution has at most N independent components because it sums
  to one. The tool removes one bin and uses the reduced covariance. Retain cross-bin
  correlations when available. Diagonal SEM fits are explicitly approximate.
- The `symmetric` flag means equal averaging of identity and **complete carbon-order
  reversal**, as in the bundled fumarate/succinate map. It is not arbitrary molecular
  symmetry. Other permutations need an explicitly supported model representation.
- Unsupported in this CLI: nonstationary MFA, isotope effects on reaction rates,
  unmodeled pools or compartments, MS/MS joint distributions, multi-element isotope
  correction, fractional carbon stoichiometry/pseudo-reactions, and organism-scale
  performance guarantees. For these, use a validated specialized model/engine and
  retain the same input/provenance and identifiability discipline.

## Implementation and validation

`scripts/mfa.py` is the CLI. `scripts/_mfa_model.py` validates inputs and adapts them to
the mfapy EMU simulator; `scripts/_mfa_fit.py` handles feasible flux coordinates,
multistart optimization, diagnostic rank, and profile calculations.
The engine is pinned in [assets/requirements.txt](assets/requirements.txt).

The repository suite at `tests/13c-metabolic-flux/` checks the published reference,
analytical split recovery and likelihood profiles, unresolved routes and exchange,
omitted-bin invariance with correlated errors, parallel tracers, absolute-rate
anchoring, repeated-substrate condensation, symmetry, invalid maps, and CLI behavior.
These checks establish the tested numerical behavior, not biological validation of a
user's model or a measured advantage over any particular language model.

## Sources

- [mfapy source at the tested revision](https://github.com/fumiomatsuda/mfapy/tree/a10433af16682386548b360297e2476152d46ede), version 0.6.3; [API documentation](https://fumiomatsuda.github.io/mfapy-document/mfapy.html).
- Matsuda et al. (2021), [mfapy: An open-source Python package for 13C-based metabolic flux analysis](https://doi.org/10.1016/j.mec.2021.e00177).
- Antoniewicz, Kelleher, and Stephanopoulos (2007), [Elementary metabolite units (EMU): A novel framework for modeling isotopic distributions](https://doi.org/10.1016/j.ymben.2006.09.001).
- The TCA network is adapted from mfapy's MIT-licensed example files; the attribution
  and full notice are in [assets/mfapy-license.txt](assets/mfapy-license.txt).

## Agent operating procedure

1. **Check the environment.** Confirm tool versions, the reference genome/annotation build and the input formats (FASTQ, BAM, VCF, h5ad).
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Run the pipeline on a small subset (one sample, one chromosome, a few thousand cells) first.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Check QC metrics, sample identities, genome build consistency and batch effects before interpreting results.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Genome builds or identifiers do not match between inputs | Stop and harmonize (liftover, ID mapping) before continuing. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Do not interpret biological significance beyond what the statistics support; report multiple-testing correction.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `cobrapy`: Runs constraint-based metabolic modeling with COBRApy (Python, import cobra) on genome-scale models in SBML, JSON, YAML, or MATLAB format.
