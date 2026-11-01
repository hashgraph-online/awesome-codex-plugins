# Changelog

## 1.1.0

### Added

- A user-confirmed export list name on contacts and companies by default, with a suggestion based on the conversation. The user may explicitly choose a different existing destination or skip the field for a push. Otherwise a missing or incompatible destination blocks the push before export until resolved and verified.
- Up to three additional contact phones from `contact_phone_numbers`, excluding the primary mobile and formatting-equivalent duplicates while preserving original values and source order.
- User-editable custom `vp_additional_phone_number_1`, `vp_additional_phone_number_2`, and `vp_additional_phone_number_3` destinations. Missing or unavailable phone fields use the ordinary mapping report; unused fields are not cleared.
- VP CSV phone parsing from a JSON-encoded array of strings, with the primary excluded wherever it occurs. The primary need not be present in the array; malformed or scalar cells are not guessed into an array.

The primary `contact_mobile_phone` → `mobilephone` mapping is unchanged. Phone-array extraction applies only when that source column is available; it does not enable a missing export column or create HubSpot properties.

## 1.0.0

First version supporting export of Vibe Prospecting data into HubSpot.

### Added

- Basic field mappings from Vibe Prospecting prospects to HubSpot Contacts and businesses to HubSpot Companies.
- A required mapping report before writing, showing which destination fields exist and which fields will be written or skipped.
- User-managed custom properties: missing destination fields are skipped and reported, never created automatically.
- Lead Status set to New for newly created contacts when that option is available.
