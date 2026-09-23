---
name: ownership
description: Look up registered vehicle owners and residents using the CarsXE Ownership API (Enterprise). Use this when the user asks who owns a VIN, who lives at an address, contact details for a named person, or people in a ZIP. Do not use for lien/theft checks or vehicle history reports.
license: MIT
version: 1.0.0
author: CarsXE
---

When the user asks who owns a vehicle, who lives at an address, contact details for a person, or people in a ZIP (Enterprise only):

1. Choose one lookup. Do **not** call `/v1/ownership/phone`.
   - VIN → `GET https://api.carsxe.com/v1/ownership/vin?key={CARSXE_API_KEY}&vin={VIN}&source=codex_plugin[&include={INCLUDE}]`
   - Person → `GET https://api.carsxe.com/v1/ownership/person?key={CARSXE_API_KEY}&first_name={FIRST}&last_name={LAST}&address={ADDRESS}&zip={ZIP}&source=codex_plugin[&include={INCLUDE}]`
   - Address → `GET https://api.carsxe.com/v1/ownership/address?key={CARSXE_API_KEY}&address={ADDRESS}&zip={ZIP}&source=codex_plugin[&include={INCLUDE}]`
   - ZIP → `GET https://api.carsxe.com/v1/ownership/zip?key={CARSXE_API_KEY}&zip={ZIP}&source=codex_plugin[&gender={GENDER}][&min_age={MIN}][&max_age={MAX}][&income={INCOME}][&page={PAGE}][&limit={LIMIT}][&include={INCLUDE}]`
2. `include` is optional: comma-separated `demographics,emails,phones,vehicle_history`. Omit it to get everything. It only shapes which sections are shown; it does not change billing.
3. Street `address` is street only — no city or state (max 100). ZIP is 5-digit US (person/address may be ZIP+4; zip lookup is exactly 5 digits). `first_name` / `last_name` max 50.
4. ZIP optional filters: `gender` (`M` or `F`), `min_age`, `max_age`, `income` (code or label, e.g. `F` or `$50,000–$59,999`), `page` (default 1), `limit` (default 15, max 100).
5. Present matches clearly (name, address, contact, demographics, linked vehicles). HTTP 404 / `no_data` means no match and is not billed.
6. Billing is per returned record (`owners` / `matches` / `records`). Warn before a ZIP search with a high `limit`.
7. If the key lacks entitlement, say this API is Enterprise-only. If the API key is missing, tell the user to set the `CARSXE_API_KEY` environment variable (see AGENTS.md).
