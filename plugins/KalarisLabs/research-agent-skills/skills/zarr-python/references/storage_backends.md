# Storage Backends

LocalStore, MemoryStore, ZipStore, and fsspec-backed remote stores (S3, GCS), including
credential handling guidance.

## Storage Backends

Zarr supports multiple storage backends through a flexible storage interface.

### Local Filesystem (Default)

```python
from zarr.storage import LocalStore

# Explicit store creation
store = LocalStore('data/my_array.zarr')
z = zarr.open_array(store=store, mode='w', shape=(1000, 1000), chunks=(100, 100))

# Or use string path (creates LocalStore automatically)
z = zarr.open_array('data/my_array.zarr', mode='w', shape=(1000, 1000),
                    chunks=(100, 100))
```

### In-Memory Storage

```python
from zarr.storage import MemoryStore

# Create in-memory store
store = MemoryStore()
z = zarr.open_array(store=store, mode='w', shape=(1000, 1000), chunks=(100, 100))

# Data exists only in memory, not persisted
```

### ZIP File Storage

```python
from zarr.storage import ZipStore

# Write to ZIP file
store = ZipStore('data.zip', mode='w')
z = zarr.open_array(store=store, mode='w', shape=(1000, 1000), chunks=(100, 100))
z[:] = np.random.random((1000, 1000))
store.close()  # IMPORTANT: Must close ZipStore

# Read from ZIP file
store = ZipStore('data.zip', mode='r')
z = zarr.open_array(store=store)
data = z[:]
store.close()
```

### Cloud Storage (S3, GCS)

Zarr 3 uses **fsspec** backends via URI strings or `FsspecStore` (preferred over legacy `S3Map`/`GCSMap`).

```python
import zarr

# S3 — prefer IAM roles/profiles; fsspec handles provider credential discovery.
# Never print, log, or copy credential values into prompts or notebooks.
z = zarr.create_array(
    store="s3://my-bucket/path/to/array.zarr",
    shape=(1000, 1000),
    chunks=(100, 100),
    dtype="f4",
    storage_options={"anon": False},
)
z[:] = data

# GCS — prefer workload identity or gcloud application-default credentials.
z = zarr.open_array(
    "gs://my-bucket/path/to/array.zarr",
    mode="r",
    storage_options={"project": "my-project"},
)

# Explicit store (any fsspec filesystem)
from zarr.storage import FsspecStore
store = FsspecStore.from_url("s3://my-bucket/data.zarr", storage_options={"anon": False})
root = zarr.open_group(store=store, mode="r+")
```

Cloud backends read credentials through the provider SDK/fsspec backend. Do not inspect broad `.env` files; if a user explicitly needs help debugging auth, ask for redacted configuration and read only the named provider variables they approve. Treat all `import zarr`, `import dask`, `import h5py`, and `import xarray` examples as third-party package imports, not bundled script files.

**Cloud Storage Best Practices**:
- Use consolidated metadata to reduce latency: `zarr.consolidate_metadata(store)`
- Align chunk sizes with cloud object sizing (typically 5-100 MB optimal)
- Enable parallel writes using Dask for large-scale data
- Consider sharding to reduce number of objects
