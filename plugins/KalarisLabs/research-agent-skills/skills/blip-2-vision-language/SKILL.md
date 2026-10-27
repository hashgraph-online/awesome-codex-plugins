---
name: blip-2-vision-language
description: Explains how to use Salesforce BLIP-2 (Q-Former bridging a frozen image encoder and an LLM such as OPT or FlanT5) through HuggingFace Transformers and LAVIS for image captioning, visual question answering, image-text matching, and feature extraction. Use when generating captions for images, building a VQA system, doing zero-shot image-text understanding without task-specific training, matching or retrieving images against text, or fitting a BLIP-2 model into limited GPU memory with INT8/INT4 quantization. Prefer LLaVA or InstructBLIP for instruction-following multimodal chat, and CLIP for plain image-text similarity.
license: MIT
metadata:
  version: 1.0.0
  category: multimodal-and-emerging
  maintainer: Kalaris Labs
  tags: Multimodal, Vision-Language, Image Captioning, VQA, Zero-Shot
  dependencies: transformers>=4.30.0, torch>=1.10.0, Pillow
---

# BLIP-2: Vision-Language Pre-training

Comprehensive guide to using Salesforce's BLIP-2 for vision-language tasks with frozen image encoders and large language models.

## When to use BLIP-2

**Use BLIP-2 when:**
- Need high-quality image captioning with natural descriptions
- Building visual question answering (VQA) systems
- Require zero-shot image-text understanding without task-specific training
- Want to leverage LLM reasoning for visual tasks
- Building multimodal conversational AI
- Need image-text retrieval or matching

**Key features:**
- **Q-Former architecture**: Lightweight query transformer bridges vision and language
- **Frozen backbone efficiency**: No need to fine-tune large vision/language models
- **Multiple LLM backends**: OPT (2.7B, 6.7B) and FlanT5 (XL, XXL)
- **Zero-shot capabilities**: Strong performance without task-specific training
- **Efficient training**: Only trains Q-Former (~188M parameters)
- **State-of-the-art results**: Beats larger models on VQA benchmarks

**Use alternatives instead:**
- **LLaVA**: For instruction-following multimodal chat
- **InstructBLIP**: For improved instruction-following (BLIP-2 successor)
- **GPT-4V/Claude 3**: For production multimodal chat (proprietary)
- **CLIP**: For simple image-text similarity without generation
- **Flamingo**: For few-shot visual learning

## Quick start

### Installation

```bash
# HuggingFace Transformers (recommended)
pip install transformers accelerate torch Pillow

# Or LAVIS library (Salesforce official)
pip install salesforce-lavis
```

### Basic image captioning

```python
import torch
from PIL import Image
from transformers import Blip2Processor, Blip2ForConditionalGeneration

# Load model and processor
processor = Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
model = Blip2ForConditionalGeneration.from_pretrained(
    "Salesforce/blip2-opt-2.7b",
    torch_dtype=torch.float16,
    device_map="auto"
)

# Load image
image = Image.open("photo.jpg").convert("RGB")

# Generate caption
inputs = processor(images=image, return_tensors="pt").to("cuda", torch.float16)
generated_ids = model.generate(**inputs, max_new_tokens=50)
caption = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
print(caption)
```

### Visual question answering

```python
# Ask a question about the image
question = "What color is the car in this image?"

inputs = processor(images=image, text=question, return_tensors="pt").to("cuda", torch.float16)
generated_ids = model.generate(**inputs, max_new_tokens=50)
answer = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
print(answer)
```

### Using LAVIS library

```python
import torch
from lavis.models import load_model_and_preprocess
from PIL import Image

# Load model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model, vis_processors, txt_processors = load_model_and_preprocess(
    name="blip2_opt",
    model_type="pretrain_opt2.7b",
    is_eval=True,
    device=device
)

# Process image
image = Image.open("photo.jpg").convert("RGB")
image = vis_processors["eval"](image).unsqueeze(0).to(device)

# Caption
caption = model.generate({"image": image})
print(caption)

# VQA
question = txt_processors["eval"]("What is in this image?")
answer = model.generate({"image": image, "prompt": question})
print(answer)
```

## Core concepts

### Architecture overview

```
BLIP-2 Architecture:
┌─────────────────────────────────────────────────────────────┐
│                        Q-Former                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │     Learned Queries (32 queries × 768 dim)          │    │
│  └────────────────────────┬────────────────────────────┘    │
│                           │                                  │
│  ┌────────────────────────▼────────────────────────────┐    │
│  │    Cross-Attention with Image Features               │    │
│  └────────────────────────┬────────────────────────────┘    │
│                           │                                  │
│  ┌────────────────────────▼────────────────────────────┐    │
│  │    Self-Attention Layers (Transformer)               │    │
│  └────────────────────────┬────────────────────────────┘    │
└───────────────────────────┼─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  Frozen Vision Encoder    │      Frozen LLM                  │
│  (ViT-G/14 from EVA-CLIP) │      (OPT or FlanT5)            │
└─────────────────────────────────────────────────────────────┘
```

