---
name: unsloth
description: Provides guidance on fine-tuning large language models with Unsloth, a library for faster, lower-memory training using LoRA and QLoRA, based on its official documentation (references/llms-txt.md). Use when setting up LoRA or QLoRA fine-tuning of an LLM with Unsloth, reducing GPU memory use during training, looking up Unsloth features or APIs, debugging Unsloth training code, or learning Unsloth best practices. Not for general model training with plain Hugging Face Transformers or PEFT without Unsloth.
license: MIT
metadata:
  version: 1.0.0
  category: ml-training
  maintainer: Kalaris Labs
  tags: Fine-Tuning, Unsloth, Fast Training, LoRA, QLoRA, Memory-Efficient, Optimization, Llama, Mistral, Gemma, Qwen
  dependencies: unsloth, torch, transformers, trl, datasets, peft
---

# Unsloth Skill

Comprehensive assistance with unsloth development, generated from official documentation.

## When to Use This Skill

This skill should be triggered when:
- Working with unsloth
- Asking about unsloth features or APIs
- Implementing unsloth solutions
- Debugging unsloth code
- Learning unsloth best practices

## Quick Reference

### Common Patterns

*Quick reference patterns will be added as you use the skill.*

## Reference Files

This skill includes comprehensive documentation in `references/`:

- **llms-txt.md** - Llms-Txt documentation

Use `view` to read specific reference files when detailed information is needed.

## Working with This Skill

### For Beginners
Start with the getting_started or tutorials reference files for foundational concepts.

### For Specific Features
Use the appropriate category reference file (api, guides, etc.) for detailed information.

### For Code Examples
The quick reference section above contains common patterns extracted from the official docs.

## Resources

### references/
Organized documentation extracted from official sources. These files contain:
- Detailed explanations
- Code examples with language annotations
- Links to original documentation
- Table of contents for quick navigation

### scripts/
Add helper scripts here for common automation tasks.

### assets/
Add templates, boilerplate, or example projects here.

## Notes

- This skill was automatically generated from official documentation
- Reference files preserve the structure and examples from source docs
- Code examples include language detection for better syntax highlighting
- Quick reference patterns are extracted from common usage examples in the docs

## Updating

To refresh this skill with updated documentation:
1. Re-run the scraper with the same configuration
2. The skill will be rebuilt with the latest information

<!-- Trigger re-upload 1763621536 -->

## Agent operating procedure

1. **Check the environment.** Check GPU type, memory and driver/CUDA versions (`nvidia-smi`), framework versions, and dataset location and size.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Do a smoke run: tiny model or subset, few steps, and confirm loss decreases and checkpoints save.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Track metrics on held-out data, compare against a baseline, and record seeds, configs and hardware.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| CUDA out-of-memory | Reduce batch size, enable gradient accumulation/checkpointing or mixed precision, or shard the model. |
| Loss is NaN or diverges | Lower the learning rate, check data for invalid values, and enable gradient clipping. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never claim training results without logs; estimate compute cost before launching large jobs.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `llama-factory`: Guides fine-tuning of large language models with LLaMA-Factory, covering the WebUI no-code interface, training across 100+ supported models…
- `peft-fine-tuning`: Fine-tunes LLMs with Hugging Face PEFT, using LoRA, QLoRA, IA3, AdaLoRA, prefix tuning, and prompt tuning so that under 1% of parameters ar…
- `axolotl`: Provides guidance for fine-tuning large language models with Axolotl, covering YAML training configs, LoRA and QLoRA, preference training w…
