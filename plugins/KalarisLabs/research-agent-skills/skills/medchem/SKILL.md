---
name: medchem
description: Filters and triages small-molecule libraries with the Python medchem library (datamol-io, v2.0.5) on top of RDKit and datamol. Covers drug-likeness rules (Lipinski, Veber, CNS, lead-like) via RuleFilters, structural alerts (ChEMBL-derived sets, NIBR, PAINS, Brenk), chemical group detection, ZINC-based complexity thresholds, scaffold constraints, and the medchem query language (QueryFilter). Use when screening a compound library for drug-likeness, removing PAINS or other structural-alert compounds, prioritizing hits for hit-to-lead or lead optimization, detecting functional groups, or combining criteria in one query. Not for computing general descriptors or fingerprints; use RDKit directly.
license: Apache-2.0 license
compatibility: Requires Python 3.9+ and datamol (installed with medchem). Optional Lilly demerit filter requires separate `lilly-medchem-rules` conda package.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.2'
  category: chemistry-and-drug-discovery
  maintainer: Kalaris Labs
  tags: medicinal chemistry, drug-likeness, PAINS, structural alerts, compound filtering
---

# Medchem

## Overview

Medchem is a Python library from [datamol-io](https://github.com/datamol-io/medchem) for molecular filtering and prioritization in drug discovery. Apply literature-derived drug-likeness rules, named alert catalogs, complexity thresholds, chemical-group detection, and a custom query language to triage compound libraries at scale. Filters are context-specific guidelines — combine with domain expertise and target knowledge.

**Version note:** Examples target **medchem 2.0.5** (PyPI stable, Nov 2024). Requires **Python ≥3.9**. Depends on **datamol** and **RDKit** (installed automatically). `RuleFilters` and structural filter classes return **pandas DataFrames**. Lilly demerits require optional native binaries (`mamba install lilly-medchem-rules`).

## When to Use This Skill

This skill should be used when:
- Applying drug-likeness rules (Lipinski, Veber, CNS, lead-like) to compound libraries
- Filtering molecules by structural alerts, PAINS, or NIBR screening-deck rules
- Prioritizing compounds for hit-to-lead or lead optimization
- Calculating complexity metrics against ZINC-derived thresholds
- Detecting functional groups or named substructure catalogs
- Building multi-criteria filters with the medchem query language

## Installation

```bash
uv pip install medchem datamol
```

Optional — Eli Lilly demerit filter (requires conda-forge native binaries):

```bash
mamba install -c conda-forge lilly-medchem-rules
```

## Core Capabilities

### 1. Medicinal Chemistry Rules

Apply established drug-likeness rules via `medchem.rules`.

**List available rules:**

```python
import medchem as mc

mc.rules.RuleFilters.list_available_rules_names()
# ['rule_of_five', 'rule_of_five_beyond', 'rule_of_four', 'rule_of_three', ...]
```

**Single rule on one molecule:**

```python
import datamol as dm
import medchem as mc

smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # aspirin
mc.rules.basic_rules.rule_of_five(smiles)   # True
mc.rules.basic_rules.rule_of_cns(smiles)    # True
mc.rules.basic_rules.rule_of_veber(smiles)  # True
```

**Multiple rules with `RuleFilters` (returns a DataFrame):**

```python
import datamol as dm
import medchem as mc

mols = [dm.to_mol(s) for s in smiles_list]

rfilter = mc.rules.RuleFilters(
    rule_list=["rule_of_five", "rule_of_oprea", "rule_of_cns", "rule_of_leadlike_soft"]
)
df = rfilter(mols=mols, n_jobs=-1, progress=True, keep_props=False)

# Columns: mol, pass_all, pass_any, rule_of_five, rule_of_oprea, ...
passing = df[df["pass_all"]]
```

Use `keep_props=True` to include computed descriptors (`mw`, `clogp`, `tpsa`, etc.) in the result.

### 2. Structural Alert Filters

Detect problematic patterns with `medchem.structural`. Both classes return **DataFrames** with `pass_filter`, `status`, and `reasons` columns.

**Common alerts (ChEMBL-derived rule sets):**

```python
import medchem as mc

alert_filter = mc.structural.CommonAlertsFilters()
df = alert_filter(mols=mol_list, n_jobs=-1, progress=True)
# df columns: mol, pass_filter, status, reasons

clean = df[df["pass_filter"]]
```

**NIBR filters (Novartis screening-deck curation):**

```python
nibr_filter = mc.structural.NIBRFilters()
df = nibr_filter(mols=mol_list, n_jobs=-1, progress=True)
# df columns: mol, pass_filter, status, severity, reasons, n_covalent_motif, special_mol
```

Compounds with `severity >= 10` are excluded by default (see NIBR paper).

### 3. Named Catalog Filters (PAINS, Brenk, etc.)

Use `medchem.catalogs.NamedCatalogs` for RDKit `FilterCatalog` instances, or the functional API:

```python
import medchem as mc

# List available named catalogs
mc.catalogs.list_named_catalogs()
# ['tox', 'pains', 'pains_a', 'brenk', 'nibr', 'zinc', ...]

# Functional API — True means molecule passes (no alert match)
passes = mc.functional.alert_filter(mols=mol_list, alerts=["pains"], n_jobs=-1)

# Or via catalog objects
passes = mc.functional.catalog_filter(
    mols=mol_list,
    catalogs=[mc.catalogs.NamedCatalogs.pains()],
    n_jobs=-1,
)
```

### 4. Functional API

`medchem.functional` provides one-call wrappers that return boolean masks (True = passes):

```python
import medchem as mc

mc.functional.rules_filter(mols=mol_list, rules=["rule_of_five", "rule_of_cns"], n_jobs=-1)
mc.functional.nibr_filter(mols=mol_list, max_severity=10, n_jobs=-1)
mc.functional.alert_filter(mols=mol_list, alerts=["pains", "brenk"], n_jobs=-1)
mc.functional.complexity_filter(mols=mol_list, complexity_metric="bertz", limit="99", n_jobs=-1)
```

Other helpers: `catalog_filter`, `chemical_group_filter`, `lilly_demerit_filter` (requires optional binaries), `macrocycle_filter`, `bredt_filter`, `protecting_groups_filter`, and more.

### 5. Chemical Groups

Detect functional groups and curated pattern collections via `medchem.groups`:

```python
import medchem as mc

# Browse available group collections
mc.groups.list_default_chemical_groups()
# ['privileged_scaffolds', 'common_warhead_covalent_inhibitors', 'rings_in_drugs', ...]

group = mc.groups.ChemicalGroup(groups=["privileged_scaffolds"])
group.has_match(mol)                          # bool
group.get_matches(mol)                        # dict of group → atom indices
group.filter(mols)                            # molecules matching the group

# Returns molecules that do NOT match the group
mc.functional.chemical_group_filter(mols=mol_list, chemical_group=group, n_jobs=-1)
```

Custom groups can be loaded from a file via `groups_db` (CSV with `smiles`/`smarts`, `name`, `group` columns).

### 6. Molecular Complexity

Compare complexity metrics to precomputed ZINC-15 percentile thresholds:

```python
import medchem as mc

# Single molecule
cf = mc.complexity.ComplexityFilter(limit="99", complexity_metric="bertz")
cf(mol)  # True if below 99th-percentile threshold

# Batch via functional API
mc.functional.complexity_filter(
    mols=mol_list,
    complexity_metric="bertz",  # also: sas, qed, whitlock, barone, smcm, twc
    limit="99",
    n_jobs=-1,
)

# Direct metric functions
mc.complexity.WhitlockCT(mol)
mc.complexity.BaroneCT(mol)
```

### 7. Scaffold Constraints

`medchem.constraints.Constraints` matches a core scaffold and applies per-atom constraint functions — not simple MW/LogP ranges. For property bounds, use `RuleFilters`, descriptors via `mc.rules.list_descriptors()`, or the query language.

```python
import datamol as dm
import medchem as mc

core = dm.to_mol("c1ccccc1")
constraints = mc.constraints.Constraints(
    core=core,
    constraint_fns={"query": lambda mol, atom_idx, query: ...},
)
constraints(mol)
```

### 8. Medchem Query Language

Build multi-criteria filters with `medchem.query.QueryFilter`:

```python
import medchem as mc

# Rule + alert combination
qf = mc.query.QueryFilter('MATCHRULE("rule_of_five") AND NOT HASALERT("pains")')
mask = qf(mols=mol_list, n_jobs=-1)  # list[bool]

# CNS-like with property bounds
qf = mc.query.QueryFilter('MATCHRULE("rule_of_cns") AND HASPROP("tpsa", <=, 90)')
mask = qf(mols=mol_list, n_jobs=-1)
```

**Query syntax:**
- `MATCHRULE("rule_of_five")` — apply a named rule
- `HASALERT("pains")` — match a named catalog (`pains`, `brenk`, `nibr`, `tox`, …)
- `HASPROP("mw", <, 500)` — compare a descriptor (unquoted comparator)
- `HASGROUP("privileged_scaffolds")` — match a chemical group
- `HASSUBSTRUCTURE("c1ccccc1")` — substructure match
- Operators: `AND`, `OR`, `NOT`

List available descriptors: `mc.rules.list_descriptors()`

## Workflow Patterns

### Pattern 1: Initial Triage of a Compound Library

```python
import datamol as dm
import medchem as mc
import pandas as pd

df = pd.read_csv("compounds.csv")
mols = [dm.to_mol(s) for s in df["smiles"]]

# Drug-likeness rules
rules_df = mc.rules.RuleFilters(rule_list=["rule_of_five", "rule_of_veber"])(mols=mols, n_jobs=-1)

# PAINS + common alerts via query
qf = mc.query.QueryFilter('MATCHRULE("rule_of_five") AND NOT HASALERT("pains")')
pass_mask = qf(mols=mols, n_jobs=-1)

df["passes_rules"] = rules_df["pass_all"].values
df["drug_like"] = pass_mask
filtered_df = df[df["drug_like"]]
filtered_df.to_csv("filtered_compounds.csv", index=False)
```

### Pattern 2: Lead Optimization Filtering

```python
import medchem as mc

rules_df = mc.rules.RuleFilters(rule_list=["rule_of_leadlike_soft"])(mols=candidates, n_jobs=-1)
nibr_df = mc.structural.NIBRFilters()(mols=candidates, n_jobs=-1)
complex_mask = mc.functional.complexity_filter(
    mols=candidates, complexity_metric="bertz", limit="95", n_jobs=-1
)

passes = (
    rules_df["pass_all"]
    & nibr_df["pass_filter"]
    & complex_mask
)
```

### Pattern 3: Detect Functional Groups

```python
import medchem as mc

group = mc.groups.ChemicalGroup(groups=["common_warhead_covalent_inhibitors"])
matches = [group.has_match(mol) for mol in mol_list]
warhead_mols = [mol for mol, m in zip(mol_list, matches) if m]
```

## Best Practices

1. **Context matters** — marketed drugs often violate Ro5; prodrugs and natural products are common exceptions.
2. **Combine filters** — rules, alert catalogs, and complexity thresholds work best together.
3. **Use parallelization** — pass `n_jobs=-1` for libraries >1000 molecules.
4. **Check return types** — `RuleFilters` and structural classes return DataFrames; functional helpers return boolean arrays.
5. **Lilly demerits are optional** — install `lilly-medchem-rules` separately; default max demerits is 160 in the functional API.
6. **Document decisions** — retain `status`, `reasons`, and `severity` columns for audit trails.

## Resources

### references/api_guide.md
Module-by-module API reference with signatures, return types, and patterns.

### references/rules_catalog.md
Catalog of available rules, alert sets, complexity metrics, and filter selection guidelines.

### scripts/filter_molecules.py
Batch filtering script for CSV/TSV/SDF/SMILES inputs with configurable rules, alerts, and complexity thresholds.

```bash
uv run python scripts/filter_molecules.py input.csv \
  --rules rule_of_five,rule_of_cns --pains --nibr --output filtered.csv
```

## Documentation

- Official docs: https://medchem-docs.datamol.io/
- GitHub: https://github.com/datamol-io/medchem
- PyPI: https://pypi.org/project/medchem/ (2.0.5)

## Agent operating procedure

1. **Check the environment.** Confirm toolkit versions and input formats (SMILES, SDF, PDB, CIF), and sanitize molecules before computing.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Process a few molecules or one target first and inspect the outputs.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Check for invalid structures, unit consistency, and applicability domain of predictive models.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Molecules fail to parse or sanitize | Report and skip them with reasons; never silently drop or alter structures. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Computational predictions are hypotheses, not experimental results; label them as such.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `datamol`: Wraps RDKit through the datamol Python library (import datamol as dm) for molecular cheminformatics, returning native rdkit.Chem.Mol object…
- `molfeat`: Converts SMILES strings or RDKit/datamol molecules into numerical features using molfeat (0.11.0), which provides calculators, scikit-learn…
- `rdkit`: Guides use of RDKit (Python) for reading and writing SMILES, MOL/SDF, and InChI, computing descriptors (MW, LogP, TPSA), generating Morgan/…
