---
name: sw-session-reporter
description: Finish a SolidWorks task by invoking sw-learner, honoring the saved feedback preference, asking the exact three-option consent question when required, and submitting validated feedback with retries. Use after the CAD result has been delivered for every task that involved SolidWorks modeling, API work, generated CAD code, engineering decisions, or debugging.
---

# SolidWorks Session Reporter

Run after delivering the CAD result. Do not run for a conversation with no
SolidWorks work.

Resolve the plugin root from this skill so the scripts below work regardless
of the user's current working directory.

## 1. Build the payload

Invoke `$sw-learner`. Stop silently if it reports no relevant SolidWorks work.
Validate the private `.sw-feedback-payload.json` file before any consent or
submission.

## 2. Check the preference

Run:

```text
python <plugin-root>/scripts/sw_session.py preference show
```

If the result is exactly `always`, skip the prompt and submit immediately. Any
other result requires consent.

## 3. Ask consent

Ask exactly this as the final message and wait for the user's reply:

```text
Share this session's SolidWorks knowledge with the knowledge base?

1. Yes, send now
2. Always send
3. Skip this session
```

Do not show the payload. Do not ask another question. Do not add closing text
after the options.

## 4. Handle the reply

- `Yes, send now`: submit this payload once through the retrying utility.
- `Always send`: first run `scripts/sw_session.py preference always`, then
  submit this payload. This choice authorizes automatic submissions in later
  SolidWorks tasks until the preference is cleared.
- `Skip this session`: do not POST. Run `scripts/sw_session.py cleanup` to
  remove the temporary payload.

Do not interpret ambiguous replies as consent. Repeat only the same three
options if necessary.

## 5. Submit

Run:

```text
python <plugin-root>/scripts/submit_feedback.py .sw-feedback-payload.json
```

The utility validates required fields, removes empty arrays, uses quoted curl
transport, retries server errors or timeouts up to three times with about two
seconds between attempts, stops immediately on `4xx`, and writes the returned
feedback ID to `.sw-learner-state.json`.

After success, run `scripts/sw_session.py cleanup`. Report only the returned
feedback ID. If the server rejects or never accepts the payload, do not expose
raw server data or bother the user; leave the CAD result unchanged and clean up
the temporary payload.
