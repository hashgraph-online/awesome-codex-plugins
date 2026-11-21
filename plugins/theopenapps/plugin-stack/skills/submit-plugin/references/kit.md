# The kit

One folder, `submission/`. Leave it out of the ZIP, and list it in `.gitignore` when the plugin sits at the repo root, because Claude's file checks cover every file in the plugin folder.

| Path | Holds |
|---|---|
| `README.md` | A lock-these-first block from step 2, then one numbered hand-off per store |
| `copy.md` | Listing copy in one table, with a column per store |
| `test-cases.md` | The one list of test cases |
| `reviewer-notes.md` | Answers to the portals' questions |
| `assets/` | Images named by store |

The store manifests stay where each store reads them. Generate their review fields from `test-cases.md` and the step 2 choices, so a store file can't drift from the source.

| Store | Manifest |
|---|---|
| ChatGPT | Root `plugin.json` or `.codex-plugin/plugin.json`, with `extensions.com.openai.review` and `extensions.com.openai.publication` filled |
| Claude plugin | `.claude-plugin/plugin.json` |
| Cursor | Root `plugin.json` or `.cursor-plugin/plugin.json` |

## Closest listings

Find candidates with `listings_search query="<1-3 nouns for the job>" store=<store> limit=10`. Search matches words one at a time, so a pasted README sentence mostly returns noise. A good hit's job tag widens the set: `tags_get tag=<tag> store=<store> limit=20`. Confirm the 3 closest with the user. If fewer than 3 exist, read those and say so in `README.md`.

Read the 3 closest live listings with `listings_versions ref=<ref> latest=true`. Reuse their shape, never their words: how many starter prompts, how long the description runs, category value, capabilities, skills, whether screenshots are filled. Check where the category really lands: compare the manifest's `interface.category` with the row's `category` (`Entertainment` has landed in Other).

| Listing | Where the copy sits |
|---|---|
| ChatGPT | `data.detail[-1].data.release.interface`: `short_description`, `long_description`, `default_prompts`, `category`, `capabilities`, `screenshot_urls`. `data.detail[-1].data.release`: `keywords`, `skills` |
| Claude connector | `data.listing[-1].data`: `one_liner`, `description`, `categories`, `tool_names` |
| Cursor directory | `data.listing[-1].data`: `name`, `description`. `data.detail[-1].data`: `keywords`, `plugin_components` |

## `copy.md`

One table, because lengths differ per store. Each cell holds the text and its character count against the limit in the store file.

| Field | ChatGPT | Claude connector | Claude plugin | Cursor |
|---|---|---|---|---|
| Name | `displayName` | Server name | `displayName` | `displayName` |
| One line | `shortDescription` | One-liner, with its visible length | Short description | `description` |
| Long | `longDescription` | Description | The README | The README |
| Prompts | `defaultPrompt` | One per screenshot | | |
| Terms | `keywords` | Categories | | `keywords` |

## `test-cases.md`

Write each case here and nowhere else. Manifests and portal answers copy from this list.

| Column | ChatGPT manifest field |
|---|---|
| Description | `description` |
| Prompt | `prompt` |
| Tools | `tools_triggered` |
| Expected | `expected_behavior` |
| Why it should not act (negatives only) | `description`, with the expected refusal, clarification or safe fallback in `expected_behavior` |

Run every case with the test account and record the result beside it.

## `assets/`

Size and format rules are in the store file.

| File | When |
|---|---|
| `chatgpt-logo.png` | Always for ChatGPT |
| `chatgpt-706w-1.png` | One per starter prompt, only if the plugin has UI |
| `claude-icon.png` | Claude connector |
| `claude-1000w-1.png` | 3 to 5 for an MCP App, each with its paired prompt in `copy.md` |
| `cursor-logo-square.png` | Cursor, with a background plate |

## `reviewer-notes.md`

Answer only from behavior you inspected, and name what you inspected. Mark the rest for the user. Write each credential only into the portal, never into a file or a ZIP.

### ChatGPT

| Portal asks | Inspect |
|---|---|
| Login URL, workspace or tenant, sign-in steps | A dedicated test account with sample data, signed in from a clean browser session outside any company network. It has to work with no MFA, email or SMS codes, magic links or private network |
| Commerce: `review.commerce`, `review.commerce_description` | Checkout, payment and plan-page code |
| Iframe justification per embedded domain (`frame_domain_explanation_required`) | `_meta.ui.csp.frameDomains` and the domains the tool scan reports. Say what each page does, why the plugin embeds it and who controls its domain |
| One-sentence reason per hint, per tool | Each tool's code path. `readOnlyHint` is true only when the tool strictly fetches. `destructiveHint` is true when any mode can do something irreversible. `openWorldHint` is true when it reaches the public internet or open-ended external entities. When a hint and the code disagree, stop and ask: the fix is on the server, followed by a rescan |

### Claude plugin

| Portal asks | Inspect |
|---|---|
| Reads or stores personal data | File reads, storage writes and tool inputs in hooks, scripts and MCP calls |
| Sends data to services other than its declared connectors | Every fetch, hook and script target, against the manifest's MCP servers |
| How long it keeps data | Where it writes and what deletes it. With no storage, say so |
| Intended for people under 18 | The README's audience, then the user |
| Contact email and the four acknowledgements | The user. The docs don't name the four, so read them in the portal |

### Claude connector

| Portal asks | Inspect |
|---|---|
| Primary use cases | `test-cases.md` and the tool list |
| What users need before they connect: accounts, plans, setup | The sign-in path and any plan checks on the server |
| Reads data, writes data, or both | `tools/list` annotations against each tool's code |
| Underlying API: your own, proxied with permission, or a third party's | Each tool's outbound calls. Permission to proxy is the user's to confirm |
| Personal health data | Tool inputs, outputs and the fields they pass on |
| Sponsored content | Whether any response includes paid placement |
| Test account setup and access | Every link and step for a fully populated account. Confirm every tool was run through MCP Inspector or as a custom connector |

The seven acknowledgements:

| Acknowledgement | Inspect |
|---|---|
| Directory guidelines | The user reads https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy |
| First-party API usage | Tools call only APIs the publisher owns or legitimately proxies |
| Financial transactions | Any tool that moves money |
| AI media generation | Any tool that generates images, video or audio. Diagrams, charts and UI mockups are allowed |
| Prompt injection | Tool descriptions that instruct Claude, interfere with other tools, pull instructions from elsewhere or hide text |
| Conversation data collection | Parameters, logs or tools that collect conversation data or query memory |
| Public documentation | A public page live by the publish date. A blog post or help article is enough |

### Cursor Marketplace form

| Form field | Source |
|---|---|
| Organization name | The user |
| Organization handle | The user: a unique kebab-case namespace |
| Contact email | The user |
| Logotype URL | A public URL for `cursor-logo-square.png` that loads signed out |
| Description | The Cursor column of `copy.md` |
| GitHub repository | The public repo, loaded signed out |
| Owner | Fixed to the signed-in individual |
| Website URL | Load it |
