# Supabase: Postgres RLS, PostgREST, Auth, Storage

In a Supabase app the database is the trust boundary. The application server is one client among several: anyone holding the public (`anon`) key and a session can call PostgREST, Storage and RPCs directly. Review the policies and grants as the guard; treat server-side validation as a convenience unless the write path is service-role only.

## Entry points
- PostgREST: every table and view in an exposed schema (default `public`) is `GET/POST/PATCH/DELETE /rest/v1/<table>` for `anon` and `authenticated`. Every function in that schema is `POST /rest/v1/rpc/<fn>`.
- Storage: `/storage/v1/object/<bucket>/...`; Auth: sign-up, OTP, email change, OAuth callbacks; Edge Functions; Realtime channels.
- The app's own routes and Server Actions come second: they add checks only for callers who choose to go through them.
- The repository is not the deployed state. Dashboard changes, default privileges and Auth settings are invisible in migrations: ask for the live values and record them as `needs-evidence` with the query that decides it.
- Enumerate:
  - `grep -rnE "CREATE (TABLE|VIEW|POLICY|FUNCTION|OR REPLACE FUNCTION)|ENABLE ROW LEVEL|GRANT|REVOKE|SECURITY DEFINER" supabase/migrations`
  - `grep -rnE "service_role|SERVICE_ROLE|createClient\(" --include=*.{ts,js,py}`
  - `grep -rnE "\.rpc\(|\.storage\.from\(|auth\.(signUp|signInWithOtp|updateUser|admin)\."`
  - live: `select * from pg_policies`, `select id, public from storage.buckets`, `has_function_privilege('anon', oid, 'EXECUTE')`, `has_table_privilege('authenticated', oid, 'TRUNCATE')`

## Where auth and authorization live
- A table without `ENABLE ROW LEVEL SECURITY` is fully readable and writable through PostgREST. RLS enabled with no policy denies everyone except `service_role`: fine for server-only tables, a bug if the app expects access.
- Compute the **effective** policy per table and command by replaying migrations in order (`DROP POLICY`, `CREATE POLICY`, `ALTER POLICY`). Permissive policies for the same command are OR-ed: one loose policy defeats the strict ones. Only `AS RESTRICTIVE` policies are AND-ed on top.
- `USING` filters the rows a statement can see or touch; `WITH CHECK` validates the row after the write. An `UPDATE` (or `ALL`) policy with no `WITH CHECK` reuses `USING` for the new row, so it is not by itself a bug. The bug is a `WITH CHECK` looser than `USING` (`WITH CHECK (true)`, or one that omits the tenant/owner predicate): the row can be moved out of the caller's scope (change `tenant_id`, `owner_id`).
- **Policies guard rows, not columns.** `WITH CHECK (tenant_id = ... AND owner = ...)` leaves every other column to the caller: sequence numbers, status, assignee, price, role, `created_by`, `revoked_at`, a storage path. Look for column-level `GRANT`s or a `BEFORE INSERT/UPDATE` trigger; if there is neither, list which columns the caller should not control.
- Tenant check without a role check: when external users (customers, portal accounts) and staff share a tenant, `tenant_id = current_tenant()` alone gives the customer the staff's rows. Each policy needs the actor's role as well.
- Identity source: `auth.uid()` and `auth.jwt()` claims set by the issuer are trustworthy; `user_metadata` is user-editable, `app_metadata` is not. A policy keyed on the `email` claim is only as strong as the Auth settings that decide who can hold a token with that email (see pitfalls). With a third-party issuer, check which claim is the join key and whether `auth.uid()` still matches local rows.
- Helper functions used in policies (`is_member()`, `current_tenant()`) are usually `SECURITY DEFINER` to avoid policy recursion. Then they need a fixed `search_path`, must derive the user from `auth.uid()` rather than take the tenant or user id as an argument, and are themselves callable as `/rpc/<fn>` if they live in an exposed schema.
- Table privileges sit under RLS and are broader than the policies suggest: Supabase's default privileges grant `ALL` on new `public` tables to `anon` and `authenticated` (check the project's live grants). `TRUNCATE`, `REFERENCES` and `TRIGGER` are not governed by RLS. PostgREST cannot issue `TRUNCATE`, so a stray `TRUNCATE` grant matters only through another path that runs SQL as that role (dynamic SQL in a function, a direct database connection): report it as hardening unless such a path exists.

