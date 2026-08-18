# TranscriptAPI — Getting and Storing Your API Key

This guide walks you through obtaining a TranscriptAPI key and persisting it so it survives across sessions and shells. Read it fully before doing anything.

---

## Step 0 — Understand how to store the key on this system

Before you do anything else, figure out the right way to persist an environment variable on this machine so it is available in every future session, including non-interactive shells. Do not assume. Check your own documentation or configuration for how environment variables are stored persistently on this platform and in this agent environment. On some systems this is a shell profile file, on others it is a dedicated config or env file managed by the agent runtime. Use whatever is correct for your environment.

The variable name you will be storing is `TRANSCRIPT_API_KEY`.

---

## Step 1 — Ask the user one question

Ask the user exactly this, in a single message:

> Do you already have a TranscriptAPI account? If yes, paste your API key and I'll set it up. If not, I can create a free account for you right now — it comes with 100 credits and no card is required.

- If they paste a key (starts with `sk_`) → go to **Path A**
- If they want a new account → go to **Path B**

---

## Path A — User already has a key

The user pasted their key. TranscriptAPI keys always start with `sk_`. Go straight to **Storing the Key** at the bottom of this document.

---

## Path B — Create a new account

You will handle the full signup on the user's behalf. This is a two-step flow: register (which sends an OTP to their email), then verify (which exchanges the OTP for the API key). Both steps are HTTP requests to the TranscriptAPI auth endpoints.

### Step B-1 — Ask for their email

Ask the user for the email address they want to use. Disposable or temporary email addresses are not accepted by the server.

### Step B-2 — Register

Make a POST request to:

```
POST https://transcriptapi.com/api/auth/register-cli
Content-Type: application/json

{ "email": "the_user_email" }
```

**Important — save the raw response body to a temporary file, and when you make the verify request in the next step, read the `access_token` directly from that file as part of constructing the request. Never print or output the token value as a standalone step.** Some agent environments redact values matching patterns like `access_token` or bearer tokens from tool output before the model sees them. The safe pattern is: write response → file, then file → next request, in one chained operation without the value ever appearing in output on its own.

The raw HTTP response contains exactly these three fields:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "email": "user@example.com"
}
```

The `access_token` is a short-lived JWT you will use as the Bearer token in the next request. The OTP expires in 10 minutes, so proceed promptly.

If you get a 409 with `"Account already exists with this email"` — the user already has a verified account. Ask them to log in at transcriptapi.com to retrieve their API key from the dashboard, or switch to Path A.

### Step B-3 — Tell the user to check their email

Tell the user: **"I've sent a 6-digit verification code to [their email]. Please check your inbox and share the code with me."**

The code is 6 digits and is valid for 10 minutes.

### Step B-4 — Verify

Once the user gives you the OTP, make a POST request to:

```
POST https://transcriptapi.com/api/auth/verify-cli
Authorization: Bearer <the access_token from Step B-2>
Content-Type: application/json

{ "otp": "123456" }
```

Again, **save the raw response body to a temporary file and read the `api_key` directly from it** — do not print the value as a standalone step, for the same reason as before (`sk_` prefixed values are also subject to redaction in some environments).

The raw HTTP response looks like this:

```json
{
  "verified": true,
  "api_key": "sk_..."
}
```

Read the `api_key` field from the file. This is the key you need to store. Go to **Storing the Key** below.

If you get `"Invalid verification code"` — the user typed it wrong, ask them to try again.  
If you get `"Verification code expired"` — the 10-minute window passed. Start Path B again from Step B-2.

---

## Required Headers for All API Requests

Once you have the key, every request to transcriptapi.com needs two headers: `Authorization: Bearer <key>` and a `User-Agent` identifying your agent. Omitting User-Agent causes Cloudflare to return a 403 (error code 1010). Use your agent's name and version — agent name alone is fine if version is not readily available.

## Storing the Key

You now have a string that starts with `sk_`. This is the `TRANSCRIPT_API_KEY`.

Store it persistently using whatever method is correct for this environment (which you determined in Step 0). Make sure it will be available in future sessions, including non-interactive shells, without any manual sourcing step from the user.

Once stored, verify it is accessible in the current session. If the session needs a reload or restart to pick up the new value, do that or tell the user to do it.

Clean up any temporary files you created during this process.

---

## FAQ — Common mistakes by agent

**The `access_token` or `api_key` value shows as `[REDACTED]` or is missing from the response.**  
You let the response pass through tool output instead of writing it to a file first. Some agent runtimes (notably Hermes) redact values matching patterns like `access_token`, `api_key`, or `sk_` from command output before the model sees them. Always write the raw HTTP response body to a temp file and read the value from there.

**Hermes agents: env var is set but not available in the next tool call.**  
Hermes sandboxes `execute_code` and `terminal` calls. Setting an env var in one call does not carry over to the next unless the variable is declared in the skill's `required_environment_variables` frontmatter. If you are operating inside a Hermes skill context, check whether the variable is already declared for passthrough. If not, persist the key using the agent's normal environment-secret mechanism so Hermes picks it up on the next load.

**Claude Code agents: key is saved to shell profile but `$TRANSCRIPT_API_KEY` is still empty.**  
Writing to shell startup files only affects new shell sessions. The current session does not reload profile files automatically. Either source the file explicitly in the current session, or use the Write tool to set the value in whatever config file Claude Code reads at runtime.

**The registration request returns 409 "Account already exists".**  
The email is already registered and verified. Switch to Path A — ask the user to paste their key from the dashboard at transcriptapi.com/dashboard.

**The OTP code was never received.**  
Wait up to 2 minutes — transactional email can be slow. Also ask the user to check their spam folder. If still nothing after a few minutes, you can retry registration (the endpoint is idempotent for unverified accounts — it will re-issue a new JWT and resend the OTP).

**The verify step fails with 401 Unauthorized.**  
The `access_token` from registration expired (tokens are short-lived JWTs, typically 30 minutes). Start over from Step B-2.
