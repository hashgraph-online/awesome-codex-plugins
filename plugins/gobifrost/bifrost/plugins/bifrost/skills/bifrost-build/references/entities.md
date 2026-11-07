# Platform Entities

Use this reference for organization/access decisions and the non-obvious relationships among forms, agents, configs, integrations, events, roles, claims, and policies. Use `../generated/cli-reference.md` for exact commands and flags.

## Ownership first

- **Solution-owned entity:** edit local `.bifrost/*.yaml` content and deploy. Do not mutate the managed live record.
- **Loose entity:** discover and mutate the live record with its dedicated CLI commands.

Outside a Solution, `.bifrost/*.yaml` is not live discovery. Use `list --json` and `get --json`. Response envelopes vary by entity; inspect the returned JSON instead of assuming every `list` is a bare array.

## Organization and access

Before creation, choose the tuple `(organization, access_level, role_ids)` and apply compatible access across the whole dependency chain.

For most supported write commands:

- omit org targeting for the caller's home org;
- use `--org <uuid-or-name>` for a specific org;
- use `--global` for global scope where permitted.

Read commands usually return the caller's combined visible scopes and do not accept org targeting. Older groups may use `--organization` only. Check generated help rather than generalizing an alias.

An app or form user must be able to access every invoked workflow/agent/resource. A role-restricted caller can use a dependency that is global and visible, org-authenticated in the same org, or assigned a compatible role. Verify with a representative non-admin account; platform-admin success does not prove the access model.

## Forms

A form collects fields and launches a registered workflow. Design the workflow signature and form schema together: field `name` maps to a workflow parameter, while `label` is user-facing.

`form_schema` has the shape `{fields: [...]}`. Select-like options are objects, not strings:

```yaml
fields:
  - name: priority
    label: Priority
    type: select
    required: true
    options:
      - { value: low, label: Low }
      - { value: high, label: High }
```

Use `@path/to/schema.yaml` for a local schema file when working with a loose form. Workflow refs may be UUID, unique name, or `path::function`; prefer the portable locator in Solution source.

Test required fields, validation, option values, file fields, the launch result, permission denial, and confirmation behavior.

## Agents

An agent combines a system prompt, tools, delegated agents, knowledge sources, model settings, and access controls.

- Tool IDs must reference registered `@tool` functions, not plain `@workflow` functions.
- Agent updates replace list fields such as tools, delegations, knowledge sources, and roles. Read the current record and send the complete intended lists.
- Use `@prompt.md` for a multiline loose-agent prompt.
- Keep tool names/descriptions distinctive enough for deferred discovery; see `workflows.md`.
- Server-side tool permissions still apply after the agent can see a tool.

Evaluate the agent with representative prompts, tool failures, permission boundaries, and an answer that requires no tool. Do not judge it only from successful tool registration.

## Configs and secrets

Configs are shared environment values with global/org resolution. A Solution packages config declarations and requirements, not portable secrets.

For loose configs, prefer `bifrost configs set <key>` as the upsert path. Secret deletion requires explicit confirmation. Never print decrypted secrets into logs, app source, tests, or handoff notes.

Solution workflow calls to `config.set()`/`delete()` mutate shared instance state rather than private install state. Treat those calls as production-sensitive. Browser apps have no direct secret/config surface; access secrets through a workflow.

## Integrations and OAuth

An Integration defines a service and config schema; mappings bind it to organizations and OAuth/config state.

- Removing config-schema keys can cascade-delete stored Config values; use forced removal only after impact review.
- Updating a mapping should preserve its OAuth token unless intentionally replacing it.
- Resolve and call integrations from Python workflows so decrypted values and tokens stay server-side.
- Solution packages carry requirements/declarations, not environment tokens or tenant mappings.

Test missing mapping, expired/absent OAuth, API failure, pagination/rate limiting, and the intended organization cascade.

## Roles, claims, and policies

Roles are permission buckets assigned to users and entities. Permissions are a mapping, not a list. Read role membership and the protected entity before changing either side.

Custom claims are org-scoped, query-derived user facts used by policy expressions. Design the backing query, source-table read policy, and consuming policy together: claim resolution is restricted by the source table's policy. Claims select one scalar value per source row, so flatten list-valued grants into separate rows. Test users with empty, single, and multiple claim values.

Table and file policies are deny-by-absence. Fresh resources commonly begin with an admin bypass only; ordinary users need explicit rules. Policy rules can be referenced by multiple resources, so inspect usages before updating or deleting a shared rule.

Read `tables.md` and `files.md` for resource-specific policy behavior.

## Events

An event source is a schedule, webhook, or topic. A subscription targets exactly one workflow or agent.

- Schedule flags build the nested schedule configuration; webhook flags build nested webhook configuration.
- Subscription target type is inferred from the workflow/agent selector.
- Changing a subscription's target is not an update: delete and recreate the subscription intentionally.
- Topic workflows receive event metadata and payload through the execution context; validate missing or malformed payload fields.
- On a Solution-owned source, deploy replaces only the subscriptions declared in the Solution's `.bifrost/events.yaml`. A subscription you create on that source from outside the Solution (for example, a workspace workflow listening to the Solution's topic or schedule) stays in place across redeploys and is not exported with the Solution. Capture adopts only subscriptions that target the Solution's own workflows or agents; capture the listener's workflow too if it belongs in the Solution.
- External listeners are still removed with what they depend on: when a redeploy drops the source from the manifest, or when the Solution is hard-deleted (the deletion summary reports them as `external_event_subscriptions`). A non-destructive uninstall leaves them in place.

Use `events.emit()` from a workflow to publish a topic. Confirm source scope, subscription access, idempotency/retry behavior, and downstream failure handling.

## Organizations

Organizations are tenant boundaries. Organization mutations can affect users and the visibility or resolution of many dependent records. List dependents and get explicit confirmation before destructive organization changes.

## Mutation checklist

1. Get the current record and its dependencies.
2. Confirm ownership: Solution deploy or loose live mutation.
3. Confirm organization, access level, roles, policies, and environment impact.
4. Use the dedicated command and exact generated flags.
5. Get the record again and verify the complete intended state.
6. Exercise the consuming form, agent, app, workflow, or event as a realistic caller.
7. Report every live mutation and anything still awaiting Solution deploy.
