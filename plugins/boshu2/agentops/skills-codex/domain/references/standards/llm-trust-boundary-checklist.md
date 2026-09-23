# LLM Trust Boundary Checklist

Domain-specific checklist for code that calls LLM APIs or processes LLM outputs.

## Mandatory Checks

### Input Validation
- [ ] User-supplied prompts are sanitized (no prompt injection vectors)
- [ ] System prompts are not exposed to end users
- [ ] Prompt templates use parameterized injection points, not string concatenation
- [ ] Input length limits enforced before API call (prevent token budget exhaustion)

### Output Validation
- [ ] LLM output is validated against expected schema before use
- [ ] JSON responses are parsed with strict schema validation (not just `json.loads()`)
- [ ] Hallucinated field names/values are detected and rejected
- [ ] Output is never used as code input without sandboxing (`eval()`, `exec()`, shell commands)
- [ ] Empty responses handled explicitly (not silently passed through)

### Error Handling
- [ ] API timeout has explicit handling (retry with backoff)
- [ ] Rate limit (429) has backoff strategy
- [ ] Model refusal detected and handled (not treated as valid output)
- [ ] Malformed response has retry-with-stricter-prompt fallback
- [ ] Cost/token budget tracked per request (prevent runaway spending)

### Trust Boundaries
- [ ] LLM output treated as untrusted input at every boundary
- [ ] No direct database writes from LLM output without validation
- [ ] No file system operations from LLM output without path validation
- [ ] No network requests to LLM-generated URLs without allowlist check
- [ ] User-visible LLM output has content safety filtering

### Observability
- [ ] Request/response pairs logged (with PII redaction)
- [ ] Token usage tracked per call and per session
- [ ] Latency metrics captured (p50, p95, p99)
- [ ] Retry counts and failure modes tracked
- [ ] Model version pinned and logged (not just "latest")

### Testing
- [ ] Tests cover malformed response handling
- [ ] Tests cover empty response handling
- [ ] Tests cover refusal handling
- [ ] Tests use deterministic fixtures, not live API calls
- [ ] Evaluation suite exists for output quality regression

## When to Apply

Load this checklist when:
- Changed files import `anthropic`, `openai`, `google.generativeai`, or similar
- Code constructs prompts or processes LLM responses
- Plan includes LLM integration or AI-powered features
- Files match patterns: `*llm*`, `*ai*`, `*prompt*`, `*completion*`, `*chat*`
