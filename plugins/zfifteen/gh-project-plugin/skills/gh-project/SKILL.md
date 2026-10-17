---
name: gh-project
description: Create new GitHub repositories with low-friction defaults. Use when the user invokes /gh-project or $gh-project, asks to create a new GitHub project, asks to create a GitHub repo/repository, or wants a local folder plus GitHub repository created from inferred defaults.
---

# GitHub Project

## Overview

Create a new GitHub repository and matching local clone from a default-first plan. In this skill, "GitHub project" means a GitHub repository unless the user explicitly asks for a GitHub Projects board.

Do not create anything until the user explicitly confirms `Create GitHub project`.

## Defaults

Infer a complete repo plan before asking questions:

- Artifact: GitHub repository.
- Owner: active authenticated `gh` account.
- Parent location: `~/IdeaProjects`.
- Visibility: public.
- License: MIT.
- Initial contents: README plus MIT license.
- Repo features: GitHub defaults; do not toggle issues, wiki, projects, or discussions unless requested.
- Folder name: GitHub-safe slug inferred from the project name.
- Repo name: same as folder name unless the user requests otherwise.
- Friendly name: human-readable title inferred from the project name.
- Description: generated from the project purpose, capped at 350 characters.
- Topics: 6-10 GitHub repository topics optimized for user search queries.

Topics are GitHub repository topics for discoverability. They are not issue labels and should not be appended as hashtag-style description text.

## Workflow

1. Resolve prerequisites.
   - Run `gh --version`.
   - Run `gh auth status`.
   - If `gh` is missing or unauthenticated, stop and report the blocker.
   - Resolve the active owner from `gh auth status` or another read-only `gh` query if needed.

2. Infer the project plan.
   - Derive the friendly name, folder name, repo name, description, and topics from the user's request.
   - Use lowercase hyphenated slugs for folder and repo names.
   - Keep the description plain and searchable, not promotional.
   - Select topics from terms users would search for on GitHub for the project subject or technology.

3. Present native menus for every configurable setting.
   - Use `request_user_input` for each menu when available.
   - Ask one setting at a time.
   - Defaults are preselected, not hidden.
   - The first option in each menu must be the inferred default with `(Recommended)` in the label.
   - Do not skip a setting just because a good default was inferred.
   - If structured menus are unavailable, stop and say the integrated menu UI is unavailable in the current mode.

4. Required setting menus, in order:
   - Parent location.
   - Repo, folder, and friendly name.
   - Description.
   - Topics.
   - Visibility.
   - License.
   - Initial contents.
   - `.gitignore`.

5. Menu requirements by setting:
   - Parent location:
     - `~/IdeaProjects (Recommended)`
     - `Specify`
     - `Do something else`
   - Repo, folder, and friendly name:
     - The inferred names as one recommended option.
     - `Change names`
     - `Do something else`
   - Description:
     - `Use generated description (Recommended)`
     - `Specify`
     - `Do something else`
   - Topics:
     - `Use generated topics (Recommended)`
     - `Specify`
     - `Do something else`
   - Visibility:
     - `Public (Recommended)`
     - `Private`
     - `Do something else`
   - License:
     - `MIT (Recommended)`
     - `Apache-2.0`
     - `GPL-3.0`
     - Rely on the tool's free-form Other path when the user wants another license.
   - Initial contents:
     - `README plus MIT license (Recommended)`
     - `README only`
     - `Do something else`
   - `.gitignore`:
     - If the stack is clear, make the matching GitHub template the recommended option.
     - If the stack is unclear, make `None (Recommended)` the recommended option.
     - Always include `Specify`.
     - Include `Do something else` when there is room within the menu option limit.

6. Check for collisions after the user has confirmed the names and location.
   - Expand `~/IdeaProjects` to an absolute path.
   - If the target local folder already exists, stop and ask for a new name or explicit instruction.
   - Check whether the target GitHub repository already exists with a read-only `gh repo view OWNER/REPO`.
   - If the target repository already exists, stop and ask for a new name or explicit instruction.

7. Present the final creation plan.
   - Show the resolved plan in chat after all setting menus and collision checks are complete.
   - Then ask for final confirmation with a native menu.
   - Because `request_user_input` supports only 2-3 explicit choices, use a compact final menu:
     - `Create GitHub project`
     - `Change settings`
     - `Do something else`
   - If the user selects `Change settings`, ask a follow-up native menu for the setting category to change:
     - `Location or names`
     - `Description or topics`
     - `Visibility, license, contents, or gitignore`
   - After any change, rerun the affected collision checks and return to the final creation plan.

8. Create only after explicit confirmation.
   - Run from the chosen parent directory.
   - Use this command shape:

```bash
gh repo create REPO --public --clone --add-readme --license mit --description "DESCRIPTION"
```

   - Include `--gitignore TEMPLATE` only when the user selected a template.
   - If visibility or license changed during confirmation, replace `--public` or `--license mit` with the confirmed value.
   - After creation, add topics:

```bash
gh repo edit OWNER/REPO --add-topic topic-a,topic-b,topic-c
```

9. Return the result.
   - Include the local path, GitHub URL, visibility, license, description, and topics.
   - If any step fails, report the exact failed command and stop. Do not retry through an alternate path unless the user asks.

## Menu Behavior

Prefer a low-friction default-first interaction. Low friction means defaults are preselected, not hidden.

```text
Menu 1: Parent location
  ~/IdeaProjects (Recommended)
  Specify
  Do something else

Menu 2: Names
  Use repo-name / Friendly Name (Recommended)
  Change names
  Do something else

Menu 3: Description
  Use generated description (Recommended)
  Specify
  Do something else

Menu 4: Topics
  Use generated topics (Recommended)
  Specify
  Do something else

Menu 5: Visibility
  Public (Recommended)
  Private
  Do something else

Menu 6: License
  MIT (Recommended)
  Apache-2.0
  GPL-3.0
  Other is available through the integrated input-control free-form path.

Menu 7: Initial contents
  README plus MIT license (Recommended)
  README only
  Do something else

Menu 8: .gitignore
  None or TEMPLATE (Recommended)
  Specify
  Do something else

Final menu:
  Create GitHub project
  Change settings
  Do something else
```

Every configurable setting gets a native menu even when the inferred default is probably correct. The user should be able to press the recommended choice repeatedly and move quickly through the wizard.

Do not replace the integrated input-control menu with a numbered Markdown menu. The intended interaction is the same structured menu surface used by planning. If that surface is unavailable, stop rather than degrading to chat options.

## Stop Conditions

Stop and ask, without creating the repository, when:

- The user asks for a GitHub Projects board instead of a repository.
- `gh` is unavailable.
- `gh` is unauthenticated.
- The active owner cannot be resolved.
- The local folder exists.
- The GitHub repository exists.
- The user has not explicitly selected `Create GitHub project`.
- The integrated input-control menu is unavailable when a menu decision is required.
