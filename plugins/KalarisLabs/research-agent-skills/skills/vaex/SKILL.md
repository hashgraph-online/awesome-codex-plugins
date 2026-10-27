---
name: vaex
description: Processes and analyzes tabular datasets too large for RAM using Vaex, a Python library for lazy, out-of-core DataFrames over memory-mapped HDF5 and Arrow files, with CSV and Parquet import/export. Covers virtual columns, filtering, groupby aggregations, large-data heatmaps and histograms, and vaex-ml transformers, PCA, and K-means. Use when opening or converting multi-gigabyte CSV/HDF5/Arrow/Parquet files, computing fast statistics on billions of rows, visualizing massive datasets, building ML pipelines that do not fit in memory, or speeding up slow aggregations with lazy evaluation and delay=True. Prefer polars when data fits in RAM, or dask for cluster-distributed work.
license: MIT
compatibility: Requires Python 3.10+ (3.12+ recommended with vaex 4.19.0). Install with uv pip install vaex. Optional s3fs/gcsfs/adlfs for cloud I/O.
allowed-tools: Read Write Edit Bash Grep Glob
metadata:
  version: '1.1'
  category: data-science-and-ml
  maintainer: Kalaris Labs
  tags: big data, out-of-core DataFrames, HDF5, data analysis, Python
---

# Vaex

## Overview

Vaex is a high-performance Python library designed for lazy, out-of-core DataFrames to process and visualize tabular datasets that are too large to fit into RAM. Vaex can process over a billion rows per second, enabling interactive data exploration and analysis on datasets with billions of rows.

## Installation

Install the full meta-package (recommended):

```bash
uv pip install vaex
```

Minimal install (pick only what you need):

```bash
uv pip install vaex-core vaex-viz vaex-hdf5 vaex-ml
```

The `vaex` package is a meta-package that pulls in `vaex-core`, `vaex-viz`, `vaex-hdf5`, `vaex-ml`, and other sub-packages. Arrow support is built into `vaex-core` (the separate `vaex-arrow` package is deprecated). `vaex-distributed` is deprecated in favor of vaex-enterprise.

**Version notes (vaex 4.19.0+):** Python 3.12 and NumPy v2 require vaex >= 4.19.0. On Windows, you may need Python dev headers to build the `annoy` dependency.

## When to Use This Skill

Use Vaex when:
- Processing tabular datasets larger than available RAM (gigabytes to terabytes)
- Performing fast statistical aggregations on massive datasets
- Creating visualizations and heatmaps of large datasets
- Building machine learning pipelines on big data
- Converting between data formats (CSV, HDF5, Arrow, Parquet)
- Needing lazy evaluation and virtual columns to avoid memory overhead
- Working with astronomical data, financial time series, or other large-scale scientific datasets

**Vaex vs alternatives:** Use **polars** when data fits in RAM and you need maximum in-memory speed. Use **dask** when you need distributed pandas/NumPy across a cluster. Use **vaex** for single-machine, out-of-core analytics on tabular data that exceeds RAM via memory-mapped HDF5/Arrow files.

## Core Capabilities

Vaex provides six primary capability areas, each documented in detail in the references directory:

### 1. DataFrames and Data Loading

Load and create Vaex DataFrames from various sources including files (HDF5, CSV, Arrow, Parquet), pandas DataFrames, NumPy arrays, and dictionaries. Reference `references/core_dataframes.md` for:
- Opening large files efficiently
- Converting from pandas/NumPy/Arrow
- Working with example datasets
- Understanding DataFrame structure

### 2. Data Processing and Manipulation

Perform filtering, create virtual columns, use expressions, and aggregate data without loading everything into memory. Reference `references/data_processing.md` for:
- Filtering and selections
- Virtual columns and expressions
- Groupby operations and aggregations
- String operations and datetime handling
- Working with missing data

### 3. Performance and Optimization

Leverage Vaex's lazy evaluation, caching strategies, and memory-efficient operations. Reference `references/performance.md` for:
- Understanding lazy evaluation
- Using `delay=True` for batching operations
- Materializing columns when needed
- Caching strategies
- Asynchronous operations

### 4. Data Visualization

