# Product flow — idea → PRD → plan

Default lightweight requirements flow for `/archcore:plan`. Best for individual features, small teams, rapid prototyping.

## Step 1: Check existing

`mcp__archcore__list_documents(types=["idea", "prd", "plan"])` — see what exists. If `$ARGUMENTS` provided, check for duplicates on this topic.

## Step 2: Determine scope

If related documents already exist (e.g., an idea without a PRD), pick up where the chain left off — don't recreate.

## Step 3: Idea

Use `AskUserQuestion` to ask: "What's the core concept? Who would benefit?"

Compose content covering **Idea**, **Value**, **Possible Implementation**, **Risks and Constraints**. Create via `mcp__archcore__create_document(type="idea")`.

## Step 4: PRD

Use `AskUserQuestion` to ask: "What problem does this solve? What are the success metrics?"

Compose content covering **Vision**, **Problem Statement**, **Goals and Success Metrics**, **Requirements**. Create via `mcp__archcore__create_document(type="prd")`.

Add relation: `mcp__archcore__add_relation` — prd `implements` idea.

## Step 5: Plan

Use `AskUserQuestion` to ask: "What are the key phases? What are the dependencies?"

Compose content covering **Goal**, **Tasks** (phased), **Acceptance Criteria**, **Dependencies**. Create via `mcp__archcore__create_document(type="plan")`.

Add relation: `mcp__archcore__add_relation` — plan `implements` prd.

## Step 6: Relate to existing

Check for ADRs, specs, or other documents that should be linked. Suggest additional `add_relation` calls.

## Result

Three linked documents: idea → prd → plan (each `implements` previous).
