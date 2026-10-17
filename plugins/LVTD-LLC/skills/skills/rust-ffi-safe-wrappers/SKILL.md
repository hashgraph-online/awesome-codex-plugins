---
name: rust-ffi-safe-wrappers
description: Design and review Rust FFI boundaries that keep raw declarations isolated behind safe ownership, lifetime, error, and cleanup wrappers. Use when writing, refactoring, or reviewing unsafe extern blocks, C ABI wrappers, repr(C) types, CString, CStr, raw handles, Drop cleanup, bindgen, cbindgen, or panic-safe foreign boundaries.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Rust FFI Safe Wrappers
  category: Rust
  tags: rust,ffi,c-abi,unsafe,bindings
---

# Rust FFI Safe Wrappers

Use this skill to wrap foreign interfaces in Rust APIs that make ownership,
lifetimes, errors, and cleanup explicit. FFI code should be unsafe at the raw
boundary and safe for normal Rust callers.

## Core Workflow

1. Separate raw declarations from safe wrappers. Put raw `unsafe extern`
   bindings in a small private module.
2. Verify ABI, type layout, calling convention, ownership, nullability,
   threading, and error conventions against the foreign header or docs.
3. Use `unsafe extern "C"` blocks for modern Rust, especially Rust 2024 edition
   code. Leave safety-conditional items unqualified or explicitly `unsafe`, and
   mark individual extern items `safe` only when calling them is safe for all
   Rust inputs.
4. Use `#[repr(C)]` for structs and enums that cross the ABI boundary. Do not
   expose Rust-only layout types across C.
5. Use `CString` for owned nul-terminated strings sent to C and `CStr` for
   borrowed C strings. Never treat arbitrary C memory as Rust-owned.
6. Wrap raw handles in Rust types with private fields and `Drop` cleanup using
   the matching foreign deallocator.
7. Prevent Rust panics from crossing `extern "C"` boundaries. Catch panics or
   expose an ABI that permits unwinding only when deliberately using
   `"C-unwind"`.

## Wrapper Rules

Read `references/ffi-boundary-patterns.md` before adding or reviewing FFI
bindings.

- Prefer `core::ffi` or `std::ffi` C types over guessing integer sizes.
- Convert foreign error codes into Rust `Result` at the wrapper boundary.
- Represent nullable handles as `Option<NonNull<T>>` internally when useful,
  but expose safe Rust types to callers.
- Tie borrowed values to owner lifetimes with normal references or
  `PhantomData` when the compiler cannot see the relationship.
- Make initialization and shutdown idempotent with `OnceLock`, `LazyLock`, or
  `Once` when the foreign library requires process-wide setup.
- Use `bindgen` for large or changing C headers and `cbindgen` when exporting a
  Rust API to C, but still review generated unsafe signatures.

## Rust 2024 Syntax Checks

```rust
unsafe extern "C" {
    pub fn library_open(path: *const core::ffi::c_char) -> *mut RawHandle;
    pub fn library_close(handle: *mut RawHandle);
    // Mark an item `safe` only when calling it is valid for all Rust inputs:
    // pub safe fn library_version() -> core::ffi::c_int;
}

// SAFETY: This exported symbol name is unique for this library.
#[unsafe(no_mangle)]
pub extern "C" fn plugin_version() -> core::ffi::c_int {
    1
}
```

Unsafe attributes such as `no_mangle`, `export_name`, and `link_section` need
the `unsafe(...)` form in Rust 2024 edition code. Include a `SAFETY` comment
where symbol uniqueness or linker behavior is part of the contract.

## Review Checklist

- Raw bindings are private or clearly separated from safe wrappers.
- Every pointer parameter has a documented nullability and ownership rule.
- Every allocation is freed by the same side or an explicitly matching
  deallocator.
- Strings and buffers preserve length, encoding, and nul-byte requirements.
- Panics, callbacks, and threads crossing the boundary have explicit behavior.
