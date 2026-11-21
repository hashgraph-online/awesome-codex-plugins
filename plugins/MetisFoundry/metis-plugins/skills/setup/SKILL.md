---
name: setup
description: Connecting Metis Check for the first time: the Metis sign-in page, the first check to try, and where reports live.
---

# Setting up Metis Check

## Connecting

Choosing **Connect** opens the Metis sign-in page in a browser window.

- Sign in with a Metis username or email and password.
- No Metis account yet: use the link under the sign-in form to create a Metis Check account. It takes a minute; afterwards you return to the sign-in page automatically and the connection completes.
- A service account can paste a live Metis API key with the `mcp:call` scope instead (under "Connecting a service account?" on the same page).

The connection is bound to that Metis account. Every check runs under it and counts against its monthly allowance.

## A first check

Try one of these:

- "Is 10.1038/s41586-020-2649-2 a real DOI?"
- "Check the LEI HWUPKR0MPOU8FGXBT394 for Apple Inc."
- "Check the citations in this paragraph:" followed by a pasted paragraph or reference list.

Each one comes back with a state per identifier (settled true, settled false, needs a person, unreachable, or not checked with the reason), the registry asked, and a report link.

## Where reports live

Every check files a report with a unique id (MC-XXXX-XXXX-XXXX), a public page, a PDF, signed receipts and a recheck button. The account page at `https://check-api.metisfoundry.com/check/account` lists the account's reports and shows the checks used this month. A report can be opened again in the chat with its id.
