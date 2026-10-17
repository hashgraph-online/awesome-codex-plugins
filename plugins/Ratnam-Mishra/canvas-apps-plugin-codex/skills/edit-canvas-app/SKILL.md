---
name: edit-canvas-app
version: 2.0.0-codex
description: Edit an existing Power Apps canvas app. USE WHEN the user wants to modify, update, change, or edit an existing Canvas App or pa.yaml files.
author: Microsoft Corporation (adapted for Codex by setup plan)
---

# Edit a Canvas App

Make the following changes to the existing Canvas App:

$ARGUMENTS

## Overview

Two paths depending on edit complexity:
- **Simple edits** (≤2 controls, ≤1 screen, no new screens/data) — handled inline
- **Complex edits** (multiple screens, new screens, structural changes) — via planner + editor agents

**Plugin root:** the directory containing `skills/`, `agents/`, and `references/`

---

## Phase 0 — Create App Folder

1. Derive a short folder name from `$ARGUMENTS` — extract the app name or use a 2–3 word summary
2. Convert to kebab-case
3. Create the folder: `mkdir -p <folder-name>`
4. Resolve its absolute path — this is the **working directory**

---

## Phase 1 — Sync and Check

Call `sync_canvas` targeting the working directory. This pulls the current app state from
the coauthoring session into local `.pa.yaml` files.

After sync, read the files and check if the app has meaningful content. An app is **empty** if:
- No `.pa.yaml` files were written, or
- No screens with actual controls (non-container children) exist

If empty, inform the user and switch to the full `generate-canvas-app` workflow.

---

## Phase 2 — Assess Complexity

**Simple** — ALL of these are true:
- Changes affect ≤2 controls or properties
- Changes are confined to ≤1 screen
- No new screens, data sources, or structural layout changes

**Complex** — ANY of these are true:
- Changes span multiple screens
- New screens need to be created
- New data sources or connectors are required
- Structural layout changes involved

---

## Phase 3a — Simple: Direct Edit

Read `../../references/TechnicalGuide.md`.

Apply changes directly to the relevant `.pa.yaml` files.

Call `compile_canvas` on the working directory. Iterate until clean.

Present summary:
> **Edit complete.** [1-2 sentence description.] Compiled clean after [N] pass(es).

---

## Phase 3b — Complex: Plan (Edit Planner Agent)

Read the edit planner agent definition:
- `../../references/TechnicalGuide.md`
- `../../references/DesignGuide.md`
- `../../agents/canvas-edit-planner.md`

Adopt the role of `canvas-edit-planner` and follow every step in that file with:
- Edit requirements: `$ARGUMENTS`
- Working directory: the absolute path from Phase 0
- Plugin root: the directory containing `skills/`, `agents/`, and `references/`
- List of synced `.pa.yaml` files

**Do not proceed to Phase 4 until the user approves the plan.**

---

## Phase 4 — Edit (Complex path only, Screen Editor Agent)

After the planner completes, read `canvas-edit-plan.md` from the working directory.

Extract screens to modify and screens to add.

For **each affected screen**, in sequence:

1. Read the editor agent definition:
   `../../agents/canvas-screen-editor.md`
2. Adopt the role of `canvas-screen-editor` for this screen
3. Follow every step in that file with:
   - Screen name and action (Modify / Add)
   - Target file name
   - Plan document path
   - Working directory

---

## Phase 5 — Validate and Fix (Complex path only)

Call `compile_canvas` on the working directory. Iterate until clean.

---

## Phase 6 — Summary

Delete `canvas-edit-plan.md`:
```bash
rm <working-directory>/canvas-edit-plan.md
```

Present final summary table of all screens modified/added, compilation passes, any remaining errors.
