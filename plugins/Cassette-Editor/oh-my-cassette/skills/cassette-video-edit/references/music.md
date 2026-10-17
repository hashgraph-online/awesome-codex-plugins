# Jamendo music and BYOK

Jamendo is strictly bring-your-own-key in every local agent host. The read-only catalog needs only
a Client ID. Never ask for or accept a Client Secret.

## Interactive setup

On `jamendo_client_id_missing`, or when the user asks to configure music:

1. Explain that they create a read-only application at <https://devportal.jamendo.com/>.
2. Explain that BYOK controls API access/quota but does not grant commercial-use rights.
3. Offer two mutually exclusive paths:
   - Chat: warn that the Client ID enters the conversation transcript, ask for it, then call
     `cassette_jamendo_setup(client_id=...)`.
   - Private terminal: relay `error.details.setup_command`, normally
     `python3 scripts/setup_local_mcp.py --jamendo`.
     Hermes guidance includes `--host hermes` so its ID is saved in `~/.hermes/.env`.

Never repeat the full Client ID after setup. The tool validates before storage, masks its reply,
and preserves any existing configuration when validation fails.

## Strict failure behavior

If Jamendo reports missing/invalid setup, a network or API error, a rate limit, no eligible results,
or a download failure, relay the structured error and stop the music flow. Do not call another
music provider and do not continue the edit without the requested BGM.

The legacy `cassette_match_bgm` tool is still callable only when the user explicitly requests the
Free To Use provider. It is never a Jamendo fallback.

## Licensing handoff

On success, relay the title, artist/attribution, Jamendo track URL, license URL, and download
eligibility returned by the tool. Tell the user to review that specific license and its attribution
requirements before publishing or commercial use. BYOK does not transfer responsibility or grant
rights beyond the selected track's license.
