# Java: Spring MVC / Boot

## Entry points
- `@RestController`/`@Controller` with `@RequestMapping`, `@GetMapping`, `@PostMapping` etc.; functional routes (`RouterFunction`); WebFlux handlers; `@MessageMapping` (WebSocket/STOMP); `@Scheduled`, `@KafkaListener`/`@RabbitListener`/`@JmsListener` (consumers); Actuator endpoints; Spring Data REST auto-exposed repositories (`@RepositoryRestResource`, any `*Repository` when the starter is present).
- Enumerate:
  - `grep -rnE "@(Request|Get|Post|Put|Patch|Delete)Mapping"`
  - `grep -rnE "@(Kafka|Rabbit|Jms|Message)(Listener|Mapping)"`
  - `grep -rn "RepositoryRestResource"`; `grep -rn "management.endpoints"` in properties/yaml.

## Where auth and authorization live
- Spring Security `SecurityFilterChain` bean: `authorizeHttpRequests` rules are evaluated in order and first match wins. A broad `permitAll()` earlier than a specific `hasRole` rule shadows it; the final `anyRequest()` should be `authenticated()` or `denyAll()`.
- Matcher pitfalls: `requestMatchers("/admin/**")` vs MVC path variants (trailing slash, suffix, case) depend on the matcher type and version: identify which matcher kind is used and avoid assuming; multiple `SecurityFilterChain` beans are chosen by `securityMatcher` and `@Order`; a request matching an earlier chain never reaches the later one.
- Method security: `@PreAuthorize("hasRole('X')")`, `@PostAuthorize`, `@Secured`; works only if `@EnableMethodSecurity` (or the legacy `@EnableGlobalMethodSecurity`) is present, and only for calls crossing the Spring proxy: self-invocation (`this.method()`) and `private`/`final` methods bypass it. Annotation on the interface vs implementation: check which one the proxy sees.
- Object-level checks: `@PreAuthorize("@perm.canEdit(#id, principal)")` or domain `hasPermission`; verify the id passed is the one used to load the resource. Authentication-only (`isAuthenticated()`) is not ownership.
- CSRF: enabled by default for session-cookie apps; `csrf().disable()` is fine for stateless bearer-token APIs, a finding for cookie-authenticated ones.
- `@PermitAll`/`web.ignoring()` for static paths removes the whole filter chain (including security headers) for those paths.

## Data access
| Safe | Unsafe |
| --- | --- |
| Spring Data derived queries, `@Query("... :name")` with `@Param`, `PreparedStatement`, `NamedParameterJdbcTemplate`, `Criteria` API | string concatenation into `@Query` (via SpEL `#{}` with user data), `entityManager.createQuery("..."+x)`, `createNativeQuery(str)`, `JdbcTemplate.query(str)`, `Sort` built from user strings unvalidated (`Sort.by(userField)` property names; allowlist) |
| `findByIdAndOwnerId(id, ownerId)` or `@PostAuthorize` on returned entity | `findById(id)` from path then return |
See `classes/sql-nosql.md`, `classes/access-control.md`.

## Rendering and output
- Thymeleaf: `th:text` and `[[ ]]` escape; `th:utext` and `[( )]` do not. Fragment/view names built from user input (`return "user/" + name`, `th:insert="${param}"`) are template injection/path concerns.
- JSP: `${x}` is not escaped by default in plain EL; `<c:out>` escapes.
- Jackson serializes entities fully: `@JsonIgnore`/`@JsonProperty(access=WRITE_ONLY)`/DTO projections; returning JPA entities exposes lazy/relational fields and password hashes.
- Binding: `@ModelAttribute`/`@RequestBody` on an entity binds every property (mass assignment: use DTOs or `@InitBinder` `setAllowedFields`).
- Error output: `server.error.include-stacktrace`, `include-message`, `include-binding-errors`.

## Framework-specific pitfalls
- Actuator endpoints (`env`, `heapdump`, `configprops`, `mappings`) exposed without auth.
- Spring Data REST exposes CRUD for repositories by default: check `@RestResource(exported=false)` and security on repository methods.
- `RestTemplate`/`WebClient` with user URLs: SSRF (see `classes/ssrf.md`).
- XML: `DocumentBuilderFactory` defaults are unsafe (see `classes/deserialization.md`); Jackson default typing; `ObjectInputStream` on message payloads.
- `@CrossOrigin` with `origins="*"` plus `allowCredentials`; global `CorsConfigurationSource` using `allowedOriginPatterns("*")` with credentials.
- Redirects: `"redirect:" + param` and `response.sendRedirect(param)`.
- `@Async`/`@Scheduled`/listener threads lose `SecurityContext` unless a delegating executor is configured: a job may run with no identity or with a stale one.
- `PasswordEncoder` choice: `NoOpPasswordEncoder` or unsalted `MessageDigestPasswordEncoder` for credentials.
