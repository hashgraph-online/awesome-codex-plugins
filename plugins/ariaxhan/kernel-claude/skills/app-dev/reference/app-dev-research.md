---
date: 2026-05-28
topic: app-dev deep reference
scope: EAS/Expo build pipeline, store submission, environment patterns, anti-patterns
---

# App Dev — Deep Reference

Consult this file when you need rationale, examples, or tooling surveys.
The executable flow lives in `../SKILL.md`.

---

## Build Pipeline Architecture

```
LOCAL DEV -> STAGING -> PRODUCTION
   |            |           |
   v            v           v
 hot reload   OTA test    store build
 simulators   TestFlight   full review
 dev API       staging API  prod API
```

Each environment gets its own:
- API endpoints (never hardcode — use env configs)
- Signing credentials (dev, staging, prod keystores)
- Feature flags (staging can enable experimental features)
- Analytics keys (separate dev/prod to avoid polluting data)

---

## EAS Build Profiles — Example eas.json

```json
{
  "build": {
    "development": { "distribution": "internal", "ios": { "simulator": true } },
    "preview": { "distribution": "internal" },
    "production": { "autoIncrement": true }
  }
}
```

---

## OTA Updates (EAS Update) — Patterns and Pitfalls

- Use `eas update` for JS-only changes (no native code changes).
- Runtime version pinning: tie OTA updates to compatible native builds.
- **Never push OTA updates that require native changes — this crashes apps.**
- Channel strategy: `production`, `staging`, `preview` channels.
- Rollback: `eas update:rollback` to revert bad OTA pushes.

---

## Environment Config Patterns

- Use `app.config.js` (dynamic) over `app.json` (static) for environment switching.
- Expo Constants for runtime env detection.
- EAS secrets for build-time environment variables.
- Never commit `.env` files — use EAS secrets or CI/CD env vars.

---

## Source Files to Load at Start

Project-specific build configs vary. Check these locations:
- `eas.json` or `eas.config.js` — EAS build profiles
- `app.config.js` or `app.json` — Expo configuration
- `fastlane/Fastfile` — if using Fastlane for native builds
- `android/app/build.gradle` — Android build config
- `ios/*.xcodeproj` or `ios/*.xcworkspace` — iOS project
- CI/CD config (`.github/workflows/`, `bitrise.yml`, etc.)

If none exist, this is likely a new project — scaffold from EAS defaults.

---

## iOS Store Submission — Detail

1. **TestFlight**: internal testing first, then external beta.
2. **App Store Review**: 24-48 hours typical. Plan for rejection cycles.
3. **Required metadata**: screenshots (6.7", 6.5", 5.5"), description, keywords, privacy URL.
4. **Privacy manifests** (required since Spring 2024): declare all API usage reasons.
5. **Signing**: use automatic signing in EAS. Manual = pain.

## Android Play Console Submission — Detail

1. **Internal testing**: fastest approval, limited testers.
2. **Closed/open testing**: broader beta before production.
3. **Production rollout**: staged rollout (start 5-10%, watch crash rates).
4. **Required metadata**: feature graphic, screenshots, descriptions, content rating.
5. **Data safety form**: declare all data collection and sharing.

---

## Anti-Pattern Rationale

| Anti-pattern | Why it hurts |
|---|---|
| Hardcoded API keys in builds | Keys in source = revoked keys. Use EAS secrets or env configs. |
| Skip store review guidelines | Rejection wastes days. Read the guidelines before submitting. |
| Deploy without physical device testing | Simulators miss real-world issues (memory, GPS, camera). |
| OTA for native changes | OTA is JS-only. Native changes need a new store build. |
| Ignore staged rollout | Going 0 to 100% is reckless. Start at 5-10%. |
| Same signing certs for dev and prod | Separate keystores per environment. |
| Skip TestFlight/internal testing | Internal testers catch what automated tests miss. |
