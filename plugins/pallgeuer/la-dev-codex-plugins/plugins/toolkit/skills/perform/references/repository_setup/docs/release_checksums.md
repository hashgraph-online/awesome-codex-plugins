# Release checksum manifests

`la-dev-codex-plugins` includes a dependency-free SHA-256 manifest library and command for generic release artifacts. It preserves caller order, validates artifact identity and portable basenames, writes exact UTF-8/LF bytes, invalidates stale output after proving the target safe, and atomically installs the completed replacement.

A checksum manifest is a small text file that binds each release filename to the SHA-256 digest of its exact contents. Publish it beside a release so that people and automation can detect an incomplete or corrupted download, the wrong artifact, or bytes that no longer match the release you checksummed.

For example, after building a wheel and source archive:

```console
$ la-dev-release-checksums --output dist/SHA256SUMS dist/acme-1.2.0-py3-none-any.whl dist/acme-1.2.0.tar.gz
68d131bc271e1d0a72f9dbe17db0f0f2efcbed8eb2a9fbd827bca42d9b44d58a  acme-1.2.0-py3-none-any.whl
34c3b311c6c136e453dc9fec4cf927d5f06b1d6c23af1b78357e224ecb04a378  acme-1.2.0.tar.gz
```

The command writes those same lines to `dist/SHA256SUMS`. After downloading all three files into one directory, a recipient can verify both artifacts at once:

```console
$ sha256sum --check SHA256SUMS
acme-1.2.0-py3-none-any.whl: OK
acme-1.2.0.tar.gz: OK
```

Any changed byte produces a failed check. The manifest is evidence only relative to a trusted copy of the manifest: publishing artifacts and `SHA256SUMS` through the same compromised channel does not by itself prove who produced them. Sign the manifest or distribute its digest through a separately trusted channel when authenticity is required.

## Library API

Import the public API from `la_dev_codex_plugins.release_checksums`:

```python
from la_dev_codex_plugins import release_checksums

artifacts = ["dist/package.whl", "dist/package.tar.gz"]
manifest = release_checksums.generate_sha256_manifest(artifacts)
persisted = release_checksums.write_sha256_manifest(artifacts, "dist/SHA256SUMS")
assert persisted == manifest
```

`generate_sha256_manifest(artifacts)` validates and hashes without writing. `write_sha256_manifest(artifacts, output)` applies the target-safety and stale-output policy before atomically writing. Expected coercion, validation, hashing, cleanup, and output failures, including invalid filesystem path representations, raise `ReleaseChecksumError` with a concise path-aware message and preserve the originating expected exception through exception chaining.

A scalar text string or text-returning `os.PathLike` is one artifact. Any other artifact argument must be a finite iterable of text strings or text-returning path-like objects and is materialized exactly once. The output is one text string or text-returning path-like object. Bytes paths and path-like objects returning bytes are rejected.

## Manifest format

Each line is:

```text
<lowercase-sha256><two spaces><supplied-basename>
```

Input order is retained and the manifest has a final LF. Persisted output is strict UTF-8 with literal LF independently of the process locale. Hashing reads binary files in bounded 1 MiB chunks.

The basename belongs to the supplied artifact path, not a resolved symlink target, so a manifest remains portable beside the named release artifacts. Spaces and strictly UTF-8-encodable names are accepted when the active Python filesystem encoding can represent the supplied text path; an unrepresentable path raises `ReleaseChecksumError`. The basename `-` is rejected because standard checksum tools reserve it for standard input. Carriage return, line feed, backslash, NUL, surrogate code points, and any other name that cannot be strictly UTF-8 encoded are rejected because the unescaped line format would be ambiguous or non-portable.

Duplicate basenames are compared by exact UTF-8 bytes without case folding or Unicode normalization.

## Artifact validation

At least one artifact is required. A final-component artifact symlink is accepted only when it resolves to a regular file. Missing paths, directories, broken/cyclic symlinks, FIFOs, sockets, devices, and other special files are rejected.