Create interactive visualizations of large datasets including heatmaps, histograms, and scatter plots. Reference `references/visualization.md` for:
- Creating 1D and 2D plots
- Heatmap visualizations
- Working with selections
- Customizing plots and subplots

### 5. Machine Learning Integration

Build ML pipelines with transformers, encoders, and integration with scikit-learn, XGBoost, and other frameworks. Reference `references/machine_learning.md` for:
- Feature scaling and encoding
- PCA and dimensionality reduction
- K-means clustering
- Integration with scikit-learn/XGBoost/CatBoost
- Model serialization and deployment

### 6. I/O Operations

Efficiently read and write data in various formats with optimal performance. Reference `references/io_operations.md` for:
- File format recommendations
- Export strategies
- Working with Apache Arrow
- CSV handling for large files
- Server and remote data access

## Quick Start Pattern

For most Vaex tasks, follow this pattern:

```python
import vaex

# 1. Open or create DataFrame
df = vaex.open('large_file.hdf5')  # or .csv, .arrow, .parquet
# OR
df = vaex.from_pandas(pandas_df)

# 2. Explore the data
print(df)  # Shows first/last rows and column info
df.describe()  # Statistical summary

# 3. Create virtual columns (no memory overhead)
df['new_column'] = df.x ** 2 + df.y

# 4. Filter with selections
df_filtered = df[df.age > 25]

# 5. Compute statistics (fast, lazy evaluation)
mean_val = df.x.mean()
stats = df.groupby('category').agg({'value': 'sum'})

# 6. Visualize (df.viz is the recommended accessor since vaex 4.0)
df.viz.heatmap(df.x, df.y, limits='99.7%', show=True)
# Legacy: df.plot1d() and df.plot() still work on the DataFrame

# 7. Export if needed
df.export_hdf5('output.hdf5')
```

## Working with References

The reference files contain detailed information about each capability area. Load references into context based on the specific task:

- **Basic operations**: Start with `references/core_dataframes.md` and `references/data_processing.md`
- **Performance issues**: Check `references/performance.md`
- **Visualization tasks**: Use `references/visualization.md`
- **ML pipelines**: Reference `references/machine_learning.md`
- **File I/O**: Consult `references/io_operations.md`

## Best Practices

1. **Use HDF5 or Apache Arrow formats** for optimal performance with large datasets
2. **Leverage virtual columns** instead of materializing data to save memory
3. **Batch operations** using `delay=True` when performing multiple calculations
4. **Export to efficient formats** rather than keeping data in CSV
5. **Use expressions** for complex calculations without intermediate storage
6. **Profile with `df.describe()` and `df.nbytes`** to understand data shape and memory usage

## Common Patterns

### Pattern: Converting Large CSV to HDF5
```python
import vaex

# Open large CSV lazily (vaex 4.14+), or use from_csv to convert to HDF5
df = vaex.open('large_file.csv')
# df = vaex.from_csv('large_file.csv', convert='large_file.hdf5')

# Export to HDF5 for faster future access
df.export_hdf5('large_file.hdf5')

# Future loads are instant
df = vaex.open('large_file.hdf5')
```

### Pattern: Efficient Aggregations
```python
# Use delay=True to batch multiple operations
mean_x = df.x.mean(delay=True)
std_y = df.y.std(delay=True)
sum_z = df.z.sum(delay=True)

# Execute all at once
results = vaex.execute([mean_x, std_y, sum_z])
```

### Pattern: Virtual Columns for Feature Engineering
```python
# No memory overhead - computed on the fly
df['age_squared'] = df.age ** 2
df['full_name'] = df.first_name + ' ' + df.last_name
df['is_adult'] = df.age >= 18
```

## Resources

This skill includes reference documentation in the `references/` directory:

- `core_dataframes.md` - DataFrame creation, loading, and basic structure
- `data_processing.md` - Filtering, expressions, aggregations, and transformations
- `performance.md` - Optimization strategies and lazy evaluation
- `visualization.md` - Plotting and interactive visualizations
- `machine_learning.md` - ML pipelines and model integration
- `io_operations.md` - File formats and data import/export

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
- `polars-bio`: Python library polars-bio for genomic interval operations and bioinformatics file I/O on Polars DataFrames, built on Arrow and DataFusion.
- `dask`: Distributed computing for larger-than-RAM pandas/NumPy workflows.
