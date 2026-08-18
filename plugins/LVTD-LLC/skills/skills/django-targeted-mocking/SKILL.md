---
name: django-targeted-mocking
description: Mock Django test boundaries safely with override_settings, pytest settings, autospecced unittest.mock objects, output/input capture, requests-mock, VCR.py, outbound HTTP blocking, and time-freezing tools. Use when tests need to replace settings, HTTP calls, time, command output, stdin, or external services without broad fragile MagicMock patches.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.0"
  displayName: Django Targeted Mocking
  category: Django
  tags: django,testing,mocking,http,pytest
---

# Django Targeted Mocking

Mock only at boundaries that are slow, nondeterministic, external, or hard to trigger. Broad mocks can make tests faster while proving less, so prefer framework helpers and interface-checked replacements.

## Boundary Workflow

1. Decide whether mocking is necessary.
   - Prefer real code for local domain logic.
   - Mock external HTTP, time, settings, output/input, and expensive service edges.

2. Patch where the code under test looks up the dependency.
   - Patch the imported symbol used by the module under test, not the original library path unless that is what the module reads.

3. Prefer specific tools.
   - Settings: `override_settings`, `modify_settings`, or pytest-django's `settings` fixture.
   - Output: `io.StringIO`, pytest `capsys`, or command test helpers.
   - HTTP: `requests-mock` for hand-authored responses; VCR.py for recorded responses.
   - Time: pass time as a parameter when possible; otherwise use `time-machine` or a similar time-specific tool.

4. Make mocks interface-aware.
   - Use `autospec=True`, `spec`, `spec_set`, `create_autospec`, or a small fake object.
   - Avoid bare `Mock`/`MagicMock` when the interface matters.

5. Block unexpected outbound HTTP.
   - A normal test run should fail if a test reaches the network unintentionally.

Read [mocking-patterns.md](references/mocking-patterns.md) for concrete patterns.

## Decision Rules

- Use Django settings helpers instead of direct assignment to `django.conf.settings`.
- Prefer a hand-built fake or `types.SimpleNamespace` when only a few attributes are needed.
- Use `requests-mock` for deterministic API responses you control.
- Use VCR.py when real recorded responses are valuable and safe to store.
- On CI, configure VCR record mode so missing cassettes fail instead of recording.
- Mock time consistently across the runtime; do not patch several datetime functions by hand.
- Do not mock the component whose behavior the test is meant to prove.

## Common Mistakes

- Patching settings directly and leaking state across tests.
- Using catch-all `MagicMock` objects that accept typoed attributes and wrong call signatures.
- Allowing tests to hit real external services.
- Recording VCR cassettes in CI.
- Mocking a view's internal helpers so thoroughly that the test no longer covers request behavior.
- Patching the wrong import path and thinking the mock is active.

## Verification

Before finishing:

- Each mock has a clear boundary reason.
- Interface-sensitive mocks use specs or fakes.
- Unexpected outbound HTTP is blocked in the normal suite.
- Settings are restored automatically by Django or pytest helpers.
- Tests still cover the behavior, not only mock calls.
