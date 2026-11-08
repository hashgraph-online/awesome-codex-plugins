# Consent and Privacy

Read this reference for any consent question, a PII question, a retention question, and the Korean privacy-policy disclosure check. It owns the Consent Mode v2 snippet and its ordering, basic versus advanced mode, the Tag Assistant check, the PII rules, retention, and the disclosure checklist.

The Korean section is a disclosure checklist for an implementation. It is not legal advice, and it does not decide whether a lawful basis exists for a particular site.

> Korean version: [`consent-and-privacy.ko.md`](consent-and-privacy.ko.md)

## Contents

- The consent default must precede the tag
- Parameters
- Region defaults
- Basic and advanced mode
- Verifying consent
- Personal data
- Retention
- Korean disclosure checklist

## The consent default must precede the tag

Call `gtag('consent', 'default', ...)` on every page, before any command that sends measurement data. Google states the failure mode plainly: "If your consent code is called out of order, consent defaults won't work."

A default that arrives after the tag has already sent a page view does not retroactively deny that page view. When the site has no consent platform, the default blocks storage until the user acts, and the report must say that the site now collects nothing from a user who never interacts with a banner.

## Parameters

```html
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}

  gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    wait_for_update: 500,
    region: ['ES', 'DE', 'FR', 'IT', 'NL', 'BE', 'AT', 'PL', 'SE', 'IE', 'DK', 'FI', 'PT', 'GR', 'CZ', 'RO', 'HU', 'SK', 'BG', 'HR', 'SI', 'LT', 'LV', 'EE', 'LU', 'MT', 'CY', 'IS', 'LI', 'NO', 'GB', 'CH'],
  });
  gtag('set', 'url_passthrough', true);
  gtag('set', 'ads_data_redaction', true);

  gtag('js', new Date());
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
```

Every one of the four Consent Mode v2 parameters appears above. The two ad parameters were added in November 2023, so a snippet carrying only `ad_storage` and `analytics_storage` predates v2 and is a finding.

| Parameter | What it controls |
|---|---|
| `ad_storage` | Cookies or local storage for advertising |
| `analytics_storage` | Cookies or local storage for analytics |
| `ad_user_data` | Sending user data related to advertising to Google |
| `ad_personalization` | Personalized advertising |

## Region defaults

- `region` takes ISO 3166-2 codes. A call carrying a region and a call without one can both exist, and "the one with a more specific region will take effect".
- When the request is silent on scope, write `denied` defaults for the EEA, the UK, and Switzerland and state that choice in the report. The list above is one concrete encoding: the 27 EU member states plus Iceland, Liechtenstein, and Norway for the EEA, then the UK and Switzerland. Keep it aligned with the site's actual market list.
- The correct pattern is a global default plus a stricter regional default, not one default that guesses.

## Basic and advanced mode

| Mode | What is sent before consent | Consequence |
|---|---|---|
| Basic | Nothing at all, "not even the consent status" | No modeling; every denied user is simply absent |
| Advanced | Cookieless pings | Behavioral and conversion modeling can fill part of the gap |

- Choose the mode from the request. When the request is silent, write the basic default and state the choice; switching to advanced changes what leaves the browser and is the site owner's decision.
- Advanced-mode modeling needs volume: at least 1,000 events per day with `analytics_storage='denied'` for at least 7 days, plus 1,000 granted daily users on 7 of 28 days. Never promise modeling on a low-traffic site.
- Modeled data does not reach Audiences, retention, BigQuery export, or predictive metrics.
- `url_passthrough` carries `gclid`, `dclid`, `gclsrc`, `_gl`, and `wbraid` across pages when cookies are denied.
- `ads_data_redaction` has no effect while `ad_storage` is granted, or when no consent command runs at all, so pairing it with granted defaults is decoration rather than control.

## Verifying consent

Tag Assistant is the check, not the banner's own state:

1. Open the page with Tag Assistant attached and start a debug session.
2. Find the Consent events. The earliest one is the on-page default and the latest one is the update.
3. Confirm all four parameters in the default event: `ad_storage`, `ad_personalization`, `ad_user_data`, `analytics_storage`.
4. Confirm the default appears before the first collection request, and that the update follows the user's action.

`gcs` encodes storage consent in the collection request, and `gcd` is sent whether or not consent mode is active. A request with `gcs` showing denied storage while a page view still counts is evidence that the default arrived too late.

## Personal data

- "Google prohibits customers from sending Personally Identifiable Information to Google Analytics."
- "Both the URL path and parameters must be free of PII." That covers `page_location`, `page_title`, query strings, and hash fragments.
- PII includes email addresses, full names and usernames, postal addresses, phone numbers, and precise location. An area smaller than 1 square mile, including latitude and longitude pairs, is prohibited. Pseudonymous cookie IDs and IP addresses are excluded from Google's definition; GA4 does not log or store IP addresses, so IP masking is not a GA4 task.
- `user_id` must be at most 256 characters, must not let a third party determine identity, must never be persisted in Analytics cookies, and should not be registered as a custom dimension.
- Data redaction in the interface is web-only, best-effort, and client-side. It does not cover Measurement Protocol or Data Import.
- An `api_secret` is private and must not appear in client-side code.
- When existing code may send a PII value, report it as a finding with the file and line, do not copy the value into the report, and propose a redaction or removal.

