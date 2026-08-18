---
name: international-vin
description: Decode an international (non-US) VIN using the CarsXE API. Use this when a user provides a VIN from a European, Asian, or other non-US vehicle and wants to decode it.
license: MIT
version: 1.0.0
author: CarsXE
---

When the user provides a VIN that appears to be from a non-US vehicle (European, Asian, etc.):

1. Make an HTTP GET request to the CarsXE International VIN Decoder API:
   ```
   GET https://api.carsxe.com/v1/international-vin-decoder?key={CARSXE_API_KEY}&vin={VIN}&source=codex_plugin
   ```
2. Present the decoded data: country of manufacture, make, model, year, engine, transmission, body style.
3. Note this endpoint is optimized for international VINs outside the US market.
4. If the API key is missing, tell the user to set the `CARSXE_API_KEY` environment variable (see AGENTS.md).
