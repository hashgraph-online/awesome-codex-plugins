# One clean front image -> untextured 3D mesh with Tencent Hunyuan3D-2 (public HF Space, ZeroGPU, no key; anonymous quota ~ a few runs/day).
# License: Tencent Hunyuan Community License (excludes EU, UK, South Korea). The Space ignores multi-view inputs (single-view DiT v2-0).
# Usage: uvx --from gradio_client python hunyuan3d_space.py front.png out.glb
import sys, shutil
from gradio_client import Client, handle_file
src, out = sys.argv[1], sys.argv[2]
c = Client("tencent/Hunyuan3D-2", verbose=False)
glb, _html, stats, _seed = c.predict(None, handle_file(src), None, None, None, None,
                                     30, 5.0, 1234, 256, True, 8000, False, api_name="/shape_generation")
path = glb.get("value") or glb.get("path") if isinstance(glb, dict) else glb
shutil.copy(path, out); print("wrote", out, stats.get("number_of_faces"), "faces,", stats.get("time", {}).get("total"), "s")