## Data access
| Safe | Unsafe |
| --- | --- |
| Client bound to the user's JWT; RLS decides | `service_role` client with a query that is not filtered by the caller's tenant |
| Service-role side effect **after** an RLS-bound query proved the caller can see the resource | Upload, external API call, email or LLM call before any RLS-bound query (the caller's identity was only read from a decoded cookie) |
| `.eq('email', email.toLowerCase())` against a column stored lower-cased | `.ilike('email', email)`: `_` and `%` in the caller's own value are wildcards |
| Row written by the server with server-chosen values | Row inserted under RLS by the user, later consumed by a service-role job (path to delete or sign, id to sync, role to propagate): confused deputy |
| `SECURITY INVOKER` function, or `DEFINER` that checks `auth.uid()`/role inside and has `SET search_path` | `SECURITY DEFINER` function executable by `PUBLIC` (the default: `REVOKE ... FROM anon` alone does not remove it), or taking `p_tenant_id` from the caller |
| View created `WITH (security_invoker = on)` | Plain view: runs with the owner's rights and bypasses the base table's RLS |
See `classes/access-control.md`, `classes/sql-nosql.md`.

## Rendering and output
- `select('*')` through PostgREST returns every column the policy exposes, including internal notes, tokens and hashes. RLS has no column filter: use column grants or a view.
- Storage serves the content type chosen at upload. A file accepted by an extension or exact-MIME check can still be stored as `image/svg+xml;charset=utf-8` or `text/html`: normalise the MIME (strip parameters) before checking and upload with the server-chosen type. Signed URLs are bearer links: check who can obtain one.
- Public buckets ignore object policies for reads. A private bucket with no `storage.objects` policy is service-role only.
- Error messages from PostgREST and `RAISE` reach the client; avoid returning raw database errors from route handlers.

## Framework-specific pitfalls
- Auth settings are part of the threat model: open sign-up, auto-confirm, email-change confirmation, enabled providers, redirect allow-list (a leftover `localhost` entry), OTP expiry and rate limits. If identity in policies is the email claim, ask: who can obtain a token carrying an address they do not own?
- A hosted-domain or invite check done in the OAuth callback (sign out after the session exists) is not a gate: the token was already issued. Put it in the access-token hook or in policies.
- Session helpers that do not verify the JWT on the server: `auth.getSession()` and `JSON.parse(atob(...))` only decode the cookie; `auth.getClaims()` and `auth.getUser()` verify it. Harmless only where the next step is an RLS-bound query with that token; see the unsafe rows above.
- Audit tables: `INSERT` open to `authenticated` with the actor stored as a client-supplied field is forgeable; `UPDATE`/`DELETE`/`TRUNCATE` must be blocked by trigger, since `service_role` bypasses RLS. Prefer triggers that stamp the actor from `auth.jwt()`.
- Role or membership tables that the client can write (even admin-only) and that a background job then replicates elsewhere: the job inherits whatever the policy allowed, without the app's guards.
- Tokens and API keys stored in tables: store a hash, and make `revoked_at` write-once (row policy alone lets the owner un-revoke).
- `pg_cron` jobs, `pg_net` calls and database webhooks run as the role that created them (usually `postgres`, which bypasses RLS): check what they call and with which secret.
- Migrations that are not idempotent or that differ from the live schema: a policy fixed in the repo may never have been applied. Ask for `pg_policies` output when the finding depends on it.
- Tests: RLS is testable in plain SQL. `set_config('request.jwt.claims', '{...}', true)` plus `SET LOCAL ROLE authenticated` reproduces a PostgREST request; a finding about a policy should come with that test.
