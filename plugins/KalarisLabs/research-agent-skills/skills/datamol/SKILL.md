---
name: datamol
description: Wraps RDKit through the datamol Python library (import datamol as dm) for molecular cheminformatics, returning native rdkit.Chem.Mol objects. Covers SMILES/SELFIES/InChI conversion, sanitization and standardization, descriptors, fingerprints and similarity, Butina clustering and diverse subset picking, Bemis-Murcko scaffolds, BRICS/RECAP fragmentation, 3D conformers, reactions, SDF/CSV/Excel I/O including cloud paths, and parallel batch processing. Use when parsing or standardizing SMILES from external sources, computing descriptors or fingerprints for a compound library, clustering or selecting diverse molecules, making scaffold-based train/test splits, or generating conformers. Use when running a molecule-processing pipeline with n_jobs. For fine-grained control or custom parameters, use RDKit directly instead.
license: Apache-2.0 license
compatibility: Requires Python 3.8+ and datamol (uv pip install). RDKit is installed automatically as a datamol dependency (since 0.12.2). Optional s3fs/gcsfs for cloud I/O via fsspec.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.2'
  category: chemistry-and-drug-discovery
  maintainer: Kalaris Labs
  tags: cheminformatics, RDKit, molecules, SMILES, drug discovery
---

# Datamol Cheminformatics Skill

## Overview

Datamol is a Python library that provides a lightweight, Pythonic abstraction layer over RDKit for molecular cheminformatics. Simplify complex molecular operations with sensible defaults, efficient parallelization, and modern I/O capabilities. All molecular objects are native `rdkit.Chem.Mol` instances, ensuring full compatibility with the RDKit ecosystem.

**Version note:** Examples target **datamol 0.12.x** (PyPI stable: **0.12.5**, June 2024). Since 0.10.0, modules are lazy-loaded by default (set `DATAMOL_DISABLE_LAZY_LOADING=1` to disable). Since 0.12.2, RDKit is a direct PyPI dependency of datamol. Fingerprints use RDKit's `rdFingerprintGenerator` API (0.12.5+).

**Key capabilities**:
- Molecular format conversion (SMILES, SELFIES, InChI)
- Structure standardization and sanitization
- Molecular descriptors and fingerprints
- 3D conformer generation and analysis
- Clustering and diversity selection
- Scaffold and fragment analysis
- Chemical reaction application
- Visualization and alignment
- Batch processing with parallelization
- Cloud storage support via fsspec

## Installation and Setup

Guide users to install datamol:

```bash
uv pip install datamol
```

RDKit is installed automatically with datamol. For remote file paths (S3, GCS, HTTP), install the matching fsspec backend:

```bash
uv pip install s3fs   # AWS S3
uv pip install gcsfs  # Google Cloud Storage
```

**Import convention**:
```python
import datamol as dm
```

## Core Workflows

Ten workflow areas, each with worked code, are documented in
[references/core_workflows.md](references/core_workflows.md):

| # | Area | Covers |
| --- | --- | --- |
| 1 | Basic molecule handling | `to_mol`, batch conversion, error handling, canonical and isomeric SMILES, sanitization and full standardization |
| 2 | Reading and writing files | SDF, SMILES, CSV, Excel with rendered structures, the universal reader/writer, and cloud or HTTPS paths |
| 3 | Descriptors and properties | the standard descriptor set, parallel computation, aromaticity, stereochemistry, flexibility, and filtering |
| 4 | Fingerprints and similarity | ECFP4 and other types, pairwise and cross-set distances, nearest-neighbour lookup (Tanimoto distance = 1 − similarity) |
| 5 | Clustering and diversity | similarity clustering, diverse subset picking, and cluster centroids |
| 6 | Scaffold analysis | Bemis-Murcko scaffolds, grouping and counting, and scaffold-disjoint train/test splits |
| 7 | Fragmentation | fragmenting molecules, finding common fragments across a library, and fragment-based scoring |
| 8 | 3D conformers | generation, access, RMSD clustering, representative selection, and SASA |
| 9 | Visualization | grids, files, publication SVG, substructure alignment, atom and bond highlighting, conformer display |
| 10 | Chemical reactions | reaction SMARTS, applying to a molecule or a whole library |

Three end-to-end pipelines — load/filter/analyze, SAR by scaffold series, and virtual
screening — are in [references/workflow_patterns.md](references/workflow_patterns.md).

## Parallelization

Datamol includes built-in parallelization for many operations. Use `n_jobs` parameter:
- `n_jobs=1`: Sequential (no parallelization)
- `n_jobs=-1`: Use all available CPU cores
- `n_jobs=4`: Use 4 cores

