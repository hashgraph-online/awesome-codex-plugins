# Advanced Features

### Embedding Projector

Visualize high-dimensional data (embeddings, features) in 2D/3D.

```python
import torch
from torch.utils.tensorboard import SummaryWriter

# Get embeddings (e.g., word embeddings, image features)
embeddings = model.get_embeddings(data)  # Shape: (N, embedding_dim)

# Metadata (labels for each point)
metadata = ['class_1', 'class_2', 'class_1', ...]

# Images (optional, for image embeddings)
label_images = torch.stack([img1, img2, img3, ...])

# Log to TensorBoard
writer.add_embedding(
    embeddings,
    metadata=metadata,
    label_img=label_images,
    global_step=epoch
)
```

**In TensorBoard:**
- Navigate to "Projector" tab
- Choose PCA, t-SNE, or UMAP visualization
- Search, filter, and explore clusters

### Hyperparameter Tuning

```python
from torch.utils.tensorboard import SummaryWriter

# Try different hyperparameters
for lr in [0.001, 0.01, 0.1]:
    for batch_size in [16, 32, 64]:
        # Create unique run directory
        writer = SummaryWriter(f'runs/lr{lr}_bs{batch_size}')

        # Log hyperparameters
        writer.add_hparams(
            {'lr': lr, 'batch_size': batch_size},
            {'hparam/accuracy': final_acc, 'hparam/loss': final_loss}
        )

        # Train and log
        for epoch in range(10):
            loss = train(lr, batch_size)
            writer.add_scalar('Loss/train', loss, epoch)

        writer.close()

# Compare in TensorBoard's "HParams" tab
```

### Text Logging

```python
# PyTorch: Log text (e.g., model predictions, summaries)
writer.add_text('Predictions', f'Epoch {epoch}: {predictions}', epoch)
writer.add_text('Config', str(config), 0)

# Log markdown tables
markdown_table = """
| Metric | Value |
|--------|-------|
| Accuracy | 0.95 |
| F1 Score | 0.93 |
"""
writer.add_text('Results', markdown_table, epoch)
```

### PR Curves

Precision-Recall curves for classification.

```python
from torch.utils.tensorboard import SummaryWriter

# Get predictions and labels
predictions = model(test_data)  # Shape: (N, num_classes)
labels = test_labels  # Shape: (N,)

# Log PR curve for each class
for i in range(num_classes):
    writer.add_pr_curve(
        f'PR_curve/class_{i}',
        labels == i,
        predictions[:, i],
        global_step=epoch
    )
```
