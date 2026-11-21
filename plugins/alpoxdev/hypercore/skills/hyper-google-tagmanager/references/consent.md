# Consent

Read this file whenever the site serves users who must consent, the container has consent settings, or a finding is about consent. Facts marked `volatile` change with Google's consent products and with privacy law. Legal rows are a checklist for what the implementation must disclose, not legal advice.

## Contents

- 1. Consent Mode v2
- 2. Defaults before measurement
- 3. Consent in the container
- 4. CMP wiring
- 5. Verification
- 6. Korean privacy-policy items
- Sources

## 1. Consent Mode v2

| Type | Controls |
|---|---|
| `ad_storage` | Advertising cookies and storage |
| `analytics_storage` | Analytics cookies and storage |
| `ad_user_data` | Sending user data to Google for advertising (added November 2023) |
| `ad_personalization` | Personalized advertising (added November 2023) |
| `functionality_storage`, `personalization_storage`, `security_storage` | Non-Google storage purposes a CMP or template can map |

- Basic mode: Google tags do not load or send anything until the user consents.
- Advanced mode: tags load with `denied` defaults and send cookieless pings, which GA4 uses for behavioral modeling once a property has enough denied traffic (`volatile`; about 1,000 denied events a day for 7 days).
- Choose the mode with the user; it changes what is collected before consent, so a change on a live site is approval tier (`rules/safety-gates.md` §1).

## 2. Defaults Before Measurement

"If your consent code is called out of order, consent defaults won't work." The default must run on every page before any measurement command.

```html
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('consent', 'default', {
  ad_storage: 'denied',
  ad_user_data: 'denied',
  ad_personalization: 'denied',
  analytics_storage: 'denied',
  wait_for_update: 500
});
</script>
<!-- then the container snippet -->
```

