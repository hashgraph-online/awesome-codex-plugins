# iOS Platform Checklist

Load this file only when the PRD's decided platforms include `ios`; fill the platform requirements block and its release gate table. Each item carries an id, a grade, the sentence or table the PRD must contain, the source, and the date it was checked. An item whose answer is not in the repository or the conversation becomes `[확인 필요: ...]` in the PRD; it does not become a guess.

## Grades

| Grade | Meaning | What the PRD owes |
|---|---|---|
| `[M]` | Enforced by App Store Review Guidelines or by law; a wrong or missing answer blocks the release | One conclusion in the release gate table |
| `[M-조건]` | Enforced only when the stated condition holds | One conclusion: applies, or not applicable with the condition named |
| `[G]` | Recommended; the review does not reject the app for missing it | Recorded only when the item matters to this product |

Every `[M]` and `[M-조건]` item in this file gets its own row in the PRD release gate table. The value of an item is a conclusion, not a restatement of the policy: `applies`, `not applicable` with the reason, or `[확인 필요]`. A sentence such as "follow the App Store Review Guidelines" is not a conclusion and is rejected in review.

## Account deletion

| Id | Grade | What the PRD records | Source | Checked |
|---|---|---|---|---|
| I1 | `[M-조건]` | Condition: the app supports account creation. The PRD then states where in the app the account is deleted, what the deletion removes, and what the user is told before it runs. Guideline 5.1.1(v): "If your app supports account creation, you must also offer account deletion within the app". An app with no account creation writes "not applicable" and names the condition. | [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 5.1.1(v) | 2026-11-07 |

## In-app purchase

| Id | Grade | What the PRD records | Source | Checked |
|---|---|---|---|---|
| I2 | `[M-조건]` | Condition: the app sells digital goods or digital services for use inside the app. The PRD then states that the purchase runs through in-app purchase under Guideline 3.1.1, and lists every paid item with its price, period, and what the buyer receives. Physical goods and services consumed outside the app are named as outside this row. | [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 3.1.1 | 2026-11-07 |
| I3 | `[M-조건]` | Condition: the app offers a paid subscription. The PRD then states what the subscriber keeps after the subscription ends, and how the app shows the price, period, and renewal terms on the purchase screen. | [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 3.1.2 | 2026-11-07 |

## Privacy declaration

| Id | Grade | What the PRD records | Source | Checked |
|---|---|---|---|---|
| I4 | `[M]` | The App Privacy label content for every data type the release handles: collected or not, linked to the user's identity or not, used for tracking or not, and the purpose. The label is required to submit a new app and every app update. | [App Privacy Details](https://developer.apple.com/app-store/app-privacy-details/) | 2026-11-07 |
| I5 | `[M]` | The privacy manifest (`PrivacyInfo.xcprivacy`) content: the collected data types, the required-reason APIs the app or its third-party SDKs call, and the tracking domains. The PRD names the owner of the manifest and the SDK list it covers. | [Privacy manifest files](https://developer.apple.com/documentation/bundleresources/privacy-manifest-files) | 2026-11-07 |

## App review access

| Id | Grade | What the PRD records | Source | Checked |
|---|---|---|---|---|
| I6 | `[M-조건]` | Condition: any part of the app requires sign-in. The PRD then states that a demo account with full access is supplied in App Store Connect, who owns the account, and what the reviewer sees after signing in. Guideline 2.1 App Completeness covers the review path; the research file recorded the clause without an extract, so this row cites the clause and not a quote. | [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 2.1 | 2026-11-07 |
| I7 | `[M]` | The minimum-functionality answer, in two sentences. Guideline 4.2: the app carries its own features, content, and UI that go beyond a repackaged website, so the PRD names that content or interaction. Guideline 4.2.2: the app is not primarily marketing materials, advertisements, web clippings, a content aggregator, or a collection of links, so the PRD names the part of the product that would otherwise be only that. | [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 4.2, 4.2.2 | 2026-11-07 |

## Permission requests

| Id | Grade | What the PRD records | Source | Checked |
|---|---|---|---|---|
| I8 | `[G]` | For each permission the app requests: the screen where the request appears, the sentence shown before the system prompt, and the feature that stops working when permission is denied. The request is made in context, not at launch: "Make the request in a context that helps people understand why your app needs authorization." | [Asking permission to use notifications](https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications) | 2026-11-07 |

## Shared data-collection matrix

When the decided platforms include both iOS and Android, write the matrix once and read it from two directions. Writing it twice lets the two statements drift, and the two stores then receive different descriptions of the same behavior.

| Data type | Collected | Shared with third parties | Linked to the user's identity | Used for tracking | Purpose | Optional | Ephemeral |
|---|---|---|---|---|---|---|---|

- The App Privacy label row (`I4`) and the Play Data safety row both resolve from this table; neither restates the data types from memory.
- A data type that one platform collects and the other does not is a product decision, not a declaration detail: record the difference and its reason in the PRD.
- A type the release handles but the table omits is a defect in the table. Fix the table before filling either store form.

## Filling the release gate table

| Column | Content |
|---|---|
| ID | The item id from this file, for example `I1` |
| Grade | The grade copied from this file, unaltered |
| Item | The obligation in one short sentence, with the threshold, measurement method, and percentile for a numeric item |
| Conclusion | `applies`, `not applicable` with the condition or reason, or `[확인 필요: <question>]` |
| Evidence | The document, App Store Connect screen, or measurement that settles the conclusion |
| Re-check | The date the dated value is checked again, or `none` for undated items |

A `[M]` row whose conclusion is `[확인 필요]` keeps the PRD at `status: draft`. Store policy values change when Apple revises the guidelines, so re-check every row against the current guideline text each quarter and after any App Store notice, and update the date rather than trusting this file.

## Sources

> Checked 2026-11-07.

| Source | What it settles | Quote |
|---|---|---|
| [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 5.1.1(v) | I1 | "If your app supports account creation, you must also offer account deletion within the app" |
| [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 3.1.1 | I2 | In-app purchase clause for digital goods; the research file recorded the clause number without an extract. |
| [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 3.1.2 | I3 | Subscription clause; the research file recorded the scope without an extract. |
| [App Privacy Details](https://developer.apple.com/app-store/app-privacy-details/) | I4 | "This information is required to submit new apps and app updates to the App Store." |
| [Privacy manifest files](https://developer.apple.com/documentation/bundleresources/privacy-manifest-files) | I5 | Manifest documentation; the research file recorded the URL without an extract. |
| [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 2.1 | I6 | App Completeness clause covering the review path; recorded without an extract. |
| [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 4.2 | I7 | Minimum Functionality body clause: an app goes beyond a repackaged website. |
| [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 4.2.2 | I7 | Minimum Functionality clause on apps that are primarily marketing materials, advertisements, web clippings, content aggregators, or a collection of links; recorded without an extract. |
| [Asking permission to use notifications](https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications) | I8 | "Make the request in a context that helps people understand why your app needs authorization." |

### Evidence grade

`QUOTED` - the items and quotes above come from the collected sources, each opened on 2026-11-07. Five clauses were recorded as clause numbers without an extract and are marked as such rather than paraphrased into a quote. The account-deletion quote is filed under the clause that carries it in the guideline. The id scheme, the grade definitions, the release gate columns, and the shared matrix columns are this package's design assembled from those sources.

Dated values (`I1`-`I8`) are store policy values, not fixed facts: they change when Apple revises the guidelines, so the check date is part of the item and the re-check row is part of the gate table.
