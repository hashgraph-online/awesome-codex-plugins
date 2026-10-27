# Model Registry

Manage model lifecycle with versioning and stage transitions.

### Register Model

```python
import mlflow

# Log and register model
with mlflow.start_run():
    model = train_model()

    # Log model
    mlflow.sklearn.log_model(
        model,
        "model",
        registered_model_name="my-classifier"  # Register immediately
    )

# Or register later
run_id = "abc123"
model_uri = f"runs:/{run_id}/model"
mlflow.register_model(model_uri, "my-classifier")
```

### Model Stages

Transition models between stages: **None** → **Staging** → **Production** → **Archived**

```python
from mlflow.tracking import MlflowClient

client = MlflowClient()

# Promote to staging
client.transition_model_version_stage(
    name="my-classifier",
    version=3,
    stage="Staging"
)

# Promote to production
client.transition_model_version_stage(
    name="my-classifier",
    version=3,
    stage="Production",
    archive_existing_versions=True  # Archive old production versions
)

# Archive model
client.transition_model_version_stage(
    name="my-classifier",
    version=2,
    stage="Archived"
)
```

### Load Model from Registry

```python
import mlflow.pyfunc

# Load latest production model
model = mlflow.pyfunc.load_model("models:/my-classifier/Production")

# Load specific version
model = mlflow.pyfunc.load_model("models:/my-classifier/3")

# Load from staging
model = mlflow.pyfunc.load_model("models:/my-classifier/Staging")

# Use model
predictions = model.predict(X_test)
```

### Model Versioning

```python
client = MlflowClient()

# List all versions
versions = client.search_model_versions("name='my-classifier'")

for v in versions:
    print(f"Version {v.version}: {v.current_stage}")

# Get latest version by stage
latest_prod = client.get_latest_versions("my-classifier", stages=["Production"])
latest_staging = client.get_latest_versions("my-classifier", stages=["Staging"])

# Get model version details
version_info = client.get_model_version(name="my-classifier", version="3")
print(f"Run ID: {version_info.run_id}")
print(f"Stage: {version_info.current_stage}")
print(f"Tags: {version_info.tags}")
```

### Model Annotations

```python
client = MlflowClient()

# Add description
client.update_model_version(
    name="my-classifier",
    version="3",
    description="ResNet50 classifier trained on 1M images with 95% accuracy"
)

# Add tags
client.set_model_version_tag(
    name="my-classifier",
    version="3",
    key="validation_status",
    value="approved"
)

client.set_model_version_tag(
    name="my-classifier",
    version="3",
    key="deployed_date",
    value="2025-01-15"
)
```
