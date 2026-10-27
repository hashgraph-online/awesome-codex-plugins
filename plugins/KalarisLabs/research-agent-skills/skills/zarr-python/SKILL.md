---
name: zarr-python
description: Guides use of Zarr-Python 3 for storing chunked, compressed N-dimensional arrays and groups, with local, in-memory, ZIP, and fsspec-backed S3/GCS/HTTP stores, plus NumPy, Dask, and Xarray integration. Covers array creation, resizing and appending, attributes, chunk and shard sizing, codecs, consolidated metadata, and v2-to-v3 migration. Use when creating or opening Zarr arrays or groups, choosing chunk sizes or compression for large datasets, reading or writing arrays on S3 or GCS, appending to time-series arrays, or migrating code from Zarr-Python 2 to 3. Use when setting up parallel I/O with Dask or Xarray. For labeled multi-dimensional datasets, use Xarray instead.
license: MIT
compatibility: Requires Python 3.12+ and zarr 3.x. Cloud I/O needs zarr[remote] plus pinned s3fs or gcsfs. Legacy Zarr v2 workflows need exact 2.x pins on older Python.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.3'
  category: data-science-and-ml
  maintainer: Kalaris Labs
  tags: Zarr, chunked arrays, cloud storage, N-dimensional data, scientific data
---

# Zarr Python

## Overview

Zarr is a Python library for storing large N-dimensional arrays with chunking and compression. Apply this skill for efficient parallel I/O, cloud-native workflows, and seamless integration with NumPy, Dask, and Xarray.

