# Risk-Proportional Testing and Validation

> Use this rule to choose evidence for a Tauri v2 + Vite + React + TanStack Router + TanStack Query architecture change. Run the project's existing commands; do not add a test framework, fake a native runtime, publish, sign, or alter a real user's data merely to satisfy this rule.

## Select Evidence by Changed Boundary

| Changed boundary | Minimum evidence | Add when risk increases |
|---|---|---|
| Pure React UI, route state, query presentation | Focused frontend test for pending, success, error, and not-found behavior | Browser-level navigation test for suspense, retry, accessibility, or reload behavior |
| Vite Router plugin, route files, or provider wiring | Production Vite build that generates the route tree and checks the Router plugin is before the React plugin | Browser-level navigation across generated routes, including validated search input |
| Query factory, loader, `loaderDeps`, mutation | Focused test with a fresh `QueryClient`; assert key inputs, loader cache reuse, and targeted invalidation | Test a stale/failed fetch and route preloading to prove Query, not Router, owns freshness |
| Desktop API adapter or IPC schema | Unit test the adapter with a typed mock and assert command name, arguments, result normalization, and rejection mapping | Rust command test plus capability/permission review for a privileged operation |
| Rust command, state, filesystem, plugin, or authorization | Rust unit/integration test for validation, authorization, state transition, and error form | Native E2E through `@wdio/tauri-service` in a disposable profile for OS integration, windows, dialogs, filesystem, updater, or plugin behavior |
| Packaged Tauri navigation or deep links | Native E2E from the packaged test build: launch, navigate between generated routes, open a supported deep link, and reload the active route | Test platform-specific protocol registration and a denied or malformed deep-link payload |
| Capabilities, permissions, scopes, CSP, asset policy, secrets | Static security review against the manifest and the least-privilege contract | Native E2E that proves an allowed path works and a denied path fails safely |
| This skill package | Skill-focused validation: frontmatter/links, bilingual rule parity, source-ledger date/version fields, and relevant eval cases | Full repository skill validation when the parent workflow requests it |

A test is not evidence when it bypasses the altered boundary. For example, a component mock does not prove Rust authorization; a successful Vite build does not prove packaged navigation or deep-link handling; and a successful allowed IPC call does not prove denial is enforced.

## Frontend, Router, and Query Cases

Keep UI tests deterministic and inject dependencies through the typed router context. For every changed generated route or query-backed route, cover the applicable cases:

1. The Vite production build generates the route tree from file routes, and `@tanstack/router-plugin/vite` is ordered before the React plugin.
2. One module-owned `QueryClient` and router are created; `QueryClientProvider` and `RouterProvider` receive those same instances.
3. The root route declares the typed router context; route code receives the narrow `DesktopApi`, not the raw Tauri bridge.
4. A loader calls `ensureQueryData` using the shared context client and the same `queryOptions` factory the component reads with `useSuspenseQuery`.
5. Result-changing route parameters and validated `loaderDeps` search values appear in the query key/factory input. Invalid search input follows the route's defined validation behavior.
6. `defaultPreloadStaleTime: 0` is present when Query is the freshness owner; freshness/refetch assertions belong to Query policy.
7. Pending UI appears during navigation; an expected fetch/IPC rejection reaches error UI and its retry path; a missing resource reaches not-found UI.
8. A successful mutation invalidates or updates only the affected keys, then the view shows the new authoritative result.

Use a new `QueryClient` per test. Disable or control retries and timers in the test client where they obscure the assertion; production defaults remain production policy. Mock the narrow `DesktopApi`, not `window.__TAURI__` or Router internals. A mock must reproduce the success, rejection, and malformed/unexpected-result paths relevant to the adapter contract.

## Rust, IPC, and Native E2E Cases

Test Rust at the policy boundary rather than only through happy-path JavaScript:

- Unit/integration-test deserialization, input validation, authorization, path/scope validation, state isolation, typed response serialization, and safe errors for each changed command.
- Use temporary directories, test state, and explicit cleanup for filesystem or persistence cases. Never point test code at a user profile, production endpoint, signing credential, or real secret store.
- For privileged commands, prove both an authorized request and an unauthorized, malformed, or out-of-scope request. The latter must fail without side effects or sensitive error disclosure.
- For packaged navigation, launch an unsigned development/test package with a disposable profile. Verify initial generated-route rendering, in-app navigation, a supported deep link, and reload of the active route; clean only artifacts created by the test.
- Do not turn a client route guard test into an authorization claim. Native command authorization needs Rust-side evidence.

**Recommended native harness.** Tauri documents WebdriverIO with `@wdio/tauri-service` as the recommended end-to-end path, and it covers Windows, Linux, and macOS:

