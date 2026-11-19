# Access control (CWE-639, CWE-862, CWE-863, CWE-915)

## Sources
- Identifiers the client chooses: path/query ids, body fields (`userId`, `orgId`, `ownerId`, `role`, `isAdmin`), GraphQL arguments/node ids, batch endpoints, file/export ids, signed-URL parameters.
- Mass-assignment input: whole `req.body`, `params`, `request.POST`, JSON merged into a model.
- Identity propagated to jobs, webhooks, caches, websockets and background tasks, where the original actor may be lost.
- Anything the UI hides or disables (buttons, tabs, form fields): the API still accepts it.

## Sinks
The sink is the read or write of the resource, not a "dangerous API".
| Pattern | Looks like | Safe shape |
| --- | --- | --- |
| Lookup by id only | `Model.findById(id)`, `Order.objects.get(pk=id)`, `Order.find(params[:id])`, `repo.findById(id)` | scope by owner/tenant in the query: `findOne({id, tenantId: user.tenantId})`, `request.user.orders.get(pk=id)`, `current_user.orders.find`, `findByIdAndOwner` |
| Write without ownership | `update(id, body)`, `.save()` on a loaded object that was not scoped | load scoped, then authorize the action (policy), then write an explicit field list |
| Mass assignment | `Model.create(req.body)`, `Object.assign(user, body)`, `User.objects.filter(pk=..).update(**request.data)`, `new User(params)`, `@ModelAttribute` binding entities, `.update(params)` | explicit allowlist of fields (zod/DTO/serializer `fields`, Rails `permit`, Laravel `$fillable`) |
| Admin action | route reachable by any authenticated user | role/permission check in middleware or policy on THIS route |
| Child resource | `/orgs/:orgId/projects/:id` checks `orgId` membership but loads project by `id` alone | load project by `(id, orgId)` |
| Bulk/list/export/search/GraphQL | list filtered but count, export, search index, or nested field is not | same scoping in every access path |

## Guards that work / Look-alike guards
Work:
- Server-derived identity (`req.user` from verified session/token), never an id taken from the body for authorization.
- Tenant/owner predicate inside the query itself, or database row-level security with the tenant set per request.
- Central policy (Pundit, CanCan, Spring `@PreAuthorize`, Laravel Policy, django-guardian/DRF permission classes) that is demonstrably attached to the route and receives the loaded object.
- Explicit field allowlists for writes; separate privileged fields (role, tenant, balance) from user-editable ones.
- For shared resources: the policy models collaborators (viewer/editor) and the check uses the specific permission needed, not just "is a member".
- Authorization re-checked at job execution time when the job outlives the request.

Look-alike:
- Authentication-only checks (`requireLogin`, `@login_required`, `authenticated()`) offered as authorization.
- UI hiding, disabled buttons, client-side role checks, route guards in the SPA router.
- A check on a different handler (GET protected, PUT or DELETE not), different HTTP method, a legacy `/v1` or admin-prefixed duplicate route.
- Ownership checked after the write or on the id from the body while the update uses the path id (or vice versa).
- Unguessable ids (UUIDs) as the only protection; they leak in lists, emails, logs.
- Checks keyed by role string comparison against a client-supplied claim not verified server-side.
- Deny-list of fields on mass assignment (`delete body.isAdmin`) instead of allowlist; nested objects/aliases (`is_admin`, `role_id`) bypass it.
- Middleware registered after the route, or matcher that omits the path (see frameworks files).

## Falsify before reporting
1. Define actors: owner, collaborator with limited permission, other tenant, anonymous, admin. Which one does the contract exclude, and can THAT actor reach the handler through routing?
2. Find the guard on this exact route/method (middleware order, decorators, policy call, method security). Does it receive the same object/id that is read or written?
3. Is the resource scoped in the query or by RLS/default scope so a foreign id yields "not found"? Check default scopes and tenancy plugins before reporting.
4. Mass assignment: does the model/serializer actually bind the sensitive field (`fillable`, `permit`, DTO class, `readOnly`)? Prove the field exists on the persisted model.
5. For a write: does the denied actor produce a side effect, or only a 403 after the write (transaction rolled back or not)?
6. Confirm: two fixtures (authorized and excluded actor) call the route; the excluded one gets 403/404 and the database row is unchanged.

## Severity cues
- Raises: cross-tenant read or write, privilege escalation (role, admin), money/PII/secrets at stake, enumerable ids, unauthenticated reach.
- Lowers: same-tenant lateral access among equally trusted users, read of non-sensitive data, admin-only reach, access requires an unguessable id obtained out of band (still report, medium or lower).
- Missing authorization on a mutating endpoint outranks the same gap on a read.

## Regression test
- Fails before: user B (other tenant) requests user A's resource by id; before the fix returns 200 with data; after, 404 (or 403 per contract).
- Write case: B sends PATCH/DELETE to A's id; assert non-success AND the stored row is unchanged.
- Mass assignment: a normal user PATCHes `{"name": "x", "role": "admin"}`; assert `name` updates and `role` does not.
- Collaborator: a viewer can read but not edit; an editor can edit; owner-only actions (delete, share) denied for editor.
- Allowed case: owner and legitimate collaborator keep their access; list endpoints return only own-tenant rows.
