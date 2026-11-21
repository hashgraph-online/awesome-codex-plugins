# Ruby on Rails

## Entry points
- `config/routes.rb`: `resources`, `get/post ... to:`, `namespace`, `scope`, `mount` (Sidekiq web, engines), `match via: :all`, wildcard `*path`. Controllers inherit from `ApplicationController`; API-only from `ActionController::API`.
- Jobs: `ActiveJob`/Sidekiq `perform` (arguments stored; re-authorize), mailers, `ActionCable` channels (`subscribed`, `receive`), webhooks controllers.
- Enumerate:
  - read `config/routes.rb` then `grep -rn "skip_before_action\|skip_forgery_protection" app`
  - `grep -rn "def " app/controllers` limited to public actions; any public method is routable if a route points at it (and `match :all` or `resources` routes)
  - `grep -rn "protect_from_forgery"`.

## Where auth and authorization live
- `before_action :authenticate_user!` (Devise) / custom `require_login` in `ApplicationController` or a concern. Check `skip_before_action`, and `only:`/`except:` lists: `only: [:index]` leaves `update` open; `except:` lists that omit a new action leave it covered by default but a new action added to an `only:` list is not.
- Order: callbacks run in declaration order; a `before_action` that loads the record (`set_post`) before `authorize` is fine, but `set_post` using `Post.find(params[:id])` rather than `current_user.posts.find` is an IDOR unless a policy runs.
- Pundit: `authorize @record` per action; `after_action :verify_authorized` and `verify_policy_scoped` make omissions fail loudly (check they are not skipped for the action). `policy_scope(Model)` for lists. A policy `update?` that defaults to `false` is safe; `ApplicationPolicy` defaults vary.
- CanCanCan: `load_and_authorize_resource` in the controller; `authorize_resource` without load; `accessible_by(current_ability)` for scoping; abilities defined with `can :manage, :all` for roles.
- CSRF: `protect_from_forgery with: :exception` on cookie-session controllers; `null_session` or `skip_forgery_protection` on API endpoints that still use cookies is a finding.

## Data access
| Safe | Unsafe |
| --- | --- |
| `where(a: x)`, `where("a = ?", x)`, `where("a = :a", a: x)`, `find_by(id: x)`, `sanitize_sql_array`, scoped `current_user.records.find(id)` | `where("a = '#{x}'")`, `order(params[:sort])`, `pluck(params[:col])`, `find_by_sql("...#{x}")`, `update_all("...#{x}")`, `group/having/joins/select` with strings, `connection.execute` with interpolation, `reorder(params[:s])` |
| `params.require(:user).permit(:name, :email)` | `params.permit!`, `Model.new(params[:user])`, `update(params.to_unsafe_h)`, `permit` including `:role`/`:admin`/`:account_id`, nested `permit(attrs: {})` |
| `has_secure_password` (bcrypt) | MD5/SHA digests for passwords |
Note: hash conditions with user-controlled keys (`where(params[:filter])`) let a caller choose columns; permit specific keys.
See `classes/sql-nosql.md`, `classes/access-control.md`.

## Rendering and output
- ERB `<%= %>` escapes; hatches: `raw`, `.html_safe`, `<%== %>`, `safe_join` misuse, `content_tag` with a `html_safe` string, `render inline:` with user data, `link_to name, user_url` (`javascript:` scheme in the URL), `sanitize` with permissive `tags`/`attributes`. Markdown renderers need HTML disabled or sanitized.
- `render json: @user` / `to_json` includes every attribute; use `as_json(only:)`, serializers (ActiveModel::Serializers, Jbuilder), and check `filter_parameters` for logging of secrets.
- `render params[:template]`, `render file: params[:f]`, `send_file params[:path]`: path traversal/template injection.

## Framework-specific pitfalls
- `redirect_to params[:url]` unless the target is validated (same-host check, allowlist, or `only_path`). Check the pinned version's default before downgrading.
- `constantize`, `send`, `public_send`, `instance_variable_get` on request input.
- `YAML.load` / `Marshal.load` on untrusted data; `secret_key_base` committed (signs cookies/Marshal-era sessions).
- Open-URI / `Net::HTTP` on user URLs (SSRF); `ActiveStorage` direct upload content types served inline.
- `config.force_ssl`, `consider_all_requests_local`, Sidekiq/ActiveAdmin/rails_admin mounted without authentication constraint (`authenticate :user, ->(u){u.admin?}`).
- `before_action` conditions with `if:` lambdas evaluated per request: read them for logic holes.
- Callbacks/`default_scope` that apply tenant scoping are bypassed by `unscoped`, `find_by_sql`, and raw SQL.
