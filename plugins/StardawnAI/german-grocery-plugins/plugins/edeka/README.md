# edeka-shopping plugin (EDEKA, E center, Marktkauf)

A skill for Codex and Claude Code that lets your assistant shop at EDEKA online markets (`<market>.edeka.shop`: EDEKA, E center and some Marktkauf stores) for pickup with your own
account: market search by postal code, weekly offers, products and prices, basket by plain words and the earliest pickup slot. Orders are placed only after you confirm the total and the pickup slot in the chat.

## How it works

- The skill drives `edeka-pp-cli`, an open-source command-line client from the
  [Printing Press library](https://github.com/mvanhorn/printing-press-library) (`library/commerce/edeka`).
  If it is missing, the assistant downloads the prebuilt binary for your system from the library's
  GitHub release and checks its SHA-256 first.
- You log in to the shop yourself in a browser window that `edeka-pp-cli auth connect` opens. The session
  is kept in a file on your computer; your password is never seen, typed or stored.

## Data it sends

- To your market's `edeka.shop` site: your shop requests (search, basket, slots, orders) with your session, directly from
  your computer.
- To GitHub: one download of the binary when installing or updating.
- Nothing to Stardawn AI or anyone else. Privacy policy: https://grocery.stardawn-service.com/privacy

Unofficial; not made or endorsed by EDEKA. Apache-2.0. Support: onedone-support@stardawnai.com
