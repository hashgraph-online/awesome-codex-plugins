---
name: stable-diffusion-image-generation
description: Generates images with Stable Diffusion models (SD 1.5, SDXL, SD 3.0, Flux) through the HuggingFace Diffusers library, covering text-to-image, image-to-image, inpainting, outpainting, ControlNet conditioning, LoRA adapters, scheduler swapping, and GPU memory optimization. Use when generating images from text prompts, transforming or restyling an existing image, filling masked regions of an image, adding spatial control from edges, poses, or depth maps, loading LoRA style adapters, or fixing out-of-memory and black-image errors in a Diffusers pipeline. Not for API-only generation without a GPU, where DALL-E 3 fits better.
license: MIT
metadata:
  version: 1.0.0
  category: multimodal-and-emerging
  maintainer: Kalaris Labs
  tags: Image Generation, Stable Diffusion, Diffusers, Text-to-Image, Multimodal, Computer Vision
  dependencies: diffusers>=0.30.0, transformers>=4.41.0, accelerate>=0.31.0, torch>=2.0.0
---

# Stable Diffusion Image Generation

Comprehensive guide to generating images with Stable Diffusion using the HuggingFace Diffusers library.

## When to use Stable Diffusion

**Use Stable Diffusion when:**
- Generating images from text descriptions
- Performing image-to-image translation (style transfer, enhancement)
- Inpainting (filling in masked regions)
- Outpainting (extending images beyond boundaries)
- Creating variations of existing images
- Building custom image generation workflows

**Key features:**
- **Text-to-Image**: Generate images from natural language prompts
- **Image-to-Image**: Transform existing images with text guidance
- **Inpainting**: Fill masked regions with context-aware content
- **ControlNet**: Add spatial conditioning (edges, poses, depth)
- **LoRA Support**: Efficient fine-tuning and style adaptation
- **Multiple Models**: SD 1.5, SDXL, SD 3.0, Flux support

**Use alternatives instead:**
- **DALL-E 3**: For API-based generation without GPU
- **Midjourney**: For artistic, stylized outputs
- **Imagen**: For Google Cloud integration
- **Leonardo.ai**: For web-based creative workflows

## Quick start

### Installation

```bash
pip install diffusers transformers accelerate torch
pip install xformers  # Optional: memory-efficient attention
```

### Basic text-to-image

```python
from diffusers import DiffusionPipeline
import torch

# Load pipeline (auto-detects model type)
pipe = DiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16
)
pipe.to("cuda")

# Generate image
image = pipe(
    "A serene mountain landscape at sunset, highly detailed",
    num_inference_steps=50,
    guidance_scale=7.5
).images[0]

image.save("output.png")
```

### Using SDXL (higher quality)

```python
from diffusers import AutoPipelineForText2Image
import torch

pipe = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe.to("cuda")

# Enable memory optimization
pipe.enable_model_cpu_offload()

image = pipe(
    prompt="A futuristic city with flying cars, cinematic lighting",
    height=1024,
    width=1024,
    num_inference_steps=30
).images[0]
```

## Architecture overview

### Three-pillar design

Diffusers is built around three core components:

```
Pipeline (orchestration)
├── Model (neural networks)
│   ├── UNet / Transformer (noise prediction)
│   ├── VAE (latent encoding/decoding)
│   └── Text Encoder (CLIP/T5)
└── Scheduler (denoising algorithm)
```

### Pipeline inference flow

```
Text Prompt → Text Encoder → Text Embeddings
                                    ↓
Random Noise → [Denoising Loop] ← Scheduler
                      ↓
               Predicted Noise
                      ↓
              VAE Decoder → Final Image
```

## Core concepts

### Pipelines

Pipelines orchestrate complete workflows:

| Pipeline | Purpose |
|----------|---------|
| `StableDiffusionPipeline` | Text-to-image (SD 1.x/2.x) |
| `StableDiffusionXLPipeline` | Text-to-image (SDXL) |
| `StableDiffusion3Pipeline` | Text-to-image (SD 3.0) |
| `FluxPipeline` | Text-to-image (Flux models) |
| `StableDiffusionImg2ImgPipeline` | Image-to-image |
| `StableDiffusionInpaintPipeline` | Inpainting |

