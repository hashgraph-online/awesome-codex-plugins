---
name: rust-reverse-engineering
description: Use when analyzing a Rust binary without source code, reverse engineering Rust executables or libraries, demangling Rust symbols, recovering likely crate namespaces, tracing panic or unwind paths, identifying FFI boundaries, or mapping behavior from ELF, Mach-O, PE, `.so`, `.dylib`, `.dll`, `.a`, `.rlib`, or object files.
---

# Rust Reverse Engineering

Reverse engineer Rust-compiled binaries methodically. Start with fast triage, confirm that the target is actually Rust, recover namespaces and runtime clues, then move into static or dynamic analysis with a clear hypothesis.

Do **not** jump straight into decompiler output and treat it as source truth. Rust binaries often contain compiler-generated glue, monomorphized generic code, panic paths, and async state machines that will drown the signal if you skip the triage stage.

## When to Use

Use this skill when the user wants to:

- analyze a Rust executable, shared library, static archive, `.rlib`, or object file
- confirm whether a binary was built from Rust
- demangle Rust symbols and recover likely crate namespaces
- trace entry points, panic/unwind paths, FFI exports/imports, or async executors
- understand high-level architecture without source code
- prepare a Rust binary for deeper work in Ghidra, IDA, Binary Ninja, `gdb`, or `lldb`

## When NOT to Use

Do **not** use this skill when:

- the user already has the Rust source code and wants normal code review or debugging
- the target is primarily an Android APK/DEX/JAR/AAR package — use an Android-focused workflow instead
- the task is generic PE/ELF malware triage with no Rust-specific angle
- the request is to bypass licensing, DRM, or authorization controls on software the user is not authorized to analyze

## Prerequisites

Required command-line tools:

- `file`
- `strings`
- `readelf` or `llvm-readelf` for ELF, or `otool` for Mach-O
- `nm` or `llvm-nm`
- `objdump` or `llvm-objdump`, or `otool` on macOS

Recommended:

- `rustfilt`
- `gdb` or `lldb`
- Ghidra, IDA Pro, or Binary Ninja

Verify availability first:

```bash
bash <path-to-skill>/scripts/check-deps.sh
```

If tooling is missing, install one dependency at a time:

```bash
bash <path-to-skill>/scripts/install-dep.sh rustfilt
bash <path-to-skill>/scripts/install-dep.sh ghidra
```

If automatic installation is not possible on the current machine, read `references/setup-guide.md`.

## Workflow

### Phase 1: Check and install dependencies

Run the dependency checker first:

```bash
bash <path-to-skill>/scripts/check-deps.sh
```

Parse the output looking for:

- `INSTALL_REQUIRED:`
- `INSTALL_OPTIONAL:`

If required tooling is missing, install it one dependency at a time:

```bash
bash <path-to-skill>/scripts/install-dep.sh <dependency>
```

The installer:

- uses Homebrew when available on macOS
- uses `apt`, `dnf`, or `pacman` on Linux when available
- uses `cargo install rustfilt` for `rustfilt` when `cargo` exists
- prints exact manual instructions and exits when a dependency cannot be installed automatically

For optional tooling, recommend at least:

- `rustfilt`
- one debugger: `gdb` or `lldb`
- `ghidra`

Re-run `check-deps.sh` after installation attempts. Do not proceed until all required dependencies show `OK`.

### Phase 2: Materialize reverse-engineering artifacts first

Do not keep the analysis ephemeral. Create an artifact bundle on disk before doing interpretation.

```bash
bash <path-to-skill>/scripts/collect-artifacts.sh /path/to/binary
```

The script writes a reusable output directory:

```text
<target>-reverse-output/
├── input/
├── triage/
├── symbols/
├── headers/
├── disassembly/
├── decompiled/
│   └── ghidra/
└── reports/
```

Treat this directory as the source of truth for the rest of the workflow. It should contain:

- `triage/summary.txt` — file type, architecture, strip/debug-info status, Rust confidence
- `triage/strings.txt` and `triage/interesting-strings.txt` — raw and filtered strings
- `symbols/raw.txt`, `symbols/demangled.txt`, `symbols/namespaces.txt`, `symbols/imports.txt`, `symbols/exports.txt`
- `headers/*` — readelf, otool, or PE header dumps
- `disassembly/disassembly.txt` — best-effort disassembly when available
- `decompiled/ghidra/status.txt`, `summary.txt`, `functions.tsv`, `decompile-errors.tsv`, and `functions/*.c` — headless Ghidra pseudocode artifacts when available
- `reports/summary.md` and `reports/pattern-hits.txt`

### Phase 3: Fast triage before any deep analysis

If you need a quick rerun or a narrower pass, the underlying triage script is still available.

```bash
bash <path-to-skill>/scripts/triage.sh /path/to/binary
```

Capture these facts before doing anything else:

1. **Container and file type**
   - ELF, Mach-O, PE/COFF, static archive, object file, or `.rlib`
   - target architecture and bitness
   - executable vs shared library vs archive

2. **Symbol quality**
   - stripped vs not stripped
   - exported vs imported symbols
   - whether a usable symbol table still exists

3. **Debug-info availability**
   - DWARF sections
   - macOS DWARF segments / dSYM hints
   - Windows PDB hints in strings
   - split-debug or external-debug indicators when visible

4. **Rust confidence**
   - v0 or legacy Rust mangling patterns
   - demangled `core::`, `alloc::`, `std::`, or crate-like namespaces
   - panic/unwind strings and runtime artifacts
   - Rust-specific crate names in symbols or strings

Do not describe the binary as “definitely Rust” from a single clue. Use multiple, independent signals.

### Phase 4: Recover symbols and namespaces

Dump symbols and demangle them as early as possible.

```bash
bash <path-to-skill>/scripts/demangle-symbols.sh /path/to/binary
```

Focus on these buckets:

- **standard runtime buckets**: `core::`, `alloc::`, `std::`, `panic`, unwinding, formatting
- **user-space buckets**: crate-like top-level namespaces that are not runtime crates
- **interop buckets**: `main`, `_start`, exported C ABI functions, imported libc / Win32 / networking APIs
- **framework buckets**: likely third-party crates such as serialization, async runtimes, HTTP stacks, crypto, CLI parsing, and logging

Build a short namespace inventory:

```text
- runtime crates:
- likely app crates:
- likely third-party crates:
- exported ABI functions:
- imported platform APIs:
```

Use `references/triage-and-fingerprinting.md` for the triage rubric and `references/rust-patterns.md` for common Rust-specific fingerprints.

For targeted bucket searches across the generated artifacts, run:

```bash
bash <path-to-skill>/scripts/find-rust-patterns.sh <target>-reverse-output
```

### Phase 5: Recover high-level structure without assuming a stable Rust ABI

Recover structure conservatively.

Look for:

1. **Entry and boundary functions**
   - `_start`, `main`, CRT glue, loader entry points
   - exported `extern "C"` / `no_mangle` style boundaries
   - plugin or callback registration functions
   - thread starts, task executors, and worker loops

2. **Subsystem anchors**
   - config parsing
   - logging initialization
   - network / filesystem / crypto imports
   - panic setup and error paths
   - serialization and IPC edges

3. **Call-shape clues**
   - large dispatcher-style functions that may be async state machines
   - indirect calls through vtable-like structures
   - formatter-heavy branches around error handling or panic paths
   - repeated monomorphized helpers with type-specific variants

Critical rule: **do not assume undocumented Rust layouts are stable**.

- Treat `Option`, `Result`, `Vec`, `String`, trait objects, and closure layouts as hypotheses until confirmed by debug info, repeated call-site evidence, or explicit `repr(C)` / `repr(transparent)` style interop boundaries.
- Do not label every two-word structure as a trait object.
- Do not infer source-level module boundaries from one demangled symbol alone; confirm using clusters of neighboring symbols, xrefs, and strings.

### Phase 6: Static analysis in a decompiler / disassembler

Once triage is complete, load the target into Ghidra, IDA, or Binary Ninja.

If `analyzeHeadless` is installed, `collect-artifacts.sh` should already materialize a decompiler bundle under `decompiled/ghidra/`. Treat those `.c` files as working pseudocode and review aids, not as original Rust source.

If the target is a universal Mach-O, thin it to the slice you actually want to analyze before trusting any disassembly or decompiler output. The automation now does this for you, defaulting to the host architecture when `--macho-arch` is omitted and recording the chosen slice in `input/analysis-target.txt` and `decompiled/ghidra/analysis-target.txt`. If the host slice is not the slice you want, pass `--macho-arch` explicitly.

Do not treat the export as complete until `decompiled/ghidra/status.txt` says `STATE: completed` or `decompiled/ghidra/complete.marker` exists. The export now writes progress and partial summary state during the run, so interrupted batches are clearly marked as partial or failed instead of looking empty.

Inside Codex, long-running Ghidra exports must stay attached to a live session and be allowed to run until `STATE: completed`. Do not interrupt them just because they are slow. Do not stop because “enough signal was gathered”, because the expected remaining value seems low, or because the auto-analysis phase looks quiet for a while. If the process is alive and `decompiled/ghidra/runner-status.txt` is still getting fresh heartbeats, the job is still in progress.

Use `decompiled/ghidra/runner-status.txt` to distinguish “slow but alive” from “actually stopped”, and use `decompiled/ghidra/warning-summary.txt` to see whether a small set of hotspot functions is dominating the `Unable to resolve constructor` / `pcode error` noise in `headless.log`. A fresh runner heartbeat together with `PROCESS_ALIVE: yes` means the export is still live. For detached jobs, `ghidra-job.sh status` now derives `RUNNER_HEARTBEAT_AGE_SECONDS`, `RUNNER_HEARTBEAT_STALE`, and `LIVENESS_HINT` so you can separate a slow analysis phase from a dead wrapper.

