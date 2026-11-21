// Builds the vector base map and the route for the demo from Natural Earth (public domain, no credit needed).
//   bun tools/build-map.ts <ne_50m_admin_0_countries.geojson>
// Download: https://github.com/nvkelso/natural-earth-vector/tree/master/geojson (ne_50m_admin_0_countries.geojson)
// Writes assets/map.svg (land, borders, graticule) and assets/route.json (projected great-circle route + city points).
import { readFileSync, writeFileSync } from "node:fs";
import { geoAzimuthalEqualArea, geoDistance, geoGraticule10, geoInterpolate, geoPath } from "d3-geo";

const W = 1920;
const H = 1080;
const src = process.argv[2];
if (!src) throw new Error("usage: bun tools/build-map.ts <ne_50m_admin_0_countries.geojson>");
const countries = JSON.parse(readFileSync(src, "utf8"));

// cities: coordinates from Natural Earth ne_50m_populated_places_simple
const A = { name: "Lisbon", lonlat: [-9.146812, 38.724669] as [number, number] };
const B = { name: "Helsinki", lonlat: [24.932457, 60.163804] as [number, number] };

// Lambert azimuthal equal-area centred on Europe (the ETRS89-LAEA idea); fit so the two cities sit
// diagonally with room for the title (top left) and labels.
const projection = geoAzimuthalEqualArea()
  .rotate([-10, -52])
  .clipExtent([
    [-20, -20],
    [W + 20, H + 20],
  ])
  .fitExtent(
    [
      [380, 210],
      [1540, 880],
    ],
    { type: "MultiPoint", coordinates: [A.lonlat, B.lonlat] },
  );
const path = geoPath(projection).digits(1);

const land = countries.features
  .map((f: any) => path(f))
  .filter(Boolean)
  .join("");
const grat = path(geoGraticule10());

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<rect width="${W}" height="${H}" fill="#0B1220"/>
<path d="${grat}" fill="none" stroke="#111C31" stroke-width="1"/>
<path d="${land}" fill="#16213A" stroke="#26355A" stroke-width="1" stroke-linejoin="round"/>
</svg>
`;
writeFileSync(new URL("../assets/map.svg", import.meta.url).pathname, svg);

// great-circle route sampled every 1/120 of the arc
const interp = geoInterpolate(A.lonlat, B.lonlat);
const pts: [number, number][] = [];
for (let i = 0; i <= 120; i++) {
  const p = projection(interp(i / 120))!;
  pts.push([+p[0].toFixed(2), +p[1].toFixed(2)]);
}
const km = Math.round((geoDistance(A.lonlat, B.lonlat) * 6371.0088) / 10) * 10;
const route = {
  a: { name: A.name, xy: projection(A.lonlat)!.map((v) => +v.toFixed(1)) },
  b: { name: B.name, xy: projection(B.lonlat)!.map((v) => +v.toFixed(1)) },
  km,
  d: "M" + pts.map((p) => p.join(" ")).join(" L"),
};
writeFileSync(new URL("../assets/route.json", import.meta.url).pathname, JSON.stringify(route, null, 1));
console.log(JSON.stringify({ a: route.a, b: route.b, km, svgKB: Math.round(svg.length / 1024) }));
