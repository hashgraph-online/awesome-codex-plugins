# Swift Patterns & Standards

This file contains the team's Swift-specific patterns, standards, and code examples. Referenced by the swift-dev skill during Research and Implementation phases.

---

## Guiding Principles

### Simplicity First

```
Simplest working solution > Clever solution > Over-engineered solution
```

- Avoid complexity and over-engineering at ALL costs
- Self-critique: If a simpler path exists, take it
- Three similar lines > premature abstraction

### Modern Swift (5.9+ / Swift 6)

```swift
// CORRECT: Structured concurrency
func fetchUserData(id: String) async throws -> User {
    async let profile = fetchProfile(id: id)
    async let preferences = fetchPreferences(id: id)
    return try await User(profile: profile, preferences: preferences)
}

// CORRECT: if/switch expressions (Swift 5.9+)
let label = if count == 0 { "empty" } else { "has items" }

let icon = switch status {
    case .active: "checkmark.circle"
    case .inactive: "xmark.circle"
    case .pending: "clock"
}

// CORRECT: Parameter packs (Swift 5.9+)
func all<each T: Equatable>(lhs: repeat each T, rhs: repeat each T) -> Bool {
    func isEqual<V: Equatable>(_ l: V, _ r: V) -> Bool { l == r }
    return (repeat isEqual(each lhs, each rhs)).allSatisfy { $0 }
}

// CORRECT: Consume / borrowing ownership
func process(_ data: consuming Data) -> ProcessedData {
    // data is consumed — caller can no longer use it
    return transform(data)
}
```

### Value Types by Default

```swift
// GOOD: Struct for data models
struct User: Codable, Sendable {
    let id: UUID
    var name: String
    var email: String
    let createdAt: Date
}

// GOOD: Enum for finite states
enum LoadingState<T: Sendable>: Sendable {
    case idle
    case loading
    case loaded(T)
    case failed(any Error & Sendable)
}

// BAD: Class when struct suffices
class User {
    var id: UUID
    var name: String
    // ... reference semantics not needed
}
```

Use classes ONLY when:
- You need reference semantics (shared mutable state)
- Inheriting from NSObject (UIKit interop)
- Using actors for concurrency safety

---

## Architecture Patterns

### Project Structure (SPM Package)

```
Sources/
├── App/
│   ├── Models/              # Domain models & DTOs
│   │   ├── User.swift
│   │   └── Requests/        # API request models
│   ├── Services/            # Business logic layer
│   │   └── UserService.swift
│   ├── Repositories/        # Data access layer
│   │   └── UserRepository.swift
│   ├── Networking/          # HTTP client & API definitions
│   │   ├── APIClient.swift
│   │   └── Endpoints.swift
│   ├── Extensions/          # Type extensions
│   └── App.swift            # Entry point
Tests/
├── AppTests/
│   ├── Services/
│   │   └── UserServiceTests.swift
│   └── Mocks/
│       └── MockUserRepository.swift
```

**Flow:** View/Controller → Service → Repository → Network/Database

### Project Structure (SwiftUI App)

```
MyApp/
├── App/
│   └── MyApp.swift          # @main entry point
├── Features/
│   ├── Auth/
│   │   ├── AuthView.swift
│   │   ├── AuthViewModel.swift
│   │   └── AuthService.swift
│   └── Home/
│       ├── HomeView.swift
│       └── HomeViewModel.swift
├── Core/
│   ├── Models/              # Shared domain models
│   ├── Services/            # Shared services
│   ├── Networking/          # API layer
│   └── Extensions/          # Type extensions
└── Resources/               # Assets, Localizable.strings
```

### Dependency Injection

```swift
// GOOD: Protocol-based injection
protocol UserRepository: Sendable {
    func findById(_ id: UUID) async throws -> User?
    func save(_ user: User) async throws
}

final class UserService {
    private let repository: UserRepository
    private let notificationService: NotificationService

    init(repository: UserRepository, notificationService: NotificationService) {
        self.repository = repository
        self.notificationService = notificationService
    }

    func getUser(id: UUID) async throws -> User {
        guard let user = try await repository.findById(id) else {
            throw UserError.notFound(id)
        }
        return user
    }
}

// BAD: Hard-coded dependencies
final class UserService {
    private let repository = PostgresUserRepository()
}

// BAD: Singleton pattern
final class UserService {
    static let shared = UserService()
}
```

