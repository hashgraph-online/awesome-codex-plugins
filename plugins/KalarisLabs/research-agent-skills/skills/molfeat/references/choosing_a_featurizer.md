# Choosing the Right Featurizer

Which featurizer suits traditional machine learning, deep learning, similarity searching,
and pharmacophore-based approaches, then worked workflows: building a QSAR model, a
virtual screening pipeline, similarity search, scikit-learn pipeline integration, and
comparing multiple featurizers.

## Choosing the Right Featurizer

### For Traditional Machine Learning (RF, SVM, XGBoost)

**Start with fingerprints:**
```python
# ECFP - Most popular, general-purpose
FPCalculator("ecfp", radius=3, fpSize=2048)

# MACCS - Fast, good for scaffold hopping
FPCalculator("maccs")

# MAP4 - Efficient for large-scale screening
FPCalculator("map4")
```

**For interpretable models:**
```python
# RDKit 2D descriptors (200+ named properties)
from molfeat.calc import RDKitDescriptors2D
RDKitDescriptors2D()

# Mordred (1800+ comprehensive descriptors)
from molfeat.calc import MordredDescriptors
MordredDescriptors()
```

**Combine multiple featurizers:**
```python
from molfeat.trans import FeatConcat

concat = FeatConcat([
    FPCalculator("maccs"),      # 167 dimensions
    FPCalculator("ecfp")         # 2048 dimensions
])  # Result: 2215-dimensional combined features
```

### For Deep Learning

**Transformer-based embeddings:**
```python
# ChemBERTa - Pre-trained on 77M PubChem compounds
PretrainedMolTransformer("ChemBERTa-77M-MLM")

# ChemGPT - Autoregressive language model
PretrainedMolTransformer("ChemGPT-1.2B")
```

**Graph neural networks:**
```python
# GIN models with different pre-training objectives
PretrainedMolTransformer("gin-supervised-masking")
PretrainedMolTransformer("gin-supervised-infomax")

# Graphormer for quantum chemistry
PretrainedMolTransformer("Graphormer-pcqm4mv2")
```

### For Similarity Searching

```python
# ECFP - General purpose, most widely used
FPCalculator("ecfp")

# MACCS - Fast, scaffold-based similarity
FPCalculator("maccs")

# MAP4 - Efficient for large databases
FPCalculator("map4")

# USR/USRCAT - 3D shape similarity
from molfeat.calc import USRDescriptors
USRDescriptors()
```

### For Pharmacophore-Based Approaches

```python
# FCFP - Functional group based
FPCalculator("fcfp")

# CATS - Pharmacophore pair distributions
from molfeat.calc import CATSCalculator
CATSCalculator(mode="2D")

# Gobbi - Explicit pharmacophore features
FPCalculator("gobbi2D")
```

## Common Workflows

### Building a QSAR Model

```python
from molfeat.trans import MoleculeTransformer
from molfeat.calc import FPCalculator
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score

# Featurize molecules
transformer = MoleculeTransformer(FPCalculator("ecfp"), n_jobs=-1)
X = transformer(smiles_train)

# Train model
model = RandomForestRegressor(n_estimators=100)
scores = cross_val_score(model, X, y_train, cv=5)
print(f"R² = {scores.mean():.3f}")

# Save configuration for deployment
transformer.to_state_yaml_file("production_featurizer.yml")
```

### Virtual Screening Pipeline

```python
from sklearn.ensemble import RandomForestClassifier

# Train on known actives/inactives
transformer = MoleculeTransformer(FPCalculator("ecfp"), n_jobs=-1)
X_train = transformer(train_smiles)
clf = RandomForestClassifier(n_estimators=500)
clf.fit(X_train, train_labels)

# Screen large library
X_screen = transformer(screening_library)  # e.g., 1M compounds
predictions = clf.predict_proba(X_screen)[:, 1]

# Rank and select top hits
top_indices = predictions.argsort()[::-1][:1000]
top_hits = [screening_library[i] for i in top_indices]
```

### Similarity Search

```python
from sklearn.metrics.pairwise import cosine_similarity

# Query molecule
calc = FPCalculator("ecfp")
query_fp = calc(query_smiles).reshape(1, -1)

# Database fingerprints
transformer = MoleculeTransformer(calc, n_jobs=-1)
database_fps = transformer(database_smiles)

# Compute similarity
similarities = cosine_similarity(query_fp, database_fps)[0]
top_similar = similarities.argsort()[-10:][::-1]
```

### Scikit-learn Pipeline Integration

```python
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

# Create end-to-end pipeline
pipeline = Pipeline([
    ('featurizer', MoleculeTransformer(FPCalculator("ecfp"), n_jobs=-1)),
    ('classifier', RandomForestClassifier(n_estimators=100))
])

# Train and predict directly on SMILES
pipeline.fit(smiles_train, y_train)
predictions = pipeline.predict(smiles_test)
```

### Comparing Multiple Featurizers

```python
featurizers = {
    'ECFP': FPCalculator("ecfp"),
    'MACCS': FPCalculator("maccs"),
    'Descriptors': RDKitDescriptors2D(),
    'ChemBERTa': PretrainedMolTransformer("ChemBERTa-77M-MLM")
}

results = {}
for name, feat in featurizers.items():
    transformer = MoleculeTransformer(feat, n_jobs=-1)
    X = transformer(smiles)
    # Evaluate with your ML model
    score = score_model(X, y)
    results[name] = score
```
