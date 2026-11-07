# Jev Route Reference

Three routes carry official documentation for calling Jev, and each one has its own contract. Mixing
them is the fastest way to a rejected request: the endpoint differs, the authentication header
differs, and the name of the yes/no question type differs between the direct routes and the Vercel
AI SDK route. This file holds the comparison, the order to pick a route in, and the routes that
carry no official documentation and must not be coded against.

Price, limits, and model aliases live in the platform snapshot next to this file, not here.

## Contents

- Refresh Policy
- Route comparison
- Route choice order
- Unverified routes
- Sources

## Refresh Policy

- last_verified_at: 2026-10-01
- refresh_when:
  - a route changes its endpoint, authentication header, or accepted model ids
  - the question type name changes on any route
  - a route on the unverified list publishes official documentation
  - a new route starts carrying Jev

## Route comparison

Status means: `verified` when an official vendor page captured in this snapshot documents the
route contract, and `unverified` when it does not. A verified row is safe to generate code from. An
unverified row is a name to look up, nothing more.

| Route | Endpoint | Auth | Model id | Question types | Confidence | Env var | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TypeSafe direct | `POST https://api.typesafe.ai/v1/systemone` | `Authorization: Bearer plus your key` | `jev-latest`, `jev-preview`, `jev-1.13.0` | `noul`, `choice`, `score` | `answers.<id>.confidence` on choice and score; none on noul | `TYPESAFE_API_KEY` | verified |
| b.ai | `POST https://api.b.ai/v1/decisions` | `Authorization: Bearer <key>`, or `x-api-key: <key>` | `jev-1.13.0`, `jev-latest` only | `noul`, `choice`, `score` | `answers.<id>.confidence` on choice and score; none on noul | `BAI_API_KEY` (project convention, not named by the vendor) | verified |
| Vercel AI SDK and AI Gateway | No direct endpoint; the SDK resolves the model, and a string id goes through Vercel AI Gateway when no default provider is configured | Gateway key through `AI_GATEWAY_API_KEY`, or Vercel OIDC | `typesafe-ai/jev` as a string id, or `typeSafeAi.evaluationModel('jev-latest')` | `boolean`, `choice`, `score` | `result.providerMetadata?.typesafe?.confidence`, keyed by question id | `AI_GATEWAY_API_KEY` | verified |

Details that the table cannot hold:

- On the two direct routes the yes/no type is spelled `noul`. On the SDK route it is spelled
  `boolean`. Writing `noul` in an SDK request, or `boolean` in a direct request, is an error.
- The b.ai route accepts exactly two model ids. The direct route also accepts `jev-preview`.
- The b.ai route supports POST only, so `stream` is omitted or set to `false`. A `true` value is
  not part of that contract.
- The SDK route is experimental: the evaluation API and the evaluation model specification may
  change in patch releases, so pin the installed package version.
- The SDK route's `boolean` answer carries a required `probability`, and choice and score
  distributions are optional there, unlike the direct routes where every choice and score answer
  carries `probabilities`.
- Environment variables are named here so code can check whether a name exists before offering a
  live call. Read the value from the environment at call time; never print it, log it, or write it
  into a file.

## Route choice order

Pick the first rule that matches, and say which route was chosen when the answer is handed over.

1. If the repository already depends on the `ai` package, use the AI SDK route and the `boolean`
   question type. The dependency decides, because the package is already installed and the
   project's other model calls already go through it.
2. Otherwise, if the environment has `BAI_API_KEY` set (check the name only, never the value),
   use the b.ai route. `BAI_API_KEY` is this project's own convention for that route; the vendor
   pages this snapshot holds name no environment variable for it. A key name being set on the
   machine is evidence about the machine, not about this project. When the project's own files,
   such as a lock file, config, existing client code, or an env example, name a different route,
   that route wins, and when the two disagree, say which route was chosen and why.
3. Otherwise use the TypeSafe direct route with `TYPESAFE_API_KEY`.

When more than one rule matches, the earlier rule wins. Changing the route is a request-level
decision, not a detail to be defaulted silently: the question type name and the confidence path
change with it, so the generated request and the parsing code change too.

Neither the presence of a key nor a high confidence value authorizes a live call. Ask the person
before the first real request, state the cost, and keep the call count to the minimum that answers
the question.

## Unverified routes

These routes market or resell Jev, and this snapshot holds no official page that documents their
contract. They are recorded here so a request naming one is recognized, not so code can be written
for it.

- OpenRouter. The vendor's own Python SDK page shows an OpenRouter base URL and an OpenRouter model
  slug as a worked example, so the route exists. The slug shown there is not the model id used
  anywhere else, and no page in this snapshot states the current supported ids or the request
  shape. Model names in circulation for this route should be treated as unconfirmed.
- Cloudflare.
- Netlify.
- DigitalOcean. The Gateway model card lists `digitalocean` as a provider, which is a listing, not
  a documented route contract.
- AI/ML API.

Instruction for every entry above: do not generate code. Read the vendor's official documentation
first, confirm the endpoint, the authentication header, the accepted model ids, and the question
type names, then write the route into this file with its own verified row before any code is
produced for it.

The same rule applies to any route not listed in the comparison table: a route with no verified
row is an unverified route, and an unverified route gets no generated code.

## Sources

> Links checked 2026-10-01. Next re-verification: 2026-10-31.

| Claim | Source |
| --- | --- |
| The direct endpoint, the Bearer header, the three question type names, the accepted model aliases, and the choice and score confidence path | <https://docs.typesafe.ai/api> |
| The alias table behind the direct route's accepted model ids | <https://docs.typesafe.ai/models> |
| The b.ai endpoint, both accepted auth headers, the two accepted model ids, POST-only behavior with `stream` omitted or false, and the answer confidence rule | <https://docs.b.ai/llmservice/api/decisions-api/> |
| The SDK route's `boolean` type, the optional distributions, the Gateway confidence path, and the `AI_GATEWAY_API_KEY` authentication note | <https://ai-sdk.dev/docs/ai-sdk-core/evaluation> |
| The string model id for the Gateway, the provider list on the model card, and the evaluation model type | <https://vercel.com/ai-gateway/models/jev> |
| The OpenRouter base URL and model slug example used to place that route on the unverified list | <https://docs.typesafe.ai/sdk/python/usage.md> |
| The environment variable names used by the direct and SDK routes | <https://docs.typesafe.ai/models> and <https://ai-sdk.dev/docs/ai-sdk-core/evaluation> |

### Evidence grade

`PRIMARY` for every verified row: each contract detail comes from the vendor page named in the
table above, captured on 2026-10-01. `SECONDARY` for the unverified list, which is a routing
warning rather than a contract. The list names routes seen in circulation; this snapshot contains
no vendor page documenting them, and one entry (OpenRouter) rests only on the vendor's own
integration example, which shows a base URL and a model slug rather than a full contract.

The environment variable names for the direct route are taken from the vendor's SDK pages, which
read the key from the environment by that name. `BAI_API_KEY` is a project convention rather than a
vendor name: the saved b.ai pages name no environment variable for that route, and the direct
provider's (non-Gateway) authentication and environment variable are not in the saved pages either,
so neither is stated as a verified fact here.

Not evidenced here and deliberately left unspecified: the version of any client package, the
current model ids on the unverified routes, and whether any unverified route supports streaming.