### SwiftUI MVVM Pattern

```swift
// ViewModel with @Observable (Swift 5.9+)
@Observable
final class UserListViewModel {
    private let service: UserService
    private(set) var users: [User] = []
    private(set) var state: LoadingState<[User]> = .idle
    var searchText = ""

    init(service: UserService) {
        self.service = service
    }

    func loadUsers() async {
        state = .loading
        do {
            users = try await service.fetchUsers()
            state = .loaded(users)
        } catch {
            state = .failed(error)
        }
    }

    var filteredUsers: [User] {
        guard !searchText.isEmpty else { return users }
        return users.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
    }
}

// View consuming the ViewModel
struct UserListView: View {
    @State private var viewModel: UserListViewModel

    init(service: UserService) {
        _viewModel = State(initialValue: UserListViewModel(service: service))
    }

    var body: some View {
        List(viewModel.filteredUsers) { user in
            UserRow(user: user)
        }
        .searchable(text: $viewModel.searchText)
        .task {
            await viewModel.loadUsers()
        }
    }
}
```

---

## Concurrency Patterns

### Structured Concurrency

```swift
// GOOD: async/await
func fetchDashboard(userId: UUID) async throws -> Dashboard {
    async let user = userService.getUser(id: userId)
    async let orders = orderService.getOrders(userId: userId)
    async let notifications = notificationService.getUnread(userId: userId)

    return try await Dashboard(
        user: user,
        orders: orders,
        notifications: notifications
    )
}

// GOOD: TaskGroup for dynamic concurrency
func fetchAllUsers(ids: [UUID]) async throws -> [User] {
    try await withThrowingTaskGroup(of: User.self) { group in
        for id in ids {
            group.addTask { try await self.userService.getUser(id: id) }
        }
        return try await group.reduce(into: []) { $0.append($1) }
    }
}

// BAD: Completion handler for new code
func fetchUser(id: UUID, completion: @escaping (Result<User, Error>) -> Void) {
    // Don't write this — use async/await
}
```

### Actor Isolation

```swift
// GOOD: Actor for shared mutable state
actor CacheStore {
    private var cache: [String: Data] = [:]

    func get(_ key: String) -> Data? {
        cache[key]
    }

    func set(_ key: String, value: Data) {
        cache[key] = value
    }

    func clear() {
        cache.removeAll()
    }
}

// GOOD: @MainActor for UI state
@MainActor
@Observable
final class ProfileViewModel {
    private(set) var user: User?
    private(set) var isLoading = false

    private let service: UserService

    init(service: UserService) {
        self.service = service
    }

    func loadProfile(id: UUID) async {
        isLoading = true
        defer { isLoading = false }
        user = try? await service.getUser(id: id)
    }
}
```

### Sendable Compliance

```swift
// GOOD: Struct is Sendable by default if all stored properties are Sendable
struct UserDTO: Codable, Sendable {
    let id: UUID
    let name: String
    let email: String
}

// GOOD: Explicitly mark final class as Sendable when safe
final class AppConfig: Sendable {
    let apiBaseURL: URL
    let apiKey: String

    init(apiBaseURL: URL, apiKey: String) {
        self.apiBaseURL = apiBaseURL
        self.apiKey = apiKey
    }
}
```

---

## Protocol-Oriented Design

### Protocols Over Inheritance

```swift
// GOOD: Small, focused protocols
// Note: Swift provides built-in Identifiable protocol. Use it directly:
//   struct User: Identifiable { let id: UUID }
// For custom domain protocols, use unique names:
protocol DomainEntity {
    var id: UUID { get }
}

protocol Timestamped {
    var createdAt: Date { get }
    var updatedAt: Date { get }
}

protocol Persistable: DomainEntity, Codable {
    static var tableName: String { get }
}

// Compose through protocol conformance
struct User: Persistable, Timestamped, Identifiable {
    let id: UUID
    var name: String
    let createdAt: Date
    var updatedAt: Date

    static let tableName = "users"
}

// BAD: Deep class hierarchy
class BaseEntity {
    var id: UUID
    // ...
}
class TimestampedEntity: BaseEntity {
    var createdAt: Date
    // ...
}
class User: TimestampedEntity {
    var name: String
    // Too deep — use composition
}
```

