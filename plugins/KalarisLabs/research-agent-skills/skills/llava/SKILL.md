---
name: llava
description: Large Language and Vision Assistant. Enables visual instruction tuning and image-based conversations. Combines CLIP vision encoder with Vicuna/LLaMA language models. Supports multi-turn image chat, visual question answering, and instruction following. Use for vision-language chatbots or image understanding tasks. Best for conversational image analysis.
license: MIT
metadata:
  version: 1.0.0
  category: multimodal-and-emerging
  maintainer: Kalaris Labs
  tags: LLaVA, Vision-Language, Multimodal, Visual Question Answering, Image Chat, CLIP, Vicuna, Conversational AI, Instruction Tuning, VQA
  dependencies: transformers, torch, pillow
---

# LLaVA - Large Language and Vision Assistant

Open-source vision-language model for conversational image understanding.

## When to use LLaVA

**Use when:**
- Building vision-language chatbots
- Visual question answering (VQA)
- Image description and captioning
- Multi-turn image conversations
- Visual instruction following
- Document understanding with images

**Metrics**:
- GPT-4V level capabilities (targeted)
- Apache 2.0 License
- Multiple model sizes (7B-34B params)

**Use alternatives instead**:
- **GPT-4V**: Highest quality, API-based
- **CLIP**: Simple zero-shot classification
- **BLIP-2**: Better for captioning only
- **Flamingo**: Research, not open-source

## Quick start

### Installation

```bash
# Clone repository
git clone https://github.com/haotian-liu/LLaVA
cd LLaVA

# Install
pip install -e .
```

### Basic usage

```python
from llava.model.builder import load_pretrained_model
from llava.mm_utils import get_model_name_from_path, process_images, tokenizer_image_token
from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN
from llava.conversation import conv_templates
from PIL import Image
import torch

# Load model
model_path = "liuhaotian/llava-v1.5-7b"
tokenizer, model, image_processor, context_len = load_pretrained_model(
    model_path=model_path,
    model_base=None,
    model_name=get_model_name_from_path(model_path)
)

# Load image
image = Image.open("image.jpg")
image_tensor = process_images([image], image_processor, model.config)
image_tensor = image_tensor.to(model.device, dtype=torch.float16)

# Create conversation
conv = conv_templates["llava_v1"].copy()
conv.append_message(conv.roles[0], DEFAULT_IMAGE_TOKEN + "\nWhat is in this image?")
conv.append_message(conv.roles[1], None)
prompt = conv.get_prompt()

# Generate response
input_ids = tokenizer_image_token(prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt').unsqueeze(0).to(model.device)

with torch.inference_mode():
    output_ids = model.generate(
        input_ids,
        images=image_tensor,
        do_sample=True,
        temperature=0.2,
        max_new_tokens=512
    )

response = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
print(response)
```

## Available models

| Model | Parameters | VRAM | Quality |
|-------|------------|------|---------|
| LLaVA-v1.5-7B | 7B | ~14 GB | Good |
| LLaVA-v1.5-13B | 13B | ~28 GB | Better |
| LLaVA-v1.6-34B | 34B | ~70 GB | Best |

```python
# Load different models
model_7b = "liuhaotian/llava-v1.5-7b"
model_13b = "liuhaotian/llava-v1.5-13b"
model_34b = "liuhaotian/llava-v1.6-34b"

# 4-bit quantization for lower VRAM
load_4bit = True  # Reduces VRAM by ~4×
```

## CLI usage

```bash
# Single image query
python -m llava.serve.cli \
    --model-path liuhaotian/llava-v1.5-7b \
    --image-file image.jpg \
    --query "What is in this image?"

# Multi-turn conversation
python -m llava.serve.cli \
    --model-path liuhaotian/llava-v1.5-7b \
    --image-file image.jpg
# Then type questions interactively
```

## Web UI (Gradio)

```bash
# Launch Gradio interface
python -m llava.serve.gradio_web_server \
    --model-path liuhaotian/llava-v1.5-7b \
    --load-4bit  # Optional: reduce VRAM

# Access at http://localhost:7860
```

## Multi-turn conversations

