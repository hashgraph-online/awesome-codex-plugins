# Refactoring Workflow — Characterization Tests

Legacy code = code without tests; you need tests before changing it. Find a seam, capture what the code DOES (not what it should — the baseline includes existing bugs), refactor under that net, then graduate golden masters to behavioral tests once you understand the code.

## Normalization (load-bearing for any golden comparison)
Without it, timestamps/IDs/float imprecision break every test. Recursively: sort dict keys, drop volatile keys (`timestamp`, `created_at`, `updated_at`, `request_id`, `trace_id`), round floats (~6 places).

## Sampling (Rainsberger)
When inputs explode combinatorially, loop over random inputs with a fixed `seed` (reproducible), normalize both old and new outputs, assert equal. Start at ~100 iterations, raise until runtime becomes annoying.

## Skip characterization when
You fully understand the code (write behavioral tests directly), or it is a prototype / will be deleted, or boundary + property tests already suffice.
