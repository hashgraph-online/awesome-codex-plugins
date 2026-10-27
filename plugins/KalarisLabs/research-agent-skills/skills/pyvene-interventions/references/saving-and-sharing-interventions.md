# Saving and Sharing Interventions

```python
# Save locally
intervenable.save("./my_intervention")

# Load from local
intervenable = pv.IntervenableModel.load(
    "./my_intervention",
    model=model,
)

# Share on HuggingFace
intervenable.save_intervention("username/my-intervention")

# Load from HuggingFace
intervenable = pv.IntervenableModel.load(
    "username/my-intervention",
    model=model,
)
```
