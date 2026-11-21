# Adding TweetAPI to an app

Look up the exact endpoint and parameters in the current docs before writing code ([sources.md](sources.md)), and use only endpoints that work without an X login.

## Call it from the server

Read the key from `TWEETAPI_API_KEY` on the server, and stop with a clear error if it's missing. The key must never reach a browser or mobile client.

```ts
const apiKey = process.env.TWEETAPI_API_KEY;

if (!apiKey) {
  throw new Error("TWEETAPI_API_KEY is not configured");
}

const url = new URL("https://api.tweetapi.com/tw-v2/user/by-username");
url.searchParams.set("username", username);

const response = await fetch(url, {
  headers: { "X-API-Key": apiKey },
  signal: AbortSignal.timeout(15_000),
});

if (!response.ok) {
  throw new Error(`TweetAPI request failed with status ${response.status}`);
}

const { data: user } = await response.json();
```

This makes one request. Validate `username` before sending it, and keep request headers and whole responses out of the logs.

## Use an SDK

- Node.js: `npm install tweetapi-node`, source at <https://github.com/tweetapi/node>
- Python: `pip install tweetapi`, source at <https://github.com/tweetapi/python>

Check a method in the SDK's README before using it, because method names don't always match endpoint paths. Use the read methods only: the SDKs also cover account actions and DMs, which are out of scope.

Both SDKs retry a failed read up to 3 times by default, after a 429, a 5xx or a network error. 429 and 5xx responses aren't billed, but a retry after a network error can be, if the first attempt reached TweetAPI. To turn retries off, pass `retry: false` in Node or `max_retries=0` in Python.

The pagination helpers (`paginate` and `paginatePages` in Node, `paginate` and `paginate_pages` in Python) keep requesting pages until the cursor runs out. Always give them a limit: `maxPages` in Node, `max_pages` in Python.

## Paging in your own code

Return the first page and its cursor by default. If the feature needs more, cap the pages and requests, add a timeout, and show the user when results are partial or the units run out.

## Test without spending units

- Mock TweetAPI's HTTP responses in tests.
- Cover a success, a 401 or 403, a 429, a validation error, a timeout and a malformed response.
- Check that the API key never shows up in errors or logs.
- Keep live calls out of unit tests, CI, previews and builds.

## Generate a client from the spec

The published contract is <https://tweetapi.com/openapi-v2.json> (OpenAPI 3.0.3). The Postman collections are generated from it: <https://tweetapi.com/postman-v2.json> holds every endpoint, and <https://tweetapi.com/postman-quickstart-v2.json> holds three public reads to start with. The spec covers the whole API, writes included, so generate or keep only the operations marked `"x-tweetapi-safety": "read-only"`.
