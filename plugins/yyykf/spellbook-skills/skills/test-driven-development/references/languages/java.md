# TDD in Java

**Load this reference when:** doing TDD in Java. The core skill is language-agnostic; this file adds only Java framework choices, idioms, anti-patterns, and tooling. Generic mock pitfalls live in [../testing-anti-patterns.md](../testing-anti-patterns.md) and are not repeated here.

## Test framework & runner

Idiomatic 2026 stack:

- **JUnit 5 (Jupiter)** — the default test framework. Use the `org.junit.jupiter:junit-jupiter` aggregator (pulls in `-api`, `-params`, `-engine`). **JUnit 6.0** (released 2025-09-30) unifies all module versions and raises the baseline to Java 17; if your project is still on Java 8–11, stay on the JUnit 5.x line. The programming model (`@Test`, `@Nested`, etc.) is essentially identical across 5.x and 6.x.
- **AssertJ** (`org.assertj:assertj-core`) — fluent, discoverable assertions. Preferred over raw Jupiter `Assertions` for everything beyond trivial checks.
- **Mockito** (`org.mockito:mockito-junit-jupiter`) — mocking, only at real seams (DB, network, clock). Since **Mockito 5.0** the inline mock-maker is the default.

Run the whole suite:

```bash
mvn -q test                 # Maven (Surefire ≥ 3.x runs JUnit Platform natively)
./gradlew test              # Gradle (needs `test { useJUnitPlatform() }`)
```

For an agent loop, prefer the quiet flag: `mvn -q test` (shown above) and `./gradlew test -q` both stay silent on green and print the full failure on red — add `-q` to the single-test commands too.

Run a single test (method-level):

```bash
mvn -Dtest='CalculatorTest#addsTwoPositiveNumbers' test
./gradlew test --tests 'com.example.CalculatorTest.addsTwoPositiveNumbers'
```

Minimal real failing test (the RED step — implementation does not exist yet, so it fails to compile/run, which is a valid red):

```java
package com.example;

import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;

class CalculatorTest {

    @Test
    void addsTwoPositiveNumbers() {
        int sum = new Calculator().add(2, 3);   // Calculator/add() not written yet
        assertThat(sum).isEqualTo(5);
    }
}
```

## Idioms & conventions

- **Test classes are package-private** (no `public` needed in JUnit 5) and live in `src/test/java` mirroring the production package, named `<Type>Test` (Surefire/Failsafe inclusion patterns expect `*Test` for unit, `*IT` for integration).
- **Name the behavior, not the method**: `returnsEmptyListWhenNoMatch()` over `testGetUsers()`. Add `@DisplayName("...")` for human-readable reports and use `@Nested` inner classes to group related scenarios (e.g. a `@Nested class WhenAccountIsClosed`).
- **Arrange-Act-Assert / given-when-then**: separate the three phases with blank lines. AssertJ chains keep the assert phase one statement: `assertThat(result).hasSize(2).extracting(User::name).containsExactly("Ann", "Bo");`.
- **Parametrize instead of copy-pasting** with `@ParameterizedTest`:
  - `@ValueSource(ints = {1, 2, 3})` for a single varying primitive.
  - `@CsvSource({"1, 1, 2", "2, 3, 5"})` — text-block form (`@CsvSource(textBlock = """ ... """)`) reads cleanly for several columns.
  - `@MethodSource("argsProvider")` returning `Stream<Arguments>` for objects/complex cases.
- **Lifecycle**: `@BeforeEach` for per-test fresh fixtures (default `PER_METHOD` lifecycle gives each test a new instance — rely on it instead of resetting state manually). Reserve `@BeforeAll` (static) for genuinely immutable, expensive setup.
- **Assert exceptions** with AssertJ: `assertThatThrownBy(() -> svc.load(id)).isInstanceOf(NotFoundException.class).hasMessageContaining(id);` — clearer than `assertThrows` + manual message checks.
- **Plain unit tests need no framework annotations beyond JUnit** — instantiate the class under test with `new` and pass test doubles in. If a test needs a Spring context to exist, that is a design signal, not the default.

## Java-specific anti-patterns