### Protocol Extensions for Default Behavior

```swift
protocol APIEndpoint {
    var path: String { get }
    var method: HTTPMethod { get }
    var headers: [String: String] { get }
}

extension APIEndpoint {
    var headers: [String: String] {
        ["Content-Type": "application/json"]
    }
}
```

---

## Error Handling

### Custom Error Hierarchy

```swift
// Domain-specific errors
enum UserError: LocalizedError {
    case notFound(UUID)
    case invalidEmail(String)
    case duplicateUsername(String)

    var errorDescription: String? {
        switch self {
        case .notFound(let id): "User not found: \(id)"
        case .invalidEmail(let email): "Invalid email: \(email)"
        case .duplicateUsername(let name): "Username already taken: \(name)"
        }
    }
}

// Network errors
enum NetworkError: LocalizedError {
    case invalidURL
    case unauthorized
    case serverError(statusCode: Int)
    case decodingFailed(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL: "Invalid URL"
        case .unauthorized: "Unauthorized"
        case .serverError(let code): "Server error: \(code)"
        case .decodingFailed(let error): "Decoding failed: \(error.localizedDescription)"
        }
    }
}
```

### Guard-First Pattern

```swift
// GOOD: Early exit with guard
func processOrder(_ order: Order?) throws -> Receipt {
    guard let order else {
        throw OrderError.missingOrder
    }
    guard !order.items.isEmpty else {
        throw OrderError.emptyOrder
    }
    guard order.total > 0 else {
        throw OrderError.invalidTotal
    }

    // Happy path — no nesting
    return Receipt(order: order, processedAt: .now)
}

// BAD: Pyramid of doom
func processOrder(_ order: Order?) throws -> Receipt {
    if let order = order {
        if !order.items.isEmpty {
            if order.total > 0 {
                return Receipt(order: order, processedAt: .now)
            }
        }
    }
    throw OrderError.invalid
}
```

### Typed Throws (Swift 6)

```swift
// Swift 6: Typed throws for precise error handling
func fetchUser(id: UUID) async throws(NetworkError) -> User {
    let data = try await apiClient.get("/users/\(id)")
    return try JSONDecoder().decode(User.self, from: data)
}
```

---

## Codable Patterns

### CRUD Model Variants

```swift
// Base model (read/response)
struct User: Codable, Identifiable, Sendable {
    let id: UUID
    let name: String
    let email: String
    let createdAt: Date
}

// Create request — no id, no timestamps
struct CreateUserRequest: Codable, Sendable {
    let name: String
    let email: String
}

// Update request — all fields optional
struct UpdateUserRequest: Codable, Sendable {
    var name: String?
    var email: String?
}
```

### CodingKeys for Field Mapping

```swift
struct User: Codable {
    let id: UUID
    let fullName: String
    let emailAddress: String
    let createdAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case fullName = "full_name"
        case emailAddress = "email_address"
        case createdAt = "created_at"
    }
}
```

### Custom Decoding with Defaults

```swift
struct Settings: Codable {
    let theme: String
    let notificationsEnabled: Bool
    let pageSize: Int

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        theme = try container.decodeIfPresent(String.self, forKey: .theme) ?? "light"
        notificationsEnabled = try container.decodeIfPresent(Bool.self, forKey: .notificationsEnabled) ?? true
        pageSize = try container.decodeIfPresent(Int.self, forKey: .pageSize) ?? 20
    }
}
```

### JSON Encoder/Decoder Configuration

```swift
extension JSONDecoder {
    static let api: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()
}

extension JSONEncoder {
    static let api: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .iso8601
        return encoder
    }()
}
```

---

## Networking

### API Client Pattern

