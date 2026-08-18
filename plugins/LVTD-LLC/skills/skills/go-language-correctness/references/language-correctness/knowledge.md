# Go Language Correctness Knowledge

## Numeric Representation

Integer conversion always produces a value; it does not report overflow.
Validate sign and bounds before narrowing or converting to an unsigned type.
Guard addition and multiplication before using their results for sizes,
offsets, capacities, or limits.

Floating-point comparison needs a domain policy: exact representation,
absolute tolerance, relative tolerance, or another error budget. A magic
epsilon without scale or units is not a correctness contract.

## Slice Ownership

A slice is a descriptor over a backing array. Assignment, slicing, and function
calls copy the descriptor, not the elements. A callee with spare capacity may
append into storage still visible to its caller.

Distinguish:

- a view: shared elements and backing storage;
- a capacity-clipped view: append cannot overwrite beyond the clipped capacity,
  but existing elements remain shared;
- an independent copy: elements copied into separately owned storage.

Small subslices and substrings may retain large inputs. Treat copying or
`strings.Clone` as targeted ownership tools, preferably supported by evidence.

## Maps and Equality

Map iteration order is unspecified. Sorting keys is part of the output contract
when deterministic human, machine, or test output matters.

Deleting entries does not promise that peak storage returns to the operating
system. Runtime bucket layout, growth thresholds, and hashing details are
implementation details, not application rules.

Use domain equality. Direct interface comparison may panic for dynamically
uncomparable values, while `reflect.DeepEqual` may assign the wrong meaning to
nil and empty collections, floats, or unexported state.

## Range and Control Flow

Range may copy the ranged expression or each element. Mutating a ranged struct
value changes the copy; mutate by index when the collection must change.
Appending does not extend the iteration set chosen when range begins.

For modules using Go 1.22 or newer semantics, variables declared by a loop are
new per iteration. Variables assigned with `=` remain shared. Diagnose the
module or file language version before prescribing capture rebinding.

`break` exits the innermost `for`, `switch`, or `select`. Use a label or return
when the intended target is an outer loop.

## Text Representation

Strings are arbitrary bytes. `len(s)` counts bytes; range decodes UTF-8 into
runes and reports byte offsets. Rune count is still not the same as
user-perceived grapheme count.

Validate UTF-8 when an external contract requires it. Use byte operations for
protocols and binary formats, rune operations for code-point logic, and a
Unicode segmentation library when limits are defined in graphemes.

Trim functions that accept cutsets do not remove literal suffixes. Use
`TrimSuffix` when the contract names an exact suffix.

## Defer and Resource Scope

Deferred function arguments and value receivers are evaluated when `defer` is
executed. Closures observe captured variables when they run. Place acquisition
in a narrow helper when a loop must release each resource before its next
iteration.

Compiler escape decisions, append growth, inlining, map layout, and memory
reclamation can change across Go releases and targets. Measure them rather than
turning observations into guarantees.
