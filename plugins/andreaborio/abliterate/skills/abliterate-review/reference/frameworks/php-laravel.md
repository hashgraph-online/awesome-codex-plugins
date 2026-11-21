# PHP: Laravel

## Entry points
- `routes/web.php` (session, CSRF), `routes/api.php` (prefix `/api`, `api` middleware group, no CSRF), `routes/channels.php` (broadcast auth), `routes/console.php`; `Route::resource`, `apiResource`, `Route::match`, `Route::any`, `Route::fallback`, route groups with `middleware([...])`, `prefix`, `controller`.
- Others: queued jobs (`ShouldQueue::handle`), event listeners, scheduled commands, Livewire components (public properties and methods are client-callable), Filament/Nova resources, Artisan commands, webhook controllers (often excluded from CSRF).
- Enumerate:
  - `grep -rnE "Route::(get|post|put|patch|delete|any|match|resource|apiResource|group)" routes`
  - `grep -rn "withoutMiddleware\|\$except" app bootstrap`
  - `grep -rn "extends Component" app/Livewire app/Http/Livewire`

## Where auth and authorization live
- Middleware: `auth`, `auth:sanctum`, `verified`, `can:update,post`, `throttle`. Check that the route or an enclosing `Route::middleware(...)->group` includes it; routes declared outside the group, or `->withoutMiddleware(...)`, are unprotected. `Route::resource` with `->only/except` lists define which methods exist: verify the controller's other public methods have no route.
- Controller constructor `$this->middleware('auth')->only(...)`/`except(...)`: same only/except trap.
- Policies/Gates: `$this->authorize('update', $post)`, `Gate::allows`, `$request->user()->can(...)`, `can:` middleware. `authorizeResource` in the constructor covers the standard resource methods only. A policy method returning `true` for any authenticated user is authentication, not ownership. Gate `before` callbacks that return `true` for admins short-circuit all checks: read them.
- Route model binding: `Route::get('/posts/{post}')` loads by id with NO ownership check; scoped bindings (`->scopeBindings()`, nested `{user}/posts/{post}`) scope children only when configured. Authorize the bound model.
- Validation (`FormRequest::rules`) is not authorization; `authorize()` in a FormRequest returning `true` is a no-op guard.
- Sanctum/Passport: token abilities (`tokenCan`) must be checked; session SPA auth needs CSRF cookie flow.
- CSRF: `VerifyCsrfToken::$except` (or `validateCsrfTokens(except:)`) lists; wide wildcards exempt state-changing routes.

## Data access
| Safe | Unsafe |
| --- | --- |
| Eloquent/query builder with values (`where('a', $x)`), `whereRaw('a = ?', [$x])`, `DB::select('... ?', [$x])`, `orderBy` with allowlisted column | `DB::raw("..$x")`, `whereRaw("a = $x")`, `selectRaw`/`orderByRaw`/`groupByRaw`/`havingRaw` with interpolation, `DB::statement("..$x")`, `orderBy($request->sort)` (column name from input), `where($request->all())`-style column control, `DB::unprepared` |
| `$fillable` allowlist; `$request->validated()`; `$request->only([...])` | `$guarded = []`, `Model::create($request->all())`, `$model->update($request->all())`, `forceFill`/`unguard()` with request data |
| scoped query `$request->user()->posts()->findOrFail($id)` | `Post::findOrFail($id)` followed by no policy |
See `classes/sql-nosql.md`, `classes/access-control.md`.

## Rendering and output
- Blade `{{ $x }}` escapes (`htmlspecialchars`); `{!! $x !!}` and `@php echo` do not. `@json($x)` is escaped for script context only with its flags; `Blade::render($userString)` is template injection. `Str::markdown` and `Markdown::parse` allow raw HTML unless configured (`html_input` => `strip`/`escape`).
- API output: returning a model (`return $user;`) serializes every attribute not in `$hidden`; use `JsonResource`/API resources. Check `$hidden` for password, tokens, 2FA secrets.
- `response()->download($userPath)`, `Storage::download`, `file_get_contents($path)`: path traversal; `Storage::disk('public')` files are web-reachable.

## Framework-specific pitfalls
- `APP_DEBUG=true` in a deployed env exposes stack traces, env values; `.env` served if web root is wrong.
- `unserialize`/`phar://` on user data; cookie/session encryption with a leaked `APP_KEY` leads to forged sessions and, with legacy serialization settings, code execution: treat a committed `APP_KEY` as a secret leak.
- Mass assignment through nested relations and `fill` on models with `$guarded = []` plus `is_admin`-style columns.
- `redirect($request->input('next'))`, `redirect()->intended()` is safe-ish; check `url()->previous()` use.
- `Http::get($userUrl)` / Guzzle on user URLs: SSRF (see `classes/ssrf.md`).
- `Hash::make` default bcrypt/argon is fine; `md5`/`sha1` custom hashing is not. `rand()`/`mt_rand`/`uniqid` for tokens (use `Str::random`, `random_bytes`).
- Livewire: authorize inside each public action method; public properties can be set by the client unless `#[Locked]` (or equivalent for the pinned version, verify).
- Cache keys without tenant/user in `Cache::remember`; queued jobs serialize models by id and re-fetch: authorize in `handle`.
