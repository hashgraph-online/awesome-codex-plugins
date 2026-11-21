# Inference Patterns

Use this file for the grounded JAX inference patterns.

## SegmentNT

```python
import haiku as hk
import jax
import jax.numpy as jnp
import numpy as np
from nucleotide_transformer.pretrained import get_pretrained_segment_nt_model

jax.config.update("jax_platform_name", "cpu")
devices = jax.devices("cpu")
num_devices = len(devices)

# Example no-N sequence length (bp).
sequence_length_bp = 32_764

# SegmentNT tokenizer (k=6) exact token count for no-N inputs.
num_dna_tokens_excluding_cls = (sequence_length_bp // 6) + (sequence_length_bp % 6)
assert num_dna_tokens_excluding_cls % 4 == 0

# For long-context inference, docs use: rescaling_factor = num_tokens_inference / 2048.
# Here num_tokens_inference includes CLS.
num_tokens_inference = num_dna_tokens_excluding_cls + 1
rescaling_factor = (num_tokens_inference / 2048) if num_tokens_inference > 5001 else None

parameters, forward_fn, tokenizer, config = get_pretrained_segment_nt_model(
    model_name="segment_nt",
    rescaling_factor=rescaling_factor,
    embeddings_layers_to_save=(29,),
    attention_maps_to_save=((1, 4), (7, 10)),
    max_positions=num_tokens_inference,
)
forward_fn = hk.transform(forward_fn)
apply_fn = jax.pmap(forward_fn.apply, devices=devices, donate_argnums=(0,))

sequences = ["A" * sequence_length_bp]
tokens_ids = [b[1] for b in tokenizer.batch_tokenize(sequences)]
tokens = jnp.stack([jnp.asarray(tokens_ids, dtype=jnp.int32)] * num_devices, axis=0)

random_key = jax.random.PRNGKey(seed=0)
keys = jax.device_put_replicated(random_key, devices=devices)
parameters = jax.device_put_replicated(parameters, devices=devices)

outs = apply_fn(parameters, keys, tokens)
logits = outs["logits"]
probabilities = np.asarray(jax.nn.softmax(logits, axis=-1))[..., -1]

idx_intron = config.features.index("intron")
probabilities_intron = probabilities[..., idx_intron]
```

Notes:

- `segment_nt_multi_species` is selected via `model_name`; this JAX path does not take a runtime species token.
- For region plotting, map coordinates from the returned tensor length rather than assuming exact bp parity.

## SegmentEnformer

```python
import haiku as hk
import jax
import jax.numpy as jnp
import numpy as np
from nucleotide_transformer.enformer.features import FEATURES
from nucleotide_transformer.enformer.pretrained import get_pretrained_segment_enformer_model

jax.config.update("jax_platform_name", "cpu")
devices = jax.devices("cpu")
num_devices = len(devices)

parameters, state, forward_fn, tokenizer, config = get_pretrained_segment_enformer_model()
forward_fn = hk.transform_with_state(forward_fn)
apply_fn = jax.pmap(forward_fn.apply, devices=devices, donate_argnums=(0,))

random_key = jax.random.PRNGKey(seed=0)
keys = jax.device_put_replicated(random_key, devices=devices)
parameters = jax.device_put_replicated(parameters, devices=devices)
state = jax.device_put_replicated(state, devices=devices)

sequences = ["A" * 196_608]
tokens_ids = [b[1] for b in tokenizer.batch_tokenize(sequences)]
tokens = jnp.stack([jnp.asarray(tokens_ids, dtype=jnp.int32)] * num_devices, axis=0)

outs, state = apply_fn(parameters, state, keys, tokens)
logits = outs["logits"]
probabilities = np.asarray(jax.nn.softmax(logits, axis=-1))[..., -1]

idx_intron = FEATURES.index("intron")
probabilities_intron = probabilities[..., idx_intron]
```

## SegmentBorzoi

```python
import haiku as hk
import jax
import jax.numpy as jnp
import numpy as np
from nucleotide_transformer.borzoi.pretrained import get_pretrained_segment_borzoi_model
from nucleotide_transformer.enformer.features import FEATURES

jax.config.update("jax_platform_name", "cpu")
devices = jax.devices("cpu")
num_devices = len(devices)

parameters, state, forward_fn, tokenizer, config = get_pretrained_segment_borzoi_model()
forward_fn = hk.transform_with_state(forward_fn)
apply_fn = jax.pmap(forward_fn.apply, devices=devices, donate_argnums=(0,))

random_key = jax.random.PRNGKey(seed=0)
keys = jax.device_put_replicated(random_key, devices=devices)
parameters = jax.device_put_replicated(parameters, devices=devices)
state = jax.device_put_replicated(state, devices=devices)

sequences = ["A" * 524_288]
tokens_ids = [b[1] for b in tokenizer.batch_tokenize(sequences)]
tokens = jnp.stack([jnp.asarray(tokens_ids, dtype=jnp.int32)] * num_devices, axis=0)

outs, state = apply_fn(parameters, state, keys, tokens)
logits = outs["logits"]
probabilities = np.asarray(jax.nn.softmax(logits, axis=-1))[..., -1]

idx_intron = FEATURES.index("intron")
probabilities_intron = probabilities[..., idx_intron]
```
