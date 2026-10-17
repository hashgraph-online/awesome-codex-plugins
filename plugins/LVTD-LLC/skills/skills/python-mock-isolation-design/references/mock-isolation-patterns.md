# Mock Isolation Patterns

## Replacement Choices

| Situation | Prefer |
| --- | --- |
| External API, email, payment, network | Fake service or mock server |
| Clock/time | Explicit time parameter or time-freezing helper |
| Small protocol with meaningful state | Hand-written fake |
| Imported collaborator in one module | `unittest.mock.patch` at lookup path |
| Complex interface that may drift | `autospec`, `spec`, or `spec_set` |
| Framework setting or request object | Framework test helper |

## Fake Object Pattern

Use fakes when behavior matters:

```python
class FakeMailer:
    def __init__(self):
        self.messages = []

    def send(self, to, subject, body):
        self.messages.append((to, subject, body))
```

Fakes are especially useful when assertions should read like domain outcomes.

## Patch Lookup Path

Patch the symbol used by the module under test:

```python
with patch("accounts.views.send_login_email", autospec=True) as send:
    response = client.post("/login/", {"email": "a@example.com"})
```

Patching the original library path may do nothing if the module already imported the dependency.

## Interaction Assertions

Interaction assertions are appropriate when:

- Sending an email is the behavior.
- Publishing an event is the behavior.
- Calling a gateway with exact data is the contract.

They are weak when they merely restate implementation steps that could change without changing behavior.

## Mock Smells

| Smell | Meaning | Response |
| --- | --- | --- |
| Many patches in one test | Hidden dependencies or large unit | Extract boundary or test at a different layer |
| Assertions only on calls | Outcome not proven | Add behavior assertion |
| Bare `MagicMock` chains | Imaginary interface | Use spec or fake |
| Test breaks on refactor | Implementation coupling | Raise test boundary or assert contract |
| Mocks of local domain functions | Testing test doubles | Use real domain code |

## Architecture Feedback

When mocks become the only way to make tests fast, consider:

- Moving pure logic into dependency-free functions.
- Passing dependencies explicitly.
- Creating ports/adapters around external systems.
- Keeping integration tests at boundaries and unit tests in the core.
