# Validation

1. Run `obsidian version` using the sanitized wrapper.
2. Run `dev:errors` and `dev:console` read-only checks.
3. Run one `dev:dom` and one `dev:css` query.
4. Validate screenshot path behavior with `dev:screenshot`.
5. Confirm the skill response reports risk level and exact command.
6. Confirm `eval` and `dev:cdp` flows require explicit request and full command disclosure.
7. With explicit runtime execution authorization and a disposable vault on 1.15.1+, verify `eval code="await Promise.resolve(42)"` returns `42` through the launcher. On older builds, stop before dispatching a request that uses top-level `await`.
