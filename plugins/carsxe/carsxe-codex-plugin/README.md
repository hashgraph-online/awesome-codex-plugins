[![Codex Plugin](https://img.shields.io/badge/OpenAI%20Codex-Plugin-10a37f)](https://www.codex-marketplace.com/)

# CarsXE Plugin for OpenAI Codex

Access the full suite of CarsXE vehicle data APIs directly from OpenAI Codex — decode VINs, look up license plates, get market values, check history, recalls, liens, OBD codes, and more.

Codex auto-invokes the right skill based on what you ask. No slash commands to memorize — just describe what you need.

## Skills

| Skill                     | What it does                                       |
| ------------------------- | -------------------------------------------------- |
| `vehicle-specs`           | Decode a VIN — full vehicle specifications         |
| `plate-decoder`           | Look up a vehicle from a license plate             |
| `market-value`            | Estimate a vehicle's current market value          |
| `vehicle-history`         | Full vehicle history report                        |
| `vehicle-images`          | Fetch vehicle photos by make/model/year            |
| `vehicle-recalls`         | Check for open safety recalls                      |
| `international-vin`       | Decode international (non-US) VINs                 |
| `vin-ocr`                 | Extract a VIN from a photo                          |
| `lien-theft`              | Check for liens and theft records                  |
| `plate-image-recognition` | Extract a license plate number from a photo        |
| `year-make-model`         | Look up a vehicle by Year/Make/Model               |
| `obd-decoder`             | Decode an OBD-II diagnostic trouble code           |

## Installation

Install from the Codex Plugin Marketplace:

```bash
npx codex-marketplace add carsxe/carsxe-codex-plugin --plugin --project
```

Or browse and install interactively from within Codex:

```
/plugins
```

## Setup

### 1. Get your CarsXE API key

Sign up at [api.carsxe.com](https://api.carsxe.com) and grab your key from the [developer dashboard](https://api.carsxe.com/dashboard/developer).

### 2. Set the `CARSXE_API_KEY` environment variable

Codex skills read your key from `CARSXE_API_KEY`. Set it before launching Codex:

```bash
# macOS / Linux
export CARSXE_API_KEY="YOUR_API_KEY_HERE"
```

```powershell
# Windows (PowerShell)
$env:CARSXE_API_KEY="YOUR_API_KEY_HERE"
```

Add it to your shell profile to persist it across sessions.

## Usage Examples

Just ask Codex naturally — the matching skill is invoked automatically:

- _"Decode VIN WBAFR7C57CC811956"_ → `vehicle-specs`
- _"Look up California plate 7XER187"_ → `plate-decoder`
- _"What's this car worth? VIN WBAFR7C57CC811956, 45k miles, clean condition"_ → `market-value`
- _"Get the history report for WBAFR7C57CC811956"_ → `vehicle-history`
- _"Does 1C4JJXR64PW696340 have any open recalls?"_ → `vehicle-recalls`
- _"Is this VIN stolen or have a lien? WBAFR7C57CC811956"_ → `lien-theft`
- _"Decode this international VIN: WF0MXXGBWM8R43240"_ → `international-vin`
- _"Look up a 2020 Toyota Camry LE"_ → `year-make-model`
- _"What does check engine code P0300 mean?"_ → `obd-decoder`
- _"Extract the VIN from this photo: https://example.com/vin.jpg"_ → `vin-ocr`
- _"Read the plate in this image: https://example.com/plate.jpg"_ → `plate-image-recognition`
- _"Show me photos of a 2019 BMW X5"_ → `vehicle-images`

You can also call a skill explicitly by name with the `@` prefix, e.g. `@vehicle-specs`.

## API Documentation

Full CarsXE API docs: [api.carsxe.com/docs](https://api.carsxe.com/docs)

## License

MIT © CarsXE
