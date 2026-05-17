# Language Templates Reference

## Python (pytest + hypothesis)

### Test file scaffold

```python
"""Tests for {module_name} — boundary, property, and invariant testing."""
import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from {module_path} import {functions_under_test}


# --- Boundary Tests ---

class TestBoundary{FunctionName}:
    """Boundary stress tests at identified thresholds."""

    @pytest.mark.parametrize("input_val, expected", [
        (THRESHOLD - 1, ...),  # Just below boundary
        (THRESHOLD, ...),      # At boundary
        (THRESHOLD + 1, ...),  # Just above boundary
    ])
    def test_{function}_at_boundary(self, input_val, expected):
        result = {function}(input_val)
        assert result == expected

    def test_{function}_empty_input(self):
        result = {function}(EMPTY)
        assert result == EXPECTED_FOR_EMPTY

    def test_{function}_null_handling(self):
        with pytest.raises(EXPECTED_ERROR):
            {function}(None)


# --- Property-Based Tests ---

class TestProperties{FunctionName}:
    """Invariants verified over random inputs."""

    @given(st.{strategy}())
    @settings(max_examples=200)
    def test_{invariant_name}(self, data):
        result = {function}(data)
        assert INVARIANT_HOLDS(result, data)

    @given(st.{strategy}())
    def test_round_trip(self, data):
        encoded = encode(data)
        decoded = decode(encoded)
        assert decoded == data


# --- Reference Implementation Tests ---

class TestInvariant{FunctionName}:
    """Compare optimized implementation against simple reference."""

    @given(st.lists(st.integers(), min_size=0, max_size=1000))
    def test_matches_reference(self, data):
        def reference_impl(d):
            # Simple, obviously correct version
            return sorted(d)

        assert {function}(data) == reference_impl(data)


# --- Random Stress Tests ---

class TestStress{FunctionName}:
    """High-volume random testing for edge cases."""

    @given(st.{strategy}())
    @settings(max_examples=1000)
    def test_no_crash_on_random_input(self, data):
        result = {function}(data)
        assert result is not None
        # Plus specific invariant assertions:
        assert INVARIANT(result)
```

### Hypothesis strategies for common types

```python
# Strings biased toward boundaries
st.text(min_size=0, max_size=300).filter(lambda s: len(s) in range(LIMIT-2, LIMIT+3))

# Integers near boundaries
st.integers(min_value=THRESHOLD-10, max_value=THRESHOLD+10)

# DataFrames (with pandas)
@st.composite
def dataframes(draw):
    n_rows = draw(st.integers(min_value=0, max_value=100))
    return pd.DataFrame({
        "col_a": draw(st.lists(st.integers(), min_size=n_rows, max_size=n_rows)),
        "col_b": draw(st.lists(st.text(min_size=1), min_size=n_rows, max_size=n_rows)),
    })

# JSON-like structures (for parser testing)
json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(),
    lambda children: st.lists(children) | st.dictionaries(st.text(min_size=1), children),
    max_leaves=50,
)
```

### Hypothesis composite strategies for domain objects

```python
from hypothesis import strategies as st

@st.composite
def valid_orders(draw):
    """Generate realistic Order objects with valid relationships."""
    user_id = draw(st.integers(min_value=1))
    items = draw(st.lists(
        st.builds(OrderItem,
            product_id=st.integers(min_value=1),
            quantity=st.integers(min_value=1, max_value=100),
            price=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("9999.99")),
        ),
        min_size=1, max_size=20,
    ))
    return Order(user_id=user_id, items=items)

@st.composite
def valid_date_ranges(draw):
    """Generate start/end date pairs where start < end."""
    start = draw(st.dates())
    delta = draw(st.timedeltas(min_value=timedelta(days=1), max_value=timedelta(days=365)))
    return start, start + delta

# Use in tests:
@given(order=valid_orders())
def test_order_total_matches_items(order):
    assert order.total == sum(item.price * item.quantity for item in order.items)
```

### Hypothesis settings profiles

```python
# conftest.py — configure profiles for different environments
from hypothesis import settings, Phase, HealthCheck

settings.register_profile("ci", max_examples=1000, deadline=None,
    suppress_health_check=[HealthCheck.too_slow])
settings.register_profile("dev", max_examples=50, deadline=500)
settings.register_profile("debug", max_examples=10,
    phases=[Phase.explicit, Phase.generate])

# Activate via CLI: pytest --hypothesis-profile=ci
# Or in pyproject.toml:
# [tool.hypothesis]
# default = "dev"
```

### Stateful testing scaffold (hypothesis RuleBasedStateMachine)

