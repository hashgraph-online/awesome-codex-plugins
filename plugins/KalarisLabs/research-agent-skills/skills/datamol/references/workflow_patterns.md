# Common Workflow Patterns

Three end-to-end pipelines: data loading through filtering to analysis, structure-activity
relationship analysis by scaffold series, and a virtual screening pipeline.

## Common Workflows and Patterns

### Complete Pipeline: Data Loading → Filtering → Analysis

```python
import datamol as dm
import pandas as pd

# 1. Load molecules
df = dm.read_sdf("compounds.sdf")

# 2. Standardize
df['mol'] = df['mol'].apply(lambda m: dm.standardize_mol(m) if m else None)
df = df[df['mol'].notna()]  # Remove failed molecules

# 3. Compute descriptors
desc_df = dm.descriptors.batch_compute_many_descriptors(
    df['mol'].tolist(),
    n_jobs=-1,
    progress=True
)

# 4. Filter by drug-likeness
druglike = (
    (desc_df['mw'] <= 500) &
    (desc_df['logp'] <= 5) &
    (desc_df['hbd'] <= 5) &
    (desc_df['hba'] <= 10)
)
filtered_df = df[druglike]

# 5. Cluster and select diverse subset
diverse_mols = dm.pick_diverse(
    filtered_df['mol'].tolist(),
    npick=100
)

# 6. Visualize results
dm.viz.to_image(
    diverse_mols,
    legends=[dm.to_smiles(m) for m in diverse_mols],
    outfile="diverse_compounds.png",
    n_cols=10
)
```

### Structure-Activity Relationship (SAR) Analysis

```python
# Group by scaffold
scaffolds = [dm.to_scaffold_murcko(mol) for mol in mols]
scaffold_smiles = [dm.to_smiles(s) for s in scaffolds]

# Create DataFrame with activities
sar_df = pd.DataFrame({
    'mol': mols,
    'scaffold': scaffold_smiles,
    'activity': activities  # User-provided activity data
})

# Analyze each scaffold series
for scaffold, group in sar_df.groupby('scaffold'):
    if len(group) >= 3:  # Need multiple examples
        print(f"\nScaffold: {scaffold}")
        print(f"Count: {len(group)}")
        print(f"Activity range: {group['activity'].min():.2f} - {group['activity'].max():.2f}")

        # Visualize with activities as legends
        dm.viz.to_image(
            group['mol'].tolist(),
            legends=[f"Activity: {act:.2f}" for act in group['activity']],
            align=True  # Align by common substructure
        )
```

### Virtual Screening Pipeline

```python
import numpy as np

# 1. Calculate Tanimoto distances between query actives and library
distances = dm.cdist(query_actives, library_mols, n_jobs=-1)

# 3. Find closest matches (min distance to any query)
min_distances = distances.min(axis=0)
similarities = 1 - min_distances  # Convert distance to similarity

# 4. Rank and select top hits
top_indices = np.argsort(similarities)[::-1][:100]  # Top 100
top_hits = [library_mols[i] for i in top_indices]
top_scores = [similarities[i] for i in top_indices]

# 5. Visualize hits
dm.viz.to_image(
    top_hits[:20],
    legends=[f"Sim: {score:.3f}" for score in top_scores[:20]],
    outfile="screening_hits.png"
)
```
