# Caveats And Troubleshooting

Use this file to keep responses grounded in the bundled AlphaGenome README.

## Capability and scale limits

- Treat AlphaGenome as suitable for small to medium analyses.
- Expect the API to handle thousands of predictions more comfortably than very large production-scale workloads.
- Push back on plans that require more than 1,000,000 predictions, because the README says the API is likely not suitable at that scale.
- For `predict_variant(...)`, use a supported sequence length (currently `16384`, `131072`, `524288`, or `1048576` bp).
- Keep each DNA sequence request at or below 1,000,000 base pairs.

## Licensing and access

- Assume non-commercial use unless the user says they have another arrangement.
- Remind the user that the API requires an API key.
- Point the user to official terms or documentation when the task has compliance implications.

## Common failure checks

Run these checks in order:

1. Verify the package is installed in the active Python environment.
2. Verify the Python runtime is `>=3.10`.
3. Verify the API key is present and passed to `dna_client.create(...)`.
4. Verify chromosome names, coordinates, and allele strings.
5. Verify the interval width is supported by the model (common error: `Sequence length ... not supported`).
6. Reduce `requested_outputs` to the smallest needed set.
7. Re-check whether an `ontology_terms` value is required for the selected assay.

## Connectivity and proxy checks

- If API calls hang during client creation or prediction, verify outbound connectivity to Google endpoints.
- Fast preflight for gRPC endpoint reachability:
  - `python - <<'PY'`
  - `import socket; s=socket.socket(); s.settimeout(5); s.connect(('gdmscience.googleapis.com', 443)); print('ok')`
  - `PY`
  - If this times out, treat direct egress as blocked and switch to proxy.
- In restricted networks, set proxy variables before running Python:
  - `grpc_proxy=http://127.0.0.1:7890`
  - `http_proxy=http://127.0.0.1:7890`
  - `https_proxy=http://127.0.0.1:7890`
- Prefer lowercase proxy variable names for gRPC compatibility.
- Typical timeout signature to match in logs:
  - `grpc.FutureTimeoutError` during `dna_client.create(...)`.

## Conservative guidance

- Do not invent unsupported helper functions or output enums.
- Confirm symbols that are not listed in the skill's grounded API surface before using them.
- Prefer a short working example over a broad but speculative code sample.
- Do not print or persist raw API keys in code snippets, logs, or docs.
