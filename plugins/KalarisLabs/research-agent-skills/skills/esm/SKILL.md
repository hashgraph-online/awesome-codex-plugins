---
name: esm
description: 'Covers the EvolutionaryScale/Biohub `esm` Python SDK: ESM3 generative protein design (sequence, structure and function tracks, chain-of-thought), ESMC embeddings, inverse folding, ESMFold2 structure prediction, and hosted Forge/Biohub inference with ESM_API_KEY. Use when generating or completing proteins with ESM3, extracting ESMC embeddings for classification or similarity, folding a sequence or designing sequences from a structure, or choosing between esm3-open, esmc_300m and Forge-hosted models. Use when batching async Forge or Biohub API calls. Not for other protein models such as AlphaFold or generic Hugging Face transformers usage.'
license: MIT
metadata:
  version: '1.2'
  category: life-sciences
  maintainer: Kalaris Labs
  tags: protein language models, protein design, structure prediction, protein embeddings
---

# ESM: Evolutionary Scale Modeling

## Overview

ESM provides protein language models for understanding, generating, and designing proteins. Use this skill for current EvolutionaryScale/Biohub workflows: ESM3 for generative design, ESMC for representation learning and embeddings, hosted Forge/Biohub inference, and ESMFold2 all-atom structure prediction.

## Core Capabilities

### 1. Protein Sequence Generation with ESM3

Generate novel protein sequences with desired properties using multimodal generative modeling.

**When to use:**
- Designing proteins with specific functional properties
- Completing partial protein sequences
- Generating variants of existing proteins
- Creating proteins with desired structural characteristics

**Basic usage:**

```python
from esm.models.esm3 import ESM3
from esm.sdk.api import ESM3InferenceClient, ESMProtein, GenerationConfig

# Load local open weights after accepting the license on Hugging Face.
model: ESM3InferenceClient = ESM3.from_pretrained("esm3-open").to("cuda")

# Create protein prompt
protein = ESMProtein(sequence="MPRT___KEND")  # '_' represents masked positions

# Generate completion
protein = model.generate(protein, GenerationConfig(track="sequence", num_steps=8))
print(protein.sequence)
```

**For remote/cloud usage via Forge API:**

```python
import os
import esm
from esm.sdk.api import ESMProtein, GenerationConfig

# Same interface as local ESM3; token from ESM_API_KEY (see Authentication)
model = esm.sdk.client("esm3-medium-2024-08", token=os.environ["ESM_API_KEY"])

# Generate
protein = model.generate(protein, GenerationConfig(track="sequence", num_steps=8))
```

See `references/esm3-api.md` for detailed ESM3 model specifications, advanced generation configurations, and multimodal prompting examples.

### 2. Structure Prediction and Inverse Folding

Use ESM3's structure track for structure prediction from sequence or inverse folding (sequence design from structure).

**Structure prediction:**

```python
from esm.sdk.api import ESM3InferenceClient, ESMProtein, GenerationConfig

# Predict structure from sequence
protein = ESMProtein(sequence="MPRTKEINDAGLIVHSP...")
protein_with_structure = model.generate(
    protein,
    GenerationConfig(track="structure", num_steps=protein.sequence.count("_"))
)

# Access predicted structure
coordinates = protein_with_structure.coordinates  # 3D coordinates
pdb_string = protein_with_structure.to_pdb()
```

**Inverse folding (sequence from structure):**

```python
# Design sequence for a target structure
protein_with_structure = ESMProtein.from_pdb("target_structure.pdb")
protein_with_structure.sequence = None  # Remove sequence

# Generate sequence that folds to this structure
designed_protein = model.generate(
    protein_with_structure,
    GenerationConfig(track="sequence", num_steps=50, temperature=0.7)
)
```

### 3. Protein Embeddings with ESM C

Generate high-quality embeddings for downstream tasks like function prediction, classification, or similarity analysis.

**When to use:**
- Extracting protein representations for machine learning
- Computing sequence similarities
- Feature extraction for protein classification
- Transfer learning for protein-related tasks

**Basic usage:**

```python
from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein, LogitsConfig

# Load ESM C model
model = ESMC.from_pretrained("esmc_300m").to("cuda")

# Get embeddings
protein = ESMProtein(sequence="MPRTKEINDAGLIVHSP...")
protein_tensor = model.encode(protein)
logits_output = model.logits(
    protein_tensor,
    LogitsConfig(sequence=True, return_embeddings=True),
)
embeddings = logits_output.embeddings
```