## Retention

- Standard properties offer 2 or 14 months of user-level retention, and event-level retention of 2, 14, or 26 months; 38 and 50 months are 360-only. Large and XL properties are forced to 2 months of event data.
- The 2-month period always applies to age, gender, and interest data.
- Deletion runs on a monthly cycle, and raising retention later can backfill data that still exists.
- Retrieved data feeds explorations and funnels; aggregated reports are unaffected.
- Lowering retention is an approval-tier action: state what is permanently deleted and that it cannot be restored, then wait.

## Korean disclosure checklist

This is a disclosure checklist for the implementation, not legal advice. Check each row against the site's actual processing and mark it present, missing, or not applicable, with the reason.

| Item | Provision | What the policy must state | GA4 hook |
|---|---|---|---|
| item 3 | 개인정보 보호법 제30조 제1항 제3호 | Third-party provision: the recipient, the purpose, the items, the retention period, and the right to refuse | Google LLC as a recipient when identifiers leave the site |
| item 4 | 개인정보 보호법 제30조 제1항 제4호 | Processing entrustment: the delegate and the scope of the entrusted work | An agency or vendor operating the tag on the site owner's behalf |
| item 7 | 개인정보 보호법 제30조 제1항 제7호 | "인터넷 접속정보파일 등 개인정보를 자동으로 수집하는 장치의 설치ㆍ운영 및 그 거부에 관한 사항" | The `_ga` and `_ga_<container-id>` cookies, what they collect, and how a visitor refuses |
| Overseas transfer | 개인정보 보호법 제28조의8 | The items transferred, the country, the timing and method, the recipient's name and contact, the purpose, the retention, and how to refuse | Collection in Google's overseas infrastructure |

Rules for this section:

- Use the article and item numbers above verbatim in the report, and quote the item 7 sentence as the law writes it.
- A policy that mentions cookies but not the refusal method fails item 7 as written.
- A policy that names Google only as an analytics tool without the recipient, purpose, items, and retention fails the overseas-transfer row.
- Report each row's state and the evidence for it. Do not write the policy text itself, and do not answer a question about whether consent is legally valid.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| The consent default runs on every page before any measurement command, out-of-order consent fails, and Consent Mode v2 added `ad_user_data` and `ad_personalization` in November 2023 | <https://developers.google.com/tag-platform/security/guides/consent> |
| Basic mode sends nothing before consent, advanced mode sends cookieless pings, `gcd` is always sent, and `gcs` encodes storage consent | <https://developers.google.com/tag-platform/security/concepts/consent-mode> |
| A more specific region takes effect; `url_passthrough` carries `gclid`, `dclid`, `gclsrc`, `_gl`, `wbraid`; `ads_data_redaction` needs `ad_storage` denied | <https://developers.google.com/tag-platform/security/guides/consent> |
| The earliest Consent event is the on-page default and the latest is the update; the four parameters are checked there | <https://developers.google.com/tag-platform/security/guides/consent-debugging> |
| Modeling needs 1,000 denied events per day for 7 days and 1,000 granted daily users on 7 of 28 days, and modeled data is absent from Audiences, retention, BigQuery export, and predictive metrics | <https://support.google.com/analytics/answer/11161109> |
| Google prohibits sending PII, and both the URL path and parameters must be free of it | <https://support.google.com/analytics/answer/6004245>, <https://support.google.com/analytics/answer/6366371> |
| Precise location under 1 square mile is prohibited, and IP addresses and pseudonymous IDs are excluded from the PII definition | <https://support.google.com/analytics/answer/7686480> |
| Data redaction is web-only and does not cover Measurement Protocol or Data Import | <https://support.google.com/analytics/answer/13544947> |
| `user_id` is at most 256 characters, must not identify a user to a third party, and should not be a custom dimension | <https://support.google.com/analytics/answer/9213390>, <https://support.google.com/analytics/answer/12675187> |
| Retention options, forced 2-month limits on Large and XL properties, and monthly deletion | <https://support.google.com/analytics/answer/7667196> |
| Privacy policy items 3, 4, and 7 of Article 30(1), in force 2026-09-11, Act No. 21445 | <https://www.law.go.kr/법령/개인정보보호법/제30조> |
| Overseas transfer disclosures in Article 28-8 | <https://www.law.go.kr/LSW/lsSideInfoP.do?lsiSeq=283839&joNo=0028&joBrNo=08&docCls=jo> |
| The `api_secret` is private and must not be exposed in client-side code | <https://developers.google.com/analytics/devguides/collection/protocol/ga4/sending-events> |

### Evidence grade

`MEASURED` for the quoted sentences, the parameter names, the thresholds, the retention options, and the article numbers, from the pages above read on 2026-11-08. `LOCAL` for the checklist rows, the region list encoding, and the instruction to write `denied` defaults when the request is silent; those are this package's design. The statute was read at its in-force revision (2026-09-11) and this section deliberately stops at disclosure content, so it does not constitute legal advice.