```python
"""Stateful tests for {module_name} — generates random sequences of operations."""
from hypothesis.stateful import (
    RuleBasedStateMachine, rule, invariant, precondition, initialize, Bundle, consumes,
)
from hypothesis import settings
from hypothesis import strategies as st

from {module_path} import {SystemUnderTest}


class {SystemName}StateMachine(RuleBasedStateMachine):
    """Models {system} as a state machine. Hypothesis generates random operation
    sequences and verifies invariants after every step.

    Pattern: maintain both the real implementation and a simple in-memory model.
    Run identical operations on both. Assert equivalence.
    """

    def __init__(self):
        super().__init__()
        self.system = {SystemUnderTest}()
        self.model = {}  # simple dict as reference implementation

    # --- Bundles: reusable values across operations ---
    keys = Bundle("keys")

    # --- Initialize: runs exactly once before any rule ---
    @initialize(target=keys, k=st.text(min_size=1, max_size=50))
    def seed_initial_key(self, k):
        self.system.create(k, "initial")
        self.model[k] = "initial"
        return k

    # --- Rules: operations that can be chained in any order ---
    @rule(target=keys, k=st.text(min_size=1, max_size=50), v=st.text())
    def create(self, k, v):
        self.system.create(k, v)
        self.model[k] = v
        return k

    @rule(k=keys, v=st.text())
    def update(self, k, v):
        self.system.update(k, v)
        self.model[k] = v

    @rule(k=consumes(keys))  # consumes: removes from bundle after use
    def delete(self, k):
        self.system.delete(k)
        del self.model[k]

    @rule(k=keys)
    def read(self, k):
        assert self.system.get(k) == self.model[k]

    # --- Preconditions: filter when rules execute ---
    @precondition(lambda self: len(self.model) > 0)
    @rule()
    def count(self):
        assert self.system.count() == len(self.model)

    # --- Invariants: checked after EVERY step ---
    @invariant()
    def model_matches_system(self):
        for k, v in self.model.items():
            assert self.system.get(k) == v

    @invariant()
    def count_non_negative(self):
        assert self.system.count() >= 0


# Run as pytest test
Test{SystemName} = {SystemName}StateMachine.TestCase
Test{SystemName}.settings = settings(max_examples=100, stateful_step_count=30)
```

**Key patterns:**
- `Bundle("name")` — pool of values reusable across rules
- `target=bundle` on rule return → adds value to bundle
- `consumes(bundle)` — draws AND removes from bundle
- `@precondition(lambda self: ...)` — skip rule if condition is false
- `@invariant()` — checked after every single step
- `@initialize(target=...)` — runs exactly once, before any rule

**Use stateful testing when:**
- System has mutable state (caches, databases, shopping carts, state machines)
- Operations can be chained in any order
- Bugs emerge from specific sequences of operations (race conditions, state corruption)
- You need to verify invariants hold across ALL possible operation sequences

### Mutation testing setup (mutmut)

```bash
# Install
pip install mutmut

# Run against specific module
mutmut run --paths-to-mutate=src/core/

# View surviving mutants (tests didn't catch these bugs)
mutmut results
mutmut show <id>  # inspect a specific surviving mutant

# CI integration: fail if mutation score drops below threshold
mutmut run --paths-to-mutate=src/core/ && mutmut results --json | \
  python -c "import sys,json; d=json.load(sys.stdin); \
  sys.exit(0 if d['killed']/(d['killed']+d['survived']) > 0.85 else 1)"
```

### Contract testing scaffold (Pact — Python consumer)

```python
"""Consumer-driven contract test — defines what this service expects from provider."""
import pytest
from pathlib import Path
from pact.v3 import Pact, match

@pytest.fixture
def pact():
    pact = Pact("my-consumer", "user-provider").with_specification("V4")
    yield pact
    pact.write_file(Path(__file__).parent / "pacts")

def test_get_user(pact):
    expected_response = {
        "id": match.int(123),
        "name": match.str("Alice"),
        "email": match.regex(r".+@.+\..+", "alice@example.com"),
    }
    (
        pact.upon_receiving("A user request")
        .given("the user exists", parameters={"id": 123})
        .with_request("GET", "/users/123")
        .will_respond_with(200)
        .with_body(expected_response, content_type="application/json")
    )
    with pact.serve() as srv:
        # Call your actual client code against the mock server
        client = UserClient(str(srv.url))
        user = client.get_user(123)
        assert user.name == "Alice"
```

### Golden fixture patterns (pytest)

