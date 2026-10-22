# Sendpaper for Codex

Send real postcards (4×6, 6×9) and letters to any US address from Codex. Printed and mailed via USPS First-Class.

## Install

```
codex plugin marketplace add ryan-tish/sendpaper-plugin
```

## Usage

Ask in plain words, for example: "Mail a thank-you postcard to Dana Kim, 12 Oak St, Austin TX 78701." The bundled `send-mail` skill confirms the addresses, creates the order, shows the exact print preview and asks you before paying.

Tools: `get_pricing`, `create_postcard`, `create_letter`, `pay_order`, `get_order`, `cancel_order` (remote MCP at `https://sendmypaper.com/mcp`, no API key).

Sending the same card or letter to several people? Say so: up to 25 recipients go in one group with one payment, and each person gets their own tracked piece.

## Security

- No secrets in this plugin; the MCP server needs no authentication.
- Money moves only with your approval: a Stripe shared payment token you approve in Stripe Link for that amount, or a Stripe Checkout link you pay yourself.
- A person reviews every piece before it is printed. See [SECURITY.md](SECURITY.md) to report a vulnerability.

Docs: https://docs.sendmypaper.com · License: MIT
