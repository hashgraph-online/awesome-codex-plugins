---
name: plate-image-recognition
description: Extract a license plate number from an image URL using the CarsXE Plate Recognition API. Use this when a user shares a photo of a vehicle or license plate and wants to identify the plate number.
license: MIT
---

When the user shares an image containing a license plate and wants to extract the plate number:

1. Make an HTTP **POST** request to the CarsXE Plate Recognition API:
   - **URL:** `https://api.carsxe.com/platerecognition?key={CARSXE_API_KEY}&source=codex_plugin`
   - **Headers:** `Content-Type: application/json`
   - **Body:**
     ```json
     {
       "image": "{IMAGE_URL}"
     }
     ```
2. Display the extracted plate number and confidence score.
3. Offer to immediately decode the plate using the plate-decoder skill.
4. If the image is unclear, suggest the user retry with a better photo.
5. If the API key is missing, tell the user to set the `CARSXE_API_KEY` environment variable (see AGENTS.md).
