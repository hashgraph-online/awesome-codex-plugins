---
name: swift-dev
description: "Swift development. Use for Swift, SwiftUI, UIKit, Vapor, SPM, XCTest, Combine."
user-invocable: true
allowed-tools: Glob, Read, Grep, Bash, Task, Skill, Edit, Write, AskUserQuestion
---

# Swift Development

**Announce:** "I'm using the swift-dev skill. Following the 4-phase workflow."

## MANDATORY: Read and Follow the Shared Workflow

**You MUST read [workflow.md](../../shared/workflow.md) NOW** and follow ALL 4 phases defined there. The sections below provide Swift-specific inputs for each phase.

Read [patterns.md](patterns.md) during Phase 1.

**If you lost workflow.md from context:** Re-read `../../shared/workflow.md` NOW before continuing.

---

## Swift-Specific Configuration

### Verification Commands (Phase 1 plan + Phase 3 verify)

WORKFLOW STATE Verification line: `swift build, swift test, swiftlint`

**Phase 3 Tier A — SPM projects:**
- `swift build` — compilation
- `swift test` — tests
- `swiftlint` — linting (if configured)
- Coverage target: 70-80%

**Phase 3 Tier C — Xcode projects:**
- `xcodebuild build` or `xcodebuild test`
- SwiftUI: `xcodebuild build -scheme [scheme] -destination 'platform=iOS Simulator,name=iPhone 16'`

### Implementation Rules (Phase 3)

- **Model structure** — Structs with Codable CRUD variants per entity (CreateRequest/UpdateRequest/Response), domain-driven file organization, composition over deep inheritance, prefer structs over classes
- **Minimize complexity** — lazy sequences for large collections, Dictionary lookups over array scans
- **Preserve compatibility** — CodingKeys for renamed fields, default values for new properties, preserve public API signatures, @available for deprecations

### Staff Review Configuration (Phase 4)

- **Patterns file path:** Path to this skill's `patterns.md`

---

## Swift-Specific Rules

- The compiler catches type errors, not logic bugs or architectural problems — verification is still mandatory
- SwiftUI previews only prove the view compiles — run `swift test` for real verification
- No positive claim without running `swift test` or `swift build`

---

## Quality Checklist (Swift-Specific)

Add these to the shared workflow's verification checklist:

- [ ] Using Swift 5.9+ / Swift 6 features where appropriate
- [ ] Structs preferred over classes (value semantics by default)
- [ ] Protocol-oriented design used
- [ ] async/await for asynchronous code
- [ ] No force unwraps outside tests
- [ ] Proper error handling with typed throws or do/catch
- [ ] `swift build` succeeds without warnings
- [ ] `swift test` passes (or `xcodebuild test`)
- [ ] `swiftlint` passes (if configured)
