# Dynamic analysis notes

## When to switch to a debugger

Move to dynamic analysis when:

- the binary is stripped enough that decompiler output is ambiguous
- you need to confirm a suspected FFI boundary
- async/runtime glue dominates the static view
- you need to see which imports are actually exercised

## High-value breakpoint ideas

Break on:

- exported ABI functions
- `main` or first reachable user-space function
- panic/abort paths
- networking imports
- file-I/O imports
- thread/task creation imports

## Debugger goals

Use the debugger to answer a narrow question:

- Which function actually handles the request?
- Is this indirect call a real dispatch boundary?
- Which strings or buffers reach the network layer?
- Which panic path is reachable in normal execution?

Do not single-step every runtime helper. Stay focused on the feature path you are trying to confirm.
