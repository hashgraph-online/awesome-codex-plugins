---
name: year-make-model
description: Look up vehicle data by Year, Make, and Model using the CarsXE YMM API. Use this when a user doesn't have a VIN but knows the year, make, and model of a vehicle and wants specs, trims, or features.
license: MIT
version: 1.0.0
author: CarsXE
---

When the user asks about a vehicle by year, make, and model (without a VIN):

1. Make an HTTP GET request to the CarsXE YMM API:
   ```
   GET https://api.carsxe.com/v1/ymm?key={CARSXE_API_KEY}&year={YEAR}&make={MAKE}&model={MODEL}&source=codex_plugin[&trim={TRIM}]
   ```
   Only include `trim` if the user specified one.
2. Present available trims, engine options, features, and specs.
3. If the user didn't specify a trim, list all available trims for that year/make/model.
4. If the API key is missing, tell the user to set the `CARSXE_API_KEY` environment variable (see AGENTS.md).