```python
# conftest.py — golden fixture loading
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "golden"

@pytest.fixture(params=["config_a", "config_b"])
def config_name(request) -> str:
    return request.param

@pytest.fixture
def golden_data(config_name: str) -> dict:
    fixture_dir = FIXTURES_DIR / config_name
    return {
        "inputs": {f.stem: json.loads(f.read_text()) for f in (fixture_dir / "inputs").glob("*.json")},
        "outputs": {f.stem: json.loads(f.read_text()) for f in (fixture_dir / "outputs").glob("*.json")},
    }

# Capture script
def capture_golden(config_name: str):
    """Run once against live system to capture golden fixtures."""
    inputs = fetch_real_inputs(config_name)
    outputs = compute(inputs)
    fixture_dir = FIXTURES_DIR / config_name
    (fixture_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (fixture_dir / "outputs").mkdir(parents=True, exist_ok=True)
    for name, data in inputs.items():
        (fixture_dir / "inputs" / f"{name}.json").write_text(json.dumps(data, default=str, indent=2))
    for name, data in outputs.items():
        (fixture_dir / "outputs" / f"{name}.json").write_text(json.dumps(data, default=str, indent=2))
```

### Integration test scaffold (pytest + testcontainers)

```python
"""Integration tests for {module_name} — real PostgreSQL, transaction-isolated."""
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from {module_path} import {repository_or_service}


# --- Container Fixtures (conftest.py, session scope) ---

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

@pytest.fixture(scope="session")
def db_engine(postgres_container):
    engine = create_engine(postgres_container.get_connection_url())
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# --- Factory Fixtures ---

@pytest.fixture
def make_{entity}(db_session):
    def make(field_a="default_a", field_b=42, **overrides):
        obj = {Entity}(field_a=field_a, field_b=field_b, **overrides)
        db_session.add(obj)
        db_session.flush()
        return obj
    yield make


# --- Integration Tests ---

class TestRepository{Entity}:
    """Tests against real PostgreSQL — each test rolls back."""

    def test_create_and_retrieve(self, db_session, make_{entity}):
        entity = make_{entity}(field_a="test_value")
        result = {repository}.get_by_id(db_session, entity.id)
        assert result is not None
        assert result.field_a == "test_value"

    def test_unique_constraint_enforced(self, db_session, make_{entity}):
        make_{entity}(unique_field="taken")
        with pytest.raises(IntegrityError):
            make_{entity}(unique_field="taken")

    def test_query_filters_correctly(self, db_session, make_{entity}):
        make_{entity}(status="active")
        make_{entity}(status="active")
        make_{entity}(status="inactive")
        results = {repository}.find_by_status(db_session, "active")
        assert len(results) == 2
        assert all(r.status == "active" for r in results)

    def test_aggregation_accuracy(self, db_session, make_{entity}):
        make_{entity}(amount=100.0)
        make_{entity}(amount=250.5)
        make_{entity}(amount=49.5)
        total = {repository}.sum_amounts(db_session)
        assert total == pytest.approx(400.0)
```

### Concurrency test scaffold (pytest + asyncio)

```python
"""Concurrency tests for {module_name} — race conditions, atomicity."""
import asyncio
import pytest

from {module_path} import {async_function}


@pytest.mark.asyncio
class TestConcurrency{Feature}:
    """Verify correctness under concurrent access."""

    async def test_no_double_booking(self, db_session, make_resource):
        """Two concurrent claims on last resource — exactly one wins."""
        resource = make_resource(available=1)
        results = await asyncio.gather(
            {async_function}(resource.id, user_a),
            {async_function}(resource.id, user_b),
            return_exceptions=True,
        )
        successes = [r for r in results if not isinstance(r, Exception)]
        assert len(successes) == 1

    async def test_counter_atomicity(self, db_session, make_counter):
        """N concurrent increments produce exactly +N."""
        counter = make_counter(value=0)
        N = 50
        await asyncio.gather(*[
            increment_counter(counter.id) for _ in range(N)
        ])
        refreshed = await get_counter(counter.id)
        assert refreshed.value == N

    async def test_idempotent_operation(self, db_session, make_resource):
        """Duplicate requests with same key produce same result."""
        key = "idempotency-key-123"
        r1 = await {async_function}(key=key, amount=100)
        r2 = await {async_function}(key=key, amount=100)
        assert r1.id == r2.id  # same record, not duplicated
```

### Characterization test scaffold (approval testing)

