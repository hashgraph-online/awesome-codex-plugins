---
name: book-technical
description: "Technical book patterns — concept progression gradient, code block rules, diagrams, API reference format, lab design."
---

# Technical Book Patterns

**Progression**: Part1 Intro(15%) → Part2 Foundations(25%) → Part3 Practice(30%) → Part4 Advanced(20%) → Part5 Reference(10%). Novice(what?) → Competent(how?) → Expert(why?).

**Chapter**: Hook(problem scenario) → Concept(linked to prior) → Code(minimal runnable) → Explanation(line-by-line) → Pitfalls(2-3 beginner mistakes) → Summary + preview.

**Code rules**: language tag always · runnable only (pseudocode labeled) · include imports · show expected output · filename as title. Beginner: 10-30 lines, Intermediate: 30-80, Advanced: 80-200.

**Diagrams**: architecture (boxes+arrows), flowchart (Mermaid TD), sequence (Mermaid sequenceDiagram), comparison (markdown table). Pair ASCII + Mermaid for EPUB/PDF compat. ≤3/chapter.

**API reference**: `functionName(params)` → one-liner → Parameters table → Returns type → Example code → See also.

**Version-independent writing**: prefer "Save the file" over "Click File > Save". Exception: security/breaking changes need specific versions.

**Labs**: objective → prerequisites → steps with verification → result check → challenge. Easy(step-by-step, 3-5), Medium(hints, 5-8), Hard(goal-only, 3-5). Parts 1-2 Easy, Part 3 Medium, Part 4 Hard.
