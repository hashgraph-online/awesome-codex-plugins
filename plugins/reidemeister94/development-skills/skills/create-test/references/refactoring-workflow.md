# Refactoring Workflow — Cover, Modify, Verify

## The Legacy Code Paradox (Feathers)

You need tests before changing code, but code must change to become testable.

**Legacy code = code without tests.** A function written yesterday without tests is legacy.

## The Five-Step Resolution

### 1. Identify Seams

A **seam** is where you alter program behavior without editing the code. Python seams:

- **Class inheritance** — subclass and override in tests
- **Function parameters** — inject dependencies
- **Module imports** — monkeypatch at test time
- **Configuration** — environment variables, settings objects

```python
# BEFORE: hard dependency, untestable
class BillingService:
    def calculate(self, order_id):
        db = PostgresConnection()  # no seam
        order = db.get_order(order_id)
        return order.total * 1.22

# AFTER: seam via parameter
class BillingService:
    def __init__(self, db):  # seam: inject dependency
        self.db = db

    def calculate(self, order_id):
        order = self.db.get_order(order_id)
        return order.total * 1.22
```

### 2. Write Characterization Tests (Golden Master)

Capture what the code DOES — not what it should do. This includes bugs.

```python
def test_billing_characterization(data_dir):
    """Locks current behavior. Failures after refactoring = behavior changed."""
    service = BillingService(db=real_db_session)

    cases = [
        {"order_id": 1, "expected_file": "order_1.json"},
        {"order_id": 99, "expected_file": "order_99.json"},
        {"order_id": 0, "expected_file": "order_0_edge.json"},
    ]

    for case in cases:
        result = service.calculate(case["order_id"])
        baseline_path = data_dir / case["expected_file"]

        actual = normalize(result)

        if not baseline_path.exists():
            # First run: capture baseline
            baseline_path.write_text(json.dumps(actual, indent=2, default=str))
            pytest.skip(f"Baseline captured: {baseline_path}")

        expected = json.loads(baseline_path.read_text())
        assert actual == expected, (
            f"Behavior changed for order {case['order_id']}. "
            f"If intentional, delete {baseline_path} and re-run."
        )
```

**Normalization is critical** — without it, timestamps, IDs, and float imprecision break every test:

```python
def normalize(obj):
    """Deterministic comparison: scrub volatile fields, sort dicts, round floats."""
    if isinstance(obj, dict):
        return {
            k: normalize(v)
            for k, v in sorted(obj.items())
            if k not in ("timestamp", "updated_at", "request_id", "trace_id", "created_at")
        }
    if isinstance(obj, list):
        return [normalize(item) for item in obj]
    if isinstance(obj, float):
        return round(obj, 6)
    return obj
```

### 3. Add Property-Based Tests on Invariants

Characterization tests lock behavior. Property tests verify invariants that must survive the refactoring:

```python
@given(
    amount=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("999999.99"), places=2),
    tax_rate=st.decimals(min_value=Decimal("0"), max_value=Decimal("0.50"), places=2),
)
def test_tax_invariants(amount, tax_rate):
    result = calculate_tax(amount, tax_rate)
    assert result >= 0                          # non-negative
    assert result <= amount                     # tax never exceeds base
    assert result == calculate_tax(amount, tax_rate)  # deterministic
```

### 4. Refactor Using Safe Techniques

With the safety net in position:

**Sprout Method** — new logic in a separate function, tested independently, called from legacy:
```python
# Legacy function — don't touch it
def process_order(order):
    # ... 200 lines of untested code ...
    discount = calculate_new_discount(order)  # sprout: new, tested
    # ...

# New, tested function
def calculate_new_discount(order):
    """Isolated, testable logic."""
    if order.total > 1000:
        return order.total * Decimal("0.1")
    return Decimal("0")
```

**Wrap Method** — rename original, create wrapper with same name:
```python
def _process_order_original(order):
    """Renamed original."""
    # ... legacy code ...

def process_order(order):
    """Wrapper: new logic before/after original."""
    validate_order(order)           # new, tested
    result = _process_order_original(order)
    log_order_processed(order)      # new, tested
    return result
```

**Scratch Refactoring** — exploratory refactoring to understand opaque code. Rule: **REVERT ALL changes when done.** This builds comprehension before formal work.

### 5. Verify and Graduate

After refactoring:

```bash
# All characterization tests must still pass
pytest tests/characterization/ -v

# Property tests with high example count
pytest tests/properties/ --hypothesis-profile=ci

# (Optional) Mutation score check on refactored code
# Introduce deliberate bugs, verify tests catch them
```

**Graduation:** characterization tests capture bugs alongside correct behavior. As you understand the code, **replace** golden masters with behavioral tests that document intent. The golden master is a bridge, not the destination.

## The Sampling Technique (Rainsberger)

When combinatorial explosion makes exhaustive golden master testing impractical, sample:

```python
import random

def test_golden_master_sampled():
    """Sample random inputs, compare old vs new behavior."""
    random.seed(42)  # deterministic, reproducible
    for _ in range(500):
        inputs = {
            "amount": random.uniform(0.01, 999999.99),
            "currency": random.choice(["EUR", "USD", "GBP"]),
            "tier": random.choice(["standard", "premium", "enterprise"]),
        }
        old_result = normalize(legacy_process(**inputs))
        new_result = normalize(refactored_process(**inputs))
        assert old_result == new_result, f"Divergence on: {inputs}"
```

**Calibration:** start with 100. Increase until test time becomes annoying. The seed guarantees reproducibility.

## When NOT to Use Characterization Tests

- Code you fully understand and can write proper behavioral tests for
- Prototypes or throwaway code
- Code that will be deleted, not refactored
- Simple functions where boundary + property tests are sufficient
