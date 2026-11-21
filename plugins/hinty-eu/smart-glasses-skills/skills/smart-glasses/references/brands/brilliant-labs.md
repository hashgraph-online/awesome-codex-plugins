# Brilliant Labs Halo and Frame (Lua over Bluetooth LE)

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Pointer coverage.

## At a glance
- Display: Halo: 0.2 inch colour OLEDoS, 640x480 panel, round 256x256 drawable area. Frame: 640x400 colour.
- How your app puts text on it: rung 1 without a vendor gatekeeper. Your host app (phone, desktop or web) connects
  over BLE and sends Lua that the glasses run; Lua calls draw text.
- Input: Halo: one button (click, double, long press) and IMU taps (single, double, triple). Frame: IMU taps only.
- Microphone for your app: yes, two MEMS mics on Halo (PCM or LC3), started from Lua.
- Speaker: Halo has stereo bone-conduction speakers (separate audio characteristic).
- Phones / where your code runs: any BLE host. Official SDKs for Python, Flutter and Web Bluetooth; native Android and
  iOS apps use the platform BLE APIs directly.
- Publishing to everyone today: yes. "Halo doesn't have its own app launcher"; you ship your own host app through any
  normal channel ([docs](https://docs.brilliant.xyz/llms-full.txt), read 2026-11-08).
- Test without hardware: `halo-emulator` on PyPI (2.3.0, experimental): Lua 5.4 with the device API stubbed and a
  256x256 framebuffer.
- Official agent skill: none. The docs publish `llms-full.txt`.

## Status (as of 2026-11-08)
- Halo is orderable from brilliant.xyz ("Shipping now" in search snippets; the product page rate-limited our checks).
  Price not confirmed on an official page: $299 at the 2025 announcement, $349 to $399 in 2026 reports (unverified).
- Brilliant's own app Noa is "coming soon" for Halo on the App Store and Google Play; it is available for Frame.
- Frame is the older model; new work targets Halo.
- Licences: SDK monorepo BSD-3-Clause, Frame firmware ISC, Halo firmware mixed (Brilliant code Apache-2.0, vendor
  chip SDK under its own licence, Lua MIT, font OFL-1.1). Writing your own Lua and BLE code is unrestricted.

## Getting text on the display
Both models expose BLE service `7A230001-5475-A6A4-654C-8431F6AD49C4`. The host writes Lua to the TX characteristic
`7A230002-...` and subscribes to notifications on RX `7A230003-...`. Halo adds an audio characteristic `7A230005-...`
(its presence tells Halo from Frame). Check the real write size on the device instead of assuming one.

Halo, minimal Lua sent after connecting (one write per line):

```lua
frame.display.power_save(false)
frame.display.clear()
frame.display.text("HELLO FROM YOUR APP", 20, 120, 0xFFFFFF)
frame.bluetooth.receive_callback(function(d) frame.display.clear() frame.display.text(d, 20, 120, 0xFFFFFF) end)
```

Frame differs: colours are palette names (`{color='WHITE'}`), there is no clear call, and you must call
`frame.display.show()` after drawing because the display is double-buffered.

## Pitfalls
- Halo's fonts are ASCII only (95 glyphs, 0x20-0x7E): accented letters, Cyrillic, CJK and Arabic do not render. For
  other scripts rasterise on the host and send a bitmap (`brilliant_msg` has helpers). Frame adds Latin-1 but no CJK
  ([#169](https://github.com/brilliantlabsAR/frame-codebase/issues/169)).
- No word wrap: split lines on the host to fit 256 px (Halo, 8 px font = 32 characters per line at size 8).
- Halo runs one Lua VM, so your callbacks replace those of any other host app such as Noa. Ask the user to close
  other glasses apps while yours runs (inference from the docs, unverified).
- On iOS a Halo already connected to the system (for notifications via ANCS) may not advertise; look it up with
  `retrieveConnectedPeripherals(withServices:)` before scanning (unverified).
- BLE throughput is small; images and fast updates are slow. Send short text, not frames.

## Official resources
- https://docs.brilliant.xyz/ and https://docs.brilliant.xyz/llms-full.txt
- https://github.com/brilliantlabsAR/halo-firmware (protocol: `applications/halo/PROTOCOL.md`, `BLE_SERVICES.md`)
- https://github.com/brilliantlabsAR/frame-codebase
- https://pypi.org/project/brilliant-ble/ , https://pypi.org/project/halo-emulator/
- https://pub.dev/packages/brilliant_ble , https://www.npmjs.com/package/brilliant-ble
- https://github.com/hkust-spark/xg-glass-sdk (community cross-brand SDK with a Frame adapter, Apache-2.0)