```swift
protocol APIClient: Sendable {
    func request<T: Decodable>(_ endpoint: APIEndpoint) async throws -> T
}

final class URLSessionAPIClient: APIClient {
    private let session: URLSession
    private let baseURL: URL
    private let decoder: JSONDecoder

    init(baseURL: URL, session: URLSession = .shared, decoder: JSONDecoder = .api) {
        self.baseURL = baseURL
        self.session = session
        self.decoder = decoder
    }

    func request<T: Decodable>(_ endpoint: APIEndpoint) async throws -> T {
        let url = baseURL.appending(path: endpoint.path)
        var request = URLRequest(url: url)
        request.httpMethod = endpoint.method.rawValue
        for (key, value) in endpoint.headers {
            request.setValue(value, forHTTPHeaderField: key)
        }

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw NetworkError.invalidResponse
        }
        guard (200..<300).contains(httpResponse.statusCode) else {
            throw NetworkError.serverError(statusCode: httpResponse.statusCode)
        }

        return try decoder.decode(T.self, from: data)
    }
}
```

### Endpoint Definition

```swift
enum UserEndpoint: APIEndpoint {
    case list
    case get(UUID)
    case create(CreateUserRequest)
    case update(UUID, UpdateUserRequest)
    case delete(UUID)

    var path: String {
        switch self {
        case .list: "/users"
        case .get(let id), .delete(let id): "/users/\(id)"
        case .create: "/users"
        case .update(let id, _): "/users/\(id)"
        }
    }

    var method: HTTPMethod {
        switch self {
        case .list, .get: .get
        case .create: .post
        case .update: .put
        case .delete: .delete
        }
    }
}
```

---

## Vapor Patterns (Server-Side Swift)

### Route Handlers

```swift
func routes(_ app: Application) throws {
    let userController = UserController(
        service: app.userService
    )

    app.group("api", "v1") { api in
        api.group("users") { users in
            users.get(use: userController.index)
            users.get(":id", use: userController.show)
            users.post(use: userController.create)
            users.put(":id", use: userController.update)
            users.delete(":id", use: userController.delete)
        }
    }
}
```

### Controller Pattern

```swift
struct UserController {
    let service: UserService

    func index(req: Request) async throws -> [UserResponse] {
        let users = try await service.listUsers()
        return users.map(UserResponse.init)
    }

    func show(req: Request) async throws -> UserResponse {
        guard let id = req.parameters.get("id", as: UUID.self) else {
            throw Abort(.badRequest, reason: "Invalid user ID")
        }
        let user = try await service.getUser(id: id)
        return UserResponse(user: user)
    }

    func create(req: Request) async throws -> UserResponse {
        let input = try req.content.decode(CreateUserRequest.self)
        let user = try await service.createUser(input)
        return UserResponse(user: user)
    }
}
```

---

## Testing

### Stack

- `XCTest` for unit and integration tests
- `swift-testing` (Swift 5.9+) for modern test syntax
- `swift-snapshot-testing` for snapshot tests
- `ViewInspector` for SwiftUI view testing

### XCTest Pattern

```swift
final class UserServiceTests: XCTestCase {
    private var sut: UserService!
    private var mockRepository: MockUserRepository!

    override func setUp() {
        super.setUp()
        mockRepository = MockUserRepository()
        sut = UserService(repository: mockRepository)
    }

    override func tearDown() {
        sut = nil
        mockRepository = nil
        super.tearDown()
    }

    func testGetUserReturnsUser() async throws {
        // Arrange
        let expected = User(id: UUID(), name: "Test", email: "test@example.com", createdAt: .now)
        mockRepository.stubbedUser = expected

        // Act
        let result = try await sut.getUser(id: expected.id)

        // Assert
        XCTAssertEqual(result.id, expected.id)
        XCTAssertEqual(result.name, expected.name)
    }

    func testGetUserThrowsNotFoundForMissingUser() async {
        // Arrange
        mockRepository.stubbedUser = nil

        // Act & Assert
        do {
            _ = try await sut.getUser(id: UUID())
            XCTFail("Expected UserError.notFound")
        } catch is UserError {
            // Expected
        } catch {
            XCTFail("Unexpected error: \(error)")
        }
    }
}
```

### Swift Testing Framework (5.9+)

