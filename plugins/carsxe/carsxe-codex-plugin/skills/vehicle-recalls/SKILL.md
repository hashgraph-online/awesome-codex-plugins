---
name: vehicle-recalls
description: Check for open safety recalls on a vehicle using the CarsXE API. Use this when a user asks whether a car has any recalls, safety issues, or wants to know if their vehicle needs a recall repair.
license: MIT
---

When the user asks about recalls or safety issues for a vehicle (by VIN):

1. Make an HTTP GET request to the CarsXE Recalls API:
   ```
   GET https://api.carsxe.com/v1/recalls?key={CARSXE_API_KEY}&vin={VIN}&source=codex_plugin
   ```
2. Present recall details:
   - Total number of open recalls
   - For each recall: campaign number, component, defect description, remedy status
3. If no recalls exist, clearly confirm the vehicle has no open recalls.
4. Emphasize any safety-critical recalls.
5. If the API key is missing, tell the user to set the `CARSXE_API_KEY` environment variable (see AGENTS.md).
