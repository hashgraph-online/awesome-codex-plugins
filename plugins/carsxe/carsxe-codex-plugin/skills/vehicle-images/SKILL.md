---
name: vehicle-images
description: Retrieve images of a vehicle by make, model, and year using the CarsXE API. Use this when a user wants to see what a vehicle looks like or asks for photos of a specific car.
license: MIT
---

When the user asks to see images or photos of a vehicle (by make, model, year):

1. Make an HTTP GET request to the CarsXE Images API:
   ```
   GET https://api.carsxe.com/images?key={CARSXE_API_KEY}&make={MAKE}&model={MODEL}&year={YEAR}&source=codex_plugin
   ```
   Optional params: `trim`, `color`, `angle`, `photoType`, `size`, `license`, `transparent`.
2. Display the returned image URLs, rendering them inline if the environment supports it.
3. Label images by type/angle if available.
4. If make/model/year are not all available, ask the user for the missing info before calling the API.
5. If the API key is missing, tell the user to set the `CARSXE_API_KEY` environment variable (see AGENTS.md).
