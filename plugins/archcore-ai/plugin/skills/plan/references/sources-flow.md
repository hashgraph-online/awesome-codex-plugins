# Sources flow — MRD → BRD → URD

Discovery-focused flow for `/archcore:plan --track sources`. Best for product teams doing market research, stakeholder alignment, business analysis before committing to a product.

## Step 1: Check existing

`mcp__archcore__list_documents(types=["mrd", "brd", "urd", "prd"])` — see what exists. If `$ARGUMENTS` provided, check for duplicates on this topic.

## Step 2: Determine scope

If related documents already exist, pick up where the chain left off. All three source documents are peer-level — order is flexible, but MRD → BRD → URD is the recommended sequence.

## Step 3: MRD (Market Requirements)

Use `AskUserQuestion` to ask: "What market are you analyzing? What's the key opportunity?"

Compose content covering **Market Landscape**, **TAM/SAM/SOM**, **Competitive Analysis**, **Market Needs**, **Opportunity and Timing**. Create via `mcp__archcore__create_document(type="mrd")`.

## Step 4: BRD (Business Requirements)

Use `AskUserQuestion` to ask: "What are the business objectives? What's the expected ROI?"

Compose content covering **Business Objectives**, **Stakeholders**, **Business Rules**, **Success Metrics and ROI**, **Dependencies**. Create via `mcp__archcore__create_document(type="brd")`.

Add relation: `mcp__archcore__add_relation` — brd `related` mrd (peer source documents).

## Step 5: URD (User Requirements)

Use `AskUserQuestion` to ask: "Who are the users? What are their key needs?"

Compose content covering **User Personas**, **User Journeys**, **User Requirements**, **Usability Requirements**, **Acceptance Criteria**. Create via `mcp__archcore__create_document(type="urd")`.

Add relations:
- urd `related` mrd
- urd `related` brd

## Step 6: Next steps

Sources feed into product decisions. Suggest:
- Create a **PRD** informed by all three sources — run `/archcore:plan` (default product flow) to continue.
- Or formalize into **BRS** to start the ISO 29148 cascade — run `/archcore:plan --track iso`.
- Link with `related` to any existing PRD, or `implements` to BRS.

## Result

Three peer source documents: MRD + BRD + URD, linked as `related`. Ready to feed into PRD or BRS.
