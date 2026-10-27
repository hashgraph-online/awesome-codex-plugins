# Advanced Patterns

### Mixtral 8x7B Architecture

```python
class MixtralMoEBlock(nn.Module):
    """Mixtral-style MoE block with 8 experts, top-2 routing."""

    def __init__(self, config):
        super().__init__()
        self.hidden_dim = config.hidden_size
        self.ffn_dim = config.intermediate_size
        self.num_experts = config.num_local_experts  # 8
        self.top_k = config.num_experts_per_tok       # 2

        # 8 expert FFNs
        self.experts = nn.ModuleList([
            nn.Sequential(
                nn.Linear(self.hidden_dim, self.ffn_dim, bias=False),
                nn.SiLU(),
                nn.Linear(self.ffn_dim, self.hidden_dim, bias=False)
            )
            for _ in range(self.num_experts)
        ])

        # Router
        self.gate = nn.Linear(self.hidden_dim, self.num_experts, bias=False)

    def forward(self, hidden_states):
        batch_size, sequence_length, hidden_dim = hidden_states.shape

        # Flatten
        hidden_states = hidden_states.view(-1, hidden_dim)

        # Router logits
        router_logits = self.gate(hidden_states)  # (batch * seq_len, num_experts)

        # Softmax and top-2
        routing_weights = torch.softmax(router_logits, dim=1)
        routing_weights, selected_experts = torch.topk(routing_weights, self.top_k, dim=-1)

        # Normalize routing weights
        routing_weights /= routing_weights.sum(dim=-1, keepdim=True)

        # Initialize output
        final_hidden_states = torch.zeros_like(hidden_states)

        # Route to experts
        for expert_idx in range(self.num_experts):
            expert_layer = self.experts[expert_idx]
            idx, top_x = torch.where(selected_experts == expert_idx)

            if idx.shape[0] == 0:
                continue

            # Current expert tokens
            current_hidden_states = hidden_states[idx]

            # Expert forward
            current_hidden_states = expert_layer(current_hidden_states)

            # Weighted by routing scores
            current_hidden_states *= routing_weights[idx, top_x, None]

            # Accumulate
            final_hidden_states.index_add_(0, idx, current_hidden_states)

        # Reshape
        return final_hidden_states.view(batch_size, sequence_length, hidden_dim)
```

### PR-MoE (Pyramid-Residual-MoE)

```bash
# DeepSpeed PR-MoE: 3x better parameter efficiency
deepspeed pretrain_gpt_moe.py \
  --num-layers 24 \
  --hidden-size 1024 \
  --num-attention-heads 16 \
  --num-experts "[128, 64, 32, 16]" \
  --mlp-type residual \
  --moe-expert-parallel-size 4 \
  --moe-loss-coeff 0.01 \
  --fp16
```
