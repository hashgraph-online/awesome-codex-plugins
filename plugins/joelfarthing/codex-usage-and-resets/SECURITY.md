# Security

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Email
<info@filamentlabs.io> with the affected CUAR version, operating system,
reproduction steps, and potential impact. Do not include credentials, tokens,
raw App Server responses, or account-specific usage data.

## Trust boundaries

CUAR runs as local code with the same operating-system account and execution
constraints as Codex. It is not a privilege boundary.

The normal runtime resolves `codex` through the inherited `PATH`, starts
`codex app-server --stdio` without a shell, initializes the stable protocol,
and sends only `account/rateLimits/read`. It does not send thread, turn, login,
logout, write, nudge, or reset-consumption methods.

CUAR writes only its bounded local reset ledger. It creates the ledger
directory with user-only permissions when possible, writes the file with mode
`0600`, uses a same-directory temporary file and atomic rename, and serializes
cooperating CUAR processes with a short-lived directory lock. Symlinked ledger,
lock, and final cache-directory paths are rejected. The ledger is derived
cache data, not an authentication or account-identity boundary. CUAR uses only
one fixed-name temporary file, removes interrupted temporary writes before the
next transaction, and invalidates its comparison chain after an untrustworthy
report.

`CUAR_CODEX_BIN` is an explicit support-and-test override. Setting it delegates
the same trust to that absolute executable path, so users should not point it
to untrusted code.

`CUAR_TEST_MODE=1` enables the fixture-only `CUAR_TEST_FETCHED_AT` clock
override. These variables can deliberately make a report non-current and must
not be enabled for ordinary use. `CUAR_LEDGER_PATH` is an absolute-path
support-and-test override; in test mode, ledger writes are disabled unless that
override is explicitly supplied. CUAR's bundled skill never sets these
variables.

App Server stdout is treated as untrusted structured input. JSONL lines,
stderr, timeouts, response envelopes, and child cleanup are bounded. Raw
responses and operating-system errors are not copied into public CUAR output.

## Operational limitations

- A malicious process already running as the same user can alter executables,
  environment variables, or local Codex state.
- CUAR projections assume the current average burn continues; they are
  planning estimates, not guarantees.
- Reset observation cannot distinguish every unscheduled OpenAI reset from an
  account switch or coincident banked-reset change.
- OpenAI may change supported App Server behavior independently of CUAR.
- The initial release targets local Codex surfaces with Node.js and shell
  execution available; it does not claim ChatGPT web-only support.