**❌ Defaulting to `@SpringBootTest` for every test**
→ *Why wrong:* It boots the full `ApplicationContext` — slow and broad. A measured comparison showed `@WebMvcTest` ready in ~3.7s vs `@SpringBootTest` ~6.9s, and a full-context test fails for reasons unrelated to the unit under test.
→ *✅ Fix:* Use a **slice**: `@WebMvcTest(controller)` for the web layer, `@DataJpaTest` for repositories/queries, `@JsonTest` for serialization — or, best of all, a plain POJO unit test with no context. Reserve `@SpringBootTest` for genuine end-to-end wiring tests. ([Spring Boot docs — Testing](https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html), [Zalando Engineering](https://engineering.zalando.com/posts/2023/11/mastering-testing-efficiency-in-spring-boot-optimization-strategies-and-best-practices.html))

**❌ Field / `@Autowired` injection on the class under test**
→ *Why wrong:* A field-injected dependency cannot be supplied with `new`; you can only set it via reflection, which breaks encapsulation and forces a container into otherwise-pure unit tests. It also lets an object exist without its invariants satisfied.
→ *✅ Fix:* **Constructor injection** — the test does `new OrderService(stubRepo, fixedClock)` directly, no Spring needed. ([Baeldung — Constructor Injection](https://www.baeldung.com/constructor-injection-in-spring))

**❌ Mocking value objects, entities, or DTOs (`mock(Money.class)`)**
→ *Why wrong:* They have no external dependency to isolate; a mock can drift from real equality/validation behavior, so the test verifies fiction.
→ *✅ Fix:* Just construct the real object: `new Money(10, EUR)`. Reserve mocks for collaborators at I/O seams. ([Mockito wiki — "How to write good tests": don't mock value objects](https://github.com/mockito/mockito/wiki/How-to-write-good-tests))

**❌ Reaching for `@MockBean` / `@SpyBean`**
→ *Why wrong:* Each distinct set of bean overrides produces a **new cached context**, multiplying startup cost across the suite; and both are **deprecated since Spring Boot 3.4 (removal in 4.0)**.
→ *✅ Fix:* Prefer plain Mockito + constructor injection. When you do need to replace a bean in a slice, use the Spring Framework annotations `@MockitoBean` / `@MockitoSpyBean` (or `@TestBean`). ([Spring Boot 3.4 release notes / deprecation](https://docs.spring.io/spring-boot/3.4/api/java/org/springframework/boot/test/mock/mockito/MockBean.html))

**❌ `assertEquals(expected, actual)` for collections / rich objects**
→ *Why wrong:* On failure you get only "expected X but was Y" with no structural diff, and argument order is easy to flip.
→ *✅ Fix:* AssertJ — `assertThat(list).containsExactlyInAnyOrder(...)`, `.usingRecursiveComparison().isEqualTo(expected)` — gives precise, readable diffs. ([AssertJ docs](https://assertj.github.io/doc/))

**❌ Shared mutable state in `static` fields or `@BeforeAll`**
→ *Why wrong:* JUnit gives no guaranteed cross-class execution order; leaked state makes tests pass/fail depending on run order ("flaky"). This is the Java face of the generic test-isolation rule.
→ *✅ Fix:* Keep fixtures in instance fields rebuilt in `@BeforeEach`; if shared state is unavoidable, reset it explicitly per test. ([JUnit 5 User Guide — test instance lifecycle](https://docs.junit.org/current/user-guide/#writing-tests-test-instance-lifecycle))

## Tooling notes

- **Coverage:** **JaCoCo** (`jacoco-maven-plugin` / Gradle `jacoco`) — use `check` rules to fail the build below a threshold. Treat coverage as a smell detector for untested branches, not a target to game.
- **Assertions / mocking:** AssertJ for assertions; Mockito for stubs/spies (`mockito-junit-jupiter` adds the `@ExtendWith(MockitoExtension.class)` integration with `@Mock`/`@InjectMocks`). Mockito 5+ mocks `final` classes and `static` methods (via `mockStatic(...)` in a try-with-resources) out of the box — but needing this is usually a design smell; prefer extracting a seam.
- **Integration / real infra:** **Testcontainers** spins up the *real* database, broker, etc. in Docker so you test against production-equivalent infra instead of H2 substitutes. Pair with `@SpringBootTest` or `@DataJpaTest(replace = NONE)` for true integration tests, named `*IT` and run by Failsafe.
- **Async:** **Awaitility** — `await().atMost(Duration.ofSeconds(2)).untilAsserted(() -> assertThat(repo.count()).isEqualTo(1));` instead of `Thread.sleep`, which is slow and flaky.
- **CI:** Surefire runs `*Test` (unit) on `mvn test`; Failsafe runs `*IT` (integration) on `mvn verify`. Keep the fast unit suite separate so the red-green loop stays sub-second.

## Quick reference

| Need | Use | Avoid |
|---|---|---|
| Test framework | JUnit 5/6 (Jupiter) | JUnit 4 (`@RunWith`), TestNG (legacy) |
| Assertions | AssertJ `assertThat(...)` | bare `assertEquals` for rich types |
| Mocking seams | Mockito at I/O boundaries | mocking value objects/entities |
| Web layer test | `@WebMvcTest` | `@SpringBootTest` for a controller |
| Repository test | `@DataJpaTest` | full-context for one query |
| Replace a bean | `@MockitoBean` / `@TestBean` | deprecated `@MockBean`/`@SpyBean` |
| DI for testability | constructor injection | field / `@Autowired` injection |
| Real DB integration | Testcontainers (`*IT`, Failsafe) | asserting against H2 then shipping Postgres |
| Wait for async | Awaitility | `Thread.sleep` |
| Parametrize | `@ValueSource` / `@CsvSource` / `@MethodSource` | copy-pasted near-identical `@Test`s |
| Coverage gate | JaCoCo `check` | chasing 100% as a goal |
