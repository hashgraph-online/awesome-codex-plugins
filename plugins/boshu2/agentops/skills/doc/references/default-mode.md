# Code/API documentation and code-maps

Use these techniques for the documentation the caller requested. The
[Doc contract](../SKILL.md) owns scope: discovery, coverage checks and code-maps
are optional task shapes, not steps that add documents or a separate report.

## Find the source and document owner

Read the selected feature's declarations, callers, tests and existing docs.
Project manifests can help identify languages and conventions; they do not
prove that every source file needs API documentation. For an informational
project or runbook, inspect the relevant content and operational source instead.

For discovery or a coverage question, enumerate the selected entities with
stable identities, such as source path plus qualified symbol or command name.
Map each entity to its source and documentation, then check the relevant
docstring, comment or reference page against the caller's criterion. An existing
syntax-aware tool can help enumerate symbols; search results are candidates to
inspect, not proof of documentation.

- A Python declaration line alone does not reveal its docstring. Inspect the
  function or class body, including async functions and methods when in scope.
- A Go declaration needs its associated comment or reference inspected.
  Exported functions, methods and types belong only when the selected scope
  includes them.
- Quote delimiters, comment lines and doc-file presence are not documented
  entity counts. They can occur in unrelated data, examples or private code.

For each selected entity, distinguish verified documentation, a verified gap,
and unknown or unexamined status. Record source/document references inline or in
the requested output; a small task needs no coverage ledger.

Only calculate a coverage ratio when numerator and denominator come from the
same explicitly enumerated entity set and each member has been checked against
the same declared criterion. State that set, criterion and counts. If membership
or documentation status remains unknown, return the scoped findings and gaps
instead of a percentage. Never imply whole-repository coverage from a sample.

## Write the requested documentation

For a feature, explain its observed behavior and write to the accepted document
owner. If the caller requests all documentation, establish what that includes
before expanding the write scope. Discovery alone authorizes no new files.

Choose details that answer the reader's question. These are example layouts,
not mandatory sections for every API:

**Function or method:**

````markdown
## function_name

**Purpose:** What it does

**Parameters:**
- `param1` (type): Description
- `param2` (type): Description

**Returns:** What it returns

**Example:**
```python
result = function_name(arg1, arg2)
```

**Notes:** Important caveats or errors
````

**Class:**

````markdown
## ClassName

**Purpose:** What this class represents

**Attributes:**
- `attr1`: Description
- `attr2`: Description

**Methods:**
- `method1()`: What it does
- `method2()`: What it does

**Usage:**
```python
obj = ClassName()
obj.method1()
```
````

## Code-map, when requested

Use the existing location or the caller's selected path. Adapt this example to
the inspected components and omit sections that do not apply:

````markdown
# Code Map: <Project>

## Overview
<High-level architecture>

## Directory Structure
```text
src/
├── module1/     # Purpose
├── module2/     # Purpose
└── utils/       # Shared utilities
```

## Key Components

### Module 1
- **Purpose:** What it does
- **Entry point:** `main.py`
- **Key files:** `handler.py`, `models.py`

## Data Flow
<How data moves through the system>

## Dependencies
<External dependencies and why>
````

## Check and return

Check the changed documentation's claims, links and examples against current
source and the applicable repository validator. A missing parameter or example
is a defect when the document's accepted purpose requires it. See
[validation techniques](validation-rules.md) for relevant checks.

Return changed paths, checks performed and unresolved factual gaps. A separate
report requires a caller request or an existing consumer; follow the Doc
contract's destination rules when one is required.

## Examples

**One API:** The caller asks to document authentication in an existing API page.
Read its implementation and callers, update that page with its observed inputs,
outputs and errors, then verify the examples. Return the page and check results.
This request adds no coverage audit or report.

**Mixed-language discovery:** The caller asks which public APIs in two selected
modules lack docs. Enumerate the Python and Go entities in those modules, inspect
each associated docstring/comment and reference page, and return the verified
gaps. Unread entities remain unexamined. A quoted Python data string contributes
no documented API; it cannot be compared with Go declaration counts.

## Troubleshooting

| Problem | Next action |
|---|---|
| Coverage denominator is unknown | Name the incomplete scope; return findings without a percentage. |
| Entity documentation cannot be inspected | Mark it unknown or unexamined and explain the missing source. |
| Usage is unclear | Read callers and tests; ask only if the missing use case changes the document. |
| Discovery exceeds the requested scope | Restrict it to the accepted feature or directories. |
| A claim is stale | Repair the affected requested document against current source. |
