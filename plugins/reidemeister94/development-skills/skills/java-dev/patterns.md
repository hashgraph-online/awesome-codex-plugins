# Java Patterns & Standards

This file contains the team's Java-specific patterns, standards, and code examples. Referenced by the java-dev skill during Research and Implementation phases.

---

## Guiding Principles

### Simplicity First

```
Simplest working solution > Clever solution > Over-engineered solution
```

- Avoid complexity and over-engineering at ALL costs
- Self-critique: If a simpler path exists, take it
- Three similar lines > premature abstraction

### Modern Java (21+)

```java
// CORRECT: Use var for local variables with clear types
var users = userRepository.findAll();
var config = new HashMap<String, Object>();

// CORRECT: Switch expressions
String result = switch (status) {
    case ACTIVE -> "Active";
    case INACTIVE -> "Inactive";
    case PENDING -> "Pending";
};

// CORRECT: Pattern matching for instanceof
if (obj instanceof String s) {
    System.out.println(s.length());
}

// CORRECT: Pattern matching in switch
String formatted = switch (obj) {
    case Integer i -> "int: " + i;
    case String s -> "string: " + s;
    case null -> "null";
    default -> "unknown";
};
```

### Records are Default for Data

Use Java Records for DTOs, value objects, and immutable data carriers:

```java
// GOOD: Record for immutable data
public record UserDto(
    Long id,
    String name,
    String email,
    Instant createdAt
) {}

public record ApiResponse<T>(
    T data,
    String message,
    boolean success
) {}

// BAD: Traditional POJO with boilerplate
public class UserDto {
    private Long id;
    private String name;
    // ... getters, setters, equals, hashCode, toString
}

// BAD: Lombok when Record suffices
@Data
@AllArgsConstructor
public class UserDto {
    private Long id;
    private String name;
}
```

Use Records unless mutability is strictly required.

### Stream API & Lambdas

```java
// GOOD: Stream API for collection processing
var activeUsers = users.stream()
    .filter(User::isActive)
    .map(User::getName)
    .toList();

// GOOD: Method references when clear
users.forEach(this::processUser);

// BAD: Verbose loop for simple transformation
List<String> names = new ArrayList<>();
for (User user : users) {
    if (user.isActive()) {
        names.add(user.getName());
    }
}
```

Prefer Streams when readable. Fall back to loops for complex logic.

---

## Architectural Rules

| Principle | Rule |
|-----------|------|
| **Dependency Injection** | Constructor injection only. No `new` for dependencies. No static singletons. |
| **Immutability** | Prefer immutable data structures. Use Records. |
| **Purity** | Methods are pure whenever possible. Side effects isolated and explicit. |
| **SRP** | Every method/class has ONE responsibility. |
| **Conciseness** | Methods under 70 lines. Longer = refactor candidate. |
| **DRY** | Refactor redundant code into reusable units. |
| **Modularity** | Small, focused, reusable classes and methods. |

### Dependency Injection

```java
// GOOD: Constructor injection
@Service
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;

    public UserService(UserRepository userRepository, EmailService emailService) {
        this.userRepository = userRepository;
        this.emailService = emailService;
    }
}

// BAD: Field injection
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;
}

// BAD: Creating dependencies internally
public class UserService {
    private final UserRepository userRepository = new UserRepositoryImpl();
}
```

---

## Exception Handling

```java
// GOOD: Domain-specific unchecked exceptions
public class DomainException extends RuntimeException {
    public DomainException(String message) {
        super(message);
    }

    public DomainException(String message, Throwable cause) {
        super(message, cause);
    }
}

public class UserNotFoundException extends DomainException {
    public UserNotFoundException(Long id) {
        super("User not found: " + id);
    }
}

// BAD: Empty catch block
try {
    process();
} catch (Exception e) {
    // ignored
}

// BAD: Catching generic Exception everywhere
try {
    process();
} catch (Exception e) {
    throw new RuntimeException(e);
}
```

---

## Documentation

```java
/**
 * Calculates the total price including tax.
 *
 * @param items line items to sum
 * @param taxRate tax multiplier (e.g., 0.08 for 8%)
 * @return total price including tax
 */
public BigDecimal calculateTotal(List<Item> items, BigDecimal taxRate) {
    // Only comment non-obvious logic
    var subtotal = items.stream()
        .map(Item::price)
        .reduce(BigDecimal.ZERO, BigDecimal::add);
    return subtotal.multiply(BigDecimal.ONE.add(taxRate));
}
```

- Brief Javadoc: summary + @param + @return
- Comments only for non-obvious logic
- Remove obvious/useless comments

---

## Workflow in Claude Code

### 1. Gather Context

Use tools to understand the codebase BEFORE proposing changes:

```
# Find relevant files
Glob: **/*.java, **/pom.xml, **/build.gradle

# Search for patterns
Grep: "class.*Service", "@Repository"

# Read specific files
Read: src/main/java/com/example/service/UserService.java
```

### 2. Plan (write it out)

Document your plan with assumptions, risks, unknowns, verification.

### 3. Implement

- Use Edit tool for modifications (surgical changes)
- Use Write tool only for new files
- Output ONLY changed code sections

### 4. Verify

- Run tests if they exist (mvn test, gradle test)
- Run build to check compilation
- Check for warnings

---

## Quick Reference

| Need | Do This |
|------|---------|
| Data carrier | Java Record |
| Local variable | `var` with clear type |
| Branching on value | Switch expression |
| Type check + cast | Pattern matching |
| Collection transform | Stream API |
| Dependency | Constructor injection |
| Side effect | Isolate, make explicit |
| Long method | Split into smaller methods |

## What NOT to Do

| Anti-Pattern | Why |
|--------------|-----|
| Raw types (`List` instead of `List<User>`) | Use generics for type safety |
| Field injection (`@Autowired` on fields) | Use constructor injection |
| `new` for dependencies inside class | Use dependency injection |
| Mutable DTOs when immutable works | Use Records |
| Lombok `@Data` when Record suffices | Records are built-in, cleaner |
| Empty catch blocks | Handle or propagate exceptions |
| Catching generic `Exception` | Catch specific exceptions |
| 100+ line methods | Break into focused units |
| Comments explaining obvious code | Delete them |
| Over-engineering "for the future" | Solve current problem only |
