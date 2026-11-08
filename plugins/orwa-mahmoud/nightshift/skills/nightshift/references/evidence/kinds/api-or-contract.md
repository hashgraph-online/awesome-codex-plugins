# API or contract — items that change a request, a response, or a schema

## When it applies

An item that changes a request, a response, or a schema someone else calls.

## Evidence lines

- A sample request and response, and the schema diff. For a breaking change, the old and new shape side by side.

## How to generate

Save a sample request as `request.json` and a sample response as `response.json` in the item's evidence folder, `receipts/<NN>-<slug>-<id>/`. Save the schema diff as `schema.diff` in that same folder. For a breaking change, the diff shows the old shape and the new shape side by side.

## How to verify

The sample is a real request and the response it produces. The diff matches that sample. A breaking change shows both shapes, not only the new one.

```evidence-check
files: *.json
min: 1
type: json
```

## Never

No secrets, tokens, or personal data in the sample. No live credential, session cookie, or real customer's payload.
