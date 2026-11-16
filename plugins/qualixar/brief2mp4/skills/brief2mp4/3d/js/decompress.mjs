// Decode EXT_meshopt_compression / KHR_mesh_quantization so Python readers (trimesh) can load the file.
// usage: node decompress.mjs <in.glb> <out.glb>
import { NodeIO } from "@gltf-transform/core";
import { ALL_EXTENSIONS } from "@gltf-transform/extensions";
import { dequantize } from "@gltf-transform/functions";
import { MeshoptDecoder } from "meshoptimizer";

const [src, out] = process.argv.slice(2);
await MeshoptDecoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ "meshopt.decoder": MeshoptDecoder });
const doc = await io.read(src);
const COMPRESSION = ["EXT_meshopt_compression", "KHR_mesh_quantization", "KHR_draco_mesh_compression"];
for (const ext of doc.getRoot().listExtensionsUsed()) {
  if (COMPRESSION.includes(ext.extensionName)) ext.dispose();
}
await doc.transform(dequantize());
await io.write(out, doc);
console.log("B2M3D_DECOMPRESS " + JSON.stringify({ out }));