Recommended order:

1. Run auto-analysis
2. Apply or verify Rust demangling
3. Rename obvious runtime buckets away from the app-specific namespace inventory
4. Start from one of:
   - exported C ABI functions
   - `main` / startup glue
   - strong strings with xrefs
   - networking / filesystem imports
   - panic and formatting anchors
5. Label crate clusters and subsystem boundaries
6. Trace only one feature path at a time

Prefer **strings, imports, exports, and clear subsystem anchors** over huge decompiler functions. In stripped Rust binaries, anchor-based analysis is more reliable than trying to understand every generic helper.

Use `references/static-analysis-workflow.md` for the detailed workflow.

### Phase 7: Dynamic analysis when static evidence is weak

When stripped code or compiler-generated glue makes static analysis ambiguous, move to a debugger.

Use `gdb` or `lldb` to:

- break at exported ABI functions or `main`
- watch network, file I/O, process creation, and crypto-adjacent imports
- break on panic / abort paths
- confirm which indirect call sites are real dispatch points
- trace buffer lifetimes and ownership hand-offs across FFI boundaries

Dynamic analysis is especially valuable for:

- heavily stripped binaries
- async runtimes
- plugin or callback architectures
- binaries with large amounts of monomorphized generic code
- distinguishing app logic from runtime support

Use `references/dynamic-analysis-notes.md` for breakpoint ideas and debugger notes.

### Phase 8: Produce a structured report

At the end, deliver both the artifact bundle and a structured report.

The artifact bundle should exist on disk and include at least:

1. **Captured input and triage**
   - original target under `input/`
   - triage summary
   - raw and filtered strings

2. **Recovered symbol artifacts**
   - raw symbols
   - demangled symbols
   - namespace histogram
   - imports and exports

3. **Low-level evidence**
   - header dumps
   - disassembly when available
   - grouped pattern hits
   - Ghidra pseudocode files when headless export is available

4. **Human-readable report**
   - `reports/summary.md`

Then, in the chat response, deliver:

1. **Binary fingerprint**
   - format, architecture, strip/debug-info status, Rust confidence

2. **Namespace inventory**
   - runtime crates
   - likely application crates
   - likely third-party crates

3. **Entry points and boundaries**
   - startup path
   - exported functions
   - imported APIs
   - likely FFI edges

4. **Recovered subsystems**
   - networking
   - storage
   - crypto
   - config
   - async/task execution
   - panic/error handling

5. **Key call flows**
   - one or two high-value paths only
   - note confidence and evidence for each path

6. **Open questions**
   - what remains ambiguous
   - what extra evidence is needed next (debug info, runtime breakpoints, comparison build, related library)

## Rationalizations to Reject

Reject these shortcuts:

- “The decompiler said it, so it must be true.”
- “This looks like a trait object because it has two pointers.”
- “Demangled symbols prove the original source layout.”
- “A crate name in strings means the feature is definitely used.”
- “This large dispatcher is obviously business logic.”  
  It may just be compiler-generated async or panic/runtime machinery.

## Output standard

Always mention the output directory first, then summarize the findings.

Use this format when reporting to the user:

```markdown
## Reverse output

- **Output dir**: `path/to/target-reverse-output`
- **Summary report**: `path/to/target-reverse-output/reports/summary.md`

## Rust binary summary

- **Target**: `path/to/binary`
- **Format / arch**: `ELF x86-64`
- **Symbols**: `partially stripped`
- **Debug info**: `DWARF absent`
- **Rust confidence**: `high`

## Namespaces

- **Runtime crates**: `core`, `alloc`, `std`
- **Likely app crates**: `my_app`, `engine`
- **Likely third-party crates**: `tokio`, `serde_json`, `reqwest`

## Entry points and boundaries

- **Startup**: `_start -> ... -> main`
- **Exports**: `plugin_init`, `process_request`
- **Imports**: `connect`, `send`, `recv`, `pthread_create`
- **FFI edges**: `plugin_init`, `process_request`

## Key findings

1. `process_request` appears to drive the request parsing path.
2. Networking likely flows through a `reqwest`/`hyper`-adjacent stack.
3. A large dispatcher near `...::poll` is a strong async-state-machine candidate.

## Next best move

- break on `process_request`
- trace the async poll path
- inspect nearby strings/xrefs for request routing or serialization formats
```

## References

- `references/setup-guide.md`
- `references/triage-and-fingerprinting.md`
- `references/rust-patterns.md`
- `references/static-analysis-workflow.md`
- `references/dynamic-analysis-notes.md`