**Current upstream:** zarr **3.2.1** (released 2026-05-05). Docs: [zarr.readthedocs.io](https://zarr.readthedocs.io/en/stable/). New arrays default to **Zarr format 3**; set `zarr_format=2` for legacy interop. Zarr 3.2 adds rectilinear chunks and continues to refine the v3 codec pipeline. This skill is a **community guide** maintained by Kalaris Labs, not an official zarr-developers package.

## Quick Start

### Installation

```bash
uv pip install "zarr==3.2.1"
```

Requires **Python 3.12+** and NumPy 2.0+ for current stable Zarr-Python. For remote stores (S3, GCS, HTTP), pin the optional extras/backends in your project lockfile:

```bash
uv pip install "zarr[remote]==3.2.1" "s3fs==2026.4.0" "gcsfs==2026.5.0"
```

Use a version range such as `zarr>=3,<4` only when your project has a committed lockfile and compatibility tests. For Zarr-Python 2 / Python 3.10–3.11 workflows, choose an exact `zarr==2.x.y` patch version from the support-v2 release notes and commit the resulting lockfile.

### Basic Array Creation

```python
import zarr
import numpy as np

# Create a 2D array with chunking and compression
z = zarr.create_array(
    store="data/my_array.zarr",
    shape=(10000, 10000),
    chunks=(1000, 1000),
    dtype="f4"
)

# Write data using NumPy-style indexing
z[:, :] = np.random.random((10000, 10000))

# Read data
data = z[0:100, 0:100]  # Returns NumPy array
```

## Core Operations

### Creating Arrays

Zarr provides multiple convenience functions for array creation:

```python
# Create empty array
z = zarr.zeros(shape=(10000, 10000), chunks=(1000, 1000), dtype='f4',
               store='data.zarr')

# Create filled arrays
z = zarr.ones((5000, 5000), chunks=(500, 500))
z = zarr.full((1000, 1000), fill_value=42, chunks=(100, 100))

# Create from existing data
data = np.arange(10000).reshape(100, 100)
z = zarr.array(data, chunks=(10, 10), store='data.zarr')

# Create like another array
z2 = zarr.zeros_like(z)  # Matches shape, chunks, dtype of z
```

### Opening Existing Arrays

```python
# Open array (read/write mode by default)
z = zarr.open_array('data.zarr', mode='r+')

# Read-only mode
z = zarr.open_array('data.zarr', mode='r')

# The open() function auto-detects arrays vs groups
z = zarr.open('data.zarr')  # Returns Array or Group
```

### Reading and Writing Data

Zarr arrays support NumPy-like indexing:

```python
# Write entire array
z[:] = 42

# Write slices
z[0, :] = np.arange(100)
z[10:20, 50:60] = np.random.random((10, 10))

# Read data (returns NumPy array)
data = z[0:100, 0:100]
row = z[5, :]

# Advanced indexing
z.vindex[[0, 5, 10], [2, 8, 15]]  # Coordinate indexing
z.oindex[0:10, [5, 10, 15]]       # Orthogonal indexing
z.blocks[0, 0]                     # Block/chunk indexing
```

### Resizing and Appending

```python
# Resize array (v3: pass shape as a tuple)
z.resize((15000, 15000))

# Append data along an axis
z.append(np.random.random((1000, 10000)), axis=0)  # Adds rows
```

## Groups and Hierarchies

Groups organize multiple arrays hierarchically, similar to directories or HDF5 groups.

### Creating and Using Groups

```python
# Create root group
root = zarr.group(store='data/hierarchy.zarr')

# Create sub-groups
temperature = root.create_group('temperature')
precipitation = root.create_group('precipitation')

# Create arrays within groups
temp_array = temperature.create_array(
    name='t2m',
    shape=(365, 720, 1440),
    chunks=(1, 720, 1440),
    dtype='f4'
)

precip_array = precipitation.create_array(
    name='prcp',
    shape=(365, 720, 1440),
    chunks=(1, 720, 1440),
    dtype='f4'
)

# Access using paths
array = root['temperature/t2m']

# Visualize hierarchy
print(root.tree())
# Output:
# /
#  ├── temperature
#  │   └── t2m (365, 720, 1440) f4
#  └── precipitation
#      └── prcp (365, 720, 1440) f4
```

### Group API (v3)

Use `create_array` / `require_array` (h5py-style `create_dataset` / `require_dataset` were removed in v3):

```python
root = zarr.group('data.zarr')
arr = root.create_array('my_data', shape=(1000, 1000), chunks=(100, 100), dtype='f4')

grp = root.require_group('subgroup')
arr2 = grp.require_array('array', shape=(500, 500), chunks=(50, 50), dtype='i4')
```

## Attributes and Metadata

Attach custom metadata to arrays and groups using attributes:

```python
# Add attributes to array
z = zarr.zeros((1000, 1000), chunks=(100, 100))
z.attrs['description'] = 'Temperature data in Kelvin'
z.attrs['units'] = 'K'
z.attrs['created'] = '2024-01-15'
z.attrs['processing_version'] = 2.1

# Attributes are stored as JSON
print(z.attrs['units'])  # Output: K

# Add attributes to groups
root = zarr.group('data.zarr')
root.attrs['project'] = 'Climate Analysis'
root.attrs['institution'] = 'Research Institute'

# Attributes persist with the array/group
z2 = zarr.open('data.zarr')
print(z2.attrs['description'])
```

**Important**: Attributes must be JSON-serializable (strings, numbers, lists, dicts, booleans, null).

## Chunking, Compression, Storage, and Performance

- [references/chunking_and_compression.md](references/chunking_and_compression.md):
  sizing chunks to the access pattern (aim for ~1 MB, 5-100 MB on cloud), sharding, and
  codec choice.
- [references/storage_backends.md](references/storage_backends.md): local, memory, ZIP,
  and fsspec remote stores (S3, GCS), with credential guidance — prefer IAM roles or
  workload identity, and never print credential values.
- [references/integration.md](references/integration.md): NumPy, Dask, and Xarray
  integration, thread safety, and consolidated metadata.
- [references/performance_and_patterns.md](references/performance_and_patterns.md):
  optimization, appendable time-series and large-matrix patterns, format conversion, and
  troubleshooting.
- [references/api_reference.md](references/api_reference.md) and
  [references/v3_migration.md](references/v3_migration.md): full API and the v2-to-v3
  migration notes.

## Additional Resources

### Bundled references

| File | Contents |
|------|----------|
| `references/api_reference.md` | Function signatures, stores, codecs, indexing |
| `references/v3_migration.md` | Zarr-Python 2→3 breaking changes and WIP features |

### Official upstream

- **Documentation**: https://zarr.readthedocs.io/en/stable/
- **3.0 migration guide**: https://zarr.readthedocs.io/en/stable/user-guide/v3_migration/
- **Storage backends**: https://zarr.readthedocs.io/en/stable/user-guide/storage/
- **Zarr specifications**: https://zarr-specs.readthedocs.io/
- **GitHub**: https://github.com/zarr-developers/zarr-python
- **Developer chat**: https://ossci.zulipchat.com/#narrow/channel/423692-Zarr-Python

**Related libraries:** [Xarray](https://docs.xarray.dev/), [Dask](https://docs.dask.org/), [NumCodecs](https://numcodecs.readthedocs.io/)

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

- `dask`: Distributed computing for larger-than-RAM pandas/NumPy workflows.
