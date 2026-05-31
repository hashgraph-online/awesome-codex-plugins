# VEF Implementation Patterns

Standards, safety patterns, and data conventions. Exact API names come
from Phase 2 bootstrap — anything named here is illustrative.

## Technical Standards & Safety Patterns

- **API Compliance.** Staged SDK headers are authoritative. The
  [vsql-extension-template](https://github.com/villagesql/vsql-extension-template)
  is authoritative for project structure and CMake patterns. Other
  published extensions may use older API patterns — do not use them as
  references. Never use `vsql_simple` or `vsql_complex` — their build and
  install structure differ from standalone extensions.

- **Typed C++ API Only.** All implementation goes through `vsql.h` and the
  `vsql/` subdirectory. Never use the raw ABI — not its structs, not its
  constants, not its headers (anything under `abi/`).

- **Thread Safety.** All functions must be re-entrant. No global mutable
  state.

- **Binary Portability.** Little-Endian bit-shifting for multi-byte
  integers; `memcpy` for floats/doubles (always native format).

- **Exception Safety.** All SQL entry points must be wrapped in `try/catch
  (...)`.

- **Memory Safety.** Bounds checking before every `memcpy` or `memset`.

- **Allocation Efficiency.** Use `std::string_view` for parsing. Never
  `push_back(c)` in a loop. Only allocate `std::string` for the final
  in-memory representation. Use `.reserve()`.

- **Move semantics in initializer lists.** Do not move from a variable
  and also use it in the same initializer list — C++ does not guarantee
  evaluation order within brace-init lists. `std::pair{key, {std::move(key), val}}`
  is undefined behaviour: `key` may be moved before the first element is
  read. Move into a local first, then construct: `auto k = std::move(key);
  return {k, {std::move(k), val}};` — or copy where the value is small.

- **No file-scope `using namespace`.** Per-function `using` declarations
  or fully-qualified names only.

## VEF Data Patterns

Semantic guide only — exact names come from Phase 2 bootstrap.

**Input values** (one struct per argument):
- Null flag — check this first, before any other field.
- String value + length (STRING inputs).
- Integer value (INT inputs).
- Real/float value (REAL inputs).
- Binary value + length (BINARY/custom type inputs).

**Result values:**
- Result type field — set to the value/null/error constant from headers.
  Never use aliases marked deprecated in the headers.
- String buffer + max length + actual length — for STRING: write to
  buffer, check max before writing, always set actual length.
- Binary buffer + max length + actual length — for custom type returns.
  Set the buffer size at registration to the type's persisted length
  (silent 0-byte allocation otherwise — standalone calls like
  `SELECT my_type('a','b')` fail with "output buffer too small").
- Integer/real value — for INT/REAL returns.
- Error message buffer — write via `snprintf` with the max error length
  constant.

**Encode/decode** (custom types): error-signaling convention depends on
which API you're calling. The typed wrappers commonly use
`out.set_length()` / `out.error()`. Older raw shapes use a boolean return
where `false` = success and `true` = error. Read the type builder header
to confirm before writing.

**Type conversion wrappers.** The builder provides methods to register
string↔type conversions. When encode/decode is registered through these
wrappers, the SDK handles NULL and error plumbing — no inner `try/catch`
needed. The `try/catch` rule applies to all entry points called directly
by the server and to every VDF implementation function.

**Deterministic attribute.** Mark VDFs used in CHECK constraints as
deterministic (exact method: from builder headers) or the server rejects
the `CREATE TABLE`. Functions returning random or time-dependent values
(e.g., `*_generate`, `uuid_*v7`) must NOT be marked deterministic.

**Entry point shape** (verbal — do not copy code from this skill): Every
VDF entry point checks the input null flag, performs its work, sets the
result type and value/buffer, and is wrapped in `try/catch (...)`. The
actual function names, struct fields, and constants come from the typed
API headers read in Phase 2 bootstrap — never from this document.

## JSON & Type Specifics

Applies to key-value and JSON-like extension types.

- **JSON Escaping.** Use a dedicated escaping function for all string
  values in JSON output. Never concatenate raw strings — they may contain
  `"`, `\`, or control characters.
- **Numeric Detection.** Handle decimals, negatives (`-5`), and scientific
  notation (`1.2e-3`).
- **Sorted Keys.** Internal storage must be sorted by key for `O(log n)`
  search.
- **Deduplication (last-key-wins).** When the same key appears multiple
  times, the last occurrence wins (PostgreSQL semantics). `std::sort` +
  `std::unique` is incorrect for this — it removes the first duplicate
  encountered, keeping the *first* occurrence, not the last. Correct
  algorithm: iterate backwards through the parsed pairs, use an
  `std::unordered_set` to track keys already seen, and keep only the
  first time you encounter each key in this reverse pass (which is the
  last occurrence in the original string). Then sort the deduplicated
  result by key.
- **MySQL backslash escaping.** MySQL processes backslash escapes in
  single-quoted literals before the string reaches your extension. A
  test input like `'"key\"quoted\""=>"val"'` arrives at your extension
  as `"key"quoted""=>"val"` — the backslashes are consumed by MySQL,
  not passed through. Write test inputs as MySQL sees them (after escape
  processing), not as the raw literal. This is a silent failure mode:
  the extension receives a different string than intended and may return
  NULL with no error.

## Function Naming Conventions

MySQL uses `TYPE_VERB` or `TYPE_NOUN` patterns with underscores:
- Good: `HTTP_GET`, `URL_ENCODE`, `AES_ENCRYPT`, `JSON_EXTRACT`,
  `INET_ATON`
- Bad: `http` (too terse), `urlencode` (compound — PHP/Python style)

When porting a PostgreSQL extension, derive MySQL-idiomatic names rather
than copying Postgres names. Do not let the extension's name leak into
function names that don't belong to the extension's type (e.g.,
`typeid_uuidv7_generate` reads as "the typeid module's UUID generator";
prefer `uuidv7_generate`).

**Reserved words to avoid as function names** (cause syntax errors
without backticks): `keys`, `values`, `check`, `table`, `index`, `select`,
`delete`, `replace`, `insert`, `update`, `primary`, `foreign`, `and`,
`or`, `in`.