**Functions supporting parallelization**:
- `dm.read_sdf(..., n_jobs=-1)`
- `dm.descriptors.batch_compute_many_descriptors(..., n_jobs=-1)`
- `dm.cluster_mols(..., n_jobs=-1)`
- `dm.pdist(..., n_jobs=-1)`
- `dm.conformers.sasa(..., n_jobs=-1)`

**Progress bars**: Many batch operations support `progress=True` parameter.

## Reference Documentation

For detailed API documentation, consult these reference files:

- **`references/core_api.md`**: Core namespace functions (conversions, standardization, fingerprints, clustering)
- **`references/io_module.md`**: File I/O operations (read/write SDF, CSV, Excel, remote files)
- **`references/conformers_module.md`**: 3D conformer generation, clustering, SASA calculations
- **`references/descriptors_viz.md`**: Molecular descriptors and visualization functions
- **`references/fragments_scaffolds.md`**: Scaffold extraction, BRICS/RECAP fragmentation
- **`references/reactions_data.md`**: Chemical reactions and toy datasets

## Best Practices

1. **Always standardize molecules** from external sources:
   ```python
   mol = dm.standardize_mol(mol, disconnect_metals=True, normalize=True, reionize=True)
   ```

2. **Check for None values** after molecule parsing:
   ```python
   mol = dm.to_mol(smiles)
   if mol is None:
       # Handle invalid SMILES
   ```

3. **Use parallel processing** for large datasets:
   ```python
   result = dm.operation(..., n_jobs=-1, progress=True)
   ```

4. **Use cloud I/O only when requested** — confirm remote write paths; install `s3fs`/`gcsfs` as needed:
   ```python
   df = dm.read_sdf("s3://bucket/compounds.sdf")
   ```

5. **Use appropriate fingerprints** for similarity:
   - ECFP (Morgan): General purpose, structural similarity
   - MACCS: Fast, smaller feature space
   - Atom pairs: Considers atom pairs and distances

6. **Consider scale limitations**:
   - Butina clustering: ~1,000 molecules (full distance matrix)
   - For larger datasets: Use diversity selection or hierarchical methods

7. **Scaffold splitting for ML**: Ensure proper train/test separation by scaffold

8. **Align molecules** when visualizing SAR series

## Error Handling

```python
# Safe molecule creation
def safe_to_mol(smiles):
    try:
        mol = dm.to_mol(smiles)
        if mol is not None:
            mol = dm.standardize_mol(mol)
        return mol
    except Exception as e:
        print(f"Failed to process {smiles}: {e}")
        return None

# Safe batch processing
valid_mols = []
for smiles in smiles_list:
    mol = safe_to_mol(smiles)
    if mol is not None:
        valid_mols.append(mol)
```

## Integration with Machine Learning

Datamol ships with `scipy` and `scikit-learn` as dependencies. Import them as normal PyPI packages — they are not scripts bundled in this skill.

```python
import numpy as np

# Feature generation
X = np.array([dm.to_fp(mol) for mol in mols])

# Or descriptors
desc_df = dm.descriptors.batch_compute_many_descriptors(mols, n_jobs=-1)
X = desc_df.values

# Train model (scikit-learn PyPI package)
from sklearn.ensemble import RandomForestRegressor  # third-party library
model = RandomForestRegressor()
model.fit(X, y_target)

# Predict
predictions = model.predict(X_test)
```

## Troubleshooting

**Issue**: Molecule parsing fails
- **Solution**: Use `dm.standardize_smiles()` first or try `dm.fix_mol()`

**Issue**: Memory errors with clustering
- **Solution**: Use `dm.pick_diverse()` instead of full clustering for large sets

**Issue**: Slow conformer generation
- **Solution**: Reduce `n_confs` or increase `rms_cutoff` to generate fewer conformers

**Issue**: Remote file access fails
- **Solution**: Install the matching fsspec backend (`uv pip install s3fs` or `gcsfs`) and verify only the provider credentials needed for that backend are set (see Remote file support above)

## Additional Resources

- **Datamol Documentation**: https://docs.datamol.io/
- **RDKit Documentation**: https://www.rdkit.org/docs/
- **GitHub Repository**: https://github.com/datamol-io/datamol

## Related skills

- `rdkit`: Guides use of RDKit (Python) for reading and writing SMILES, MOL/SDF, and InChI, computing descriptors (MW, LogP, TPSA), generating Morgan/…
- `molfeat`: Converts SMILES strings or RDKit/datamol molecules into numerical features using molfeat (0.11.0), which provides calculators, scikit-learn…
- `medchem`: Filters and triages small-molecule libraries with the Python medchem library (datamol-io, v2.0.5) on top of RDKit and datamol.