- In a GTM install the sanctioned path is a consent template (the CMP's Community Template Gallery template, or a custom template) on **Consent Initialization - All Pages**, which "will always fire before all other tags, including any Initialization triggers", calling `setDefaultConsentState` and later `updateConsentState`. "Don't create templates that use the `gtag consent` command." The page-code block above is the fallback when no template is possible; it must then sit above the container snippet.
- Always set a default. Unset consent behaves as granted, so a page that only sends `update` measures before the choice. Any value other than `'granted'` is treated as `'denied'`.
- Regional defaults: one default per region list (`region: ['KR']`); the most specific region wins and a default without `region` covers everyone else.
- `wait_for_update` (milliseconds) makes tags wait for the CMP's update before firing.
- Update after the user's choice: `updateConsentState` in a template, or `gtag('consent', 'update', {...})` in the page-code fallback.
- `ad_user_data` is required for ads measurement uses (enhanced conversions, conversion tracking); both `ad_user_data` and `ad_personalization` must be granted for personalized advertising.
- `url_passthrough: true` (`gtag('set', 'url_passthrough', true)`) keeps ad click identifiers in URLs when storage is denied; `ads_data_redaction: true` has effect only when `ad_storage` is denied.
- The Google tag's **Set consent mode override** setting (`volatile`, since 2024-08-28) forces `denied` defaults for chosen regions when the code order cannot be fixed.
- Never set consent in a Custom HTML tag: gtag commands queue behind pending dataLayer messages, so tags fired by the same event can see different consent states.

## 3. Consent in the Container

- Turn on Admin > Container Settings > **Enable consent overview** to see every tag's consent state in one place.
- Each tag has **Consent Settings**: built-in consent checks (Google tags read the consent types themselves), **No additional consent required** (`notNeeded`), or **Require additional consent for tag to fire** (`needed`) with the consent types listed. `notSet` means nobody decided.
- Do not add **Require additional consent** to Google tags that have built-in checks: "If you have implemented consent mode and use additional consent checks at the same time, they won't work properly", because a blocked tag does not fire again when consent is granted later.
- Non-Google tags (Meta, TikTok, Hotjar, Custom HTML) have no built-in checks: set `needed` with the matching types, or they fire before consent.
- Custom templates set and read consent with `setDefaultConsentState`, `updateConsentState`, `isConsentGranted`, and `addConsentListener`; templates declare the `access_consent` permission.
- `scripts/gtm-container-audit.sh` reports `CONSENT_NOT_SET` per tag and `NO_CONSENT_INIT` when nothing fires on Consent Initialization.

## 4. CMP Wiring

- Load the consent banner in page code or as the CMP vendor's own script, not as a tag inside GTM: "some users block tag managers", and a banner delivered by GTM then disappears.
- Publishers serving personalized ads through Google's ad products to users in the EEA and the UK (since 2024-01-16) and Switzerland (since 2024-07-31) must use a Google-certified CMP integrated with the IAB TCF. Advertisers must obtain consent under Google's EU user consent policy; Google's CMP Partner badge lists integrated vendors but "adopting any of these partners" does not guarantee compliance (`volatile`).
- Recommend one CMP and ask once before choosing a vendor; adding a vendor is approval tier.
- A CMP with a Community Template Gallery template should use it, on the Consent Initialization trigger.

## 5. Verification

- Tag Assistant **Consent** tab: read the **On-page Default** and **On-page Update** columns; the earliest consent event is the default, the latest is the update. Check before and after clicking the banner. The tab shows the four consent-mode types only.
- `/g/collect` requests carry the consent state in `gcs` (`ad_storage` and `analytics_storage`) and `gcd`; a request before consent with `analytics_storage` denied must be a cookieless ping in advanced mode or absent in basic mode.
- `scripts/gtm-site-check.sh` reports `CONSENT_AFTER_LOADER` when the default appears after the loader in served HTML.
- DebugView shows no events when analytics consent was not given; an empty DebugView with a CMP active is not a broken install.
- Tag Diagnostics flags "Consent mode installation out of order" and "0% consent rate detected".

## 6. Korean Privacy-Policy Items

For sites serving Korean users, the privacy policy must state (개인정보 보호법 제30조 제1항):

- the installation, operation, and refusal of automatic collection devices such as cookies (제7호, "인터넷 접속정보파일 등 개인정보를 자동으로 수집하는 장치의 설치ㆍ운영 및 그 거부에 관한 사항")
- provision to third parties (제3호) and entrusted processing (제4호), which covers Google as the analytics processor
- overseas transfer details (제28조의8) when data goes to Google's servers abroad

Report missing items as findings for the policy owner; the skill does not write legal text. The 개인정보보호위원회 privacy-policy guideline (2026-04) treats third-party 행태정보 disclosure as recommended where it applies and notes fines of up to 10 million won for not publishing a policy (`volatile`).

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Consent types, defaults before measurement, order rule, `wait_for_update`, `region` | <https://developers.google.com/tag-platform/security/guides/consent> |
| Basic and advanced mode | <https://developers.google.com/tag-platform/security/concepts/consent-mode> |
| Behavioral modeling thresholds | <https://support.google.com/analytics/answer/11161109> |
| Consent debugging in Tag Assistant | <https://developers.google.com/tag-platform/security/guides/consent-debugging> |
| Consent settings, consent overview, Consent Initialization order, ad consent types | <https://support.google.com/tagmanager/answer/10718549>, <https://support.google.com/tagmanager/answer/13802165> |
| Template consent APIs and the `gtag consent` prohibition in templates | <https://developers.google.com/tag-platform/tag-manager/templates/consent-apis>, <https://developers.google.com/tag-platform/tag-manager/templates/api> |
| Additional consent checks on Google tags | <https://support.google.com/tagmanager/answer/12962079> |
| Certified TCF CMP for publishers; EU user consent policy | <https://support.google.com/adsense/answer/13554116>, <https://www.google.com/about/company/user-consent-policy/> |
| No consent through Custom HTML | <https://developers.google.com/tag-platform/devguides/datalayer> |
| Consent mode override setting | <https://support.google.com/tagmanager/answer/4620708> |
| Tag managers blocked by users | <https://web.dev/articles/tag-best-practices> |
| Korean privacy-policy items | <https://www.law.go.kr/법령/개인정보보호법/제30조>, <https://www.law.go.kr/LSW/lsSideInfoP.do?lsiSeq=283839&joNo=0028&joBrNo=08&docCls=jo> |

### Evidence grade

Official Google documentation, the Korean statute text (시행 2026-09-11), and the PIPC guideline PDF (pages 9, 14-15) read 2026-11-08. Google's own pages disagree on what advanced mode does with no default; this file follows the template API rule (unset is granted). The CMP requirements and the override setting change with Google's policy; recheck them before relying on them.
