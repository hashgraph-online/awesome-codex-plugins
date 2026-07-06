# TDD in Python

**Load this reference when:** doing TDD in Python. The core skill is language-agnostic; this file adds only Python framework choices, idioms, anti-patterns, and tooling. Generic mock pitfalls live in [../testing-anti-patterns.md](../testing-anti-patterns.md) and are not repeated here.

## Test framework & runner

Use **pytest** (current line: 9.x, e.g. 9.0.3). It is the de-facto standard over stdlib `unittest`: plain-function tests, `assert` rewriting (rich failure diffs without an assertion API), fixtures, and a large plugin ecosystem. `unittest` test cases still *run* under pytest, so you can adopt pytest incrementally on a `unittest` codebase.

```bash
pytest -q                              # run the whole suite, quiet
pytest tests/test_cart.py::test_empty_cart_total_is_zero -xvs
#       └ file ──────────┘ └ test ──┘  -x stop on first fail, -v verbose, -s don't capture stdout
pytest -k "total and not slow"         # select by name expression
pytest --lf                            # rerun only last-failed (tight red→green loop)
```

In the red→green loop, `pytest -q` is the quiet default (silent on green, full diff on red). The `-x` above stops at the first failure; the `-v`/`-s` are for **debugging one test's output** — drop them in the normal loop.

Configure in `pyproject.toml` (pytest 9.0 added a native `[tool.pytest]` table; the long-standing `[tool.pytest.ini_options]` still works):

```toml
# INI-style table — works on every pytest version (pytest 9.0+ also accepts a native [tool.pytest]):
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"   # report reasons for all non-passing outcomes
```

Minimal real failing test (RED) — derive the expectation independently, never paste the computed value back:

```python
# tests/test_cart.py
from shop.cart import Cart   # NameError/ImportError until shop.cart.Cart exists → a real failing test

def test_empty_cart_total_is_zero():
    assert Cart().total() == 0
```

## Idioms & conventions

- **Discovery:** files `test_*.py` / `*_test.py`, functions `test_*`, classes `Test*` (no `__init__`). Mirror your package under `tests/`.
- **Plain `assert`:** pytest rewrites assertions, so `assert response.status == 200` already prints both sides on failure. Don't reach for `self.assertEqual`.
- **Exceptions / warnings:** `with pytest.raises(ValueError, match="empty"):` and `pytest.warns(...)`. `match` is a regex on the message.
- **Fixtures** supply test dependencies and run setup/teardown via `yield`:
  ```python
  import pytest
  @pytest.fixture
  def cart():
      c = Cart()
      yield c            # everything after yield is teardown
      c.close()
  def test_add(cart):    # request by parameter name
      cart.add("apple")
      assert cart.count() == 1
  ```
- **`conftest.py`:** fixtures (and hooks) placed here are auto-discovered by every test in that directory tree — no import needed. Use it for shared fixtures, not for production code.
- **`@pytest.mark.parametrize`** runs one test body over many inputs, each a separate reported case:
  ```python
  @pytest.mark.parametrize("items, expected", [([], 0), (["a"], 1), (["a", "b"], 2)])
  def test_count(items, expected):
      assert Cart(items).count() == expected
  ```
- **Built-in fixtures for I/O & env:** `tmp_path` (a per-test `pathlib.Path` temp dir) for filesystem work; `monkeypatch` to set env vars / attributes / `chdir` with automatic restore (`monkeypatch.setenv("API_KEY", "x")`). `capsys` captures stdout/stderr.

## Python-specific anti-patterns

