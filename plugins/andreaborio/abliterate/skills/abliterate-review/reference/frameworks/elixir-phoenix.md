# Elixir: Phoenix

## Entry points
- Phoenix: `scope` and `pipe_through` define router pipelines; `get`, `post`, `put`, `patch`, `delete`, and `live` register HTTP and LiveView routes.
- Plugs: `plug` declarations in routers, controllers, and endpoint modules run in declaration order. A custom `Plug` module implements `init/1` and `call/2`.
- LiveView: `live_session` and `live` expose mount and event handlers; `handle_event/3` receives client-supplied event parameters.
- Jobs and webhooks: Oban workers, `handle_info/2`, and controller actions that consume webhook bodies. Verify signatures before decoding or dispatching work.

## Where auth and authorization live
- Router pipelines are opt-in. A `scope` that omits `pipe_through :authenticated` is public even when a sibling scope is protected. Check every route and nested scope.
- Pipeline order matters. A plug that assigns `current_user` does not authorize an object or role. The controller, LiveView `mount/3`, or context function must enforce ownership and capability checks.
- A plug must halt after writing an error response. `Plug.Conn.halt/1` (or returning the halted connection) is required; assigning a 401 status and continuing still reaches the endpoint.
- `live_session` hooks run for LiveView navigation, but event handlers remain public client input. Re-check authorization in `handle_event/3` before changing a record.
- Never treat `conn.params`, LiveView params, or a user-provided `user_id` as identity. Use the verified assign set by the authentication plug and scope database queries to that identity.

## Data access
| Safe | Unsafe |
| --- | --- |
| Ecto `where: [id: ^id]`, `Repo.get_by(Item, id: ^id)`, changesets with an allowlist | `fragment("... #{value} ...")`, `Ecto.Adapters.SQL.query` with interpolated SQL |
| `Ecto.Multi` and changesets that cast only permitted fields | `cast/4` with a broad field list that includes role, owner or balance fields |
| Queries scoped by `current_user` or tenant before loading an object | `Repo.get(Item, params["id"])` or `Repo.get!(Item, id)` followed by no ownership check (an authorization gap, not injection: the id is cast and bound) |

`^` binds a value in an Ecto query; it is not string interpolation. Review `fragment/1` and raw SQL separately because they can bypass query parameterization.

## Rendering and output
- HEEx escapes interpolated values by default. `raw/1`, `Phoenix.HTML.raw/1`, and `{:safe, iodata}` bypass escaping and require trusted, sanitized content.
- Do not place user-controlled values in an HTML attribute without the normal HEEx attribute escaping. Validate redirect destinations before passing them to `redirect/2` or `Phoenix.Controller.redirect/2`.
- JSON views and API serializers should explicitly select fields. Returning an Ecto schema directly can expose internal columns or associations added later.
- LiveView assigns are rendered to the client. Keep tokens, secrets, internal authorization data, and unneeded fields out of assigns used by templates.

## Framework-specific pitfalls
- `pipe_through` applies to the routes in that scope; adding a protected pipeline to one scope does not protect routes declared in another scope.
- Plug ordering is security-sensitive: a body parser, session loader, CSRF plug, and authentication plug must run before the endpoint code that relies on them.
- `live_session` `on_mount` hooks are not a replacement for checks in event handlers that mutate state. A user can send an event with arbitrary parameters after the LiveView mounts.
- Ecto `fragment` accepts SQL fragments, not an automatic safety boundary. Keep SQL structure static and bind values with `^`; do not interpolate identifiers or expressions from request data.
- Phoenix's `raw/1` and `Phoenix.HTML.raw/1` are output escape hatches. Treat any value reaching them as a potential XSS path.
- Do not trust `x-forwarded-for`, `x-forwarded-proto`, or similar headers unless the deployment proxy is configured to overwrite them before Phoenix uses them.

## Official references
- [Phoenix router](https://hexdocs.pm/phoenix/routing.html)
- [Phoenix plugs](https://hexdocs.pm/plug/readme.html)
- [Phoenix LiveView security considerations](https://hexdocs.pm/phoenix_live_view/security-model.html)
- [Ecto query API](https://hexdocs.pm/ecto/Ecto.Query.html)
- [Phoenix.HTML raw output](https://hexdocs.pm/phoenix_html/Phoenix.HTML.html#raw/1)