**Batch processing:**

```python
# Encode multiple proteins
proteins = [
    ESMProtein(sequence="MPRTKEIND..."),
    ESMProtein(sequence="AGLIVHSPQ..."),
    ESMProtein(sequence="KTEFLNDGR...")
]

embeddings_list = [
    model.logits(
        model.encode(p),
        LogitsConfig(sequence=True, return_embeddings=True),
    ).embeddings
    for p in proteins
]
```

See `references/esm-c-api.md` for ESM C model details, efficiency comparisons, and advanced embedding strategies.

### 4. Function Conditioning and Annotation

Use ESM3's function track to generate proteins with specific functional annotations or predict function from sequence.

**Function-conditioned generation:**

```python
from esm.sdk.api import ESMProtein, FunctionAnnotation, GenerationConfig

# Create protein with desired function
protein = ESMProtein(
    sequence="_" * 200,  # Generate 200 residue protein
    function_annotations=[
        FunctionAnnotation(label="fluorescent_protein", start=50, end=150)
    ]
)

# Generate sequence with specified function
functional_protein = model.generate(
    protein,
    GenerationConfig(track="sequence", num_steps=200)
)
```

### 5. Chain-of-Thought Generation

Iteratively refine protein designs using ESM3's chain-of-thought generation approach.

```python
from esm.sdk.api import GenerationConfig

# Multi-step refinement
protein = ESMProtein(sequence="MPRT" + "_" * 100 + "KEND")

# Step 1: Generate initial structure
config = GenerationConfig(track="structure", num_steps=50)
protein = model.generate(protein, config)

# Step 2: Refine sequence based on structure
config = GenerationConfig(track="sequence", num_steps=50, temperature=0.5)
protein = model.generate(protein, config)

# Step 3: Predict function
config = GenerationConfig(track="function", num_steps=20)
protein = model.generate(protein, config)
```

### 6. Batch Processing with Forge API

Process multiple proteins efficiently using Forge's async methods.

```python
import os
import asyncio
import esm
from esm.sdk.api import ESMProtein, GenerationConfig

client = esm.sdk.client("esm3-medium-2024-08", token=os.environ["ESM_API_KEY"])

# Async batch processing
async def batch_generate(proteins_list):
    tasks = [
        client.async_generate(protein, GenerationConfig(track="sequence"))
        for protein in proteins_list
    ]
    return await asyncio.gather(*tasks)

# Execute
proteins = [ESMProtein(sequence=f"MPRT{'_' * 50}KEND") for _ in range(10)]
results = asyncio.run(batch_generate(proteins))
```

See `references/forge-api.md` for detailed Forge API documentation, authentication, rate limits, and batch processing patterns.

## Model Selection Guide

**ESM3 Models (Generative):**
- `esm3-open` (1.4B) - Open weights, local usage after accepting the Hugging Face license
- `esm3-medium-2024-08` (7B) - Best balance of quality and speed (Forge only)
- `esm3-large-2024-03` (98B) - Highest quality, slower (Forge only)

**ESM C Models (Embeddings):**
- `esmc_300m` / `esmc-300m-2024-12` (30 layers) - Lightweight, fast inference (open weights, local)
- `esmc_600m` / `esmc-600m-2024-12` (36 layers) - Balanced performance (open weights, local)
- `esmc-6b-2024-12` (80 layers) - Maximum quality (Forge API; local 6B weights require Forge or SageMaker)

Local `ESMC.from_pretrained()` examples use underscore aliases (`esmc_300m`, `esmc_600m`). Hosted API clients use dated model IDs such as `esmc-600m-2024-12`.

**Selection criteria:**
- **Local development/testing:** Use `esm3-open` or `esmc_300m`
- **Production quality:** Use `esm3-medium-2024-08` via Forge
- **Maximum accuracy:** Use `esm3-large-2024-03` or `esmc-6b-2024-12` via Forge
- **High throughput:** Use Forge or Biohub APIs with explicit async concurrency limits
- **Cost optimization:** Use smaller models, implement caching strategies

## Installation

