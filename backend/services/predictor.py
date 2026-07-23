import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from PIL import Image

# Matches Colab class_names order:
# ["Mild Impairment", "Moderate Impairment", "No Impairment", "Very Mild Impairment"]
CLASSES: List[str] = [
    "Mild Impairment",
    "Moderate Impairment",
    "No Impairment",
    "Very Mild Impairment",
]


class ModelUnavailableError(RuntimeError):
    """Raised when real MRI inference cannot run without a trained model."""


def _device():
    import torch

    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _resolve_model_path(model_path: str) -> str:
    """Resolve MODEL_PATH relative to repo root when CWD differs."""
    if not model_path:
        return model_path
    if os.path.isabs(model_path) and os.path.exists(model_path):
        return model_path
    if os.path.exists(model_path):
        return os.path.abspath(model_path)

    repo_root = Path(__file__).resolve().parent.parent.parent
    candidate = (repo_root / model_path).resolve()
    if candidate.exists():
        return str(candidate)

    # Common fallback when .env uses ./models/model.pth
    fallback = repo_root / "models" / "model.pth"
    if fallback.exists():
        return str(fallback)
    return model_path


def _extract_state_dict(raw) -> dict:
    """Accept raw state_dict or common checkpoint wrappers."""
    if not isinstance(raw, dict):
        raise ModelUnavailableError("Model file is not a state_dict/checkpoint dict.")

    # Already a flat state_dict (OrderedDict of tensors)
    tensor_like = sum(
        1 for v in raw.values() if hasattr(v, "shape") or hasattr(v, "dtype")
    )
    if tensor_like >= max(1, len(raw) // 2) and "state_dict" not in raw:
        return raw

    for key in ("state_dict", "model_state_dict", "model", "net"):
        nested = raw.get(key)
        if isinstance(nested, dict):
            return nested

    return raw


def _strip_module_prefix(state: dict) -> dict:
    if not state:
        return state
    if all(isinstance(k, str) and k.startswith("module.") for k in state.keys()):
        return {k[len("module.") :]: v for k, v in state.items()}
    return state


@lru_cache(maxsize=1)
def _load_model():
    """
    Loads ResNet18 (pure PyTorch) and the state_dict from MODEL_PATH.

    Does not import torchvision — avoids broken/blocked torchvision ops on Windows.
    """
    from backend.config import get_settings
    from backend.services.resnet18 import build_resnet18

    settings = get_settings()
    model_path = _resolve_model_path(settings.MODEL_PATH)
    if not model_path or not os.path.exists(model_path):
        raise ModelUnavailableError(
            f"Trained model file is unavailable at '{model_path or 'MODEL_PATH not set'}'."
        )

    try:
        import torch

        model = build_resnet18(num_classes=4)

        try:
            raw = torch.load(model_path, map_location="cpu", weights_only=True)
        except TypeError:
            # Older torch without weights_only
            raw = torch.load(model_path, map_location="cpu")
        except Exception:
            # Some checkpoints need weights_only=False
            raw = torch.load(model_path, map_location="cpu", weights_only=False)

        state = _strip_module_prefix(_extract_state_dict(raw))
        model.load_state_dict(state, strict=True)
        model.eval()
        model.to(_device())
        return model
    except ModelUnavailableError:
        raise
    except Exception as error:
        raise ModelUnavailableError(
            f"Trained model could not be loaded from '{model_path}': {error}"
        ) from error


def _preprocess(pil_img: Image.Image):
    """Resize → ToTensor → Normalize without torchvision."""
    import torch
    import torch.nn.functional as F
    import numpy as np

    img = pil_img.convert("RGB").resize((224, 224), Image.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0  # HWC, [0,1]
    # CHW
    tensor = torch.from_numpy(arr).permute(2, 0, 1).contiguous()
    # Normalize mean=0.5 std=0.5  →  (x - 0.5) / 0.5
    tensor = (tensor - 0.5) / 0.5
    return tensor.unsqueeze(0).to(_device())


def _risk_score_from_probs(probs) -> float:
    import torch

    # Mild(0)->55, Moderate(1)->85, No(2)->5, Very Mild(3)->25
    class_risk = torch.tensor([55.0, 85.0, 5.0, 25.0], device=probs.device)
    score = torch.sum(probs * class_risk).item()
    return float(round(score, 2))


def predict_stage_and_scores(image: Image.Image) -> Dict:
    import torch
    import torch.nn.functional as F

    model = _load_model()
    x = _preprocess(image)

    with torch.no_grad():
        logits = model(x)  # [1,4]
        probs = F.softmax(logits, dim=1)[0]  # [4]
        pred_idx = int(torch.argmax(probs).item())
        confidence = float(round(probs[pred_idx].item(), 4))
        risk = _risk_score_from_probs(probs)

    return {
        "predicted_stage": CLASSES[pred_idx],
        "confidence_score": confidence,
        "risk_score": risk,
        "raw_probs": [float(p.item()) for p in probs],
        "predicted_index": pred_idx,
    }
