# Quick Start

Use this file for the smallest grounded AlphaGenome workflow.

## Install

Prefer an isolated Python environment, then install from a local clone:

```bash
python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
  || { echo "AlphaGenome requires Python >= 3.10"; exit 1; }

git clone https://github.com/google-deepmind/alphagenome.git
pip install ./alphagenome
```

If the repository is already present, install from that checkout instead of recloning.
If cloning is blocked by network policy, use a package-index fallback:

```bash
pip install alphagenome
```

## Create the client

Start from this minimal scaffold:

```python
import os
from alphagenome.data import genome
from alphagenome.models import dna_client

API_KEY = os.environ["ALPHAGENOME_API_KEY"]
model = dna_client.create(API_KEY)
```

## Run a minimal variant prediction

Use a variant workflow when the task is "compare REF vs ALT" or "estimate the effect of this mutation."

```python
import os
from alphagenome.data import genome
from alphagenome.models import dna_client

API_KEY = os.environ["ALPHAGENOME_API_KEY"]
model = dna_client.create(API_KEY)

position = 36_201_698
window = 16_384  # supported `predict_variant` width
start = position - 8_192
end = start + window

interval = genome.Interval(
    chromosome="chr22",
    start=start,
    end=end,
)
variant = genome.Variant(
    chromosome="chr22",
    position=position,
    reference_bases="A",
    alternate_bases="C",
)

outputs = model.predict_variant(
    interval=interval,
    variant=variant,
    ontology_terms=["UBERON:0001157"],
    requested_outputs=[dna_client.OutputType.RNA_SEQ],
)
```

Replace the coordinates, alleles, ontology term, and output list with task-specific values.

## Stay conservative

- Treat `predict_variant(...)` as the only grounded prediction call from the bundled source.
- Confirm any interval-only helper or additional output enum against the installed package or official docs before using it.
- Use a supported `predict_variant` interval width (currently `16384`, `131072`, `524288`, or `1048576` bp).
- Keep the requested interval at or below 1,000,000 base pairs.
- Avoid hardcoding API keys in scripts or notebooks.