### Schedulers

Schedulers control the denoising process:

| Scheduler | Steps | Quality | Use Case |
|-----------|-------|---------|----------|
| `EulerDiscreteScheduler` | 20-50 | Good | Default choice |
| `EulerAncestralDiscreteScheduler` | 20-50 | Good | More variation |
| `DPMSolverMultistepScheduler` | 15-25 | Excellent | Fast, high quality |
| `DDIMScheduler` | 50-100 | Good | Deterministic |
| `LCMScheduler` | 4-8 | Good | Very fast |
| `UniPCMultistepScheduler` | 15-25 | Excellent | Fast convergence |

### Swapping schedulers

```python
from diffusers import DPMSolverMultistepScheduler

# Swap for faster generation
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config
)

# Now generate with fewer steps
image = pipe(prompt, num_inference_steps=20).images[0]
```

## Generation parameters

Details, code examples and parameter tables: [references/generation-parameters.md](references/generation-parameters.md). Read it when this step applies.

## Image-to-image

Transform existing images with text guidance:

```python
from diffusers import AutoPipelineForImage2Image
from PIL import Image

pipe = AutoPipelineForImage2Image.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda")

init_image = Image.open("input.jpg").resize((512, 512))

image = pipe(
    prompt="A watercolor painting of the scene",
    image=init_image,
    strength=0.75,  # How much to transform (0-1)
    num_inference_steps=50
).images[0]
```

## Inpainting

Fill masked regions:

```python
from diffusers import AutoPipelineForInpainting
from PIL import Image

pipe = AutoPipelineForInpainting.from_pretrained(
    "runwayml/stable-diffusion-inpainting",
    torch_dtype=torch.float16
).to("cuda")

image = Image.open("photo.jpg")
mask = Image.open("mask.png")  # White = inpaint region

result = pipe(
    prompt="A red car parked on the street",
    image=image,
    mask_image=mask,
    num_inference_steps=50
).images[0]
```

## ControlNet

Details, code examples and parameter tables: [references/controlnet.md](references/controlnet.md). Read it when this step applies.

## LoRA adapters

Load fine-tuned style adapters:

```python
from diffusers import DiffusionPipeline

pipe = DiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda")

# Load LoRA weights
pipe.load_lora_weights("path/to/lora", weight_name="style.safetensors")

# Generate with LoRA style
image = pipe("A portrait in the trained style").images[0]

# Adjust LoRA strength
pipe.fuse_lora(lora_scale=0.8)

# Unload LoRA
pipe.unload_lora_weights()
```

### Multiple LoRAs

```python
# Load multiple LoRAs
pipe.load_lora_weights("lora1", adapter_name="style")
pipe.load_lora_weights("lora2", adapter_name="character")

# Set weights for each
pipe.set_adapters(["style", "character"], adapter_weights=[0.7, 0.5])

image = pipe("A portrait").images[0]
```

## Memory optimization

### Enable CPU offloading

```python
# Model CPU offload - moves models to CPU when not in use
pipe.enable_model_cpu_offload()

# Sequential CPU offload - more aggressive, slower
pipe.enable_sequential_cpu_offload()
```

### Attention slicing

```python
# Reduce memory by computing attention in chunks
pipe.enable_attention_slicing()

# Or specific chunk size
pipe.enable_attention_slicing("max")
```

### xFormers memory-efficient attention

```python
# Requires xformers package
pipe.enable_xformers_memory_efficient_attention()
```

### VAE slicing for large images

```python
# Decode latents in tiles for large images
pipe.enable_vae_slicing()
pipe.enable_vae_tiling()
```

## Model variants

### Loading different precisions

