---
name: autopilot-intake
description: Structured one-question-at-a-time intake for Auto Pilot. Use when a new autopilot project starts and the required setup information has not been collected yet.
summary: Ask one numbered question at a time, show remaining count, then lock the spec.
metadata:
  priority: 9
  promptSignals:
    phrases:
      - "오토파일럿 시작"
      - "autopilot start"
      - "새 프로젝트 시작"
      - "intake"
      - "필수 정보부터"
      - "질문 하나씩"
      - "하나씩 물어봐"
      - "start autopilot"
    anyOf:
      - "intake"
      - "질문"
      - "하나씩"
      - "start"
      - "시작"
    minScore: 4
retrieval:
  aliases:
    - 오토파일럿 intake
    - autopilot intake
    - startup questionnaire
    - project setup interview
  intents:
    - collect required project inputs
    - ask setup questions one by one
    - initialize a new autopilot project
  entities:
    - intake
    - questions
    - setup
    - definition of done
---

# Auto Pilot Intake

Use this skill to collect the minimum project contract before autonomous execution begins.

## UX Rules

### Ask one question at a time

- Never dump the whole questionnaire in a single message.
- Ask exactly one question per turn.
- Wait for the user's answer before asking the next one.

### Numbered progress format

Every intake question must follow this format:

`{index}. {question}`

Then on the next line:

`Questions remaining: {remaining}`

Example:

`1. What do you want to build?`
`Questions remaining: 14`

### Keep each question short

- Prefer one sentence.
- Avoid compound questions.
- If an answer can be inferred safely, skip the question and store the default.

### Confirmation

- Do not ask the user to retype everything at the end.
- After the last answer, summarize the captured inputs once and move directly into spec lock.

## Question Order

Use this order by default. Skip questions only if the answer is already explicit in the user's earlier messages.

1. product summary
2. target user
3. core features
4. non-goals for this version
5. stack preference or permission to use defaults
6. architecture preset
7. auth requirement
8. payment requirement
9. admin requirement
10. deploy target
11. data store
12. theme preset
13. visual vibe
14. design direction refinement
15. definition of done

## Data Capture Rules

Store answers into the intake record with these keys:

- `product_summary`
- `target_user`
- `core_features`
- `non_goals`
- `stack_preferences`
- `architecture_preset`
- `auth_mode`
- `payments_mode`
- `admin_required`
- `deploy_target`
- `data_store`
- `theme_preset`
- `visual_vibe`
- `design_direction`
- `definition_of_done`

## Default Handling

If the user says "use the defaults" or an equivalent phrase:

- frontend: Next.js
- UI system: Tailwind CSS + shadcn/ui
- backend: Next.js route handlers or simple managed backend
- architecture: Feature-based
- deploy: Vercel
- data store: Supabase or managed Postgres depending on project shape
- theme: Minimal
- visual vibe: derive from theme by default (`Minimal -> Calm`, `Bold -> Techy`, `Playful -> Playful`, `Premium -> Premium`)
- auth: none unless clearly required
- payments: none unless clearly required
- admin: lightweight admin page only if the use case implies operational control
- blocker policy: retry technical failures automatically, defer low-risk polish, collect required integration env values in one upfront setup step, and ask later only for approvals, payments, OAuth console work, and production launch

Record every inferred default in the final summary.

## Transition To Execution

After the final question:

1. Summarize the captured project contract.
2. Determine the team profile:
   - `team-product` for user-facing work, `Scalable` projects, or auth/payments/admin-heavy projects
   - `team-lite` for clearly CLI-only, backend-only, library-only, or simple internal utilities
   - `serial-fallback` only when the runtime later confirms native sub-agents are unavailable
3. Detect whether the selected auth or managed services require upfront integration env values.
4. If all required env values are already present, write or update:
   - `docs/spec.md`
   - `docs/design.md` for user-facing products
   - `docs/progress.md`
   - `docs/next.md`
   - `autopilot/state.json`
   - `autopilot/blockers.json`
   - `autopilot/secrets-status.json`
5. If any required env values are missing, switch to the `setup-secrets` phase and write or update:
   - `docs/next.md`
   - `autopilot/state.json`
   - `autopilot/blockers.json`
   - `autopilot/secrets-status.json`
   - collect the missing env payload in one step before execution starts
6. Start execution immediately with the manager taking the first step and dispatching Planner only after the required env values are ready.

If script usage is appropriate, use:

```bash
python3 ../../scripts/init_intake.py --workspace <target-workspace> --prompt "<initial prompt>"
python3 ../../scripts/record_answer.py --workspace <target-workspace> --answer "<user answer>"
```

The second command should be repeated once per answer. On the final answer it will generate the spec, progress, next, and runtime state files automatically.
If the project needs external integration env values, the final answer may instead move the workspace into `setup-secrets` and wait for one consolidated env payload before the full bootstrap finishes.

## Design Research Rule

If the project is user-facing, design synthesis is mandatory before the first UI implementation.

- Use the local `frontend-ui-ux` skill as the default design helper
- Use Figma first when a Figma reference exists
- Otherwise rely on curated inspiration sources such as Mobbin, Refero, Land-book, and Page Collective
- Keep the default UI base on white or light-neutral surfaces with slightly compact typography
- Choose header, sidebar, or mobile navigation from the project type instead of defaulting every app to a sidebar shell
- Treat theme and vibe as modulation of accent, spacing tone, contrast, and component shape rather than a full base override
- Write the result into `docs/design.md`

## Team Handoff Rule

The intake step does not finish at “spec lock only”.
It also sets the initial team handoff:

- Manager confirms the real execution backend first
- Planner goes first
- Designer joins only for user-facing products
- Architect joins only when structure decisions are non-trivial
- QA is always required before a slice is treated as done

## Output Style

- Be direct.
- Do not add long explanations before the question.
- Do not ask multiple questions in one message.
- Preserve the numbered intake sequence for every turn.
