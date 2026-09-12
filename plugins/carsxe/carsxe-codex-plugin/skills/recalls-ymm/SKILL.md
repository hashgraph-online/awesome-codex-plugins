---
name: recalls-ymm
description: Check safety recalls by year, make, and model (no VIN) using the CarsXE Recalls by YMM API. Use this when the user asks about recalls for a model line, or has year/make/model but no VIN.
license: MIT
version: 1.0.0
author: CarsXE
---

When the user asks about recalls or safety issues for a year/make/model and does **not** have a VIN:

1. Make an HTTP GET request to the CarsXE Recalls by YMM API:
   ```
   GET https://api.carsxe.com/v1/recalls-ymm?key={CARSXE_API_KEY}&year={YEAR}&make={MAKE}&model={MODEL}&source=codex_plugin
   ```
   `year` must be a 4-digit model year between 1900 and the current model year plus one. If year, make, or model are missing, ask for them before calling the API.
2. Present recall details:
   - Total `recall_count` and `has_recalls`
   - For each recall: NHTSA campaign number, manufacturer, component, summary, consequence, remedy, report date
   - Highlight `park_it`, `park_outside`, or over-the-air remedy flags
3. If no recalls exist, clearly confirm the model line has no safety recalls.
4. Emphasize this is a model-line result, not a specific vehicle. If they later provide a VIN, use the `vehicle-recalls` skill (`/v1/recalls`) instead. For many VINs, use `recalls-batch`.
5. If the API key is missing, tell the user to set the `CARSXE_API_KEY` environment variable (see AGENTS.md).
