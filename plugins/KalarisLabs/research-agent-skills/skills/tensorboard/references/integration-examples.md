# Integration Examples

### PyTorch Training Loop

```python
import torch
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter

# Setup
writer = SummaryWriter('runs/resnet_experiment')
model = ResNet50()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

# Log model graph
dummy_input = torch.randn(1, 3, 224, 224)
writer.add_graph(model, dummy_input)

# Training loop
for epoch in range(50):
    model.train()
    train_loss = 0.0
    train_correct = 0

    for batch_idx, (data, target) in enumerate(train_loader):
        optimizer.zero_grad()
        output = model(data)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()

        train_loss += loss.item()
        pred = output.argmax(dim=1)
        train_correct += pred.eq(target).sum().item()

        # Log batch metrics (every 100 batches)
        if batch_idx % 100 == 0:
            global_step = epoch * len(train_loader) + batch_idx
            writer.add_scalar('Loss/train_batch', loss.item(), global_step)

    # Epoch metrics
    train_loss /= len(train_loader)
    train_acc = train_correct / len(train_loader.dataset)

    # Validation
    model.eval()
    val_loss = 0.0
    val_correct = 0

    with torch.no_grad():
        for data, target in val_loader:
            output = model(data)
            val_loss += criterion(output, target).item()
            pred = output.argmax(dim=1)
            val_correct += pred.eq(target).sum().item()

    val_loss /= len(val_loader)
    val_acc = val_correct / len(val_loader.dataset)

    # Log epoch metrics
    writer.add_scalars('Loss', {'train': train_loss, 'val': val_loss}, epoch)
    writer.add_scalars('Accuracy', {'train': train_acc, 'val': val_acc}, epoch)

    # Log learning rate
    writer.add_scalar('Learning_rate', optimizer.param_groups[0]['lr'], epoch)

    # Log histograms (every 5 epochs)
    if epoch % 5 == 0:
        for name, param in model.named_parameters():
            writer.add_histogram(name, param, epoch)

    # Log sample predictions
    if epoch % 10 == 0:
        sample_images = data[:8]
        writer.add_image('Sample_inputs', make_grid(sample_images), epoch)

writer.close()
```

### TensorFlow/Keras Training

```python
import tensorflow as tf

# Define model
model = tf.keras.models.Sequential([
    tf.keras.layers.Conv2D(32, 3, activation='relu', input_shape=(28, 28, 1)),
    tf.keras.layers.MaxPooling2D(),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dense(10, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# TensorBoard callback
tensorboard_callback = tf.keras.callbacks.TensorBoard(
    log_dir='logs/fit',
    histogram_freq=1,          # Log histograms every epoch
    write_graph=True,          # Visualize model graph
    write_images=True,         # Visualize weights as images
    update_freq='epoch',       # Log metrics every epoch
    profile_batch='500,520',   # Profile batches 500-520
    embeddings_freq=1          # Log embeddings every epoch
)

# Train
model.fit(
    x_train, y_train,
    epochs=10,
    validation_data=(x_val, y_val),
    callbacks=[tensorboard_callback]
)
```
