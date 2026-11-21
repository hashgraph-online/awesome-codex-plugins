# Korean Formats

> Number formats, dates, and CSV encodings for Korean workbooks. The traps are locale and encoding, not translation.

## Number formats

| Purpose | Format code | Stored value |
|---|---|---|
| 원화 금액 | `#,##0"원"` | `1200000` |
| 원화, 음수 빨강 | `#,##0"원";[Red]-#,##0"원"` | `-5000` |
| 천 단위, 소수 없음 | `#,##0` | `1200000` |
| 천 단위, 소수 2자리 | `#,##0.00` | `1200000.5` |
| 퍼센트 1자리 | `0.0%` | `0.153` → `15.3%` |
| 음수 괄호 회계 | `#,##0;(#,##0)` | `-1200` → `(1,200)` |
| 우편번호·코드 텍스트 | `@` | `"00123"` |
| 날짜 | `yyyy-mm-dd` | `46053` (serial) |
| 날짜+시간 | `yyyy-mm-dd hh:mm` | `46053.5` |
| 연월 | `yyyy-mm` | `46053` |

Rules:

- The unit is part of the format, never the value. `"원"` in the value makes the cell text and kills every sum.
- A percent value is a fraction. `15%` displays `0.15` stored as `0.15`; storing `15` shows `1,500%`.
- A leading-zero code must be text and must carry `@`; otherwise Excel helpfully converts it back to a number on the next edit.
- `#,##0"원"` is not the same as `₩#,##0`: the second is currency-formatted and follows the OS currency settings; the first is literal and stable across machines.

## Dates

Excel stores a date as a serial number counting days from 1899-12-30 (1900 date system) or 1904-01-01 (1904 date system). The format decides what it looks like.

- Write the serial, apply `yyyy-mm-dd`. Do not write `"2026-01-31"` as text.
- `inspect` reports `date1904` from the workbook properties (`workbookPr`); a file built under the 1904 system shows dates four years and a day off when opened under the 1900 system. Check it before trusting any date arithmetic.
- Korean Excel entered locally writes `2026. 1. 31.` when a date is typed in a text-formatted cell. That string parses as 2026-01-31 under a Korean locale and fails or misparses elsewhere.

Measured on this machine 2026-11-13: `2026. 1. 31.`, `2026-01-31`, and `2026/01/31` all parse to the same date. `profile` reports them as `LOCALE_DATE_TEXT` — stored as text but not locale-flippable. A column holding `01/31/2026` or `31/01/2026` is reported as `AMBIGUOUS_DATE` with severity `high`, because nothing in the value says which of the two is meant.

## CSV encoding

Korean CSVs arrive in one of four encodings. Detection order that works in practice:

1. `utf-8-sig` — BOM present; strip it or the first header cell keeps an invisible `\ufeff` and every header lookup fails.
2. `utf-8` — strict decode succeeds.
3. `cp949` — Microsoft's Korean codepage; superset of `euc-kr` for practical purposes, so decode with `cp949` and it covers both.
4. `euc-kr` — only reached when `cp949` fails, which is rare.
5. `latin-1` — last resort; decodes any byte sequence but produces mojibake, so treat the result as a guess, not a decode. `profile` still succeeds and reports `encoding: latin-1`, and `build` raises `W_ENCODING_GUESS` for the same file; when you see either, report the encoding assumption instead of presenting the text as trusted.

`profile_table.py` tries this order and reports which one was used. Always state the encoding in the report: a user who gets mojibake needs to know what was assumed.

Notepad on Korean Windows saves `cp949` without a BOM; Excel's own "CSV UTF-8" export writes `utf-8-sig`. Both are common.

## Delimiters and decimal marks

Korean CSVs use comma as delimiter and period as decimal separator, same as US. The problematic imports are the ones exported by European systems (semicolon delimiter, comma decimal) or from ERP exports that quote every field. `profile` reports the detected delimiter in the `delimiter` field. It does not warn about a wrong guess, so if the column count is 1 on a file you expected to be wide, re-run with an explicit `--delimiter` and compare the column count.

## Sheet names

- Hangul sheet names are valid and need no quoting in the UI, but a formula reference must be quoted when the name contains a space, a hyphen, or starts with a digit: `='월별 손익'!B2`.
- Sheet name limit is 31 characters; forbidden characters are `: \ / ? * [ ]`.
- Renaming a sheet in Excel updates the formulas that reference it; a raw XML rename does not. `patch --rename-sheet` changes the `<sheet>` name only and warns that quoting formulas and defined names are not rewritten, so after a rename you must update those references yourself and then run `verify`.
- Excel rejects duplicate sheet names, and names that differ only by case are also rejected on open. `build` refuses exact duplicates; it does not check case-only collisions, so check those yourself before shipping a file with names like `Data` and `data`.

## Text that looks like a formula

A customer name beginning with `=`, `+`, `-`, or `@` is a formula injection vector (DDE). The builder writes such values as text and reports them in the build output as `I_NEUTRALIZED` with a count and the cells. Do not delete the value silently; report the column and count so a human can decide.

## Hangul in output

- Keep the source language. A Korean workbook's headers, sheet names, and units stay Korean.
- The report is Korean; cell contents are quoted verbatim.
- Column widths for Hangul need about 1.6× the character count of Latin text since each syllable occupies roughly two Latin character widths. Set widths by looking at the longest value, not by a fixed default.

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| Number format codes `#,##0"원"`, `0.0%`, `@`, `yyyy-mm-dd` behave as described | <https://support.microsoft.com/en-us/office/number-format-codes-5026bbd6-04bc-48cd-bf33-80f18b4eae68> |
| A date is a serial number from 1899-12-30 (or 1904-01-01) | <https://support.microsoft.com/en-us/office/date-systems-in-excel-e7fe7167-48a9-4b96-bb53-5612a800b487> |
| `2026. 1. 31.`, `2026-01-31`, `2026/01/31` parse to one date; `01/31/2026` stays ambiguous | `profile_table.py` run on crafted CSVs on 2026-11-13; `LOCALE_DATE_TEXT` vs `AMBIGUOUS_DATE` |
| cp949 is a superset of euc-kr for practical decoding | <https://learn.microsoft.com/en-us/windows/win32/intl/code-page-identifiers> |
| Sheet name limits (31 characters, forbidden characters) | <https://support.microsoft.com/en-us/office/rename-a-worksheet-3f1f7148-ee83-404d-8ef0-9ff99fbad1f9> |

### Evidence grade

`LOCAL` for the measured date-parsing and encoding-detection rows; the format and limit rows are Microsoft's documentation.
