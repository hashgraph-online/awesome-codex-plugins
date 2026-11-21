// Apply glTF materials to meshes by node/mesh name.
// usage: node material_apply.mjs <in.glb> <out.glb> <mapping.json>   (mapping: {name|*: gltfMaterial})
import { NodeIO } from "@gltf-transform/core";
import {
  ALL_EXTENSIONS, KHRMaterialsClearcoat, KHRMaterialsEmissiveStrength, KHRMaterialsIOR,
  KHRMaterialsSheen, KHRMaterialsTransmission, KHRMaterialsVolume,
} from "@gltf-transform/extensions";
import { MeshoptDecoder, MeshoptEncoder } from "meshoptimizer";
import { readFileSync } from "node:fs";

const [src, out, mappingPath] = process.argv.slice(2);
const mapping = JSON.parse(readFileSync(mappingPath, "utf8"));

function build(doc, spec) {
  const m = doc.createMaterial(spec.name)
    .setBaseColorFactor(spec.baseColorFactor)
    .setMetallicFactor(spec.metallicFactor)
    .setRoughnessFactor(spec.roughnessFactor);
  if (spec.emissiveFactor) m.setEmissiveFactor(spec.emissiveFactor);
  const e = spec.extensions || {};
  if (e.KHR_materials_clearcoat) {
    const x = doc.createExtension(KHRMaterialsClearcoat).createClearcoat()
      .setClearcoatFactor(e.KHR_materials_clearcoat.clearcoatFactor)
      .setClearcoatRoughnessFactor(e.KHR_materials_clearcoat.clearcoatRoughnessFactor);
    m.setExtension("KHR_materials_clearcoat", x);
  }
  if (e.KHR_materials_transmission) {
    m.setExtension("KHR_materials_transmission", doc.createExtension(KHRMaterialsTransmission)
      .createTransmission().setTransmissionFactor(e.KHR_materials_transmission.transmissionFactor));
    m.setExtension("KHR_materials_volume", doc.createExtension(KHRMaterialsVolume)
      .createVolume().setThicknessFactor(e.KHR_materials_volume?.thicknessFactor ?? 0.01));
  }
  if (e.KHR_materials_ior) {
    m.setExtension("KHR_materials_ior", doc.createExtension(KHRMaterialsIOR)
      .createIOR().setIOR(e.KHR_materials_ior.ior));
  }
  if (e.KHR_materials_emissive_strength) {
    m.setExtension("KHR_materials_emissive_strength", doc.createExtension(KHRMaterialsEmissiveStrength)
      .createEmissiveStrength().setEmissiveStrength(e.KHR_materials_emissive_strength.emissiveStrength));
  }
  if (e.KHR_materials_sheen) {
    m.setExtension("KHR_materials_sheen", doc.createExtension(KHRMaterialsSheen).createSheen()
      .setSheenColorFactor(e.KHR_materials_sheen.sheenColorFactor)
      .setSheenRoughnessFactor(e.KHR_materials_sheen.sheenRoughnessFactor));
  }
  return m;
}

await MeshoptDecoder.ready;
await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ "meshopt.decoder": MeshoptDecoder, "meshopt.encoder": MeshoptEncoder });
const doc = await io.read(src);
const cache = new Map();
const mat = (key) => {
  if (!cache.has(key)) cache.set(key, build(doc, mapping[key]));
  return cache.get(key);
};
const hits = {};
for (const node of doc.getRoot().listNodes()) {
  const mesh = node.getMesh();
  if (!mesh) continue;
  const names = [node.getName(), mesh.getName()].filter(Boolean);
  const leaves = names.map((n) => n.split("/").pop());
  const key = [...names, ...leaves].find((n) => n in mapping) ?? ("*" in mapping ? "*" : null);
  if (!key) continue;
  for (const prim of mesh.listPrimitives()) prim.setMaterial(mat(key));
  hits[node.getName() || mesh.getName()] = mapping[key].name;
}
// Drop the materials this script replaced, so they do not ship as dead weight.
for (const m of doc.getRoot().listMaterials()) {
  if (m.listParents().every((parent) => parent.propertyType === "Root")) m.dispose();
}
await io.write(out, doc);
console.log("B2M3D_MATERIAL " + JSON.stringify({ out, assigned: hits }));
