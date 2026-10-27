# RDKit Workflows and Best Practices

Worked workflows (drug-likeness analysis, similarity screening, substructure filtering)
followed by error handling, performance optimization, version-sensitive behavior, thread
safety, and memory management.

## Common Workflows

### Drug-likeness Analysis

```python
from rdkit import Chem
from rdkit.Chem import Descriptors

def analyze_druglikeness(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    # Calculate Lipinski descriptors
    results = {
        'MW': Descriptors.MolWt(mol),
        'LogP': Descriptors.MolLogP(mol),
        'HBD': Descriptors.NumHDonors(mol),
        'HBA': Descriptors.NumHAcceptors(mol),
        'TPSA': Descriptors.TPSA(mol),
        'RotBonds': Descriptors.NumRotatableBonds(mol)
    }

    # Check Lipinski's Rule of Five
    results['Lipinski'] = (
        results['MW'] <= 500 and
        results['LogP'] <= 5 and
        results['HBD'] <= 5 and
        results['HBA'] <= 10
    )

    return results
```

### Similarity Screening

```python
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from rdkit import DataStructs

def similarity_screen(query_smiles, database_smiles, threshold=0.7):
    query_mol = Chem.MolFromSmiles(query_smiles)
    if query_mol is None:
        return []

    morgan_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    query_fp = morgan_gen.GetFingerprint(query_mol)

    hits = []
    for idx, smiles in enumerate(database_smiles):
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            fp = morgan_gen.GetFingerprint(mol)
            sim = DataStructs.TanimotoSimilarity(query_fp, fp)
            if sim >= threshold:
                hits.append((idx, smiles, sim))

    return sorted(hits, key=lambda x: x[2], reverse=True)
```

### Substructure Filtering

```python
from rdkit import Chem

def filter_by_substructure(smiles_list, pattern_smarts):
    query = Chem.MolFromSmarts(pattern_smarts)

    hits = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol and mol.HasSubstructMatch(query):
            hits.append(smiles)

    return hits
```

## Best Practices

### Error Handling

Always check for `None` when parsing molecules:

```python
mol = Chem.MolFromSmiles(smiles)
if mol is None:
    print(f"Failed to parse: {smiles}")
    continue
```

### Performance Optimization

**Use safe storage formats:**

```python
import base64
import json
from pathlib import Path
from rdkit import Chem

# Portable exchange formats such as SMILES and SDF are safest for shared data.
# For local caches, RDKit's binary molecule representation avoids generic pickle.
payload = [base64.b64encode(mol.ToBinary()).decode("ascii") for mol in mols]
Path("molecules.rdmol.json").write_text(json.dumps(payload))

cached = json.loads(Path("molecules.rdmol.json").read_text())
mols = [Chem.Mol(base64.b64decode(item)) for item in cached]
```

Do not load Python pickle files from untrusted sources. Pickle deserialization can execute arbitrary code; prefer SMILES/SDF for interchange and RDKit binary payloads for trusted local caches.

**Use bulk operations:**

```python
from rdkit import DataStructs
from rdkit.Chem import rdFingerprintGenerator

# Calculate fingerprints for all molecules at once
morgan_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
fps = [morgan_gen.GetFingerprint(mol) for mol in mols]

# Use bulk similarity calculations
similarities = DataStructs.BulkTanimotoSimilarity(fps[0], fps[1:])
```

### Version-Sensitive Behavior

Pin RDKit versions when exact molecular identifiers or numeric features are part of a persisted dataset, model feature pipeline, or regulated report. Recent releases changed or documented behavior in several Python-facing areas:

- **Canonical SMILES and stereo:** 2026.03 changed canonical double-bond handling to avoid stereo corruption, so some stereo-containing SMILES may differ from older releases.
- **Descriptors and hashes:** 2024.09 corrected unbranched-alkane fragment descriptor SMARTS and changed some tautomer/protomer hash outputs.
- **Drawing:** legacy `rdkit.Chem.Draw` canvas modules and functions such as `MolToImageFile`, `MolToMPL`, and `MolToQPixmap` were removed; use `Draw.MolToFile`, `Draw.MolToImage`, or `rdMolDraw2D`.
- **MolStandardize:** use `rdkit.Chem.MolStandardize.rdMolStandardize`; the older Python MolStandardize implementation was removed.
- **Similarity maps:** `GetSimilarityMapFromWeights()`, `GetSimilarityMapForFingerprint()`, and `GetSimilarityMapForModel()` now require an `rdMolDraw2D` drawing object.

### Thread Safety

RDKit operations are generally thread-safe for:
- Molecule I/O (SMILES, mol blocks)
- Coordinate generation
- Fingerprinting and descriptors
- Substructure searching
- Reactions
- Drawing

**Not thread-safe:** MolSuppliers when accessed concurrently.

### Memory Management

For large datasets:

```python
# Use ForwardSDMolSupplier to avoid loading entire file
with open('large.sdf') as f:
    suppl = Chem.ForwardSDMolSupplier(f)
    for mol in suppl:
        # Process one molecule at a time
        pass

# Use MultithreadedSDMolSupplier for parallel processing
suppl = Chem.MultithreadedSDMolSupplier('large.sdf', numWriterThreads=4)
```
