---
name: vin-ocr
description: Extract a VIN from a photo or image URL using the CarsXE VIN OCR API. Use this when a user shares an image of a vehicle or VIN plate and wants to identify the VIN.
license: MIT
---

When the user shares an image containing a VIN (photo of dashboard, door jamb, windshield, etc.):

1. Make an HTTP **POST** request to the CarsXE VIN OCR API:
   - **URL:** `https://api.carsxe.com/v1/vinocr?key={CARSXE_API_KEY}&source=codex_plugin`
   - **Headers:** `Content-Type: application/json`
   - **Body:**
     ```json
     {
       "image": "{IMAGE_URL}"
     }
     ```
2. Display the extracted VIN and confidence score.
3. Offer to immediately decode the VIN using the vehicle-specs skill.
4. If the image quality is poor or the VIN can't be extracted, suggest the user try a clearer photo with better lighting and angle.
5. If the API key is missing, tell the user to set the `CARSXE_API_KEY` environment variable (see AGENTS.md).
