# TDD Workflow — Test-First through the Public Interface

Reference for `create-test`'s TDD mode. Adds two pieces of guidance on top of the project's canonical RED/GREEN/REFACTOR loop: how tests should read once they exist, and how to use mocking sparingly.

**Canonical RED/GREEN/REFACTOR + vertical-slice + "wrote production code first? delete it":** `shared/iron-rules.md` Process Rule B + `shared/phases/phase-3-implement-verify.md` Step 2. Do not paraphrase those here.

**When to apply this file:** new features with clear behavior, reproducible bug fixes, refactors covered by characterization tests. **When NOT:** exploratory prototypes where behavior emerges as you code.

## Tests through the public interface

A test verifies *behavior* through the public API, not implementation details. Code can change entirely; tests shouldn't. A good test name reads like a specification — `"user can checkout with valid cart"` tells you exactly what capability exists. Bad tests mock internal collaborators, assert on private methods, or verify through external channels (e.g., direct DB query instead of the documented interface). The warning sign: the test breaks when you refactor without behavior change.

## Interface-first ask

Before writing tests for a new feature, confirm with the user **which public-API behaviors matter most**. You can't test everything; concentrate effort on critical paths and complex logic, not every possible edge case. Ask: *"What should the public interface look like? Which behaviors matter most?"*

## Per-cycle checklist

```
[ ] The test describes behavior, not implementation
[ ] The test uses the public interface only
[ ] The test would survive an internal refactor
[ ] The code is minimal for this test
[ ] No speculative features added
```

## Good vs Bad Tests

### Good test (integration-style)

```python
# GOOD: tests observable behavior through the public interface
def test_user_can_checkout_with_valid_cart():
    cart = create_cart()
    cart.add(product)
    result = checkout(cart, payment_method)
    assert result.status == "confirmed"
```

Characteristics: tests behavior callers care about · uses public API only · survives internal refactors · describes WHAT, not HOW · one logical assertion per test.

### Bad test (implementation-coupled)

```python
# BAD: tests implementation details
def test_checkout_calls_payment_service_process():
    mock_payment = mocker.patch('payment_service.process')
    checkout(cart, payment)
    mock_payment.assert_called_once_with(cart.total)
```

Red flags: mocking internal collaborators · testing private methods · asserting on call counts/order · test name describes HOW not WHAT · verifying through external channels instead of the interface.

```python
# BAD: bypasses the interface to verify
def test_create_user_saves_to_database():
    create_user(name="Alice")
    row = db.query("SELECT * FROM users WHERE name = 'Alice'").first()
    assert row is not None

# GOOD: verifies through the interface
def test_create_user_makes_user_retrievable():
    user = create_user(name="Alice")
    retrieved = get_user(user.id)
    assert retrieved.name == "Alice"
```

## Mocking — only at boundaries

Mock ONLY at **system boundaries**: external APIs (payment, email, SMS), databases (sometimes — prefer a real test DB), time/randomness, file system (sometimes). **Don't mock** your own classes/modules, internal collaborators, or anything you control.

### Designing for mockability

**Dependency injection** — pass external dependencies in rather than creating them internally:

```python
# Easy to mock
def process_payment(order, payment_client):
    return payment_client.charge(order.total)

# Hard to mock
def process_payment(order):
    client = StripeClient(os.environ["STRIPE_KEY"])
    return client.charge(order.total)
```

**SDK-style interfaces** beat generic fetchers — each function is independently mockable, mocks return one specific shape, no conditional logic in test setup:

```python
# GOOD
class Api:
    def get_user(self, id): ...
    def get_orders(self, user_id): ...
    def create_order(self, data): ...

# BAD: mocking requires conditional logic inside the mock
class Api:
    def fetch(self, endpoint, options): ...
```

## Cross-link

- Canonical RED/GREEN/REFACTOR: `shared/iron-rules.md` Process Rule B + `shared/phases/phase-3-implement-verify.md`.
- Deep modules / deletion test / architecture glossary: `roast-my-code/references/architectural-depth.md`.
- Advanced test patterns (property-based, characterization, golden fixture, e2e): other files in `create-test/references/`.