Install from PyPI ([`esm` on PyPI](https://pypi.org/project/esm/) by EvolutionaryScale). Current PyPI release: **3.2.3** (Oct 14, 2025). Requires **Python >=3.12,<3.13**.

**Basic installation:**

```bash
uv pip install "esm==3.2.3"
```

**With Flash Attention (recommended for faster inference on NVIDIA GPUs):**

```bash
uv pip install "esm==3.2.3"
uv pip install flash-attn --no-build-isolation
```

The Forge client ships with the `esm` package - no extra install for ESM3 or ESMC Forge inference.

## Authentication

Forge API access requires an API key. Never hardcode tokens in scripts or commit them to version control.

1. Check whether `ESM_API_KEY` is already set in the environment.
2. If not, check a local `.env` for `ESM_API_KEY` only (do not load unrelated secrets).
3. If still missing, create a key in the [Biohub developer console](https://biohub.ai/developer-console/api-keys) for Biohub APIs or [Forge](https://forge.evolutionaryscale.ai) for legacy Forge-hosted ESM3/ESMC access.

```python
import os

token = os.environ["ESM_API_KEY"]  # raises KeyError if unset
```

`esm.sdk.client()` reads `ESM_API_KEY` automatically when `token` is omitted. Keep endpoint URLs fixed to trusted hosts such as `https://forge.evolutionaryscale.ai` or `https://biohub.ai`; do not take API hosts from untrusted user input.

**Biohub platform:** EvolutionaryScale and Forge now surface current hosted models through [biohub.ai](https://biohub.ai). SDK class names may still reference "Forge". See `references/biohub-platform.md` for ESMFold2 and Biohub-specific setup.

## Common Workflows

For detailed examples and complete workflows, see `references/workflows.md` which includes:
- Novel GFP design with chain-of-thought
- Protein variant generation and screening
- Structure-based sequence optimization
- Function prediction pipelines
- Embedding-based clustering and analysis

## References

This skill includes comprehensive reference documentation:

- `references/esm3-api.md` - ESM3 model architecture, API reference, generation parameters, and multimodal prompting
- `references/esm-c-api.md` - ESM C model details, embedding strategies, and performance optimization
- `references/forge-api.md` - Forge platform documentation, authentication, batch processing, and deployment
- `references/biohub-platform.md` - Biohub API migration, ESMFold2 structure prediction, and developer-console auth
- `references/workflows.md` - Complete examples and common workflow patterns

These references contain detailed API specifications, parameter descriptions, and advanced usage patterns. Load them as needed for specific tasks.

## Best Practices

**For generation tasks:**
- Start with smaller models for prototyping (`esm3-open`)
- Use temperature parameter to control diversity (0.0 = deterministic, 1.0 = diverse)
- Implement iterative refinement with chain-of-thought for complex designs
- Validate generated sequences with structure prediction or wet-lab experiments

**For embedding tasks:**
- Batch process sequences when possible for efficiency
- Cache embeddings for repeated analyses
- Normalize embeddings when computing similarities
- Use appropriate model size based on downstream task requirements

**For production deployment:**
- Use Forge API for scalability and latest models
- Implement error handling and retry logic for API calls
- Monitor token usage and implement rate limiting
- Consider AWS SageMaker deployment for dedicated infrastructure

## Resources and Documentation

- **GitHub Repository:** https://github.com/Biohub/esm (current ESMC/ESMFold2/Biohub docs; ESM3 docs remain linked from the repository)
- **Forge Platform:** https://forge.evolutionaryscale.ai
- **Biohub Platform:** https://biohub.ai
- **Scientific Paper:** Hayes et al., Science (2025) - https://www.science.org/doi/10.1126/science.ads0018
- **Blog Posts:**
  - ESM3 Release: https://www.evolutionaryscale.ai/blog/esm3-release
  - ESM C Launch: https://www.evolutionaryscale.ai/blog/esm-cambrian
- **Community:** Slack community at https://bit.ly/3FKwcWd
- **Model Weights:** Hugging Face EvolutionaryScale and Biohub organizations

## Responsible Use

ESM is designed for beneficial applications in protein engineering, drug discovery, and scientific research. Follow the Responsible Biodesign Framework (https://responsiblebiodesign.ai/) and Biohub Acceptable Use Policy (https://biohub.org/acceptable-use-policy/) when designing novel proteins. Consider biosafety and ethical implications of protein designs before experimental validation.

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

- `sentence-transformers`: Generates sentence, text, and image embeddings locally with the Python sentence-transformers (SBERT) library, using pre-trained Hugging Fac…
- `adaptyv`: How to use the Adaptyv Bio Foundry API and Python SDK for protein experiment design, submission, and results retrieval.
- `tamarind`: Access a collection of open-source molecular design and structural biology tools on the Tamarind Bio platform, via its REST API or MCP serv…
