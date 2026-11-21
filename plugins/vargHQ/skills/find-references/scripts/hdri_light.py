#!/usr/bin/env python3
"""Measure the key light of an equirectangular Radiance .hdr file (for example a Poly Haven HDRI).

  python3 hdri_light.py file_1k.hdr [more_1k.hdr ...]

Prints one JSON object per file:

  key_azimuth_map_deg     where the brightest 0.1% of pixels sit, in degrees from the centre of the map. A position
                          in this file, not a compass bearing: many HDRIs are rotated before release
  key_altitude_deg        height of those pixels above the horizon of the map
  key_k                   apparent colour of those pixels (McCamy). The colour in the file after its white balance,
                          not the Kelvin of the lamp
  top_energy_share        share of the sphere's energy in those pixels. A hardness proxy: 0.65 to 0.90 read as hard
                          and 0.05 to 0.11 as soft on 13 HDRIs, a small sample
  key_vs_opposite_ratio   mean energy of the half of the sphere facing the key against the half facing away
  key_vs_opposite_stops   the same ratio in stops
  range_stops             log2(brightest pixel / p1 of luminance)

Check `evs_cap` in the Poly Haven API and range_stops first. A sun that was not captured reads as soft: one clear-sky
map with evs_cap 12 ranged 11.6 stops and read 0.06, against 21.5 to 26.9 stops on seven others.

Use the 1k file: 1024x512 takes under a second, larger files take far longer. .exr is not read.

Standard library only: no numpy and no HDR library. Reads uncompressed and adaptive run-length RGBE files.
"""
import array
import json
import math
import os
import re
import sys


def read_hdr(path):
    """Return (width, height, r, g, b) with one float per pixel, top row first."""
    with open(path, "rb") as handle:
        data = handle.read()
    if not data.startswith((b"#?RADIANCE", b"#?RGBE")):
        sys.exit(f"{path}: not a Radiance .hdr file")
    end = data.find(b"\n\n")
    if end < 0:
        sys.exit(f"{path}: no end of header")
    if b"FORMAT=32-bit_rle_xyze" in data[:end]:
        sys.exit(f"{path}: XYZE files are not supported")
    pos = end + 2
    newline = data.index(b"\n", pos)
    match = re.fullmatch(rb"-Y (\d+) \+X (\d+)", data[pos:newline].strip())
    if not match:
        sys.exit(f"{path}: unsupported orientation {data[pos:newline]!r}")
    height, width = int(match[1]), int(match[2])
    pos = newline + 1

    scale = [0.0] + [2.0 ** (e - 136) for e in range(1, 256)]
    red, green, blue = array.array("d"), array.array("d"), array.array("d")
    planes = [bytearray(width) for _ in range(4)]
    for _ in range(height):
        adaptive = (data[pos] == 2 and data[pos + 1] == 2 and data[pos + 2] < 128
                    and (data[pos + 2] << 8 | data[pos + 3]) == width)
        if adaptive:
            pos += 4
            for plane in planes:
                x = 0
                while x < width:
                    run = data[pos]
                    pos += 1
                    if run > 128:
                        run -= 128
                        plane[x:x + run] = bytes((data[pos],)) * run
                        pos += 1
                    else:
                        plane[x:x + run] = data[pos:pos + run]
                        pos += run
                    x += run
        else:
            if data[pos] == 1 and data[pos + 1] == 1 and data[pos + 2] == 1:
                sys.exit(f"{path}: old-style run-length rows are not supported")
            for c, plane in enumerate(planes):
                plane[:] = data[pos + c:pos + 4 * width:4]
            pos += 4 * width
        r, g, b, e = planes
        factors = [scale[v] for v in e]
        red.extend(map(float.__mul__, map(float, r), factors))
        green.extend(map(float.__mul__, map(float, g), factors))
        blue.extend(map(float.__mul__, map(float, b), factors))
    return width, height, red, green, blue


def mccamy(r, g, b):
    x_, y_, z_ = (0.4124 * r + 0.3576 * g + 0.1805 * b, 0.2126 * r + 0.7152 * g + 0.0722 * b,
                  0.0193 * r + 0.1192 * g + 0.9505 * b)
    total = x_ + y_ + z_
    if total <= 0 or y_ / total == 0.1858:
        return None
    n = (x_ / total - 0.3320) / (0.1858 - y_ / total)
    return round(449 * n ** 3 + 3525 * n ** 2 + 6823.3 * n + 5520.33)


def measure(path):
    width, height, red, green, blue = read_hdr(path)
    count = width * height
    lum = [0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in zip(red, green, blue)]
    ranked = sorted(lum)
    threshold = ranked[int(count * 0.999)]
    low = ranked[int(count * 0.01)] or 1e-6

    # Pixels near the poles of the map cover less of the sphere, so every pixel is weighted by cos(latitude).
    lats = [(0.5 - (y + 0.5) / height) * math.pi for y in range(height)]
    weights = [math.cos(lat) for lat in lats]
    lons = [((x + 0.5) / width - 0.5) * 2 * math.pi for x in range(width)]
    sin_lon, cos_lon = [math.sin(v) for v in lons], [math.cos(v) for v in lons]

    sum_x = sum_y = sum_lat = key_energy = key_weight = total = key_r = key_g = key_b = 0.0
    for y in range(height):
        lat, weight = lats[y], weights[y]
        row = y * width
        for x in range(width):
            i = row + x
            value = lum[i]
            energy = value * weight
            total += energy
            if value >= threshold:
                sum_x += sin_lon[x] * energy
                sum_y += cos_lon[x] * energy
                sum_lat += lat * energy
                key_energy += energy
                key_r += red[i] * weight
                key_g += green[i] * weight
                key_b += blue[i] * weight
                key_weight += weight

    azimuth = math.atan2(sum_x, sum_y)
    facing = [math.cos(lon - azimuth) > 0 for lon in lons]
    near_e = near_w = far_e = far_w = 0.0
    for y in range(height):
        weight = weights[y]
        row = y * width
        for x in range(width):
            energy = lum[row + x] * weight
            if facing[x]:
                near_e += energy
                near_w += weight
            else:
                far_e += energy
                far_w += weight
    ratio = (near_e / near_w) / max(far_e / far_w, 1e-12)
    return {
        "file": os.path.basename(path),
        "size": f"{width}x{height}",
        "key_azimuth_map_deg": round(math.degrees(azimuth), 1),
        "key_altitude_deg": round(math.degrees(sum_lat / key_energy), 1),
        "key_k": mccamy(key_r / key_weight, key_g / key_weight, key_b / key_weight),
        "top_energy_share": round(key_energy / total, 2),
        "key_vs_opposite_ratio": round(ratio, 2),
        "key_vs_opposite_stops": round(math.log2(ratio), 2),
        "range_stops": round(math.log2(ranked[-1] / low), 1),
    }


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) > 1 else 2)
    for path in sys.argv[1:]:
        print(json.dumps(measure(path), ensure_ascii=False))


if __name__ == "__main__":
    main()