- The default `embedded` provider runs an in-app WebDriver server through `tauri-plugin-wdio-webdriver`, so no external driver is installed; this is also how macOS is supported. `tauri-driver` remains the route for Windows and Linux when an external driver is preferred, and CrabNebula's fork covers all platforms but needs a paid key for macOS.
- `tauri-plugin-wdio` adds backend access: `browser.tauri.execute()` for Rust-side calls, command (IPC) mocking, and frontend/backend log capture. Use `execute()` to assert native authorization and denial instead of inferring them from UI state.
- The service's **browser mode** runs the frontend in plain Chrome against the Vite dev server and intercepts `invoke()`. Treat it as renderer evidence only: it never launches the packaged app, so it cannot stand in for packaging, plugin, OS-dialog, or native-permission evidence.
- Pin the service and plugin versions in the test project, record which provider a run used, and re-run release-critical flows on each shipped operating system rather than assuming one provider's result transfers.

## Build and Security Gates

For a packaged Vite SPA, build and package evidence MUST establish all of the following:

- The Vite production build completes, emits static frontend assets, and generates the route tree from file routes with the Router plugin before the React plugin.
- The Tauri build consumes the intended frontend distribution and, when navigation or native behavior changed, the generated package launches in the target test environment.
- Packaged-app testing covers generated-route navigation, a supported deep link, and reload of an active route without relying on a development server.
- The final capability/permission/scope/CSP/asset configuration grants only the commands, windows, origins, paths, and assets required by the tested behavior.
- Test logs, snapshots, fixture data, error reports, and packaged frontend assets contain no credentials, private paths, or raw native errors.

Treat a failed Vite production build, missing generated route tree, incorrect plugin order, packaged navigation/deep-link/reload failure, widened capability, or untested denial path as a release blocker.

## Bounded Correction Loop

Validation is a bounded correction loop, not open-ended optimization:

1. Run the smallest risk-matched gate and record the failing command/scenario, affected boundary, and observable failure.
2. Fix only the demonstrated cause, preserving the established architecture contract.
3. Re-run the same gate plus any directly affected gate.
4. Make **at most two validate/fix passes against the same gates**. Stop immediately on success.

After the second failed pass, stop changing code. Report the two observed failures, changed hypotheses, commands/scenarios, environment constraints, and the smallest unresolved blocker. Do not weaken tests, permissions, CSP, type checks, or error handling to manufacture a pass. Escalate a required production deployment, signing, credential, destructive migration, or external action for explicit authority instead of performing it.

## Skill Package Checks

When this skill package changes, run these repository-root checks in order:

```bash
node -e "const fs=require('node:fs'); const p='skills/hyper-architecture/assets/evals/tauri-cases.jsonl'; fs.readFileSync(p,'utf8').trim().split(/\\n/).forEach((line,index)=>{try{JSON.parse(line)}catch(error){throw new Error(`${p}:${index+1}: ${error.message}`)}});"
bash scripts/check-sources.sh --offline
bash scripts/verify.sh
```

The repository's skill-corpus validator is the structural gate; it is a repository-maintenance command, so this file names it instead of embedding a sibling skill's path: `validate-skills-corpus.sh --root skills --only hyper-architecture --json`. The JSONL parse is a fixture-integrity gate, not behavioral execution. This package has no package-specific behavior runner; inspect the stable positive, negative, boundary, missing-context, unsafe-action, source-guard, and regression cases in the fixture instead of claiming they executed. Do not invent a validator or treat fixture presence as proof of behavior.

## Readback Checklist

Before handoff, state which gates ran and their outcomes, or state precisely why a gate was not runnable. Confirm:

- [ ] Tests match every changed frontend, Router, Query, Rust, IPC, native, build, security, and skill surface that is in scope.
- [ ] Router tests confirm file-route generation and Router plugin order; Query tests use one injected client and a narrow desktop API mock.
- [ ] Authorization and denial evidence is Rust-side, not only a route guard.
- [ ] Packaged SPA evidence covers the Vite production build plus generated-route navigation, deep-link handling, and reload without a development server.
- [ ] Native E2E used only disposable state and made no publication, signing, credential, or destructive production change.
- [ ] The same gates passed within no more than two correction passes.

## Sources

> Links checked 2026-11-04.

| Claim | Source |
|---|---|
| Tauri's testing layers, IPC mocks, mock runtime, and the WebdriverIO-based native harness behind the native-evidence rows | [tauri-v2-2026-11-04.md](../../references/official/tauri/tauri-v2-2026-11-04.md); <https://v2.tauri.app/develop/tests/>; <https://v2.tauri.app/develop/tests/mocking/>; <https://v2.tauri.app/develop/tests/webdriver/>; <https://webdriver.io/docs/desktop-testing/tauri> |
| Router plugin order, the generated route tree, `defaultPreloadStaleTime`, and the loader/Query assertions | [tanstack-vite-react-2026-11-04.md](../../references/official/tauri/tanstack-vite-react-2026-11-04.md) |
| Packaged navigation, deep-link, and reload evidence in a disposable profile | [tauri-v2-2026-11-04.md](../../references/official/tauri/tauri-v2-2026-11-04.md); <https://v2.tauri.app/develop/tests/webdriver/> |
| The bounded correction loop, the skill package checks, and the readback checklist | This file's convention; the repository commands it names are repository policy, not external sources |
