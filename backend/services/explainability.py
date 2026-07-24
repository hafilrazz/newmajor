"""Faithful, deterministic explanation of an actual Grad-CAM++ result.

Two grounded XAI techniques are applied to the CAM the model really produces:

1. Region attention analysis — where the activation mass concentrates
   (image-space grid + hemisphere split), how focused it is, and how much
   of the scan it covers. Pure statistics over the real CAM; nothing invented.

2. Deletion faithfulness — mask the top-attention region of the input, re-run
   the model, and measure how far the target-class confidence drops. A large
   drop means the highlighted region genuinely drove the prediction, so the
   Grad-CAM++ explanation is trustworthy; a small drop flags a weak explanation.

The narrative is templated from these numbers with fixed rules, so it is fully
reproducible and can never hallucinate.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import numpy as np
from PIL import Image

from backend.services.gradcam import (
    CamResult,
    compute_cam_bundle,
    render_overlay_base64,
)

logger = logging.getLogger(__name__)

_ROW_LABELS = ("upper", "middle", "lower")
_COL_LABELS = ("left", "central", "right")

# Fraction of the highest-attention pixels removed for the deletion test.
_DELETION_TOP_PCT = 80.0  # keep the top (100 - 80) = 20% most-active pixels
# Normalised value of a black pixel after the (mean=0.5, std=0.5) transform.
# MRI backgrounds are black, so black is the natural "information removed" baseline.
_BASELINE_VALUE = -1.0


def _region_label(row: int, col: int) -> str:
    if row == 1 and col == 1:
        return "central"
    return f"{_ROW_LABELS[row]}-{_COL_LABELS[col]}"


def analyze_cam_regions(cam: np.ndarray) -> Dict[str, Any]:
    """Summarise where the actual CAM concentrates its attention."""
    cam = np.asarray(cam, dtype=np.float32)
    h, w = cam.shape
    total = float(cam.sum()) + 1e-8

    # 3x3 image-space grid of attention mass fractions.
    r = (0, h // 3, 2 * h // 3, h)
    c = (0, w // 3, 2 * w // 3, w)
    grid = np.zeros((3, 3), dtype=np.float32)
    for i in range(3):
        for j in range(3):
            grid[i, j] = float(cam[r[i]:r[i + 1], c[j]:c[j + 1]].sum()) / total

    ti, tj = np.unravel_index(int(np.argmax(grid)), grid.shape)
    top_region = _region_label(int(ti), int(tj))
    top_fraction = float(grid[ti, tj])

    # Peak (single most-active pixel) region.
    py, px = np.unravel_index(int(np.argmax(cam)), cam.shape)
    peak_row = 0 if py < h / 3 else (1 if py < 2 * h / 3 else 2)
    peak_col = 0 if px < w / 3 else (1 if px < 2 * w / 3 else 2)
    peak_region = _region_label(peak_row, peak_col)

    # Left/right hemisphere split (image space).
    left = float(cam[:, : w // 2].sum()) / total
    right = float(cam[:, w // 2:].sum()) / total
    if abs(left - right) <= 0.10:
        hemisphere = "balanced across both sides"
    elif left > right:
        hemisphere = "left-dominant"
    else:
        hemisphere = "right-dominant"

    # Concentration: share of mass held by the most-active 10% of pixels.
    flat = np.sort(cam.ravel())[::-1]
    k = max(1, int(0.10 * flat.size))
    concentration = float(flat[:k].sum()) / total
    if concentration >= 0.35:
        concentration_label = "focused"
    elif concentration >= 0.22:
        concentration_label = "moderately focused"
    else:
        concentration_label = "diffuse"

    # Coverage: share of the scan that is strongly active (CAM >= 0.5).
    coverage = float((cam >= 0.5).mean())

    return {
        "top_region": top_region,
        "top_region_fraction": round(top_fraction, 4),
        "peak_region": peak_region,
        "peak_xy": [int(px), int(py)],
        "hemisphere": {
            "left": round(left, 4),
            "right": round(right, 4),
            "balance": hemisphere,
        },
        "concentration": round(concentration, 4),
        "concentration_label": concentration_label,
        "coverage": round(coverage, 4),
        "grid": [[round(float(v), 4) for v in row] for row in grid],
    }


def compute_deletion_faithfulness(bundle: CamResult) -> Optional[Dict[str, Any]]:
    """Mask the top-attention region and measure the target-class confidence drop."""
    try:
        import torch
        import torch.nn.functional as F

        from backend.services.predictor import _load_model

        cam = np.asarray(bundle.cam, dtype=np.float32)
        threshold = float(np.percentile(cam, _DELETION_TOP_PCT))
        mask = cam >= threshold
        masked_area = float(mask.mean())
        if masked_area <= 0.0:
            return None

        model = _load_model()
        x = bundle.x
        mask_t = torch.from_numpy(mask).to(device=x.device)

        x_masked = x.clone()
        # Zero out (to black baseline) the top-attention pixels across all channels.
        x_masked[:, :, mask_t] = _BASELINE_VALUE

        with torch.no_grad():
            probs = F.softmax(model(x_masked), dim=1)[0]
            masked_conf = float(probs[bundle.target_index].item())

        orig_conf = float(bundle.orig_confidence)
        abs_drop = orig_conf - masked_conf
        rel_drop = abs_drop / (orig_conf + 1e-8)

        if rel_drop >= 0.5:
            label = "HIGH"
        elif rel_drop >= 0.2:
            label = "MODERATE"
        else:
            label = "LOW"

        return {
            "original_confidence": round(orig_conf, 4),
            "masked_confidence": round(masked_conf, 4),
            "absolute_drop": round(abs_drop, 4),
            "relative_drop": round(rel_drop, 4),
            "masked_area": round(masked_area, 4),
            "label": label,
        }
    except Exception:
        logger.exception("Deletion faithfulness computation failed.")
        return None


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def build_narrative(
    stage_name: str,
    regions: Dict[str, Any],
    faithfulness: Optional[Dict[str, Any]],
) -> str:
    """Compose a deterministic, grounded explanation from the computed metrics."""
    stage = stage_name or "the predicted class"
    hemi = regions["hemisphere"]
    parts = []

    parts.append(
        f"For the “{stage}” prediction, the model’s attention was strongest in the "
        f"{regions['top_region']} region of the scan, which held "
        f"{_pct(regions['top_region_fraction'])} of the total activation "
        f"(peak at the {regions['peak_region']} region)."
    )

    if hemi["balance"] == "balanced across both sides":
        parts.append(
            f"Attention was balanced across both sides of the image "
            f"({_pct(hemi['left'])} left vs {_pct(hemi['right'])} right)."
        )
    else:
        side = "left" if hemi["balance"] == "left-dominant" else "right"
        parts.append(
            f"Attention leaned toward the {side} side of the image "
            f"({_pct(hemi['left'])} left vs {_pct(hemi['right'])} right)."
        )

    parts.append(
        f"The activation was {regions['concentration_label']} — the most active 10% of "
        f"pixels accounted for {_pct(regions['concentration'])} of the signal, "
        f"and {_pct(regions['coverage'])} of the scan was strongly highlighted."
    )

    if faithfulness:
        strength = {
            "HIGH": "relied heavily on",
            "MODERATE": "relied partly on",
            "LOW": "did not rely much on",
        }[faithfulness["label"]]
        parts.append(
            f"Faithfulness check ({faithfulness['label']}): masking the highlighted region "
            f"({_pct(faithfulness['masked_area'])} of the image) changed confidence for "
            f"“{stage}” from {_pct(faithfulness['original_confidence'])} to "
            f"{_pct(faithfulness['masked_confidence'])} "
            f"({_pct(faithfulness['relative_drop'])} relative drop) — the model "
            f"{strength} this region, so the overlay is a "
            f"{faithfulness['label'].lower()}-confidence explanation of the decision."
        )
    else:
        parts.append(
            "Faithfulness could not be measured for this scan, so treat the overlay as "
            "an indicative rather than validated explanation."
        )

    return " ".join(parts)


def explain_prediction(
    image: Image.Image,
    target_index: Optional[int] = None,
    stage_name: str = "",
) -> Dict[str, Any]:
    """Produce the overlay plus a faithful, deterministic explanation of it.

    Computes the CAM once and reuses it for the overlay, region analysis, and
    the deletion faithfulness test. Returns a self-contained, JSON-serialisable
    dict; on failure the overlay is "" and ``explanation`` is None.
    """
    result: Dict[str, Any] = {
        "gradcam_image_base64": "",
        "explanation": None,
    }
    if not isinstance(image, Image.Image):
        return result

    bundle = compute_cam_bundle(image, target_index)
    if bundle is None:
        return result

    result["gradcam_image_base64"] = render_overlay_base64(image, bundle.cam)

    try:
        regions = analyze_cam_regions(bundle.cam)
        faithfulness = compute_deletion_faithfulness(bundle)
        narrative = build_narrative(stage_name, regions, faithfulness)
        result["explanation"] = {
            "method": "Grad-CAM++ + region attention analysis + deletion faithfulness",
            "target_class": stage_name or None,
            "narrative": narrative,
            "regions": regions,
            "faithfulness": faithfulness,
        }
    except Exception:
        logger.exception("Explanation assembly failed.")
        result["explanation"] = None

    return result
