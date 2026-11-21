// b2m3d optimize: glTF Transform + meshoptimizer pipeline for web and HyperFrames delivery.
// usage: node optimize.mjs <in.glb> <out.glb> [--simplify 0.5] [--error 0.001] [--join] [--no-compress]
// Node names are kept (the shot runtime's `explode` addresses parts by node name), so meshes are
// only merged when --join is passed.
// Prints: B2M3D_OPTIMIZE {json}
import { NodeIO } from "@gltf-transform/core";
import { ALL_EXTENSIONS } from "@gltf-transform/extensions";
import { dedup, join, meshopt, prune, resample, simplify, weld } from "@gltf-transform/functions";
import { MeshoptDecoder, MeshoptEncoder, MeshoptSimplifier } from "meshoptimizer";
import { statSync } from "node:fs";

function parse(argv) {
  const opts = { simplify: 1, error: 0.001, compress: true, join: false };
  const pos = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--simplify") opts.simplify = Number(argv[++i]);
    else if (a === "--error") opts.error = Number(argv[++i]);
    else if (a === "--no-compress") opts.compress = false;
    else if (a === "--join") opts.join = true;
    else pos.push(a);
  }
  if (pos.length !== 2) throw new Error("usage: optimize.mjs <in.glb> <out.glb> [opts]");
  if (!(opts.simplify > 0 && opts.simplify <= 1)) throw new Error("--simplify must be in (0, 1]");
  return { src: pos[0], out: pos[1], ...opts };
}

function countTriangles(doc) {
  let tris = 0;
  for (const mesh of doc.getRoot().listMeshes()) {
    for (const prim of mesh.listPrimitives()) {
      const idx = prim.getIndices();
      const pos = prim.getAttribute("POSITION");
      tris += idx ? idx.getCount() / 3 : (pos ? pos.getCount() / 3 : 0);
    }
  }
  return Math.round(tris);
}

async function main() {
  const o = parse(process.argv.slice(2));
  await Promise.all([MeshoptEncoder.ready, MeshoptDecoder.ready, MeshoptSimplifier.ready]);
  const io = new NodeIO()
    .registerExtensions(ALL_EXTENSIONS)
    .registerDependencies({ "meshopt.encoder": MeshoptEncoder, "meshopt.decoder": MeshoptDecoder });
  const doc = await io.read(o.src);
  const before = countTriangles(doc);

  const steps = [dedup(), weld(), resample(), prune()];
  if (o.join) steps.push(join());
  if (o.simplify < 1) {
    steps.push(simplify({ simplifier: MeshoptSimplifier, ratio: o.simplify, error: o.error }));
  }
  if (o.compress) steps.push(meshopt({ encoder: MeshoptEncoder, level: "medium" }));
  await doc.transform(...steps);
  await io.write(o.out, doc);

  console.log("B2M3D_OPTIMIZE " + JSON.stringify({
    out: o.out, triangles_before: before, triangles_after: countTriangles(doc),
    bytes_before: statSync(o.src).size, bytes_after: statSync(o.out).size,
    meshopt_compressed: o.compress,
  }));
}

main().catch((e) => { console.error(e.stack || String(e)); process.exit(1); });
