# Core Capabilities

Dask provides five main components, each suited to different use cases:

### 1. DataFrames - Parallel Pandas Operations

**Purpose**: Scale pandas operations to larger datasets through parallel processing.

**When to Use**:
- Tabular data exceeds available RAM
- Need to process multiple CSV/Parquet files together
- Pandas operations are slow and need parallelization
- Scaling from pandas prototype to production

**Reference Documentation**: For comprehensive guidance on Dask DataFrames, refer to `references/dataframes.md` which includes:
- Reading data (single files, multiple files, glob patterns)
- Common operations (filtering, groupby, joins, aggregations)
- Custom operations with `map_partitions`
- Performance optimization tips
- Common patterns (ETL, time series, multi-file processing)

**Quick Example**:
```python
import dask.dataframe as dd

# Read multiple files as single DataFrame
ddf = dd.read_csv('data/2024-*.csv')

# Operations are lazy until compute()
filtered = ddf[ddf['value'] > 100]
result = filtered.groupby('category').mean().compute()
```

**Key Points**:
- Operations are lazy (build task graph) until `.compute()` called
- Use `map_partitions` for efficient custom operations
- Convert to DataFrame early when working with structured data from other sources

### 2. Arrays - Parallel NumPy Operations

**Purpose**: Extend NumPy capabilities to datasets larger than memory using blocked algorithms.

**When to Use**:
- Arrays exceed available RAM
- NumPy operations need parallelization
- Working with scientific datasets (HDF5, Zarr, NetCDF)
- Need parallel linear algebra or array operations

**Reference Documentation**: For comprehensive guidance on Dask Arrays, refer to `references/arrays.md` which includes:
- Creating arrays (from NumPy, random, from disk)
- Chunking strategies and optimization
- Common operations (arithmetic, reductions, linear algebra)
- Custom operations with `map_blocks`
- Integration with HDF5, Zarr, and XArray

**Quick Example**:
```python
import dask.array as da

# Create large array with chunks
x = da.random.random((100000, 100000), chunks=(10000, 10000))

# Operations are lazy
y = x + 100
z = y.mean(axis=0)

# Compute result
result = z.compute()
```

**Key Points**:
- Chunk size is critical (aim for ~100 MB per chunk)
- Operations work on chunks in parallel
- Rechunk data when needed for efficient operations
- Use `map_blocks` for operations not available in Dask

### 3. Bags - Parallel Processing of Unstructured Data

**Purpose**: Process unstructured or semi-structured data (text, JSON, logs) with functional operations.

**When to Use**:
- Processing text files, logs, or JSON records
- Data cleaning and ETL before structured analysis
- Working with Python objects that don't fit array/dataframe formats
- Need memory-efficient streaming processing

**Reference Documentation**: For comprehensive guidance on Dask Bags, refer to `references/bags.md` which includes:
- Reading text and JSON files
- Functional operations (map, filter, fold, groupby)
- Converting to DataFrames
- Common patterns (log analysis, JSON processing, text processing)
- Performance considerations

**Quick Example**:
```python
import dask.bag as db
import json

# Read and parse JSON files
bag = db.read_text('logs/*.json').map(json.loads)

# Filter and transform
valid = bag.filter(lambda x: x['status'] == 'valid')
processed = valid.map(lambda x: {'id': x['id'], 'value': x['value']})

# Convert to DataFrame for analysis
ddf = processed.to_dataframe()
```

**Key Points**:
- Use for initial data cleaning, then convert to DataFrame/Array
- Use `foldby` instead of `groupby` for better performance
- Operations are streaming and memory-efficient
- Convert to structured formats (DataFrame) for complex operations

### 4. Futures - Task-Based Parallelization

**Purpose**: Build custom parallel workflows with fine-grained control over task execution and dependencies.

**When to Use**:
- Building dynamic, evolving workflows
- Need immediate task execution (not lazy)
- Computations depend on runtime conditions
- Implementing custom parallel algorithms
- Need stateful computations

**Reference Documentation**: For comprehensive guidance on Dask Futures, refer to `references/futures.md` which includes:
- Setting up distributed client
- Submitting tasks and working with futures
- Task dependencies and data movement
- Advanced coordination (queues, locks, events, actors)
- Common patterns (parameter sweeps, dynamic tasks, iterative algorithms)

**Quick Example**:
```python
from dask.distributed import Client

client = Client()  # Create local cluster

# Submit tasks (executes immediately)
def process(x):
    return x ** 2

futures = client.map(process, range(100))

# Gather results
results = client.gather(futures)

client.close()
```

**Key Points**:
- Requires distributed client (even for single machine)
- Tasks execute immediately when submitted
- Pre-scatter large data to avoid repeated transfers
- ~1ms overhead per task (not suitable for millions of tiny tasks)
- Use actors for stateful workflows

### 5. Schedulers - Execution Backends

**Purpose**: Control how and where Dask tasks execute (threads, processes, distributed).

**When to Choose Scheduler**:
- **Threads** (default): NumPy/Pandas operations, GIL-releasing libraries, shared memory benefit
- **Processes**: Pure Python code, text processing, GIL-bound operations
- **Synchronous**: Debugging with pdb, profiling, understanding errors
- **Distributed**: Need dashboard, multi-machine clusters, advanced features

**Reference Documentation**: For comprehensive guidance on Dask Schedulers, refer to `references/schedulers.md` which includes:
- Detailed scheduler descriptions and characteristics
- Configuration methods (global, context manager, per-compute)
- Performance considerations and overhead
- Common patterns and troubleshooting
- Thread configuration for optimal performance

**Quick Example**:
```python
import dask
import dask.dataframe as dd

# Use threads for DataFrame (default, good for numeric)
ddf = dd.read_csv('data.csv')
result1 = ddf.mean().compute()  # Uses threads

# Use processes for Python-heavy work
import dask.bag as db
bag = db.read_text('logs/*.txt')
result2 = bag.map(python_function).compute(scheduler='processes')

# Use synchronous for debugging
dask.config.set(scheduler='synchronous')
result3 = problematic_computation.compute()  # Can use pdb

# Use distributed for monitoring and scaling
from dask.distributed import Client
client = Client()
result4 = computation.compute()  # Uses distributed with dashboard
```

**Key Points**:
- Threads: Lowest overhead (~10 µs/task), best for numeric work
- Processes: Avoids GIL (~10 ms/task), best for Python work
- Distributed: Monitoring dashboard (~1 ms/task), scales to clusters
- Can switch schedulers per computation or globally
