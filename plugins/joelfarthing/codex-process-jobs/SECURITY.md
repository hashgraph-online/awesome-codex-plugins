# Security: hook-free candidate

This experimental marketplace package registers no hooks and includes no hook scripts. The source checkout retains historical hook tests; those files are excluded from the ZIP. No installer or hook approval is required by this package.

CPJ starts commands with argv arrays unless explicit shell mode is selected. It validates saved job state and process identity before cancellation. Logs are bounded. Process output, command arguments, and job labels are untrusted data. A completion notice contains only validated identifiers, terminal status, exit code, and fixed result-handling instructions. The result skill retrieves output separately and treats it as untrusted evidence.

The worker starts a separate notification relay. Local delivery uses the existing queue and fallback transports. Host authentication and permissions remain host-controlled. A missing local lifecycle for a cloud Work owner does not authorize a private cloud callback or a live queue probe.

Without hooks, an ordinary later prompt does not automatically recover a missed completion. Skill instructions retain the launch-turn and delegation boundaries without hook enforcement. A live local canary is required before treating this candidate as release-ready.

Report suspected vulnerabilities privately to info@filamentlabs.io. Do not include credentials or sensitive output.