```python
# FP16 (recommended for GPU)
pipe = DiffusionPipeline.from_pretrained(
    "model-id",
    torch_dtype=torch.float16,
    variant="fp16"
)

# BF16 (better precision, requires Ampere+ GPU)
pipe = DiffusionPipeline.from_pretrained(
    "model-id",
    torch_dtype=torch.bfloat16
)
```

### Loading specific components

```python
from diffusers import UNet2DConditionModel, AutoencoderKL

# Load custom VAE
vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse")

# Use with pipeline
pipe = DiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    vae=vae,
    torch_dtype=torch.float16
)
```

## Batch generation

Generate multiple images efficiently:

```python
# Multiple prompts
prompts = [
    "A cat playing piano",
    "A dog reading a book",
    "A bird painting a picture"
]

images = pipe(prompts, num_inference_steps=30).images

# Multiple images per prompt
images = pipe(
    "A beautiful sunset",
    num_images_per_prompt=4,
    num_inference_steps=30
).images
```

## Common workflows

### Workflow 1: High-quality generation

```python
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
import torch

# 1. Load SDXL with optimizations
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16"
)
pipe.to("cuda")
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_model_cpu_offload()

# 2. Generate with quality settings
image = pipe(
    prompt="A majestic lion in the savanna, golden hour lighting, 8k, detailed fur",
    negative_prompt="blurry, low quality, cartoon, anime, sketch",
    num_inference_steps=30,
    guidance_scale=7.5,
    height=1024,
    width=1024
).images[0]
```

### Workflow 2: Fast prototyping

```python
from diffusers import AutoPipelineForText2Image, LCMScheduler
import torch

# Use LCM for 4-8 step generation
pipe = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16
).to("cuda")

# Load LCM LoRA for fast generation
pipe.load_lora_weights("latent-consistency/lcm-lora-sdxl")
pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
pipe.fuse_lora()

# Generate in ~1 second
image = pipe(
    "A beautiful landscape",
    num_inference_steps=4,
    guidance_scale=1.0
).images[0]
```

## Common issues

**CUDA out of memory:**
```python
# Enable memory optimizations
pipe.enable_model_cpu_offload()
pipe.enable_attention_slicing()
pipe.enable_vae_slicing()

# Or use lower precision
pipe = DiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
```

**Black/noise images:**
```python
# Check VAE configuration
# Use safety checker bypass if needed
pipe.safety_checker = None

# Ensure proper dtype consistency
pipe = pipe.to(dtype=torch.float16)
```

**Slow generation:**
```python
# Use faster scheduler
from diffusers import DPMSolverMultistepScheduler
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

# Reduce steps
image = pipe(prompt, num_inference_steps=20).images[0]
```

## References

- **[Advanced Usage](references/advanced-usage.md)** - Custom pipelines, fine-tuning, deployment
- **[Troubleshooting](references/troubleshooting.md)** - Common issues and solutions

## Resources

- **Documentation**: https://huggingface.co/docs/diffusers
- **Repository**: https://github.com/huggingface/diffusers
- **Model Hub**: https://huggingface.co/models?library=diffusers
- **Discord**: https://discord.gg/diffusers

## Agent operating procedure

1. **Check the environment.** Confirm GPU memory, model checkpoint and licence, framework versions and input formats.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Run inference on a single sample at low resolution or short length first.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Inspect outputs qualitatively and with task metrics; check licence restrictions for generated content.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Out-of-memory on large inputs | Reduce resolution or sequence length, use half precision, or tile the input. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Check model and dataset licences before commercial or published use.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `peft-fine-tuning`: Fine-tunes LLMs with Hugging Face PEFT, using LoRA, QLoRA, IA3, AdaLoRA, prefix tuning, and prompt tuning so that under 1% of parameters ar…
- `blip-2-vision-language`: Explains how to use Salesforce BLIP-2 (Q-Former bridging a frozen image encoder and an LLM such as OPT or FlanT5) through HuggingFace Trans…
- `fine-tuning-openvla-oft`: Fine-tunes and evaluates OpenVLA-OFT and OpenVLA-OFT+ policies for robot action generation with continuous action heads, LoRA adaptation, a…
