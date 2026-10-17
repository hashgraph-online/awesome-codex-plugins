---
name: generate-canvas-app
version: 2.0.0-codex
description: Generate a complete, visually distinctive Power Apps canvas app with YAML. USE WHEN the user wants to create, build, or generate a Canvas App or pa.yaml files.
author: Microsoft Corporation (adapted for Codex by setup plan)
---

# Generate a Canvas App

Generate a complete Power Apps canvas app for the following requirements:

$ARGUMENTS

## Overview

This skill uses two specialist agent definitions (read from the `agents/` folder):

1. **`canvas-app-planner`** — discovers controls and data sources, designs the app,
   presents a screen plan for approval, writes a shared plan document
2. **`canvas-screen-builder`** — writes exactly one screen's YAML; multiple builders
   run sequentially after the plan is approved

You coordinate the agents and own the compilation + error-fixing loop after all screens
are written.

**Plugin root:** the directory containing `skills/`, `agents/`, and `references/`

---

## Phase 0 — Create App Folder

1. Extract the app name or a 2–4 word summary from `$ARGUMENTS`
2. Convert to kebab-case (e.g., "Expense Tracker" → `expense-tracker`)
3. Create the folder: `mkdir -p <folder-name>`
4. Resolve its absolute path — this is the **working directory** for all subsequent phases

---

## Phase 1 — Plan (Planner Agent)

Read these files before planning:
- `../../references/TechnicalGuide.md`
- `../../references/DesignGuide.md`
- `../../agents/canvas-app-planner.md`

Adopt the role of the `canvas-app-planner` and follow every step in that file, with:

- User requirements: `$ARGUMENTS`
- Working directory: the absolute path resolved in Phase 0
- Plugin root: the directory containing `skills/`, `agents/`, and `references/`

Complete ALL steps in the planner agent file, including:
- Using the already loaded `TechnicalGuide.md` and `DesignGuide.md`
- Calling `list_controls`, `list_apis`, `list_data_sources`
- Presenting the screen plan to the user and waiting for approval
- Writing `canvas-app-plan.md` and `App.pa.yaml` to the working directory

**Do not proceed to Phase 2 until the user approves the plan.**

---

## Phase 2 — Build (Screen Builder Agent, One Screen at a Time)

After the planner completes, read `canvas-app-plan.md` from the working directory.

Extract the screen list from the `## Screens` table.

For **each screen** in the list, in sequence:

1. Read the builder agent definition:
   `../../agents/canvas-screen-builder.md`
2. Adopt the role of `canvas-screen-builder` for this screen
3. Follow every step in that file with:
   - Screen name
   - Target file name
   - Plan document: `<working-directory>/canvas-app-plan.md`
   - Working directory: the absolute path from Phase 0
4. Write `[ScreenName].pa.yaml` to the working directory before moving to the next screen

---

## Phase 3 — Validate and Fix

After all screen files are written, call `compile_canvas` on the working directory.

**On success:** Proceed to Phase 4.

**On failure:** For each error in the output:
1. Read the referenced `.pa.yaml` file
2. Fix the error
3. Call `compile_canvas` again

Repeat until `compile_canvas` reports no errors.

---

## Phase 4 — Summary

Delete `canvas-app-plan.md`:
```bash
rm <working-directory>/canvas-app-plan.md
```

Present final summary:

> **App generation complete.**
>
> | Screen | File | Status |
> |--------|------|--------|
> | [Screen Name] | [filename].pa.yaml | Written |
>
> **Compiled clean** after [N] pass(es). | **Screens:** [N] | **Data:** [source or collections]
