---
name: bankbridge
description: Answer questions about the user's own money with live, read-only data from their connected US banks, credit cards and brokerages through the BankBridge MCP server. Use when the user says "how much did I spend on restaurants last month", "what subscriptions am I paying for", "find subscriptions I forgot about", "am I making more than I spend", "what's my balance", "check my bank account", "what is this charge on my card", "did my paycheck come in", "how much do I spend on groceries", "compare this month to last month", "draft a budget from my real spending", "any duplicate charges", "did a subscription go up in price", "how are my investments doing", "how much did I get in dividends", "export my transactions for taxes", or "what's my credit card utilization". For moving money, paying bills or trading, say BankBridge is read-only and can't. For general money advice that needs no account data, answer without this skill.
---

# BankBridge: questions about the user's real accounts

BankBridge is a remote MCP server at `https://bankbridge.money/api/mcp` that gives you read-only access to the user's connected bank, credit card and brokerage accounts. Every tool call fetches live data from the bank. Nothing can move money, pay a bill or place a trade.

## Setup

- If the BankBridge tools (`list_accounts`, `list_transactions`, ...) are not available, the user connects once: in Claude, add BankBridge from the Connectors Directory (https://claude.ai/directory/connectors/bankbridge) or this plugin's Connectors tab; in Claude Code, run `/mcp` and sign in. Other agents: https://bankbridge.money/docs
- If a result says `setup_required` or has a NO_CONNECTIONS notice, show the user the link in the result. It finishes the subscription or connects a bank. Pricing is $5 a month per connected bank, or $50 a year.

## Which tool for which question

| Question | Tool |
|---|---|
| Balances, account list, credit utilization | `list_accounts`, `get_account` |
| "How much did I spend on X?" | `get_spending_summary` (group by category, merchant, month or week) |
| Find a specific charge or merchant | `search_transactions`, then `get_merchant_history` |
| Subscriptions and bills | `get_recurring_charges` |
| "Am I making more than I spend?" | `get_monthly_cashflow` (one call per month, `month: "YYYY-MM"`) |
| Raw transactions with filters | `list_transactions` (date range, amount, category, account; paginate with `offset`) |
| Category names to filter by | `list_categories` |
| Portfolio, gains, dividends | `list_holdings`, `list_investment_transactions` |
| Add another bank | `connect_bank` (returns a link for the user) |

## Reading the data correctly

- Amounts are dollars. Positive = money leaving the account (spending). Negative = money coming in (income, refunds).
- Credit card payments from checking are not new spending: the purchases already appear on the card. Leave them out of spending totals.
- Transfers between the user's own accounts are not spending either. Transfers to other people (rent to a landlord, for example) are.
- One subscription can appear under several descriptor spellings. Check `get_merchant_history` before calling two charges duplicates.
- Don't project a year from one month. Use at least three months for averages, and say when a category is seasonal (utilities, travel).
- Every result has a `warnings` array. If it is not empty, tell the user (for example, a bank that needs reconnecting, with its reconnect link) and say the totals cover only the banks that answered.

## Good habits

- Start a session with `list_accounts` so you know which accounts exist; account ids can change when a bank is reconnected, so don't reuse old ids.
- Answer with the numbers first, then the detail: totals, the biggest items, and the change versus the previous period.
- Keep the user's data in the conversation. Don't paste it into other tools or services unless the user asks.