### Model variants

| Model | LLM Backend | Size | Use Case |
|-------|-------------|------|----------|
| `blip2-opt-2.7b` | OPT-2.7B | ~4GB | General captioning, VQA |
| `blip2-opt-6.7b` | OPT-6.7B | ~8GB | Better reasoning |
| `blip2-flan-t5-xl` | FlanT5-XL | ~5GB | Instruction following |
| `blip2-flan-t5-xxl` | FlanT5-XXL | ~13GB | Best quality |

### Q-Former components

| Component | Description | Parameters |
|-----------|-------------|------------|
| Learned queries | Fixed set of learnable embeddings | 32 × 768 |
| Image transformer | Cross-attention to vision features | ~108M |
| Text transformer | Self-attention for text | ~108M |
| Linear projection | Maps to LLM dimension | Varies |

## Advanced usage

Details, code examples and parameter tables: [references/advanced-usage-2.md](references/advanced-usage-2.md). Read it when this step applies.

## Common workflows

### Workflow 1: Image captioning pipeline

```python
import torch
from PIL import Image
from transformers import Blip2Processor, Blip2ForConditionalGeneration
from pathlib import Path

class ImageCaptioner:
    def __init__(self, model_name="Salesforce/blip2-opt-2.7b"):
        self.processor = Blip2Processor.from_pretrained(model_name)
        self.model = Blip2ForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )

    def caption(self, image_path: str, prompt: str = None) -> str:
        image = Image.open(image_path).convert("RGB")

        if prompt:
            inputs = self.processor(images=image, text=prompt, return_tensors="pt")
        else:
            inputs = self.processor(images=image, return_tensors="pt")

        inputs = inputs.to("cuda", torch.float16)

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=50,
            num_beams=5
        )

        return self.processor.decode(generated_ids[0], skip_special_tokens=True)

    def caption_batch(self, image_paths: list, prompt: str = None) -> list:
        images = [Image.open(p).convert("RGB") for p in image_paths]

        if prompt:
            inputs = self.processor(
                images=images,
                text=[prompt] * len(images),
                return_tensors="pt",
                padding=True
            )
        else:
            inputs = self.processor(images=images, return_tensors="pt", padding=True)

        inputs = inputs.to("cuda", torch.float16)

        generated_ids = self.model.generate(**inputs, max_new_tokens=50)
        return self.processor.batch_decode(generated_ids, skip_special_tokens=True)

# Usage
captioner = ImageCaptioner()

# Single image
caption = captioner.caption("photo.jpg")
print(f"Caption: {caption}")

# With prompt for style
caption = captioner.caption("photo.jpg", "a detailed description of")
print(f"Detailed: {caption}")

# Batch processing
captions = captioner.caption_batch(["img1.jpg", "img2.jpg", "img3.jpg"])
for i, cap in enumerate(captions):
    print(f"Image {i+1}: {cap}")
```

### Workflow 2: Visual Q&A system

```python
class VisualQA:
    def __init__(self, model_name="Salesforce/blip2-flan-t5-xl"):
        self.processor = Blip2Processor.from_pretrained(model_name)
        self.model = Blip2ForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        self.current_image = None
        self.current_inputs = None

    def set_image(self, image_path: str):
        """Load image for multiple questions."""
        self.current_image = Image.open(image_path).convert("RGB")

    def ask(self, question: str) -> str:
        """Ask a question about the current image."""
        if self.current_image is None:
            raise ValueError("No image set. Call set_image() first.")

        # Format question for FlanT5
        prompt = f"Question: {question} Answer:"

        inputs = self.processor(
            images=self.current_image,
            text=prompt,
            return_tensors="pt"
        ).to("cuda", torch.float16)

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=50,
            num_beams=5
        )

        return self.processor.decode(generated_ids[0], skip_special_tokens=True)

    def ask_multiple(self, questions: list) -> dict:
        """Ask multiple questions about current image."""
        return {q: self.ask(q) for q in questions}

# Usage
vqa = VisualQA()
vqa.set_image("scene.jpg")

# Ask questions
print(vqa.ask("What objects are in this image?"))
print(vqa.ask("What is the weather like?"))
print(vqa.ask("How many people are there?"))

# Batch questions
results = vqa.ask_multiple([
    "What is the main subject?",
    "What colors are dominant?",
    "Is this indoors or outdoors?"
])
```

