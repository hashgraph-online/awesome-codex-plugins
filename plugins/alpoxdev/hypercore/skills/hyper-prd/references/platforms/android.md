# Android Platform Checklist

Load this file only when the PRD's decided platforms include `android`; fill the platform requirements block and its release gate table. Each item carries an id, a grade, the sentence or table the PRD must contain, the source, and the date it was checked. An item whose answer is not in the repository or the conversation becomes `[확인 필요: ...]` in the PRD; it does not become a guess.

## Contents

- Grades
- Target API level
- Data safety
- Permissions
- Billing
- Publishing format
- Performance and usability
- Shared data-collection matrix
- Filling the release gate table
- Sources

## Grades

| Grade | Meaning | What the PRD owes |
|---|---|---|
| `[M]` | Enforced by Google Play policy or by law; a wrong or missing answer blocks the release | One conclusion in the release gate table |
| `[M-조건]` | Enforced only when the stated condition holds | One conclusion: applies, or not applicable with the condition named |
| `[G]` | Recommended; the store does not reject the app for missing it | Recorded only when the item matters to this product |

Every `[M]` and `[M-조건]` item in this file gets its own row in the PRD release gate table. The value of an item is a conclusion, not a restatement of the policy: `applies`, `not applicable` with the reason, or `[확인 필요]`. A sentence such as "follow the Play policies" is not a conclusion and is rejected in review.

## Target API level

