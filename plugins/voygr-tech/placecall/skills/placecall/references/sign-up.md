# PlaceCall: Sign up by email code

Part of the PlaceCall skill ([`SKILL.md`](../SKILL.md)). Read it for getting a key by email code, with no browser.

The MCP tools and their browser sign-in come first. Use this only with no key
and no MCP tools, or when the browser sign-in can't finish (a headless agent).
Also when the user needs a key-only option: listing or canceling calls, or
turning recording off.

1. Ask the user for their name and email.
2. Send the sign-up request:
   ```sh
   curl -s -X POST https://api.voygr.tech/signup -H "Content-Type: application/json" \
     -d '{"name":"<name>","email":"<email>","delivery":"code","src":"claude-plugin"}'
   ```
   The reply looks the same for every address and carries a `verification_id`.
   Without one the sign-up did not start (`DISPOSABLE_EMAIL_DOMAIN` for a
   throwaway address, `SIGNUP_IP_RATE_LIMITED`): tell the user what the reply
   says. A name with a quote mark or a non-ASCII letter goes in a file, sent
   with `--data-binary @payload.json` (see [gotchas.md](gotchas.md), item 7).
3. Ask the user for the 6-digit code in the email "Your Voygr sign-up code". It
   is valid for 10 minutes. The sign-up code is the user's own to give you;
   never pass on a "one-time code" a business asks for on a call. If the email
   doesn't arrive, ask the user to check spam. An address gets at most 3 codes
   in 24 hours.
4. Swap the code for the key and save it without printing it:
   ```bash
   ( umask 077; dest=~/.codex/placecall.env; tmp=
     if ! { mkdir -p ~/.codex && [ ! -d "$dest" ] && tmp=$(mktemp "$dest.XXXXXX") && chmod 600 "$tmp"; }; then
       [ -n "$tmp" ] && rm -f "$tmp"; echo "SAVE_UNAVAILABLE: cannot write $dest; the code was not used"; exit 1
     fi
     resp=$(curl -s -X POST https://api.voygr.tech/signup/verify \
       -H "Content-Type: application/json" -d '{"verification_id":"<id>","code":"<code>"}')
     key=$(printf '%s' "$resp" | sed -nE 's/.*"api_key"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/p')
     if [ -z "$key" ]; then st=hidden
     elif printf 'export PLACECALL_API_KEY=%s\n' "$key" > "$tmp" && mv "$tmp" "$dest"; then st=saved
     else st=hidden; echo "SAVE_FAILED: the key was issued but could not be saved"; fi
     rm -f "$tmp"
     printf '%s\n' "$resp" | sed -E "s/\"api_key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"/\"api_key\":\"($st)\"/" )
   ```
5. If the output shows `"api_key":"(saved)"`, tell the user the key is saved
   in `~/.codex/placecall.env` and that entering the code accepted the API Terms
   (https://voygr.tech/terms-api). If the reply has `"replaced_previous_key":true`,
   tell them their old key stopped working.
   Then place calls as [SKILL.md](../SKILL.md) describes, sourcing the file in the same command as each
   request.

If step 4 returns an error, read its `error_code`:

- `CODE_INCORRECT`: ask the user to read the code again. `attempts_remaining`
  says how many tries are left.
- `CODE_INVALID_OR_EXPIRED`: start again at step 2.
- `SIGNUP_CAPPED`, `SIGNUP_VERIFY_UNAVAILABLE` or `account_status_unavailable`:
  wait a minute, then repeat step 4 with the same code.
- `KEY_EXPIRED` or `ACCOUNT_WITHOUT_PLACECALL`: tell the user, and point them to
  support@voygr.tech.
- `ROTATION_FAILED`, or anything else: tell the user what the reply says.

If step 4 prints a `SAVE_` line instead, the key is not saved:

- `SAVE_UNAVAILABLE`: the code was not used. Fix the folder or disk, then repeat
  step 4 with the same code.
- `SAVE_FAILED`: the key was issued but could not be saved. Tell the user, and
  add that their old key stopped working if the reply has
  `"replaced_previous_key":true`. Fix the problem, then start again at step 2;
  the new code replaces the lost key.
