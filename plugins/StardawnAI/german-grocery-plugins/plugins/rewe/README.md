# rewe-shopping plugin (REWE)

A skill for Codex and Claude Code that lets your assistant shop at REWE (www.rewe.de) for pickup with your own
account: offers of your market, products and prices, basket by plain words, the earliest pickup slot, REWE recipes to basket and past orders. Orders are placed only after you confirm the total and the pickup slot in the chat.

## How it works

- The skill drives `rewe-pp-cli`, an open-source command-line client from the
  [Printing Press library](https://github.com/mvanhorn/printing-press-library) (`library/commerce/rewe`).
  If it is missing, the assistant downloads the prebuilt binary for your system from the library's
  GitHub release and checks its SHA-256 first.
- You log in to the shop yourself in a browser window that `rewe-pp-cli auth connect` opens. The session
  is kept in a file on your computer; your password is never seen, typed or stored.

## Data it sends

- To www.rewe.de: your shop requests (search, basket, slots, orders) with your session, directly from
  your computer.
- To GitHub: one download of the binary when installing or updating.
- Nothing to Stardawn AI or anyone else. Privacy policy: https://grocery.stardawn-service.com/privacy

Unofficial; not made or endorsed by REWE. Apache-2.0. Support: onedone-support@stardawnai.com
