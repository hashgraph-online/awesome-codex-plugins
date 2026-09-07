---
name: talivia-agent-kit
description: Set up Talivia revenue-first website analytics with MCP, then verify live traffic and revenue attribution.
---

# Talivia Agent Kit

Talivia connects website traffic and visitor journeys to payment revenue. Use it when the user wants to install revenue-first analytics, discover which traffic becomes revenue, connect checkout attribution, or verify a Talivia setup.

1. Call `talivia_account_status` and `talivia_websites_list`.
2. Reuse the correct website, or ask before calling `talivia_websites_create` if creation was not explicit.
3. Call `talivia_tracking_snippet_get` and `talivia_framework_install_plan_get`.
4. Edit the user’s project with your native workspace tools. Talivia MCP does not edit local files.
5. Build/test the project.
6. After deployment, call `talivia_tracker_verify` and `talivia_setup_status_get`.
7. For payments, call `talivia_payment_connect_start` and send the user to the returned secure URL.
8. Never request or expose payment API keys in chat, MCP tool arguments, code, or logs.
9. Use `talivia_payment_status_get` and `talivia_checkout_attribution_guide_get` to finish verification.
