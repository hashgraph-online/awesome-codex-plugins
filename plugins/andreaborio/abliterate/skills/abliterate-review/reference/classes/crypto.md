# Cryptography and TLS misuse (CWE-327, CWE-328, CWE-330, CWE-329, CWE-295)

## Sources
- Not an input class: findings come from choices in code/config. Check what the primitive protects: passwords, session/reset tokens, signatures, stored sensitive data, transport to other services.
- Attacker influence matters where it exists: attacker-chosen algorithm/IV/mode parameters, predictable token inputs (time, counter, user id), attacker-controlled endpoint certificate.

## Sinks
| Concern | Smell | Safe alternative |
| --- | --- | --- |
| Weak randomness (330) | `Math.random()`, `random.random/randint`, `rand()`, `mt_rand`, `java.util.Random`, `math/rand`, `Date.now()`-seeded ids, UUIDv1/v4 from a non-CSPRNG, for tokens/OTP/reset/session/nonce | `crypto.randomBytes/randomUUID`, `secrets.token_urlsafe`, `random_bytes`, `SecureRandom`, `crypto/rand`, `SecureRandom.hex` |
| Weak hash (328) | `md5`, `sha1` for signatures, integrity, password storage; `==` on MACs | SHA-256+ for integrity, HMAC for MACs, password KDF (see authn-session.md) |
| Weak cipher/mode (327) | DES/3DES/RC4, AES-ECB (`AES/ECB/...`, `MODE_ECB`), CBC without MAC (padding oracle), home-made XOR/rot | AES-GCM or ChaCha20-Poly1305 via a high-level library (libsodium, Tink, `cryptography` Fernet) |
| Static/reused IV or nonce (329) | constant `iv = Buffer.alloc(16)`, IV derived from key/plaintext, GCM nonce reuse with the same key | fresh random IV/nonce per message, stored with the ciphertext |
| Key handling | key literal in code, key derived from a short passphrase with a fast hash, same key for encryption and signing | KMS/secret manager, KDF (scrypt/argon2/HKDF), separate keys per purpose |
| Disabled TLS verification (295) | Node `rejectUnauthorized: false`, `NODE_TLS_REJECT_UNAUTHORIZED=0`; Python `verify=False`, `ssl._create_unverified_context`, `CERT_NONE`; Go `InsecureSkipVerify: true`; Java trust-all `TrustManager`, `HostnameVerifier` returning true, `ALLOW_ALL_HOSTNAME_VERIFIER`; curl `-k`/`CURLOPT_SSL_VERIFYPEER=false`; Ruby `VERIFY_NONE` | verify with system or pinned CA; add the private CA to the trust store (`ca:` option, `REQUESTS_CA_BUNDLE`, `RootCAs`) |
| Signature checks | RSA PKCS#1 v1.5 encryption (padding oracle), compare with `==`, unauthenticated encryption | OAEP, constant-time compare, AEAD |

## Guards that work / Look-alike guards
Work:
- CSPRNG output of at least 128 bits for any secret token; stored hashed when it acts as a credential.
- Authenticated encryption with a random nonce per message; library-managed IV.
- Full certificate and hostname verification, with a custom CA added instead of disabling checks.
- TLS-skip flag gated to a test-only configuration that cannot be enabled by an env var in production builds.

Look-alike:
- `Math.random().toString(36)` "with extra characters" or concatenated with `Date.now()`.
- Hashing a predictable seed with SHA-256 (output looks random, input is guessable).
- Base64/hex presented as encryption; "AES" without stating the mode (ECB default in some APIs).
- Encrypt-then-hope: ciphertext without authentication, so tampering is undetected.
- `rejectUnauthorized: false` "only in dev" with no environment guard; `verify=False` hidden behind a settings default of False.
- Rotating the IV per process start but reusing it per message.

## Falsify before reporting
1. What does the primitive protect? `Math.random` for a UI animation id or A/B bucket is not a finding; for a reset token or session id it is.
2. Is the weak choice reachable in production, or only under a test/dev branch that production cannot enable? Read the condition and the config default.
3. Is the hash for passwords/credentials, or for a non-security checksum/cache key (md5 of a cache key is fine)?
4. Is there a compensating control on the same path: AEAD wrapper, transport already authenticated by another layer, token bound server-side?
5. TLS skip: is it a connection to an attacker-reachable network (internet, shared network) or loopback/same-pod? Does the call carry credentials or sensitive data?
6. Confirm: a test shows the generated token is not reproducible from a known seed/time, or the HTTP client in test mode rejects a self-signed certificate served by a local test server.

## Severity cues
- Raises: predictable reset/session tokens (account takeover), disabled TLS verification on calls carrying credentials, ECB/static IV on sensitive stored data, hardcoded key protecting many records.
- Lowers: non-security uses, loopback or intra-process TLS skip, defense-in-depth gaps where another authenticated layer exists, weak hash used only for cache keys.

## Regression test
- Tokens: generate 1,000 tokens and assert uniqueness, length at least 22 URL-safe chars (128 bits), and that the generator module imports the CSPRNG (or stub the CSPRNG and assert it is called).
- IV: encrypt the same plaintext twice; assert different ciphertexts and a ciphertext that fails decryption after a bit flip.
- TLS: point the client at a local test server with a self-signed certificate; assert the call fails; with the test CA configured it succeeds.
- Allowed case: existing stored data (old format) still decrypts or the migration path handles it.
