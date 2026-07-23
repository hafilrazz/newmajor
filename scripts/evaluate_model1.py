"""
Evaluate Model 1 (ResNet18) on the Kaggle Alzheimer MRI test split.

Dataset: https://www.kaggle.com/datasets/lukechugh/best-alzheimer-mri-dataset-99-accuracy

Usage:
  python scripts/evaluate_model1.py --data-dir path/to/dataset
  python scripts/evaluate_model1.py --data-dir path/to/dataset/test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch.utils.data import DataLoader, Dataset
from torchvision.models import resnet18

# Matches backend/services/predictor.py (Colab training order)
CLASS_NAMES = [
    "Mild Impairment",
    "Moderate Impairment",
    "No Impairment",
    "Very Mild Impairment",
]

# Common folder-name aliases in the Kaggle / augmented datasets
FOLDER_ALIASES = {
    "mild impairment": 0,
    "moderate impairment": 1,
    "no impairment": 2,
    "very mild impairment": 3,
    "mild demented": 0,
    "milddemented": 0,
    "mild_demented": 0,
    "moderate demented": 1,
    "moderatedemented": 1,
    "moderate_demented": 1,
    "non demented": 2,
    "nondemented": 2,
    "non_demented": 2,
    "non-demented": 2,
    "no demented": 2,
    "very mild demented": 3,
    "verymilddemented": 3,
    "very_mild_demented": 3,
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def _normalize_folder_name(name: str) -> str:
    return name.strip().lower().replace("_", " ").replace("-", " ")


def resolve_test_dir(data_dir: Path) -> Path:
    """Find the test split folder inside a Kaggle-style dataset root."""
    candidates = [
        data_dir,
        data_dir / "test",
        data_dir / "Test",
        data_dir / "testing",
        data_dir / "valid",
        data_dir / "validation",
    ]
    for candidate in candidates:
        if not candidate.is_dir():
            continue
        subdirs = [p for p in candidate.iterdir() if p.is_dir()]
        if not subdirs:
            continue
        mapped = sum(1 for p in subdirs if _normalize_folder_name(p.name) in FOLDER_ALIASES)
        if mapped >= 2:
            return candidate
    raise FileNotFoundError(
        f"Could not find a class-folder test split under '{data_dir}'. "
        "Expected subfolders like 'Mild Impairment', 'No Impairment', etc."
    )


def collect_samples(test_dir: Path) -> tuple[list[Path], list[int], dict[str, int]]:
    paths: list[Path] = []
    labels: list[int] = []
    folder_counts: dict[str, int] = {}

    for class_dir in sorted(test_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        key = _normalize_folder_name(class_dir.name)
        if key not in FOLDER_ALIASES:
            print(f"  [skip] unknown class folder: {class_dir.name}")
            continue
        label = FOLDER_ALIASES[key]
        count = 0
        for file_path in class_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
                paths.append(file_path)
                labels.append(label)
                count += 1
        folder_counts[class_dir.name] = count

    if not paths:
        raise RuntimeError(f"No images found under '{test_dir}'.")

    return paths, labels, folder_counts


class MriEvalDataset(Dataset):
    def __init__(self, paths: list[Path], labels: list[int], transform):
        self.paths = paths
        self.labels = labels
        self.transform = transform

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, idx: int):
        image = Image.open(self.paths[idx]).convert("RGB")
        return self.transform(image), self.labels[idx]


def load_model(model_path: Path, device: torch.device):
    model = resnet18(weights=None)
    model.fc = torch.nn.Linear(model.fc.in_features, len(CLASS_NAMES), bias=True)
    state = torch.load(model_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=True)
    model.eval()
    model.to(device)
    return model


def evaluate(model, loader, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    y_true: list[int] = []
    y_pred: list[int] = []

    with torch.no_grad():
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            logits = model(batch_x)
            preds = torch.argmax(F.softmax(logits, dim=1), dim=1).cpu().numpy()
            y_pred.extend(preds.tolist())
            y_true.extend(batch_y.numpy().tolist())

    return np.array(y_true), np.array(y_pred)


def format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def write_report(
    report_path: Path,
    *,
    model_path: Path,
    test_dir: Path,
    folder_counts: dict[str, int],
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict:
    acc = accuracy_score(y_true, y_pred)
    precision_macro = precision_score(y_true, y_pred, average="macro", zero_division=0)
    recall_macro = recall_score(y_true, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average="macro", zero_division=0)
    precision_weighted = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    recall_weighted = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    f1_weighted = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(CLASS_NAMES))))
    cls_report = classification_report(
        y_true,
        y_pred,
        target_names=CLASS_NAMES,
        digits=4,
        zero_division=0,
    )

    metrics = {
        "model_name": "model1_resnet18",
        "model_path": str(model_path),
        "dataset": "lukechugh/best-alzheimer-mri-dataset-99-accuracy",
        "test_dir": str(test_dir),
        "num_samples": int(len(y_true)),
        "folder_counts": folder_counts,
        "accuracy": float(acc),
        "precision_macro": float(precision_macro),
        "recall_macro": float(recall_macro),
        "f1_macro": float(f1_macro),
        "precision_weighted": float(precision_weighted),
        "recall_weighted": float(recall_weighted),
        "f1_weighted": float(f1_weighted),
        "confusion_matrix": cm.tolist(),
        "classification_report": cls_report,
    }

    lines = [
        "# Model 1 — ResNet18 MRI Evaluation",
        "",
        f"**Model:** `{model_path}`",
        f"**Dataset:** [lukechugh/best-alzheimer-mri-dataset-99-accuracy](https://www.kaggle.com/datasets/lukechugh/best-alzheimer-mri-dataset-99-accuracy)",
        f"**Test directory:** `{test_dir}`",
        f"**Samples evaluated:** {len(y_true)}",
        "",
        "## Per-class folder counts",
        "",
    ]
    for name, count in folder_counts.items():
        lines.append(f"- {name}: {count}")
    lines.extend(
        [
            "",
            "## Test metrics",
            "| Metric | Value |",
            "|--------|------:|",
            f"| **Accuracy** | **{format_pct(acc)}** |",
            f"| Precision (macro) | {format_pct(precision_macro)} |",
            f"| Recall (macro) | {format_pct(recall_macro)} |",
            f"| F1 (macro) | {format_pct(f1_macro)} |",
            f"| Precision (weighted) | {format_pct(precision_weighted)} |",
            f"| Recall (weighted) | {format_pct(recall_weighted)} |",
            f"| F1 (weighted) | {format_pct(f1_weighted)} |",
            "",
            "## Classification report",
            "```",
            cls_report.strip(),
            "```",
            "",
            "## Confusion matrix",
            "(rows = true class, columns = predicted class)",
            "",
            "```",
            np.array2string(cm, separator="  "),
            "```",
            "",
            "## Class order",
            "",
        ]
    )
    for idx, name in enumerate(CLASS_NAMES):
        lines.append(f"{idx}: {name}")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    meta_path = report_path.with_suffix(".json")
    meta_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Evaluate Model 1 (ResNet18) on MRI test data.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=project_root / "data" / "alzheimer-mri-dataset",
        help="Path to dataset root or test split folder.",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=project_root / "models" / "model.pth",
        help="Path to model.pth (Model 1 weights).",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "models" / "model1_metrics_report.md",
    )
    args = parser.parse_args()

    if not args.model_path.is_file():
        print(f"ERROR: model not found at {args.model_path}")
        return 1
    if not args.data_dir.is_dir():
        print(f"ERROR: dataset directory not found at {args.data_dir}")
        print("Download from Kaggle, then pass --data-dir to the extracted folder.")
        return 1

    test_dir = resolve_test_dir(args.data_dir)
    paths, labels, folder_counts = collect_samples(test_dir)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    transform = T.Compose(
        [
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]),
        ]
    )

    loader = DataLoader(
        MriEvalDataset(paths, labels, transform),
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=0,
    )

    print(f"Model:   {args.model_path}")
    print(f"Test:    {test_dir}")
    print(f"Device:  {device}")
    print(f"Images:  {len(paths)}")
    for name, count in folder_counts.items():
        print(f"  - {name}: {count}")

    model = load_model(args.model_path, device)
    y_true, y_pred = evaluate(model, loader, device)
    metrics = write_report(
        args.output,
        model_path=args.model_path,
        test_dir=test_dir,
        folder_counts=folder_counts,
        y_true=y_true,
        y_pred=y_pred,
    )

    print("\n=== Results ===")
    print(f"Accuracy:        {format_pct(metrics['accuracy'])}")
    print(f"F1 (macro):      {format_pct(metrics['f1_macro'])}")
    print(f"F1 (weighted):   {format_pct(metrics['f1_weighted'])}")
    print("\nConfusion matrix (true x pred):")
    print(np.array(metrics["confusion_matrix"]))
    print(f"\nReport saved: {args.output}")
    print(f"JSON saved:   {args.output.with_suffix('.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())