Repeated, relative, normalized, and symlinked paths are compared by lexical and resolved identity. Existing POSIX device/inode identity also makes hard-linked names aliases. Any duplicate artifact identity is rejected. Every artifact and basename is validated before hashing begins.

Callers must keep artifact contents stable during the call. Version 1 does not lock artifacts or perform post-hash change detection.

## Output safety and stale invalidation

Output handling intentionally has two phases.

First, the library materializes and coerces every requested path far enough to identify the mutation target set. It requires the output parent to exist as a directory, following parent-directory symlinks. It inspects the final output component without following it and supports only an absent path or existing regular file. A final-component symlink, including a broken one, and any directory or special file are refused and preserved. Lexical, resolved/symlink, and existing hard-link identity checks reject an output that aliases any artifact, also without mutation. If an existing artifact's file identity cannot be inspected because of a permission or other filesystem error, the check fails closed and preserves the output; only a demonstrably missing or non-traversable artifact path proceeds to ordinary artifact validation.

Path-coercion, parent, unsafe-output-type, and artifact/output-alias failures therefore preserve an existing output.

Once the target is proven safe, an existing regular output is removed before artifact count, basename, existence/type, duplicate, or hashing validation. A failed invocation after this point leaves the final output absent rather than allowing an older manifest to appear current. This includes empty library input, invalid artifacts, hashing failures, temporary creation/write/flush/file-`fsync`/close failures, and replacement failures. Temporary cleanup is attempted after every failure. Expected failures report a cleanup failure without hiding the primary failure; unexpected exceptions and process-control exceptions are cleaned up and re-raised unchanged.

The deliberate invalidation creates a period during hashing when the final path is absent. This is not an in-place update guarantee.

## Atomic placement and permissions

The completed manifest is created exclusively in the output directory under a collision-resistant basename independent of the output basename. Creation requests POSIX mode `0666`, so the process umask selects the effective final mode. The complete UTF-8 bytes are written, flushed, file-`fsync`ed, closed, and installed with `os.replace`.

Atomicity refers to placement of the completed new file after stale invalidation. The implementation does not promise parent-directory `fsync` or crash durability beyond the flushed temporary and atomic final placement. It also does not preserve a stale output's mode, ownership, timestamps, or extended attributes.

Callers must use a single writer per output and keep artifacts stable. Version 1 has no locking or concurrent-mutation detection. The guarantee that failure leaves the final path absent assumes that documented single-writer contract.

## Command

Generate a manifest for one or more generic artifacts:

```text
la-dev-release-checksums --output dist/SHA256SUMS dist/package.whl
la-dev-release-checksums --output dist/SHA256SUMS dist/package.whl dist/package.tar.gz
```

The successful command writes the exact persisted manifest bytes to stdout as well as the output file. This makes comparison straightforward:

```text
la-dev-release-checksums --output dist/SHA256SUMS dist/package.whl dist/package.tar.gz > /tmp/printed-SHA256SUMS
cmp /tmp/printed-SHA256SUMS dist/SHA256SUMS
```

Status `0` means success, help, or version output. Expected generation/runtime failure returns `1` and emits a concise `la-dev-release-checksums:` diagnostic on stderr without a traceback. Diagnostic paths preserve printable Unicode but backslash-escape controls, format characters, surrogates, line separators, and literal backslashes so each diagnostic remains on one physical line; library exceptions retain the raw supplied path. Generation failures occur before stdout and therefore emit no manifest there. The stdout mirror is not transactional: if its stream fails after the valid output file has been installed, the file is retained and stdout may contain a partial or complete manifest before the status-`1` diagnostic. Argparse usage errors return `2`; `--output` and at least one artifact are required.

## Release workflow integration

Generate checksums only after building artifacts and completing metadata, installation, and smoke validation. Pass the wheel and source archive in the intended published order. Treat an absent checksum file after failure as deliberate invalidation; never restore or publish an older manifest as if it described the current artifacts.

When a GitHub Release accompanies a package-index publication, upload the generated checksum manifest as a release asset so users can obtain hashes for the listed wheel and source archive independently of the package index.
