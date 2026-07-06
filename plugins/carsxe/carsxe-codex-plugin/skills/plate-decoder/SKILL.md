---
name: plate-decoder
description: Look up vehicle information from a license plate number using the CarsXE API. Use this when a user mentions a license plate and wants to know what vehicle it belongs to.
license: MIT
---

When the user provides a license plate number:

1. Extract the following from the user's message:
   - `plate` (required): the license plate number — if not provided, ask:
     > "Please provide a license plate number."
   - `country` (required): ISO 3166-1 alpha-2 country code (e.g., `US`, `AU`, `GB`) — if not provided, ask:
     > "Please provide a country code (e.g., US, AU, GB)."
   - `state` (required): 2-letter state/province code (e.g., `CA`, `NY`) — if not provided, ask:
     > "Please provide a state code (e.g., CA, NY, TX)."

2. Do not call the API until all three fields are provided.

3. Make an HTTP GET request to the CarsXE Plate Decoder API:
   ```
   GET https://api.carsxe.com/v2/platedecoder?key={CARSXE_API_KEY}&plate={PLATE}&country={COUNTRY}&state={STATE}&source=codex_plugin
   ```

4. Present the results: vehicle Make, Model, Year, VIN (if returned), and registration info.

5. If the API key is missing, tell the user to set the `CARSXE_API_KEY` environment variable (see AGENTS.md).
