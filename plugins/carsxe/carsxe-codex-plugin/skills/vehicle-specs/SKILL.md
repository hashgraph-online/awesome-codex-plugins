---
name: vehicle-specs
description: Fetch full vehicle specifications from a VIN using the CarsXE API. Use this when the user provides a VIN and wants to know details about a vehicle (make, model, year, engine, trim, equipment, etc.).
license: MIT
version: 1.0.0
author: CarsXE
---

When the user provides a VIN and asks about vehicle specs, details, or information:

1. Make an HTTP GET request to the CarsXE Specifications API:
   ```
   GET https://api.carsxe.com/specs?key={CARSXE_API_KEY}&vin={VIN}&source=codex_plugin
   ```
   Replace `{CARSXE_API_KEY}` with the value of the `CARSXE_API_KEY` environment variable. Optional params: `deepdata=true` for extended data, `disableIntVINDecoding=true` to skip the international VIN fallback.
2. Present the results in a clean, organized format covering:
   - Basic info: Make, Model, Year, Trim
   - Engine: type, cylinders, displacement, horsepower, torque
   - Transmission & drivetrain
   - Fuel type and economy (city/highway/combined)
   - Body style, doors, seats
   - Standard & optional equipment
3. A valid VIN is exactly 17 characters (letters and numbers, excluding I, O, Q).
4. If the API key is missing, tell the user to set the `CARSXE_API_KEY` environment variable (see AGENTS.md).