**1. Patching where the object is *defined*, not where it is *used*.** The single most common pytest mocking bug.
- ❌ `service.py` does `from shop.api import fetch`; the test patches `shop.api.fetch`.
- Why it's wrong: `from shop.api import fetch` binds a *new name* `service.fetch`. Patching the original leaves `service.fetch` pointing at the real function, so the mock is silently ignored and the test hits the network. The official docs state: "patch where an object is *looked up*, which is not necessarily the same place as where it is defined."
- ✅ Patch the lookup name: `mocker.patch("service.fetch")` (or `import shop.api` + use `shop.api.fetch`, then patch `shop.api.fetch`).
- Source: [unittest.mock — "Where to patch"](https://docs.python.org/3/library/unittest.mock.html#where-to-patch).

**2. Hand-patching `datetime.now` / `time.time`.**
- ❌ `mocker.patch("module.datetime")` then juggling a fake `.now()`.
- Why it's wrong: `datetime` is a C type whose methods can't be set as attributes, so you end up replacing the whole class and re-stubbing every method you touch — brittle and easy to get wrong. (Note: `datetime.utcnow()` has been deprecated since Python 3.12 and is still present in 3.14 — migrate anyway; use timezone-aware `datetime.now(timezone.utc)`.)
- ✅ Inject a clock (`now: Callable[[], datetime]` defaulting to `lambda: datetime.now(tz)`) — the testable, DI-friendly fix — or use a library: `freezegun`'s `@freeze_time("2026-06-04")` or `time-machine`'s `time_machine.travel(...)`.
- Source: [time-machine README — why freezing time needs a tool](https://github.com/adamchainz/time-machine), [freezegun](https://github.com/spulec/freezegun).

**3. Broad-scope fixtures leaking state.**
- ❌ `@pytest.fixture(scope="session")` (or `module`) returning a mutable object (DB connection, dict, client) that tests mutate.
- Why it's wrong: one instance is shared across many tests, so order-dependent failures appear and a test can pass or fail based on what ran before it. Default function scope gives each test a fresh object.
- ✅ Keep mutable state at function scope; reserve `session`/`module` for genuinely read-only or expensive-immutable setup, and reset shared resources in teardown.
- Source: [pytest — fixture scopes](https://docs.pytest.org/en/stable/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session).

**4. `autouse=True` fixtures with hidden side effects.**
- ❌ An `autouse` fixture that silently patches the network, seeds a DB, or freezes time for *every* test in scope.
- Why it's wrong: tests pass for reasons not visible in their own body; a reader can't tell what's mocked, and removing the fixture breaks distant tests. It hides exactly the dependency TDD wants explicit.
- ✅ Make dependencies explicit by requesting fixtures by name. Reserve `autouse` for harmless, universal setup (e.g. enforcing a deterministic timezone), not behavior the test asserts on.
- Source: [pytest — autouse fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html#autouse-fixtures-fixtures-you-don-t-have-to-request).

**5. Mocking the standard library / third-party internals instead of your own boundary.**
- ❌ `mocker.patch("requests.get", ...)` scattered through tests.
- Why it's wrong: you couple tests to a library's internal call shape; an upgrade or a swap to `httpx` breaks green tests even though behavior is unchanged. You're also asserting on the library, not your code.
- ✅ Wrap external calls behind your own thin function/class and patch *that* seam, or use a purpose-built fake (`responses`/`respx` for HTTP, `moto` for AWS) that emulates the real protocol.
- Source: ../testing-anti-patterns.md (mock at your own boundary); [responses](https://github.com/getsentry/responses).

**6. `unittest`-style `self.assertEqual` verbosity in a pytest codebase.**
- ❌ Subclassing `unittest.TestCase` just to call `self.assertEqual(a, b)`, `self.assertTrue(...)`.
- Why it's wrong: it forfeits pytest's assertion rewriting (so you get worse failure messages), blocks `parametrize`/fixture *injection by argument*, and adds class boilerplate for no gain.
- ✅ Write module-level functions with plain `assert`. Convert legacy `TestCase` files opportunistically.
- Source: [pytest — assert with the assert statement](https://docs.pytest.org/en/stable/how-to/assert.html).

**7. Over-`parametrize` that hides genuinely distinct behaviors.**
- ❌ Cramming the happy path, an exception case, and a boundary case into one parametrized body full of `if expected is Error: with pytest.raises(...)`.
- Why it's wrong: a single test name now covers different behaviors with branching logic, so a failure is harder to read and the test list (Canon TDD) stops mapping one behavior → one test. `parametrize` is for the *same* behavior over varied data.
- ✅ Parametrize equivalent inputs only; give distinct behaviors their own named tests. Use `pytest.param(..., id="negative-qty")` to label cases.
- Source: [pytest — parametrizing tests](https://docs.pytest.org/en/stable/how-to/parametrize.html).

## Tooling notes

- **Mocking:** `pytest-mock` exposes a `mocker` fixture — `mocker.patch(...)` with automatic teardown (no decorator/`with` nesting), `mocker.spy(obj, "method")` to wrap a real method while recording calls, `mocker.stub()` for lightweight callbacks. It wraps `unittest.mock`, so the "where to patch" rule still applies.
- **Coverage:** `coverage.py`, usually via `pytest-cov`: `pytest --cov=shop --cov-report=term-missing`. Treat coverage as a gap-finder, not a TDD goal — write the test for the behavior, not to color a line green.
- **Freezing time:** `freezegun` (`@freeze_time`) is ubiquitous; `time-machine` (`time_machine.travel`) is far faster (mocks at the C layer) and handles attributes freezegun's import-scan misses. Prefer injecting a clock when you control the code.
- **Property-based:** `hypothesis` (6.x) — `@given(st.lists(st.integers()))` generates many inputs and *shrinks* a failure to a minimal counterexample. Excellent for invariants ("round-trip", "sorted output is a permutation of input"). Composes with `parametrize` and fixtures.
- **Async:** `anyio`'s pytest plugin or `pytest-asyncio` (`@pytest.mark.asyncio`) to await coroutine tests.
- **Integration:** `tmp_path` for filesystem; `responses`/`respx` for HTTP boundaries; `testcontainers` or `pytest-docker` to spin a real DB/queue in a container instead of over-mocking.

## Quick reference

| Need | Use |
|---|---|
| Run whole suite | `pytest -q` |
| Run one test | `pytest path::test_name -xvs` |
| Rerun only failures | `pytest --lf` |
| Assert | plain `assert x == y` (rewritten) |
| Expect exception | `with pytest.raises(E, match="…"):` |
| Setup/teardown + DI | `@pytest.fixture` (+ `yield`) |
| Share fixtures | `conftest.py` (auto-discovered) |
| Same behavior, many inputs | `@pytest.mark.parametrize` |
| Temp dir / env vars | `tmp_path` / `monkeypatch` |
| Mock (auto-cleanup) | `pytest-mock` `mocker.patch("where.it.is.used")` |
| Coverage | `pytest --cov=pkg --cov-report=term-missing` |
| Freeze time | inject a clock · `freezegun` · `time-machine` |
| Property-based | `hypothesis` `@given(st.…)` |