### Workflow 3: Image search/retrieval

```python
import torch
import numpy as np
from PIL import Image
from lavis.models import load_model_and_preprocess

class ImageSearchEngine:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model, self.vis_processors, self.txt_processors = load_model_and_preprocess(
            name="blip2_feature_extractor",
            model_type="pretrain",
            is_eval=True,
            device=self.device
        )
        self.image_features = []
        self.image_paths = []

    def index_images(self, image_paths: list):
        """Build index from images."""
        self.image_paths = image_paths

        for path in image_paths:
            image = Image.open(path).convert("RGB")
            image = self.vis_processors["eval"](image).unsqueeze(0).to(self.device)

            with torch.no_grad():
                features = self.model.extract_features({"image": image}, mode="image")
                # Use projected features for matching
                self.image_features.append(
                    features.image_embeds_proj.mean(dim=1).cpu().numpy()
                )

        self.image_features = np.vstack(self.image_features)

    def search(self, query: str, top_k: int = 5) -> list:
        """Search images by text query."""
        # Get text features
        text = self.txt_processors["eval"](query)
        text_input = {"text_input": [text]}

        with torch.no_grad():
            text_features = self.model.extract_features(text_input, mode="text")
            text_embeds = text_features.text_embeds_proj[:, 0].cpu().numpy()

        # Compute similarities
        similarities = np.dot(self.image_features, text_embeds.T).squeeze()
        top_indices = np.argsort(similarities)[::-1][:top_k]

        return [(self.image_paths[i], similarities[i]) for i in top_indices]

# Usage
engine = ImageSearchEngine()
engine.index_images(["img1.jpg", "img2.jpg", "img3.jpg", ...])

# Search
results = engine.search("a sunset over the ocean", top_k=5)
for path, score in results:
    print(f"{path}: {score:.3f}")
```

## Output format

### Generation output

```python
# Direct generation returns token IDs
generated_ids = model.generate(**inputs, max_new_tokens=50)
# Shape: [batch_size, sequence_length]

# Decode to text
text = processor.batch_decode(generated_ids, skip_special_tokens=True)
# Returns: list of strings
```

### Feature extraction output

```python
# Q-Former outputs
features = model.extract_features({"image": image}, mode="image")

features.image_embeds          # [B, 32, 768] - Q-Former outputs
features.image_embeds_proj     # [B, 32, 256] - Projected for matching
features.text_embeds          # [B, seq_len, 768] - Text features
features.text_embeds_proj     # [B, 256] - Projected text (CLS)
```

## Performance optimization

### GPU memory requirements

| Model | FP16 VRAM | INT8 VRAM | INT4 VRAM |
|-------|-----------|-----------|-----------|
| blip2-opt-2.7b | ~8GB | ~5GB | ~3GB |
| blip2-opt-6.7b | ~16GB | ~9GB | ~5GB |
| blip2-flan-t5-xl | ~10GB | ~6GB | ~4GB |
| blip2-flan-t5-xxl | ~26GB | ~14GB | ~8GB |

### Speed optimization

```python
# Use Flash Attention if available
model = Blip2ForConditionalGeneration.from_pretrained(
    "Salesforce/blip2-opt-2.7b",
    torch_dtype=torch.float16,
    attn_implementation="flash_attention_2",  # Requires flash-attn
    device_map="auto"
)

# Compile model (PyTorch 2.0+)
model = torch.compile(model)

# Use smaller images (if quality allows)
processor = Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
# Default is 224x224, which is optimal
```

## Common issues

| Issue | Solution |
|-------|----------|
| CUDA OOM | Use INT8/INT4 quantization, smaller model |
| Slow generation | Use greedy decoding, reduce max_new_tokens |
| Poor captions | Try FlanT5 variant, use prompts |
| Hallucinations | Lower temperature, use beam search |
| Wrong answers | Rephrase question, provide context |

## References

- **[Advanced Usage](references/advanced-usage.md)** - Fine-tuning, integration, deployment
- **[Troubleshooting](references/troubleshooting.md)** - Common issues and solutions

## Resources

- **Paper**: https://arxiv.org/abs/2301.12597
- **GitHub (LAVIS)**: https://github.com/salesforce/LAVIS
- **HuggingFace**: https://huggingface.co/Salesforce/blip2-opt-2.7b
- **Demo**: https://huggingface.co/spaces/Salesforce/BLIP2
- **InstructBLIP**: https://arxiv.org/abs/2305.06500 (successor)

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

- `clip`: OpenAI's model connecting vision and language.
- `llava`: Large Language and Vision Assistant.
- `quantizing-models-bitsandbytes`: Quantizes LLMs to 8-bit or 4-bit for 50-75% memory reduction with minimal accuracy loss.
