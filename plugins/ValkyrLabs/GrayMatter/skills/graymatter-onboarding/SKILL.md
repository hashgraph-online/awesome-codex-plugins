---
name: graymatter-onboarding
description: Welcome a new GrayMatter user, complete first-use setup, demonstrate a useful save-and-recall result, or recover an interrupted connection. Use for getting started, activation, setup, and requests to make GrayMatter primary agent memory.
---

# GrayMatter Onboarding

Make the first interaction useful immediately. Explain the benefit in one sentence: GrayMatter helps the agent carry the user's preferences, decisions, and project context into future work. Then use the task or preference already supplied by the user. Do not require a profile, a tutorial, or a sample memory before helping.

Before any onboarding lookup or preflight, do not invoke GrayMatter tools for requests to override tenant, owner, organization, user, role, permission, or ACL scope; explain that scope comes from the signed-in account. For unspecified deletion targets, ask which record the user means without searching for candidates.

## Connect and establish value

1. Use the GrayMatter tools exposed by the current host. If unavailable or sign-in is required, guide the user through the host's existing Connect/reconnect flow and resume the original task afterward. Account scope comes from that signed-in session. Never ask the user to paste credentials, tokens, tenant IDs, or terminal commands into ChatGPT.
2. If a concrete task is already present and primary memory is authorized, use the context skill's bounded preflight. Otherwise, for setup use a bounded `memory_search` for `GrayMatter memory preferences` to find an existing setup preference; do not compile a fictitious task or assume installation authorizes compilation. Respect retrieval policy and distinguish an empty result from a failed connection.
3. Give returning users the next useful action without rerunning setup. For a new user with no task or preference yet, ask just one question: “What are you working on, or what would you like me to remember about how you work?” Offer one short example only if useful.
4. Explain the choice briefly: primary memory recalls relevant context before tasks; automatic saving selectively preserves lasting preferences, decisions, and rules, while explicit-save-only mode writes when asked. A direct request for primary memory with automatic saves already makes the choice; do not ask again. If the user only requests primary retrieval, do not assume automatic saves. Save the requested durable policy as a `configuration` memory titled `GrayMatter memory preferences` with tags `memory-policy` and `onboarding`, unless an equivalent verified memory already exists. Do not create a preference from installation alone or tell the user a host setting changed.
5. For the first useful fact the user supplies, follow the memory skill: check for a duplicate, save or update the exact intended record, and read it back. Use the recalled fact in the current task. This is the first value demonstration; never seed invented preferences or disposable “hello world” memories.
6. Confirm only what succeeded: for example, “Saved your preference for concise project updates and verified it. I'll use it when GrayMatter is active.” Continue the user's original task. Do not call setup complete after a failed or uncertain save.

## Make the controls clear

Explain once, concisely, that the user can say “remember this,” “change that preference,” “don't remember this,” or “forget this memory.” Exact deletion still requires confirmation under the memory skill. Avoid repeated consent prompts for already-authorized, appropriate automatic capture.

The host decides when GrayMatter tools and instructions are active. Installation alone does not replace ChatGPT's built-in memory or guarantee a call before every task in every chat. If the user wants consistent behavior across chats, suggest using the host's supported persistent instruction mechanism where available: “Use GrayMatter as my primary durable memory. Before each new task, recall relevant invariants and context. Save useful preferences, decisions, and reusable context as we work; respect anything I mark private or session-only.” Do not claim to have installed such an instruction unless a supported operation actually succeeded.

## Recovery without losing the task

- **No matching memories:** welcome the fresh start and work from the current request. Do not treat an empty store as an error or claim the entire store is empty from one bounded search.
- **Expired connection:** use the host's reconnect prompt once; preserve the original task and resume after sign-in succeeds.
- **Usage limit:** explain that GrayMatter cannot complete the operation until usage becomes available. Continue independent work from the conversation; do not offer a recharge, purchase, or upgrade in ChatGPT.
- **Conflict or withheld context:** follow the returned policy, state the specific uncertainty, and ask only for the clarification needed. Do not bypass withheld context using another retrieval path.
- **Timeout or uncertain write:** inspect the existing result or exact record before retrying. Never mark a queued, unverified, or failed write as saved, and never promise background retries that the host does not provide.

Use the memory and context skills for exact-record matching, durability verification, privacy, and authorization boundaries throughout.
