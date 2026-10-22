# Reusable Project Verification

Use this guidance when a project repeatedly needs the same setup, user path, or evidence collection. Reuse existing scripts, tests, CI, and operational notes first. A one-off check does not need a new document, skill, or feature map.

## Find the maintained entrypoint

Inspect the relevant repository instructions, package/task definitions, test targets, and CI jobs. Follow their source links to confirm the command's actual scope, working directory, dependencies, and output. A task named `test` may exclude integration tests; a successful launch command may exit before the application is usable.

Use the smallest existing path that supports the requested claim. Keep the authoritative command in its existing script or task definition and link to it from any recipe. Record only the operational details missing there, such as a readiness signal or a user interaction. Do not copy configuration, acceptance contracts, or a second full command inventory into a parallel source of truth.

Normal verification remains read-only with respect to source and the Git index. If no recipe exists, discover the path and report the evidence directly. Persist a concise recipe in an existing project documentation location only when repeated use justifies maintenance and the main execution lane is already authorized to write it. New or broken test harnesses are implementation work for that lane, not permission for an independent verifier to edit source or staging state.

## Keep only the facts needed to repeat the check

A useful recipe supplies the following where the existing entrypoint does not. Choose the detail relevant to the behavior; these are not mandatory document headings.

- **Entry and readiness:** Link the current task definition, script, test, or CI job. State the working directory and the observable readiness condition: a successful health response, an enabled UI control, or a completed initialization event. Merely starting a process or opening a port is insufficient if the behavior depends on more setup.
- **Environment:** Identify the necessary runtime, service, fixture, account role, device/firmware, and relevant configuration by reference. Use safe test data and environment variable names; keep secrets out of recipes and artifacts. Distinguish an unavailable prerequisite from a failing check and an explicitly skipped path. A missing device or credential leaves that path unverified; a broken setup command is a failure to investigate, not evidence that the behavior passed.
- **Action and observation:** Describe how to drive the actual UI, CLI, or API path and what would prove success. Include relevant side effects such as persisted data, emitted requests, files, or state after reopening. Observe the starting state and resulting state where needed to distinguish success from stale output. Add failure, repeat, or recovery paths only when the requested behavior requires them. A mock or local adapter validates its own boundary; it does not establish real service or device execution.
- **Evidence and freshness:** Record the command, exit status, meaningful output, artifact location, and the file state or revision and environment the result covers. Save relevant screenshots, logs, or traces in an isolated output location, with sensitive data excluded. Reuse inspected evidence while its tested inputs and environment remain unchanged. Recheck affected paths after relevant source, fixture, dependency, configuration, service, or device changes.
- **Lifecycle:** Note which process, container, session, or fixture this run created and how to identify it. Inspect existing instances before starting another. Stop or remove only resources owned by this run and authorized for cleanup; do not kill every process on a port or reset a shared device. Preserve the evidence needed to assess the result before cleaning temporary runtime state.

Existing task authorization still governs starting services, modifying test data, operating devices, or accessing external environments. A saved recipe is a repeatable method, not standing permission for those actions.

## Establish and maintain the recipe

During an authorized authoring task, run the proposed path and inspect its expected observations before calling the first recipe executable. Record the scope actually exercised. If the environment is unavailable or steps remain unrun, label the recipe **draft** and identify the unverified steps. A copied command or static review alone does not make it executable.

Keep static checks, local tests, simulated integrations, and real service/device paths distinct. A recipe can have a proven local path and a draft device path; its status must not imply both ran. Later verification still needs evidence for the current change, even if the recipe ran successfully in the past.

The maintainer of the referenced script, test, or owning feature should maintain the operational notes alongside changes that invalidate them. Update only affected details when an entrypoint moves, readiness changes, fixtures or roles change, an assertion no longer covers the contract, or runtime/service/device requirements change. Treat a stale recipe as a lead: inspect the current sources, run feasible checks, and report any remaining gap. Route persistent repairs to the authorized execution lane; do not let missing or outdated notes block checks that are otherwise possible.
