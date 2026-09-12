---
name: vehicle-recalls
description: Check for open safety recalls on a vehicle using the CarsXE API. Use this when a user asks whether a car has any recalls, safety issues, or wants to know if their vehicle needs a recall repair.
license: MIT
version: 1.0.0
author: CarsXE
---

When the user asks about recalls or safety issues:

- If they have a VIN, call the CarsXE Recalls API:
  ```
  GET https://api.carsxe.com/v1/recalls?key={CARSXE_API_KEY}&vin={VIN}&source=codex_plugin
  ```
- If they have year/make/model but no VIN, use the `recalls-ymm` skill (`/v1/recalls-ymm`).
- If they have many VINs (fleet, inventory, CSV), use the `recalls-batch` skill (`/v1/recalls-batch/*`).

1. Present recall details:
   - Total number of open recalls
   - For each recall: campaign number, component, defect description, remedy status
2. If no recalls exist, clearly confirm the vehicle has no open recalls.
3. Emphasize any safety-critical recalls.
4. If the API key is missing, tell the user to set the `CARSXE_API_KEY` environment variable (see AGENTS.md).
