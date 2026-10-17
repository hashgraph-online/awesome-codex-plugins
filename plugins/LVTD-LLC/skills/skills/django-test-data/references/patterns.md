# Test Data Patterns

## Test Base Class Selection

| Need | Class |
|------|-------|
| Pure Python logic, form validation without DB, middleware unit, helper method | `SimpleTestCase` |
| Models, ORM reads/writes, ordinary view tests | `TestCase` |
| Committed transaction behavior, low-level transaction edge cases | `TransactionTestCase` |
| Browser/live server behavior | `LiveServerTestCase` |

Split test classes when only some methods need database access.

## Arrange-Act-Assert

Use Arrange-Act-Assert as a readability guide:

- Arrange only the data needed for the behavior.
- Act once when the behavior has one meaningful effect.
- Assert all facts that describe that effect.

Avoid splitting one expensive request into many tests just to enforce "one assertion per test". That can make the suite slower without improving clarity.

## Factories

Small factory functions are enough for simple projects:

```python
def make_book(**kwargs):
    defaults = {"title": "Django Patterns"}
    defaults.update(kwargs)
    return Book.objects.create(**defaults)
```

Use Factory Boy or Model Bakery when:

- Relationships are repetitive.
- Many tests need valid default objects.
- Variants would otherwise create long setup blocks.

Keep factories lean. If every call creates users, permissions, orders, payments, and logs, the factory has become another fixture file.

## setUpTestData

Use `setUpTestData()` to create class-level database objects once for a `TestCase`:

```python
class BookTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.book = Book.objects.create(title="Django Patterns")
```

Django rolls back database writes between methods, but Python object mutation can still surprise you. Refresh from the database or avoid mutating shared instances directly.

## Transaction Edge Cases

For `IntegrityError` inside `TestCase`, wrap the failing operation in an inner transaction:

```python
with transaction.atomic():
    with self.assertRaises(IntegrityError):
        create_duplicate()
```

For `transaction.on_commit()`, prefer `TestCase.captureOnCommitCallbacks()` before switching to `TransactionTestCase`.

## Component Boundaries

| Component | Faster Test Boundary |
|-----------|----------------------|
| Form | Instantiate form, inspect `errors`, `cleaned_data`, and validity |
| Management command | Extract helper methods; keep one `call_command()` smoke/integration test |
| Middleware | Use `RequestFactory` and simple `get_response` callable |
| View | Keep request-path tests for wiring; move complex branching into testable functions |
