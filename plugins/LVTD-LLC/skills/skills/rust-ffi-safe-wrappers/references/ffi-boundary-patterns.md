# FFI Boundary Patterns

Use this reference when wrapping C APIs or exporting Rust functions to C.

## Private Raw Module

```rust
// Rust 2024 edition syntax. Use `extern "C" { ... }` on Rust 2021
// and earlier, or migrate with `cargo fix --edition`.
mod raw {
    #[repr(C)]
    pub struct RawHandle {
        _private: [u8; 0],
    }

    unsafe extern "C" {
        pub fn lib_open(path: *const core::ffi::c_char) -> *mut RawHandle;
        pub fn lib_close(handle: *mut RawHandle);
    }
}
```

Keep the raw module small. Safe code should not spread raw calls across the
crate.

## Owned Handle Wrapper

```rust
pub struct Handle {
    raw: std::ptr::NonNull<raw::RawHandle>,
}

impl Drop for Handle {
    fn drop(&mut self) {
        // SAFETY: `raw` came from `lib_open` and is owned by this Handle.
        unsafe { raw::lib_close(self.raw.as_ptr()) };
    }
}
```

## String Handling

- Rust to C: build a `CString`; pass `as_ptr`; keep the `CString` alive for the
  whole call.
- C to Rust borrowed: use `CStr::from_ptr` only when the pointer is non-null,
  nul-terminated, and valid for the borrow.
- C to Rust owned: copy into Rust-owned memory unless ownership transfer and the
  correct deallocator are documented.

## Error Mapping

Convert at the edge:

```rust
let code = unsafe { raw::lib_do_work(self.raw.as_ptr()) };
if code == 0 {
    Ok(())
} else {
    Err(Error::from_code(code))
}
```

Do not leak raw integer status codes through the safe API unless they are the
domain model.

## Callback Checklist

- Is the callback allowed to be called after registration returns?
- Who owns the user data pointer?
- Which thread can call it?
- Can it panic? If yes, catch before returning to C.
- How is callback deregistration synchronized with `Drop`?

## Exported Rust Symbols

Use Rust 2024 unsafe attributes for exported ABI symbols, and document why the
symbol name or linker section is sound:

```rust
// SAFETY: This exported symbol name is unique for this library.
#[unsafe(no_mangle)]
pub extern "C" fn library_version() -> core::ffi::c_int {
    1
}
```
