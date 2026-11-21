---
name: kin-accounts
description: Work with several accounts of one service in Kin, such as a work and a personal GitHub. Use when the person names one of their accounts, or when Kin's search returns more than one account for a task.
---

# Several accounts of one service

In Kin, each connected account is its own connection, with its own label (such as "Work GitHub" or "Personal GitHub") and its own rules. Search results show the label of the connection each action belongs to.

- When the person names an account ("my work GitHub", "the personal Notion"), use the action from the connection whose label matches.
- When they don't name one and more than one account fits, Kin's answer includes `ambiguity`, which lists the accounts that fit. Ask the person which one to use. Don't choose for them.
- Keep using the same account for the later steps of one task, unless the person says otherwise.
- Rules are set per account. The same action can be allowed on one account and set to Ask me or Block on another. If a change is refused on the account the person chose, tell them. Don't run it on a different account instead unless they ask you to.