```python
# Initialize conversation
conv = conv_templates["llava_v1"].copy()

# Turn 1
conv.append_message(conv.roles[0], DEFAULT_IMAGE_TOKEN + "\nWhat is in this image?")
conv.append_message(conv.roles[1], None)
response1 = generate(conv, model, image)  # "A dog playing in a park"

# Turn 2
conv.messages[-1][1] = response1  # Add previous response
conv.append_message(conv.roles[0], "What breed is the dog?")
conv.append_message(conv.roles[1], None)
response2 = generate(conv, model, image)  # "Golden Retriever"

# Turn 3
conv.messages[-1][1] = response2
conv.append_message(conv.roles[0], "What time of day is it?")
conv.append_message(conv.roles[1], None)
response3 = generate(conv, model, image)
```

## Common tasks

### Image captioning

```python
question = "Describe this image in detail."
response = ask(model, image, question)
```

### Visual question answering

```python
question = "How many people are in the image?"
response = ask(model, image, question)
```

### Object detection (textual)

```python
question = "List all the objects you can see in this image."
response = ask(model, image, question)
```

### Scene understanding

```python
question = "What is happening in this scene?"
response = ask(model, image, question)
```

### Document understanding

```python
question = "What is the main topic of this document?"
response = ask(model, document_image, question)
```

## Training custom model

```bash
# Stage 1: Feature alignment (558K image-caption pairs)
bash scripts/v1_5/pretrain.sh

# Stage 2: Visual instruction tuning (150K instruction data)
bash scripts/v1_5/finetune.sh
```

## Quantization (reduce VRAM)

```python
# 4-bit quantization
tokenizer, model, image_processor, context_len = load_pretrained_model(
    model_path="liuhaotian/llava-v1.5-13b",
    model_base=None,
    model_name=get_model_name_from_path("liuhaotian/llava-v1.5-13b"),
    load_4bit=True  # Reduces VRAM ~4×
)

# 8-bit quantization
load_8bit=True  # Reduces VRAM ~2×
```

## Best practices

1. **Start with 7B model** - Good quality, manageable VRAM
2. **Use 4-bit quantization** - Reduces VRAM significantly
3. **GPU required** - CPU inference extremely slow
4. **Clear prompts** - Specific questions get better answers
5. **Multi-turn conversations** - Maintain conversation context
6. **Temperature 0.2-0.7** - Balance creativity/consistency
7. **max_new_tokens 512-1024** - For detailed responses
8. **Batch processing** - Process multiple images sequentially

## Performance

| Model | VRAM (FP16) | VRAM (4-bit) | Speed (tokens/s) |
|-------|-------------|--------------|------------------|
| 7B | ~14 GB | ~4 GB | ~20 |
| 13B | ~28 GB | ~8 GB | ~12 |
| 34B | ~70 GB | ~18 GB | ~5 |

*On A100 GPU*

## Benchmarks

LLaVA achieves competitive scores on:
- **VQAv2**: 78.5%
- **GQA**: 62.0%
- **MM-Vet**: 35.4%
- **MMBench**: 64.3%

## Limitations

1. **Hallucinations** - May describe things not in image
2. **Spatial reasoning** - Struggles with precise locations
3. **Small text** - Difficulty reading fine print
4. **Object counting** - Imprecise for many objects
5. **VRAM requirements** - Need powerful GPU
6. **Inference speed** - Slower than CLIP

## Integration with frameworks

### LangChain

```python
from langchain.llms.base import LLM

class LLaVALLM(LLM):
    def _call(self, prompt, stop=None):
        # Custom LLaVA inference
        return response

llm = LLaVALLM()
```

### Gradio App

```python
import gradio as gr

def chat(image, text, history):
    response = ask_llava(model, image, text)
    return response

demo = gr.ChatInterface(
    chat,
    additional_inputs=[gr.Image(type="pil")],
    title="LLaVA Chat"
)
demo.launch()
```

## Resources

- **GitHub**: https://github.com/haotian-liu/LLaVA ⭐ 23,000+
- **Paper**: https://arxiv.org/abs/2304.08485
- **Demo**: https://llava.hliu.cc
- **Models**: https://huggingface.co/liuhaotian
- **License**: Apache 2.0

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
- `blip-2-vision-language`: Explains how to use Salesforce BLIP-2 (Q-Former bridging a frozen image encoder and an LLM such as OPT or FlanT5) through HuggingFace Trans…
- `fine-tuning-with-trl`: Fine-tune LLMs using reinforcement learning with TRL - SFT for instruction tuning, DPO for preference alignment, PPO/GRPO for reward optimi…
