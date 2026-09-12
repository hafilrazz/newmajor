"""CT Stacking Ensemble inference service.

Combines MobileNetV2 + EfficientNet-B0 base models with a Meta-Neural-Network
trained on Alzheimer 4-class CT scan datasets.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms

from backend.services.gradcam import render_overlay_base64

logger = logging.getLogger(__name__)

CLASS_NAMES: List[str] = [
    "Mild Impairment",
    "Moderate Impairment",
    "No Impairment",
    "Very Mild Impairment",
]
NUM_CLASSES = len(CLASS_NAMES)

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _resolve_path(rel_or_abs: str, fallback_filename: str) -> Path:
    p = Path(rel_or_abs)
    if p.is_file():
        return p
    in_repo = _REPO_ROOT / "models" / fallback_filename
    if in_repo.is_file():
        return in_repo
    in_ext = Path("C:/model/outputs") / fallback_filename
    if in_ext.is_file():
        return in_ext
    return in_repo


def build_mobilenetv2(num_classes: int = NUM_CLASSES) -> nn.Module:
    model = models.mobilenet_v2(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes, bias=True)
    return model


def build_efficientnet_b0(num_classes: int = NUM_CLASSES) -> nn.Module:
    model = models.efficientnet_b0(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes, bias=True)
    return model


class MetaNeuralNetwork(nn.Module):
    def __init__(self, in_dim: int = 8, num_classes: int = NUM_CLASSES):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, 32),
            nn.ReLU(inplace=True),
            nn.Dropout(0.25),
            nn.Linear(32, 16),
            nn.ReLU(inplace=True),
            nn.Dropout(0.15),
            nn.Linear(16, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def _load_weights(model: nn.Module, path: Path, dev: torch.device) -> nn.Module:
    raw = torch.load(path, map_location=dev, weights_only=False)
    state = raw["state_dict"] if isinstance(raw, dict) and "state_dict" in raw else raw
    if isinstance(state, dict):
        if all(k.startswith("module.") for k in state.keys()):
            state = {k[7:]: v for k, v in state.items()}
    model.load_state_dict(state, strict=True)
    model.eval()
    model.to(dev)
    return model


@lru_cache(maxsize=1)
def load_ct_models() -> Tuple[nn.Module, nn.Module, nn.Module]:
    dev = _device()

    mn_path = _resolve_path("models/mobilenetv2_ct.pth", "mobilenetv2_ct.pth")
    en_path = _resolve_path("models/model2_ct.pth", "model2_ct.pth")
    if not en_path.is_file():
        en_path = _resolve_path("models/efficientnet_b0_ct.pth", "efficientnet_b0_ct.pth")
    meta_path = _resolve_path("models/ct_stacking_ensemble.pth", "ct_stacking_ensemble.pth")

    if not mn_path.is_file():
        raise RuntimeError(f"MobileNetV2 model not found at {mn_path}")
    if not en_path.is_file():
        raise RuntimeError(f"EfficientNet-B0 model not found at {en_path}")
    if not meta_path.is_file():
        raise RuntimeError(f"CT Stacking Ensemble model not found at {meta_path}")

    mn = _load_weights(build_mobilenetv2(NUM_CLASSES), mn_path, dev)
    en = _load_weights(build_efficientnet_b0(NUM_CLASSES), en_path, dev)
    meta = _load_weights(MetaNeuralNetwork(8, NUM_CLASSES), meta_path, dev)

    return mn, en, meta


def _preprocess_ct(image: Image.Image, dev: torch.device) -> torch.Tensor:
    tf = transforms.Compose(
        [
            transforms.Resize((224, 224), Image.Resampling.BILINEAR),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )
    img_rgb = image.convert("RGB")
    tensor = tf(img_rgb).unsqueeze(0).to(dev)
    return tensor


def _risk_score_from_probs(probs: torch.Tensor) -> float:
    # Mild(0)->55, Moderate(1)->85, No(2)->5, Very Mild(3)->25
    class_risk = torch.tensor([55.0, 85.0, 5.0, 25.0], device=probs.device)
    score = torch.sum(probs * class_risk).item()
    return float(round(score, 2))


def predict_ct_stage_and_scores(image: Image.Image) -> Dict[str, Any]:
    """Execute CT Stacking Ensemble prediction over input brain CT image."""
    dev = _device()
    mn, en, meta = load_ct_models()
    x = _preprocess_ct(image, dev)

    with torch.no_grad():
        mn_logits = mn(x)
        en_logits = en(x)
        mn_probs = F.softmax(mn_logits, dim=1)
        en_probs = F.softmax(en_logits, dim=1)

        stacked = torch.cat([mn_probs, en_probs], dim=1)
        meta_logits = meta(stacked)
        ens_probs = F.softmax(meta_logits, dim=1)[0]

        pred_idx = int(torch.argmax(ens_probs).item())
        confidence = float(round(ens_probs[pred_idx].item(), 4))
        risk = _risk_score_from_probs(ens_probs)

        mn_idx = int(torch.argmax(mn_probs[0]).item())
        en_idx = int(torch.argmax(en_probs[0]).item())

    gradcam_b64 = generate_ct_gradcam(image, target_index=pred_idx)

    return {
        "predicted_stage": CLASS_NAMES[pred_idx],
        "confidence_score": confidence,
        "risk_score": risk,
        "raw_probs": [float(p.item()) for p in ens_probs],
        "predicted_index": pred_idx,
        "class_names": CLASS_NAMES,
        "gradcam_image_base64": gradcam_b64,
        "base_models": {
            "mobilenet_v2": {
                "name": "MobileNetV2 (Base 1)",
                "predicted_stage": CLASS_NAMES[mn_idx],
                "confidence": float(round(mn_probs[0, mn_idx].item(), 4)),
                "probs": [float(p.item()) for p in mn_probs[0]],
            },
            "efficientnet_b0": {
                "name": "EfficientNet-B0 (Base 2)",
                "predicted_stage": CLASS_NAMES[en_idx],
                "confidence": float(round(en_probs[0, en_idx].item(), 4)),
                "probs": [float(p.item()) for p in en_probs[0]],
            },
            "meta_learner": {
                "name": "Meta Neural Network (Stacking)",
                "architecture": "MLP (8 -> 32 -> 16 -> 4)",
            },
        },
    }


def generate_ct_gradcam(image: Image.Image, target_index: Optional[int] = None) -> str:
    """Generate Grad-CAM heatmap on the EfficientNet-B0 backbone for the CT scan."""
    try:
        dev = _device()
        _, en, _ = load_ct_models()

        target_layer = None
        for m in reversed(list(en.features.modules())):
            if isinstance(m, nn.Conv2d):
                target_layer = m
                break

        if target_layer is None:
            return ""

        activations = []
        gradients = []

        def forward_hook(module, inp, out):
            activations.append(out)

        def backward_hook(module, grad_in, grad_out):
            gradients.append(grad_out[0])

        h1 = target_layer.register_forward_hook(forward_hook)
        h2 = target_layer.register_full_backward_hook(backward_hook)

        x = _preprocess_ct(image, dev)
        x.requires_grad_(True)

        logits = en(x)
        if target_index is None:
            target_index = int(logits.argmax(dim=1).item())

        score = logits[0, target_index]
        en.zero_grad()
        score.backward()

        h1.remove()
        h2.remove()

        if not activations or not gradients:
            return ""

        act = activations[0].detach()  # [1, C, H, W]
        grad = gradients[0].detach()   # [1, C, H, W]

        weights = torch.mean(grad, dim=(2, 3), keepdim=True)
        cam = torch.relu(torch.sum(weights * act, dim=1, keepdim=True))

        cam = F.interpolate(cam, size=(224, 224), mode="bilinear", align_corners=False)
        cam = cam[0, 0].cpu().numpy()

        cam_min, cam_max = cam.min(), cam.max()
        if cam_max - cam_min > 1e-8:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        return render_overlay_base64(image, cam)
    except Exception as err:
        logger.warning(f"CT Grad-CAM generation failed: {err}")
        return ""
