---
name: aident-loadout
description: Coordinate multi-step work across services the user has authorized through Aident Loadout, using live action schemas, connection checks, cost preflight, and explicit approval for side effects.
---

# Aident Loadout

Use this Skill when a user asks to discover or perform work across connected services supported by Aident Loadout. Do not invoke it for unrelated questions or when the user only needs an answer from the current conversation.

## Workflow

1. Identify the concrete outcome and the services involved.
2. If the exact canonical Action name is unknown, call `capabilities_search` with a concise description of the operation.
3. Call `capabilities_get` before the first use of an Action to inspect its current input schema, side effects, account requirements, and approval behavior.
4. Use `vault` to check connection status. If a connection is missing, give the user the returned Aident-hosted connection URL. Never request credentials, API keys, MFA codes, or authentication secrets in chat.
5. Call `capabilities_preflight` before a dynamically priced or metered Action. Explain the returned cost or approval requirement before proceeding.
6. Before a side-effecting Action, state the target, effect, and important inputs. Obtain any user acknowledgement required by the Action and preserve the exact acknowledged request.
7. Call `capabilities_execute` with the exact canonical Action name and schema-valid input. Report the result without exposing internal identifiers or private provider data that the user did not request.

Use `skills_search` and `skills_read` when the user needs reusable domain guidance or a multi-step procedure rather than a single known operation.

## Safety and scope

- Treat connection, acknowledgement, and credit-approval requirements as hard gates.
- Do not use this plugin to buy subscriptions, digital services, credits, tokens, or other digital goods.
- Do not send, publish, delete, disconnect, or modify external data unless the user requested that effect and any required acknowledgement is satisfied.
- Keep provider access within the user's authorized accounts and the requested task.
- Do not claim an Action succeeded until its terminal result confirms success.
