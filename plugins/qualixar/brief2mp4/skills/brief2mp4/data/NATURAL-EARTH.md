# Map data: Natural Earth

`ne_110m_countries.json.gz` is a simplified subset of **Natural Earth** "Admin 0 - Countries" at 1:110 million
(from the natural-earth-vector repository, tag v5.1.2), made by `scripts/build_map_data.py`. Natural Earth is made by Tom Patterson, Nathaniel Vaughn Kelso
and many contributors, and is in the **public domain**: any use, including modification, is allowed, and no credit is
required (https://www.naturalearthdata.com/about/terms-of-use/). brief2mp4 credits it anyway in `references/ecosystem.md`.

- Source file: `geojson/ne_110m_admin_0_countries.geojson` from https://github.com/nvkelso/natural-earth-vector (tag v5.1.2)
- Source SHA-256: `6866c877d39cba9c357620878839b336d569f8c662d3cfab4cb1dbe2d39c977f`
- Kept per country: name, full name, three-letter code, continent, outline rounded to 2 decimals
- Size: about 54 KB gzipped (169 KB unpacked), so it ships with the skill and `make_map.py` works offline

The 110m set leaves out very small countries and islands. For one of those, or for a closer map, download a finer
Natural Earth file (for example `ne_50m_admin_0_countries.geojson`), check it against the checksums in the
Natural Earth repository, and pass it with `make_map.py --geojson FILE`.
