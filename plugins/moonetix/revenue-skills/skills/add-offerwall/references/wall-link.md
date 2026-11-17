# The wall link

The offerwall is a page hosted by the network. Your app sends the user there with a link that says who the user is. Everything the user earns later is credited to the id in that link, so the link is built on the server, for the signed-in user, and nowhere else.

## Rules for the link

- **The user id comes from the session.** Never from a query parameter, a form field, a header set by the client or a value stored in the page. A `user_id` in the request is ignored.
- **Signatures and tokens are computed on the server.** The signing secret and any API key live in the server's environment. They are never sent to a browser, bundled into a mobile or desktop app, or committed.
- **The id is the app's own stable identifier:** the primary key or a public id of the account. Not an email address, a username or a phone number. The id travels to another company and into URLs and logs.
- **Check the id's characters against what the network accepts,** and refuse to build a link for an id that does not fit. Do not strip or replace characters: two accounts could end up with the same id.
- **Build the link per request.** Do not cache it in a shared cache or a CDN. Send `Cache-Control: private, no-store` on any response that contains it.
- **Decide who gets a link.** Signed-in accounts only. Apply the app's own gates first (banned, under review, not yet verified) and the network's rules on age and country. Check the network's terms for both.

## Building it

Many networks sign the link with an HMAC of the user id, so that a user cannot swap in another id. The parameter names and what exactly is signed differ: check the network's documentation, and see network-facts.md for one documented format.

Node:

```js
import { createHmac } from 'node:crypto';

const USER_ID = /^[A-Za-z0-9._:-]{1,64}$/;

// Server side only. userId comes from the session, never from the request.
export function wallUrl({ baseUrl, appId, linkSecret }, userId) {
  const id = String(userId);
  if (!USER_ID.test(id)) throw new RangeError('this user id cannot be carried in a wall link');
  const url = new URL(`${baseUrl}/${encodeURIComponent(appId)}`);
  url.searchParams.set('user_id', id);
  url.searchParams.set('hash', createHmac('sha256', linkSecret).update(id).digest('hex'));
  return url.toString();
}
```

Python:

```python
import hashlib
import hmac
import re
from urllib.parse import quote, urlencode

_USER_ID = re.compile(r"[A-Za-z0-9._:-]{1,64}")


def wall_url(base_url: str, app_id: str, link_secret: str, user_id: str) -> str:
    """Server side only. user_id comes from the session, never from the request."""
    if not _USER_ID.fullmatch(user_id):
        raise ValueError("this user id cannot be carried in a wall link")
    signature = hmac.new(link_secret.encode(), user_id.encode(), hashlib.sha256).hexdigest()
    return f"{base_url}/{quote(app_id, safe='')}?{urlencode({'user_id': user_id, 'hash': signature})}"
```

The link secret is not the postback secret. Load both from the environment at start-up, with no default, and fail to start when one is missing.

If the network does not sign links, anyone can open the wall under any id. Nobody can take coins that way, since rewards go to the id in the link, but a banned user can earn into another account. Then send an id that cannot be guessed: a random public id stored on the account, not a sequential number.

Sub ids and other tracking parameters are not signed on most networks. Use them for reporting, never to decide who is credited or how much.

## Serving it

**Server-rendered page.** The handler reads the user from the session, builds the URL and writes it into the `src` of an iframe. Escape it as an attribute value.

**Single-page front end.** An authenticated endpoint returns the URL. The front end sends no user id; the endpoint knows who is asking.

```js
app.get('/api/offerwall-link', requireUser, (req, res) => {
  res.set('Cache-Control', 'private, no-store');
  res.json({ url: wallUrl(config.wall, req.user.id) });
});
```

`requireUser`, `config.wall` and the route style stand for whatever the project already has. Answer 401 when nobody is signed in and 403 when the account may not use the wall.

**The iframe.**

- Give it a title and a height that fits the screen. Walls scroll inside the frame.
- If the site sends a Content-Security-Policy, add the wall's origin to `frame-src`. Without it the frame stays blank and nothing is logged on the server.
- Some networks load the wall only on the domain registered for the app, and only over HTTPS. On `localhost` the frame can stay blank: open the link in its own tab while developing.
- Do not add a `sandbox` attribute unless the network documents the tokens its wall needs. A sandbox without them blocks the new tabs and redirects that offers use.
- The page that holds the frame is a normal authenticated page. Guests are sent to sign in, not shown a wall with an empty id.

## Mobile apps and games

The app asks the app's own backend for the link, with the user's normal authentication, and opens it in a web view, a browser tab or the network's SDK. The signing secret is never in the app: anyone can read the files of an installed app.

- **Link in a web view.** The same endpoint as above.
- **SDK with a session token.** Some SDKs open the wall with a short-lived token. The backend requests the token from the network with its API key and returns only the token. The app requests a new one each time the user opens the wall and does not store it.
- **SDK that takes a user id from the app.** Then the id is whatever the app says, and only the postback protects the credit. Use an id that cannot be guessed, and check the network's documentation for a server-signed alternative.

Callbacks that an SDK fires in the app ("reward earned", "wall closed") are for the interface only. Use them to reload the balance from the server. Never credit from them: the app can be modified, and the callback can be called by hand.

In a game, the same applies to any client: the game client shows the wall and the new balance, and the game server learns about rewards from the postback.

## Bots and communities

A chat bot has no browser session. The bot's backend maps the platform's user id (from the signed interaction or webhook of the platform, after verifying that signature) to an account in the app, and builds the link for that account.

- Send the link where only that member can see it: a private chat, or a reply that is visible to the member alone. A wall link is personal. Posted in a channel, it lets everyone earn into one account, and the network's fraud checks will see one user on many devices.
- If the member has no linked account yet, send them to link one first. Do not create wall ids from display names.
- Prefer a button to a short-lived page on the app's own site, which checks the member and then shows the wall. The signed link then never appears in chat history.
- Check the platform's rules on rewarded offers before posting anything about them in public channels.

## What the user sees afterwards

- The balance comes from the server. After the wall closes, reload it. Do not add the reward in the client.
- Coins inside the hold are shown as pending, with the date they become available.
- A reward that was reversed appears in the history as its own line, pointing at the offer. A balance that drops without an explanation is a support ticket.
- Rewards are not instant on every offer. Say so near the wall, and link to the place where a user reports a missing reward.
