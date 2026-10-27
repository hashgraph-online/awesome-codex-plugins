---
name: dask
description: Distributed computing for larger-than-RAM pandas/NumPy workflows. Use when you need to scale existing pandas/NumPy code beyond memory or across clusters. Best for parallel file processing, distributed ML, integration with existing pandas code. For out-of-core analytics on single machine use vaex; for in-memory speed use polars.
license: BSD-3-Clause license
compatibility: Requires Python 3.10+ and dask 2025.1+. DataFrame workflows need pandas 2+ and PyArrow 16+. Cloud paths (s3://, gcs://) need s3fs or gcsfs. Cluster deployment uses dask.distributed (included with dask[complete]).
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.2'
  category: data-science-and-ml
  maintainer: Kalaris Labs
  tags: parallel computing, big data, pandas, distributed computing, data science
---

# Dask

## Overview

Dask is a Python library for parallel and distributed computing that enables three critical capabilities:
- **Larger-than-memory execution** on single machines for data exceeding available RAM
- **Parallel processing** for improved computational speed across multiple cores
- **Distributed computation** supporting terabyte-scale datasets across multiple machines

Dask scales from laptops (processing ~100 GiB) to clusters (processing ~100 TiB) while maintaining familiar Python APIs.

**Current upstream:** dask **2026.3.0** (PyPI, March 2026). Docs: [docs.dask.org](https://docs.dask.org/en/stable/). Since **2025.1.0**, the expression-based DataFrame API with query planning is the only implementation — do not install `dask-expr` separately or set `dataframe.query-planning: False`.

## Quick Start

### Installation

```bash
uv pip install "dask>=2025.1"
```

For a typical pandas/NumPy workflow with the distributed scheduler and dashboard:

```bash
uv pip install "dask[complete]"
```

Remote object storage (S3, GCS, Azure):

```bash
uv pip install s3fs    # s3:// paths
uv pip install gcsfs   # gs:// paths
```

Requires **Python 3.10+** (3.9 support dropped in 2024.12). DataFrame I/O requires **PyArrow 16+** (as of dask 2026.1.2).

## When to Use This Skill

This skill should be used when:
- Process datasets that exceed available RAM
- Scale pandas or NumPy operations to larger datasets
- Parallelize computations for performance improvements
- Process multiple files efficiently (CSVs, Parquet, JSON, text logs)
- Build custom parallel workflows with task dependencies
- Distribute workloads across multiple cores or machines

## Core Capabilities

Details, code examples and parameter tables: [references/core-capabilities.md](references/core-capabilities.md). Read it when this step applies.

## Best Practices

For comprehensive performance optimization guidance, memory management strategies, and common pitfalls to avoid, refer to `references/best-practices.md`. Key principles include:

### Start with Simpler Solutions
Before using Dask, explore:
- Better algorithms
- Efficient file formats (Parquet instead of CSV)
- Compiled code (Numba, Cython)
- Data sampling

### Critical Performance Rules

**1. Don't Load Data Locally Then Hand to Dask**
```python
# Wrong: Loads all data in memory first
import pandas as pd
df = pd.read_csv('large.csv')
ddf = dd.from_pandas(df, npartitions=10)

# Correct: Let Dask handle loading
import dask.dataframe as dd
ddf = dd.read_csv('large.csv')
```

**2. Avoid Repeated compute() Calls**
```python
# Wrong: Each compute is separate
for item in items:
    result = dask_computation(item).compute()

# Correct: Single compute for all
computations = [dask_computation(item) for item in items]
results = dask.compute(*computations)
```

**3. Don't Build Excessively Large Task Graphs**
- Increase chunk sizes if millions of tasks
- Use `map_partitions`/`map_blocks` to fuse operations
- Check task graph size: `len(ddf.__dask_graph__())`

**4. Choose Appropriate Chunk Sizes**
- Target: ~100 MB per chunk (or 10 chunks per core in worker memory)
- Too large: Memory overflow
- Too small: Scheduling overhead

**5. Use the Dashboard**
```python
from dask.distributed import Client
client = Client()
print(client.dashboard_link)  # Monitor performance, identify bottlenecks
```

## Common Workflow Patterns

### ETL Pipeline
```python
import dask.dataframe as dd

# Extract: Read data
ddf = dd.read_csv('raw_data/*.csv')

# Transform: Clean and process
ddf = ddf[ddf['status'] == 'valid']
ddf['amount'] = ddf['amount'].astype('float64')
ddf = ddf.dropna(subset=['important_col'])

# Load: Aggregate and save
summary = ddf.groupby('category').agg({'amount': ['sum', 'mean']})
summary.to_parquet('output/summary.parquet')
```

### Unstructured to Structured Pipeline
```python
import dask.bag as db
import json

# Start with Bag for unstructured data
bag = db.read_text('logs/*.json').map(json.loads)
bag = bag.filter(lambda x: x['status'] == 'valid')

# Convert to DataFrame for structured analysis
ddf = bag.to_dataframe()
result = ddf.groupby('category').mean().compute()
```

### Large-Scale Array Computation
```python
import dask.array as da

# Load or create large array
x = da.from_zarr('large_dataset.zarr')

# Process in chunks
normalized = (x - x.mean()) / x.std()

# Save result (use mode= for overwrite; zarr_array_kwargs for compression)
da.to_zarr(normalized, 'normalized.zarr', mode='w')
```

### Custom Parallel Workflow
```python
from dask.distributed import Client

client = Client()

# Scatter large dataset once
data = client.scatter(large_dataset)

# Process in parallel with dependencies
futures = []
for param in parameters:
    future = client.submit(process, data, param)
    futures.append(future)

# Gather results
results = client.gather(futures)
```

## Selecting the Right Component

Use this decision guide to choose the appropriate Dask component:

**Data Type**:
- Tabular data → **DataFrames**
- Numeric arrays → **Arrays**
- Text/JSON/logs → **Bags** (then convert to DataFrame)
- Custom Python objects → **Bags** or **Futures**

**Operation Type**:
- Standard pandas operations → **DataFrames**
- Standard NumPy operations → **Arrays**
- Custom parallel tasks → **Futures**
- Text processing/ETL → **Bags**

**Control Level**:
- High-level, automatic → **DataFrames/Arrays**
- Low-level, manual → **Futures**

**Workflow Type**:
- Static computation graph → **DataFrames/Arrays/Bags**
- Dynamic, evolving → **Futures**

## Integration Considerations

### File Formats
- **Efficient**: Parquet, HDF5, Zarr (columnar, compressed, parallel-friendly)
- **Compatible but slower**: CSV (use for initial ingestion only)
- **For Arrays**: HDF5, Zarr, NetCDF

### Conversion Between Collections
```python
# Bag → DataFrame
ddf = bag.to_dataframe()

# DataFrame → Array (for numeric data)
arr = ddf.to_dask_array(lengths=True)

# Array → DataFrame
ddf = dd.from_dask_array(arr, columns=['col1', 'col2'])
```

### With Other Libraries
- **XArray**: Wraps Dask arrays with labeled dimensions (geospatial, imaging)
- **Dask-ML**: Machine learning with scikit-learn compatible APIs
- **Distributed**: Advanced cluster management and monitoring

## Debugging and Development

### Iterative Development Workflow

1. **Test on small data with synchronous scheduler**:
```python
dask.config.set(scheduler='synchronous')
result = computation.compute()  # Can use pdb, easy debugging
```

2. **Validate with threads on sample**:
```python
sample = ddf.head(1000)  # Small sample
# Test logic, then scale to full dataset
```

3. **Scale with distributed for monitoring**:
```python
from dask.distributed import Client
client = Client()
print(client.dashboard_link)  # Monitor performance
result = computation.compute()
```

### Common Issues

**Memory Errors**:
- Decrease chunk sizes
- Use `persist()` strategically and delete when done
- Check for memory leaks in custom functions

**Slow Start**:
- Task graph too large (increase chunk sizes)
- Use `map_partitions` or `map_blocks` to reduce tasks

**Poor Parallelization**:
- Chunks too large (increase number of partitions)
- Using threads with Python code (switch to processes)
- Data dependencies preventing parallelism

## Reference Files

All reference documentation files can be read as needed for detailed information:

- `references/dataframes.md` - Complete Dask DataFrame guide
- `references/arrays.md` - Complete Dask Array guide
- `references/bags.md` - Complete Dask Bag guide
- `references/futures.md` - Complete Dask Futures and distributed computing guide
- `references/schedulers.md` - Complete scheduler selection and configuration guide
- `references/best-practices.md` - Comprehensive performance optimization and troubleshooting

Load these files when users need detailed information about specific Dask components, operations, or patterns beyond the quick guidance provided here.

## Agent operating procedure

1. **Check the environment.** Confirm the Python environment and library versions (`python -c "import pkg; print(pkg.__version__)"`) and inspect the data's shape, types and missing values.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Run on a sample or a single fold first and check runtime and memory.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Use held-out data, fixed random seeds and appropriate metrics; check for leakage; report uncertainty (CIs, std over seeds).
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Out-of-memory or very slow execution | Subsample, use chunked or lazy computation, or reduce model size, and tell the user what changed. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never report a metric you did not compute in this session; show the code path that produced every number.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `polars`: High-performance DataFrame library for Python ETL, analytics, and pandas migration.
- `ray-data`: Scalable data processing for ML workloads.
- `ray-train`: Distributed training orchestration across clusters.
