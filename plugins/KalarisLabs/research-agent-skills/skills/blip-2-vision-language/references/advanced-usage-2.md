# Advanced usage

### Batch processing

```python
from PIL import Image
import torch

# Load multiple images
images = [Image.open(f"image_{i}.jpg").convert("RGB") for i in range(4)]
questions = [
    "What is shown in this image?",
    "Describe the scene.",
    "What colors are prominent?",
    "Is there a person in this image?"
]

# Process batch
inputs = processor(
    images=images,
    text=questions,
    return_tensors="pt",
    padding=True
).to("cuda", torch.float16)

# Generate
generated_ids = model.generate(**inputs, max_new_tokens=50)
answers = processor.batch_decode(generated_ids, skip_special_tokens=True)

for q, a in zip(questions, answers):
    print(f"Q: {q}\nA: {a}\n")
```

### Controlling generation

```python
# Control generation parameters
generated_ids = model.generate(
    **inputs,
    max_new_tokens=100,
    min_length=20,
    num_beams=5,              # Beam search
    no_repeat_ngram_size=2,   # Avoid repetition
    top_p=0.9,                # Nucleus sampling
    temperature=0.7,          # Creativity
    do_sample=True,           # Enable sampling
)

# For deterministic output
generated_ids = model.generate(
    **inputs,
    max_new_tokens=50,
    num_beams=5,
    do_sample=False,
)
```

### Memory optimization

```python
# 8-bit quantization
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(load_in_8bit=True)

model = Blip2ForConditionalGeneration.from_pretrained(
    "Salesforce/blip2-opt-6.7b",
    quantization_config=quantization_config,
    device_map="auto"
)

# 4-bit quantization (more aggressive)
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

model = Blip2ForConditionalGeneration.from_pretrained(
    "Salesforce/blip2-flan-t5-xxl",
    quantization_config=quantization_config,
    device_map="auto"
)
```

### Image-text matching

```python
# Using LAVIS for ITM (Image-Text Matching)
from lavis.models import load_model_and_preprocess

model, vis_processors, txt_processors = load_model_and_preprocess(
    name="blip2_image_text_matching",
    model_type="pretrain",
    is_eval=True,
    device=device
)

image = vis_processors["eval"](raw_image).unsqueeze(0).to(device)
text = txt_processors["eval"]("a dog sitting on grass")

# Get matching score
itm_output = model({"image": image, "text_input": text}, match_head="itm")
itm_scores = torch.nn.functional.softmax(itm_output, dim=1)
print(f"Match probability: {itm_scores[:, 1].item():.3f}")
```

### Feature extraction

```python
# Extract image features with Q-Former
from lavis.models import load_model_and_preprocess

model, vis_processors, _ = load_model_and_preprocess(
    name="blip2_feature_extractor",
    model_type="pretrain",
    is_eval=True,
    device=device
)

image = vis_processors["eval"](raw_image).unsqueeze(0).to(device)

# Get features
features = model.extract_features({"image": image}, mode="image")
image_embeds = features.image_embeds  # Shape: [1, 32, 768]
image_features = features.image_embeds_proj  # Projected for matching
```
