# Go: net/http, chi, gin, echo

## Entry points
- `net/http`: `http.HandleFunc`, `mux.Handle`, `http.NewServeMux` (Go 1.22+ patterns can include method and wildcards), `http.Handler` implementations.
- chi: `r.Get/Post/...`, `r.Route("/x", func(r chi.Router){...})`, `r.Mount`, `r.Group`. gin: `r.GET`, `r.Group("/api")`, `group.Use(mw)`. echo: `e.GET`, `e.Group`, `g.Use`.
- Others: gRPC services (`RegisterXServer`) with interceptors, queue consumers, cron goroutines, `net/http/pprof` or `expvar` imported for side effects.
- Enumerate:
  - `grep -rnE "\.(GET|POST|PUT|PATCH|DELETE|Get|Post|Put|Patch|Delete|Handle|HandleFunc|Mount|Group|Route)\("`
  - `grep -rn "net/http/pprof\|expvar"`; `grep -rn "RegisterService\|Register.*Server("`

## Where auth and authorization live
- Middleware wraps handlers: `r.Use(auth)` in chi/gin/echo applies only to routes registered AFTER `Use` on that router/group (chi panics if `Use` follows routes; in gin, `Use` affects only routes registered after it). Check that the route sits inside the guarded group and not on the root router.
- A middleware that fails must `return` after writing the error; in `net/http` a missing `return` still calls the next handler. gin: `c.Abort()` (or `AbortWithStatus`) is required, `c.JSON(401, ...)` alone continues the chain.
- `Mount`ed sub-routers and `http.Handle("/static/", ...)` may not inherit middleware.
- Identity should come from the request context set by the verified middleware (`r.Context().Value(...)`), not from headers like `X-User-ID` that a client or other path can set. Look for trusting proxy headers without stripping them at the edge.
- JWT libs: `ParseWithClaims` must check `token.Method` in the keyfunc (alg confusion), and `token.Valid`; `ParseUnverified` is not authentication.
- gRPC: unary and stream interceptors are separate chains; a stream method skipped by a unary-only auth interceptor is unprotected.
- Authorization on the object: handler loads by id from the URL; verify the query includes the caller's tenant/user id.

## Data access
| Safe | Unsafe |
| --- | --- |
| `db.QueryContext(ctx, "... WHERE id = $1", id)`, `sqlx.NamedQuery`, GORM `Where("a = ?", x)`, `Where(&Model{A: x})` (zero-value fields ignored: not a filter bug but a scoping bug), sqlc generated queries | `fmt.Sprintf` / `+` into `db.Query`, GORM `Where(fmt.Sprintf(...))`, `Order(userInput)`, `Raw`/`Exec` with concatenation, `Select(userInput)`; GORM struct-condition zero values dropping a tenant filter |
| `json.Decoder` into a dedicated request struct, `DisallowUnknownFields` | decoding straight into the DB model that has privileged fields (mass assignment) |
Placeholders differ by driver (`$1`, `?`); identifiers cannot be bound: allowlist.
See `classes/sql-nosql.md`, `classes/access-control.md`.

## Rendering and output
- `html/template` autoescapes by context; hatches: `template.HTML`, `template.JS`, `template.JSStr`, `template.URL`, `template.HTMLAttr` conversions of user data. `text/template` does NO escaping: using it for HTML is XSS; check the import (`text/template` vs `html/template`).
- `w.Write([]byte(userString))` with default sniffed Content-Type may render as HTML: set `Content-Type` and `X-Content-Type-Options: nosniff`.
- `json.Marshal` of structs exposes all exported fields without `json:"-"`; use response structs.
- `http.ServeFile(w, r, userPath)` and `http.Dir(".")` file servers: traversal and directory listing; `http.FileServer(http.Dir(...))` cleans `..` but follows symlinks and serves dotfiles.

## Framework-specific pitfalls
- Default `http.Client` has no timeout and follows redirects; `http.Get(userURL)` is SSRF (see `classes/ssrf.md`); validate at dialer level via `net.Dialer.Control`.
- `tls.Config{InsecureSkipVerify: true}`.
- `math/rand` for tokens (use `crypto/rand`); `==` on secrets (use `subtle.ConstantTimeCompare`).
- `exec.Command("sh", "-c", ...)` with user input; `filepath.Join(base, userPath)` without a prefix check; `archive/zip` entry names (zip slip).
- Loop variable capture in goroutines using request data, shared mutable state across requests (data races between users): `go test -race` evidence.
- `r.FormValue`/`r.Form` merges query and body; `r.PostFormValue` is body only: a guard on one and use of the other.
- `http.MaxBytesReader` missing on body reads (availability).
- CORS middleware `AllowedOrigins: []string{"*"}` with `AllowCredentials: true` (libraries differ in whether they reflect origin: read its docs/source for the pinned version).