```swift
import Testing

@Suite("UserService Tests")
struct UserServiceTests {
    let mockRepository = MockUserRepository()
    let sut: UserService

    init() {
        sut = UserService(repository: mockRepository)
    }

    @Test("Returns user when found")
    func getUserReturnsUser() async throws {
        let expected = User(id: UUID(), name: "Test", email: "test@example.com", createdAt: .now)
        mockRepository.stubbedUser = expected

        let result = try await sut.getUser(id: expected.id)

        #expect(result.id == expected.id)
        #expect(result.name == expected.name)
    }

    @Test("Throws notFound for missing user")
    func getUserThrowsNotFound() async {
        mockRepository.stubbedUser = nil

        await #expect(throws: UserError.self) {
            try await sut.getUser(id: UUID())
        }
    }
}
```

### Mock Pattern

```swift
final class MockUserRepository: UserRepository, @unchecked Sendable {
    var stubbedUser: User?
    var savedUsers: [User] = []

    func findById(_ id: UUID) async throws -> User? {
        stubbedUser
    }

    func save(_ user: User) async throws {
        savedUsers.append(user)
    }
}
```

### Coverage Target: 70-80%

---

## Swift Package Manager

### Package.swift

```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MyApp",
    platforms: [.macOS(.v14), .iOS(.v17)],
    products: [
        .library(name: "MyApp", targets: ["MyApp"]),
    ],
    dependencies: [
        .package(url: "https://github.com/vapor/vapor.git", from: "4.0.0"),
    ],
    targets: [
        .target(
            name: "MyApp",
            dependencies: [
                .product(name: "Vapor", package: "vapor"),
            ]
        ),
        .testTarget(
            name: "MyAppTests",
            dependencies: ["MyApp"]
        ),
    ]
)
```

### Build Commands

```bash
# Build
swift build

# Test
swift test

# Test with coverage
swift test --enable-code-coverage

# Build for release
swift build -c release

# Resolve dependencies
swift package resolve

# Update dependencies
swift package update
```

---

## Git & Versioning

### Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production |
| `staging` | UAT/pre-prod |
| `dev` | Daily development |
| `feat/<JIRA>-desc` | New features |
| `fix/<JIRA>-desc` | Bug fixes |

### Commit Prefixes

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation
- `chore:` - Maintenance
- `bump:` - Version tags

### Merge Strategy

- Create branch from `main`
- Merge to `dev`/`staging` for testing
- PR + Code Review to merge to `main`
- Use squash commits for clean history

---

## Code Quality

### SwiftLint Configuration

```yaml
# .swiftlint.yml
disabled_rules:
  - trailing_whitespace
opt_in_rules:
  - empty_count
  - closure_spacing
  - force_unwrapping
  - implicit_return
  - modifier_order
included:
  - Sources
  - Tests
excluded:
  - .build
  - Package.swift
line_length:
  warning: 120
  error: 150
function_body_length:
  warning: 50
  error: 70
type_body_length:
  warning: 200
  error: 300
```

---

## Quick Reference

| Need | Do This |
|------|---------|
| Data model | `struct` with Codable |
| Shared mutable state | `actor` |
| Async operation | `async/await` |
| Multiple async | `async let` or `TaskGroup` |
| Finite states | `enum` with associated values |
| Object shape contract | `protocol` |
| Dependency | Pass as init parameter (protocol type) |
| Optional handling | `guard let` / `if let` / `??` |
| Side effect | Isolate, make explicit |
| Long function | Split into smaller functions |
| JSON mapping | Codable + CodingKeys |

## What NOT to Do

| Anti-Pattern | Instead |
|--------------|---------|
| Force unwrap (`!`) in production | `guard let`, `if let`, `??` |
| Deep class inheritance | Protocol composition |
| Completion handlers (new code) | async/await |
| Singleton pattern | Dependency injection |
| Implicitly unwrapped optionals | Proper optionals or non-optional |
| `Any` / `AnyObject` everywhere | Proper types, generics, protocols |
| Massive view controllers | MVVM with focused ViewModels |
| 100+ line functions | Break into focused units |
| Comments for obvious code | Delete them |
| Over-engineering "for the future" | Solve current problem only |
| Raw `DispatchQueue` (new code) | Structured concurrency |
| Mutable global state | Actor or proper DI |