| Id | Grade | What the PRD records | Source | Checked |
|---|---|---|---|---|
| A1 | `[M]` | The target API level the build declares (the `targetSdk` value) for the first release and for every later update, and the date that decision is re-checked. From 2026-08-31, new apps and app updates must target Android 16 (API level 36) or higher. A release that ships before that date may target a lower level, but the PRD names the level either way. | [Target API level](https://support.google.com/googleplay/android-developer/answer/11926878) | 2026-11-07 |

## Data safety

| Id | Grade | What the PRD records | Source | Checked |
|---|---|---|---|---|
| A2 | `[M]` | The completed Data safety declaration, including the case of no collection: the form is required even when the app collects no user data, so the PRD states the declaration as "no data collected" instead of leaving the item open. | [Provide information for Google Play's Data safety section](https://support.google.com/googleplay/android-developer/answer/10787469) | 2026-11-07 |
| A3 | `[M]` | For each data type the declaration names: collected or not, shared or not, purpose, whether it is optional, and whether it is processed ephemerally. The declared set equals the set the release actually handles. | [Provide information for Google Play's Data safety section](https://support.google.com/googleplay/android-developer/answer/10787469) | 2026-11-07 |

## Permissions

| Id | Grade | What the PRD records | Source | Checked |
|---|---|---|---|---|
| A4 | `[M]` | The rule the permission list is judged by: only permissions necessary to implement current features or services that the store listing promotes. A permission for a planned or hidden feature is a policy violation, so the PRD does not reserve permissions for later. | [Permissions and APIs that Access Sensitive Information](https://support.google.com/googleplay/android-developer/answer/9888170) | 2026-11-07 |
| A5 | `[M]` | A mapping table with one row per runtime permission: permission, the current feature that needs it, the listing text or screenshot that promotes that feature, and the screen where the request appears. A permission with no promoted feature in the same row is removed from scope or the feature is added to the listing plan. | [Permissions and APIs that Access Sensitive Information](https://support.google.com/googleplay/android-developer/answer/9888170) | 2026-11-07 |
| A6 | `[M-조건]` | Condition: the app requests a permission that Play treats as sensitive or restricted. The PRD then names the declared use case and the review evidence for it, because the declaration is reviewed before the release is accepted. Without such a permission the row reads "not applicable". | [Permissions and APIs that Access Sensitive Information](https://support.google.com/googleplay/android-developer/answer/9888170) | 2026-11-07 |

## Billing

| Id | Grade | What the PRD records | Source | Checked |
|---|---|---|---|---|
| A7 | `[M-조건]` | Condition: the app sells digital goods or digital services inside the app. The PRD then states that the purchase runs through Play's billing system, and lists every paid item with its price, billing period, and what the buyer receives. Physical goods, physical services, and content consumed outside the app fall outside this row and say so. | [Payments policy](https://support.google.com/googleplay/android-developer/answer/10281818), [Play Billing integration](https://developer.android.com/google/play/billing/integrate) | 2026-11-07 |
| A8 | `[M-조건]` | Condition: the app uses Play Billing. The Billing Library version is then 8 or later, because all new apps and updates to existing apps must use version 8 or later by 2026-08-31. The PRD names the chosen version and the date it is re-checked. | [Play Billing integration](https://developer.android.com/google/play/billing/integrate) | 2026-11-07 |

## Publishing format

| Id | Grade | What the PRD records | Source | Checked |
|---|---|---|---|---|
| A9 | `[M]` | The published artifact format: an Android App Bundle (AAB, `.aab`) uploaded to Play, not an APK. The PRD also records which delivery split the app relies on for the size or feature goal, if any. | [Android App Bundles](https://developer.android.com/guide/app-bundle) | 2026-11-07 |

## Performance and usability

| Id | Grade | What the PRD records | Source | Checked |
|---|---|---|---|---|
| A10 | `[G]` | The stability floor and how it is read: user-perceived crash rate at or below 1.09% and ANR rate at or below 0.47%, the bad-behavior thresholds Play shows for an app version. Measurement method: Play Console > Android vitals, per app version, for the reporting window the console displays. The PRD copies the metric names from the console rather than restating the denominator by memory. | [Android vitals](https://developer.android.com/topic/performance/vitals) | 2026-11-07 |
| A11 | `[G]` | A sentence that every interactive control has a touch target of at least 48 dp. Measurement method: read each control's layout bounds in dp on a device or in the layout inspector, at one compact and one large screen size. A target smaller than 48 dp is recorded with the control name and the planned size. | [Core app quality](https://developer.android.com/docs/quality-guidelines/core-app-quality) | 2026-11-07 |

A numeric item states three things: the threshold with its unit, the measurement method that produces the number, and the population or window the number covers. A percentile-based metric names the percentile (`@p75`); the two vitals thresholds here are rates over the console reporting window rather than percentiles, so they name that window instead. An item written as "stable" or "large enough" without all three is not a requirement.

The collected sources record no clause number for these Play pages, so each row cites the page by its title and URL and quotes the sentence that binds. A page title alone does not say what the rule is.

## Shared data-collection matrix

When the decided platforms include both iOS and Android, write the matrix once and read it from two directions. Writing it twice lets the two statements drift, and the two stores then receive different descriptions of the same behavior.

| Data type | Collected | Shared with third parties | Linked to the user's identity | Used for tracking | Purpose | Optional | Ephemeral |
|---|---|---|---|---|---|---|---|

- The iOS privacy label row and the Play Data safety row both resolve from this table; neither restates the data types from memory.
- A data type that one platform collects and the other does not is a product decision, not a declaration detail: record the difference and its reason in the PRD.
- A type the release handles but the table omits is a defect in the table. Fix the table before filling either store form.

## Filling the release gate table

| Column | Content |
|---|---|
| ID | The item id from this file, for example `A1` |
| Grade | The grade copied from this file, unaltered |
| Item | The obligation in one short sentence, with the threshold, measurement method, and percentile for a numeric item |
| Conclusion | `applies`, `not applicable` with the condition or reason, or `[확인 필요: <question>]` |
| Evidence | The document, console screen, or measurement that settles the conclusion |
| Re-check | The date the dated value is checked again, or `none` for undated items |

A `[M]` row whose conclusion is `[확인 필요]` keeps the PRD at `status: draft`. The dated values in this file are store policy values: they change when Google Play revises the policy, so re-check every dated row each quarter and after any store notice.

## Sources

> Checked 2026-11-07.

| Source | What it settles | Quote |
|---|---|---|
| [Target API level](https://support.google.com/googleplay/android-developer/answer/11926878) | A1 | "Starting August 31, 2026: New apps and app updates must target Android 16 (API level 36) or higher" |
| [Data safety](https://support.google.com/googleplay/android-developer/answer/10787469) | A2, A3 | "Even developers with apps that do not collect any user data must complete this form" |
| [Permissions and APIs that Access Sensitive Information](https://support.google.com/googleplay/android-developer/answer/9888170) | A4, A5, A6 | "You may only request permissions ... that are necessary to implement current features or services in your app that are promoted in your Google Play listing." |
| [Payments policy](https://support.google.com/googleplay/android-developer/answer/10281818) | A7 | Policy page for in-app digital goods; the research file recorded the URL without an extract. |
| [Play Billing integration](https://developer.android.com/google/play/billing/integrate) | A7, A8 | "By Aug 31, 2026, all new apps and app updates to existing apps must use Billing Library version 8 or later." |
| [Android App Bundles](https://developer.android.com/guide/app-bundle) | A9 | The publishing-format page; the research file recorded the URL without an extract. |
| [Android vitals](https://developer.android.com/topic/performance/vitals) | A10 | Bad-behavior thresholds: user-perceived crash rate 1.09%, ANR rate 0.47%. |
| [Core app quality](https://developer.android.com/docs/quality-guidelines/core-app-quality) | A11 | "Touch targets are at least 48 dp." |

### Evidence grade

`QUOTED` - the items and quotes above come from the collected sources, each opened on 2026-11-07. Two pages were recorded as URLs without an extract and are marked as such rather than paraphrased into a quote. The id scheme, the grade definitions, the release gate columns, and the shared matrix columns are this package's design assembled from those sources.

Dated values (`A1`, `A8`) are store policy values, not fixed facts: they change when Google Play revises the policy, so the check date is part of the item and the re-check row is part of the gate table.
