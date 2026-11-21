#!/usr/bin/env python3
"""NTv3 CSV binary classification full training entrypoint.

This script fine-tunes an NTv3 pretrained backbone on sequence,label CSV data.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForMaskedLM, AutoTokenizer


DNA_BASES = set("ACGTN")


@dataclass
class Record:
    sequence: str
    label: float


class SequenceDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    """Simple dataset wrapping encoded input_ids and binary labels."""

    def __init__(self, input_ids: torch.Tensor, labels: torch.Tensor) -> None:
        self.input_ids = input_ids
        self.labels = labels

    def __len__(self) -> int:
        return self.input_ids.shape[0]

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.input_ids[idx], self.labels[idx]


class NTv3BinaryClassifier(nn.Module):
    """NTv3 backbone + mean pooling + linear binary head."""

    def __init__(self, model_id: str, token: str | None = None) -> None:
        super().__init__()
        self.backbone = AutoModelForMaskedLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            token=token,
        )
        config = self.backbone.config
        hidden_size = getattr(config, "hidden_size", None)
        if hidden_size is None:
            for key in ("embed_dim", "token_embed_dim", "ffn_embed_dim"):
                value = getattr(config, key, None)
                if isinstance(value, int) and value > 0:
                    hidden_size = value
                    break
        if hidden_size is None:
            raise ValueError(
                "Unable to infer hidden_size from backbone config. "
                "Tried hidden_size/embed_dim/token_embed_dim/ffn_embed_dim."
            )
        self.dropout = nn.Dropout(p=0.1)
        self.head = nn.Linear(int(hidden_size), 1)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        outputs = self.backbone(input_ids=input_ids, output_hidden_states=True)
        hidden_states = outputs.hidden_states
        if hidden_states is None:
            raise ValueError("Backbone did not return hidden_states.")
        sequence_repr = hidden_states[-1].mean(dim=1)
        logits = self.head(self.dropout(sequence_repr)).squeeze(-1)
        return logits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune NTv3 for CSV binary classification."
    )
    parser.add_argument("--train-csv", required=True)
    parser.add_argument("--dev-csv", required=True)
    parser.add_argument("--test-csv", required=True)
    parser.add_argument("--model", default="InstaDeepAI/NTv3_8M_pre")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--context-length", type=int, required=True)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--early-stopping-patience", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cpu")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def resolve_device(device: str) -> torch.device:
    lowered = device.strip().lower()
    if lowered == "mps":
        raise ValueError(
            "NTv3 training with trust_remote_code is not supported on mps due to "
            "torch.autocast device_type limitations. Use --device cpu or cuda."
        )
    if lowered == "cuda":
        if not torch.cuda.is_available():
            raise ValueError("CUDA requested but not available.")
        return torch.device("cuda")
    if lowered != "cpu":
        raise ValueError(f"Unsupported device: {device}")
    return torch.device("cpu")


def normalize_sequence(raw_sequence: str, context_length: int) -> str:
    seq = raw_sequence.strip().upper()
    if not seq:
        raise ValueError("Empty sequence encountered.")
    invalid = sorted(set(seq) - DNA_BASES)
    if invalid:
        raise ValueError(f"Invalid DNA characters found: {''.join(invalid)}")
    if len(seq) > context_length:
        return seq[:context_length]
    if len(seq) < context_length:
        return seq + ("N" * (context_length - len(seq)))
    return seq


def load_records(csv_path: Path, context_length: int) -> list[Record]:
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        raise ValueError(f"CSV missing or empty: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {csv_path}")
        fields = [x.strip().lower() for x in reader.fieldnames]
        if fields != ["sequence", "label"]:
            raise ValueError(
                f"CSV header must be sequence,label in {csv_path}, got {reader.fieldnames}"
            )

        records: list[Record] = []
        for row_num, row in enumerate(reader, start=2):
            seq = normalize_sequence(row.get("sequence", ""), context_length)
            raw_label = str(row.get("label", "")).strip()
            try:
                label_int = int(raw_label)
            except ValueError as exc:
                raise ValueError(
                    f"{csv_path}:{row_num} label is not an integer: {raw_label}"
                ) from exc
            if label_int not in (0, 1):
                raise ValueError(
                    f"{csv_path}:{row_num} label must be 0 or 1, got {label_int}"
                )
            records.append(Record(sequence=seq, label=float(label_int)))
    if not records:
        raise ValueError(f"No records loaded from {csv_path}")
    return records


def encode_records(
    tokenizer: Any, records: list[Record], split_name: str
) -> tuple[torch.Tensor, torch.Tensor]:
    sequences = [r.sequence for r in records]
    labels = torch.tensor([r.label for r in records], dtype=torch.float32)

    encoded = tokenizer(
        sequences,
        return_tensors="pt",
        padding=False,
        add_special_tokens=False,
    )
    if "input_ids" not in encoded:
        raise ValueError(f"Tokenizer did not return input_ids for split={split_name}")
    input_ids = encoded["input_ids"]
    if input_ids.ndim != 2:
        raise ValueError(f"input_ids rank must be 2 for split={split_name}")
    if input_ids.shape[0] != labels.shape[0]:
        raise ValueError(
            f"input_ids/labels size mismatch for split={split_name}: "
            f"{input_ids.shape[0]} vs {labels.shape[0]}"
        )
    return input_ids, labels


def collate_batch(
    batch: list[tuple[torch.Tensor, torch.Tensor]]
) -> tuple[torch.Tensor, torch.Tensor]:
    input_ids, labels = zip(*batch)
    return torch.stack(input_ids, dim=0), torch.stack(labels, dim=0)


def compute_binary_metrics(logits: torch.Tensor, labels: torch.Tensor) -> dict[str, float]:
    probs = torch.sigmoid(logits)
    preds = (probs >= 0.5).to(torch.int64)
    truth = labels.to(torch.int64)

    tp = int(((preds == 1) & (truth == 1)).sum().item())
    tn = int(((preds == 0) & (truth == 0)).sum().item())
    fp = int(((preds == 1) & (truth == 0)).sum().item())
    fn = int(((preds == 0) & (truth == 1)).sum().item())

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    if precision + recall:
        f1 = 2.0 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    mcc_den = float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    if mcc_den > 0:
        mcc = float((tp * tn - fp * fn) / np.sqrt(mcc_den))
    else:
        mcc = 0.0

    return {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "mcc": float(mcc),
    }


def evaluate(
    model: nn.Module,
    dataloader: DataLoader[tuple[torch.Tensor, torch.Tensor]],
    criterion: nn.Module,
    device: torch.device,
) -> dict[str, float]:
    model.eval()
    total_loss = 0.0
    total_size = 0
    all_logits: list[torch.Tensor] = []
    all_labels: list[torch.Tensor] = []

    with torch.no_grad():
        for input_ids, labels in dataloader:
            input_ids = input_ids.to(device)
            labels = labels.to(device)
            logits = model(input_ids)
            loss = criterion(logits, labels)

            batch_size = labels.shape[0]
            total_loss += float(loss.item()) * batch_size
            total_size += batch_size
            all_logits.append(logits.detach().cpu())
            all_labels.append(labels.detach().cpu())

    if total_size == 0:
        raise ValueError("Dataloader is empty during evaluation.")

    logits = torch.cat(all_logits, dim=0)
    labels = torch.cat(all_labels, dim=0)
    metrics = compute_binary_metrics(logits, labels)
    metrics["loss"] = total_loss / total_size
    return metrics


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    model_output_dir = output_dir / "model_output"
    model_output_dir.mkdir(parents=True, exist_ok=True)

    eval_metrics_path = output_dir / "eval-metrics.json"
    history_path = output_dir / "training_history.json"
    checkpoint_path = model_output_dir / "best_checkpoint.pt"

    try:
        set_seed(args.seed)
        device = resolve_device(args.device)

        token = os.getenv("HF_TOKEN")
        if not token:
            raise ValueError("HF_TOKEN is required for gated NTv3 model access.")

        train_records = load_records(Path(args.train_csv).resolve(), args.context_length)
        dev_records = load_records(Path(args.dev_csv).resolve(), args.context_length)
        test_records = load_records(Path(args.test_csv).resolve(), args.context_length)

        tokenizer = AutoTokenizer.from_pretrained(
            args.model,
            trust_remote_code=True,
            token=token,
        )

        train_input_ids, train_labels = encode_records(tokenizer, train_records, "train")
        dev_input_ids, dev_labels = encode_records(tokenizer, dev_records, "dev")
        test_input_ids, test_labels = encode_records(tokenizer, test_records, "test")

        train_loader = DataLoader(
            SequenceDataset(train_input_ids, train_labels),
            batch_size=args.batch_size,
            shuffle=True,
            collate_fn=collate_batch,
        )
        dev_loader = DataLoader(
            SequenceDataset(dev_input_ids, dev_labels),
            batch_size=args.batch_size,
            shuffle=False,
            collate_fn=collate_batch,
        )
        test_loader = DataLoader(
            SequenceDataset(test_input_ids, test_labels),
            batch_size=args.batch_size,
            shuffle=False,
            collate_fn=collate_batch,
        )

        model = NTv3BinaryClassifier(model_id=args.model, token=token).to(device)
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=args.lr,
            weight_decay=args.weight_decay,
        )
        criterion = nn.BCEWithLogitsLoss()

        history: list[dict[str, Any]] = []
        best_dev_f1 = -1.0
        best_epoch = 0
        best_dev_metrics: dict[str, float] | None = None
        patience_counter = 0

        for epoch in range(1, args.epochs + 1):
            model.train()
            running_loss = 0.0
            sample_count = 0

            for input_ids, labels in train_loader:
                input_ids = input_ids.to(device)
                labels = labels.to(device)

                optimizer.zero_grad(set_to_none=True)
                logits = model(input_ids)
                loss = criterion(logits, labels)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), max_norm=args.grad_clip)
                optimizer.step()

                batch_size = labels.shape[0]
                running_loss += float(loss.item()) * batch_size
                sample_count += batch_size

            if sample_count == 0:
                raise ValueError("No training samples were processed.")

            train_loss = running_loss / sample_count
            dev_metrics = evaluate(model, dev_loader, criterion, device)
            epoch_payload = {
                "epoch": epoch,
                "train_loss": train_loss,
                "dev_loss": dev_metrics["loss"],
                "dev_accuracy": dev_metrics["accuracy"],
                "dev_precision": dev_metrics["precision"],
                "dev_recall": dev_metrics["recall"],
                "dev_f1": dev_metrics["f1"],
                "dev_mcc": dev_metrics["mcc"],
            }
            history.append(epoch_payload)
            print(json.dumps(epoch_payload))

            if dev_metrics["f1"] > best_dev_f1:
                best_dev_f1 = dev_metrics["f1"]
                best_epoch = epoch
                best_dev_metrics = dev_metrics
                patience_counter = 0
                torch.save(
                    {
                        "model_state_dict": model.state_dict(),
                        "optimizer_state_dict": optimizer.state_dict(),
                        "epoch": epoch,
                        "dev_metrics": dev_metrics,
                        "model_id": args.model,
                    },
                    checkpoint_path,
                )
            else:
                patience_counter += 1
                if patience_counter >= args.early_stopping_patience:
                    print(
                        f"early_stopping=true epoch={epoch} "
                        f"patience={args.early_stopping_patience}"
                    )
                    break

        if not checkpoint_path.exists():
            raise ValueError("Best checkpoint was not created.")
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])

        test_metrics = evaluate(model, test_loader, criterion, device)
        if best_dev_metrics is None:
            raise ValueError("best_dev_metrics is missing after training.")

        write_json(
            history_path,
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "model": args.model,
                "device": str(device),
                "context_length": args.context_length,
                "history": history,
                "best_epoch": best_epoch,
                "best_dev_metrics": best_dev_metrics,
                "test_metrics": test_metrics,
            },
        )

        eval_payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
            "task": "fine-tuning",
            "selected_skill": "nucleotide-transformer-v3",
            "model": args.model,
            "device": str(device),
            "context_length": args.context_length,
            "train_epochs": len(history),
            "best_epoch": best_epoch,
            "best_dev_metrics": best_dev_metrics,
            "test_metrics": test_metrics,
            "checkpoint_path": str(checkpoint_path),
            "training_history": str(history_path),
        }
        write_json(eval_metrics_path, eval_payload)
        print(json.dumps(eval_payload, indent=2))
    except Exception as exc:  # pylint: disable=broad-except
        failure_payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
            "task": "fine-tuning",
            "selected_skill": "nucleotide-transformer-v3",
            "model": args.model,
            "device": args.device,
            "context_length": args.context_length,
            "train_epochs": 0,
            "best_dev_metrics": None,
            "test_metrics": None,
            "checkpoint_path": str(checkpoint_path),
            "training_history": str(history_path),
            "reason": f"{exc.__class__.__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }
        write_json(eval_metrics_path, failure_payload)
        print(json.dumps(failure_payload, indent=2))
        raise


if __name__ == "__main__":
    main()