```python
"""Characterization tests for {module_name} — locks current behavior for safe refactoring."""
import json
import pytest
from pathlib import Path

from {module_path} import {function_under_test}

BASELINES_DIR = Path(__file__).parent / "baselines"


def normalize(obj):
    """Scrub volatile fields for deterministic comparison."""
    if isinstance(obj, dict):
        return {k: normalize(v) for k, v in sorted(obj.items())
                if k not in ("timestamp", "updated_at", "request_id")}
    if isinstance(obj, list):
        return [normalize(item) for item in obj]
    if isinstance(obj, float):
        return round(obj, 6)
    return obj


class TestCharacterization{Module}:
    """WARNING: These tests lock CURRENT behavior, including bugs.
    Failures after refactoring = behavior changed (intended or not)."""

    @pytest.mark.parametrize("case_name", ["case_a", "case_b", "case_c"])
    def test_output_matches_baseline(self, case_name):
        input_file = BASELINES_DIR / case_name / "input.json"
        baseline_file = BASELINES_DIR / case_name / "output.json"

        input_data = json.loads(input_file.read_text())
        actual = {function_under_test}(**input_data)
        actual_normalized = normalize(actual)

        if not baseline_file.exists():
            # First run: capture baseline
            baseline_file.parent.mkdir(parents=True, exist_ok=True)
            baseline_file.write_text(json.dumps(actual_normalized, indent=2))
            pytest.skip(f"Baseline captured for {case_name} — re-run to verify")

        expected = json.loads(baseline_file.read_text())
        assert actual_normalized == expected, (
            f"Behavior changed for {case_name}. "
            f"If intentional, delete {baseline_file} and re-run to capture new baseline."
        )


# --- Capture Script (run once to generate baselines) ---

def capture_baselines():
    """Run against live system to capture golden baselines.
    Usage: python -c 'from test_{module} import capture_baselines; capture_baselines()'
    """
    cases = {
        "case_a": {"param1": "value1", "param2": 42},
        "case_b": {"param1": "value2", "param2": 0},
        "case_c": {"param1": "edge_case", "param2": -1},
    }
    for name, inputs in cases.items():
        output = {function_under_test}(**inputs)
        case_dir = BASELINES_DIR / name
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "input.json").write_text(json.dumps(inputs, indent=2))
        (case_dir / "output.json").write_text(json.dumps(normalize(output), indent=2))
    print(f"Captured {len(cases)} baselines to {BASELINES_DIR}")
```

---

## Java (JUnit 5 + jqwik) — Key Patterns

Same concepts as Python. Key syntax differences:

```java
// Boundary: @ParameterizedTest + @CsvSource
@ParameterizedTest
@CsvSource({"255, BELOW", "256, AT", "257, ABOVE"})
void boundaryTest(int input, String expected) {
    assertThat(subject.method(input)).isEqualTo(expected);
}

// Property-based: jqwik @Property
@Property(tries = 200)
void roundTrip(@ForAll String input) {
    assertThat(subject.decode(subject.encode(input))).isEqualTo(input);
}

// Reference implementation
@Property(tries = 500)
void matchesReference(@ForAll @Size(max = 100) List<Integer> data) {
    assertThat(subject.process(data)).isEqualTo(data.stream().sorted().toList());
}

// Null handling: AssertJ
assertThatThrownBy(() -> subject.method(null)).isInstanceOf(IllegalArgumentException.class);
```

---

## TypeScript (vitest + fast-check) — Key Patterns

Same concepts as Python. Key syntax differences:

```typescript
// Boundary: it.each
it.each([
  [THRESHOLD - 1, EXPECTED_BELOW],
  [THRESHOLD, EXPECTED_AT],
  [THRESHOLD + 1, EXPECTED_ABOVE],
])('boundary %i', (input, expected) => {
  expect(functionUnderTest(input)).toEqual(expected);
});

// Property-based: fast-check
it('round-trip', () => {
  fc.assert(fc.property(fc.string(), (input) => {
    expect(decode(encode(input))).toEqual(input);
  }), { numRuns: 200 });
});

// Reference implementation
it('matches naive', () => {
  fc.assert(fc.property(fc.array(fc.integer(), { maxLength: 100 }), (data) => {
    expect(functionUnderTest(data)).toEqual([...data].sort((a, b) => a - b));
  }), { numRuns: 500 });
});
```

For Playwright E2E and Pact contract scaffolds, see `e2e-browser-patterns.md`.

---

## Swift (swift-testing) — Key Patterns

Same concepts as Python. Key syntax differences:

```swift
import Testing
@testable import ModuleName

// Boundary: @Test with arguments
@Test("boundary", arguments: [
    (THRESHOLD - 1, ExpectedBelow), (THRESHOLD, ExpectedAt), (THRESHOLD + 1, ExpectedAbove),
])
func boundary(input: Int, expected: Output) {
    #expect(functionUnderTest(input) == expected)
}

// Invariant: loop with random inputs (no hypothesis equivalent in Swift)
@Test("round-trip")
func roundTrip() {
    for _ in 0..<200 {
        let input = randomInput()
        #expect(decode(encode(input)) == input)
    }
}

// Reference implementation
@Test("matches reference")
func matchesReference() {
    for _ in 0..<500 {
        let data = (0..<Int.random(in: 0...100)).map { _ in Int.random(in: -1000...1000) }
        #expect(functionUnderTest(data) == data.sorted())
    }
}
```
