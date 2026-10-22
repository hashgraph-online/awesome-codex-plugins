# Security policy

Please report credential-handling or profile-isolation issues privately through
GitHub Security Advisories for this repository. Do not attach `auth.json`, access
tokens, refresh tokens, or diagnostic output containing credentials.

Masaka deliberately keeps one Codex-owned `CODEX_HOME` per account/workspace
profile. It does not copy credentials into its index and never replaces the
user's global `~/.codex/auth.json`. Profile credentials use Codex's documented
file store and owner-only filesystem permissions; they are not additionally
encrypted by Masaka.
