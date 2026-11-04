# Image -> 3D with Microsoft TRELLIS.2 (MIT) through its public Hugging Face Space (ZeroGPU, no key; anonymous quota is small).
# Usage: uvx --from gradio_client python trellis2_space.py front.png out.glb
import sys, shutil
from gradio_client import Client, handle_file
src, out = sys.argv[1], sys.argv[2]
c = Client("microsoft/TRELLIS.2", verbose=False)
c.predict(api_name="/start_session")
img = c.predict(handle_file(src), api_name="/preprocess_image")           # background removal + crop
c.predict(handle_file(img), 0, "512", api_name="/image_to_3d")            # 512 = fastest preset
glb, _ = c.predict(100000, 1024, api_name="/extract_glb")                 # decimate + bake texture
shutil.copy(glb, out); print("wrote", out)
