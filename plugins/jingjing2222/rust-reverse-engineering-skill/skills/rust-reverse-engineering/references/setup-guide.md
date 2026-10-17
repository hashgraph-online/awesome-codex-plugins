# Setup guide

## Automatic installer

The skill ships with an installer helper:

```bash
bash <path-to-skill>/scripts/install-dep.sh <dependency>
```

Examples:

```bash
bash <path-to-skill>/scripts/install-dep.sh rustfilt
bash <path-to-skill>/scripts/install-dep.sh ghidra
```

The helper uses Homebrew on macOS when possible, Linux package managers when available, and `cargo install rustfilt` for `rustfilt`. When it cannot install something directly, it prints the exact manual next step.

## Required tools

Install at least these:

- `file`
- `strings`
- `readelf` or `llvm-readelf`
- `nm` or `llvm-nm`
- `objdump` or `llvm-objdump`

On Linux, these usually come from `file`, `binutils`, or LLVM packages.
On macOS, install Xcode command-line tools first, then add GNU binutils or LLVM if you want `readelf`-style output.
On Windows, use an environment that provides LLVM/binutils-style tools, or perform triage from WSL.

Quick mapping:

- `file` -> `install-dep.sh file`
- `strings` -> `install-dep.sh strings`
- `headers` -> `install-dep.sh headers`
- `nm` -> `install-dep.sh nm`
- `disassembler` -> `install-dep.sh disassembler`

## Recommended tools

### rustfilt

Best-effort demangler for Rust symbol names:

```bash
cargo install rustfilt
```

Or use:

```bash
bash <path-to-skill>/scripts/install-dep.sh rustfilt
```

If `cargo` is unavailable, the skill still works, but symbol recovery is worse.

### Debuggers

Install at least one of:

- `gdb`
- `lldb`

### GUI reverse-engineering tools

At least one of:

- Ghidra
- IDA Pro
- Binary Ninja

For Ghidra:

```bash
bash <path-to-skill>/scripts/install-dep.sh ghidra
```

## Sanity check

Run:

```bash
bash <path-to-skill>/scripts/check-deps.sh
```

Required tools must show `OK`. Optional tools are not blockers.

## Notes

- `rustfilt` is the single highest-value optional dependency in this skill.
- Prefer LLVM variants (`llvm-readelf`, `llvm-nm`, `llvm-objdump`) when GNU tools are missing.
- On macOS, `readelf` is often absent by default. That is expected.
