import base64
import io
import logging
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
from PIL import Image

from backend.services.predictor import _load_model, _preprocess

logger = logging.getLogger(__name__)


@dataclass
class CamResult:
    """Everything downstream explainability needs from a single CAM pass."""

    cam: np.ndarray            # normalised attention map, shape (224, 224), values in [0, 1]
    target_index: int          # class the CAM explains
    x: Any                     # preprocessed input tensor on the model device (reused for deletion)
    orig_confidence: float     # softmax probability of target_index for the original input

# Overlay is rendered at this resolution (matches the model input grid).
_OUT_SIZE = 224
# Fraction of the base MRI that remains visible under peak attention.
_MAX_ALPHA = 0.62
# Percentiles used to normalise the CAM — clipping extremes gives far better
# contrast than raw min/max, which is dominated by single hot/cold pixels.
_LOW_PCT = 2.0
_HIGH_PCT = 98.0


def _to_rgb_array_for_overlay(pil_img: Image.Image) -> np.ndarray:
    img = pil_img.convert("RGB").resize((_OUT_SIZE, _OUT_SIZE))
    return np.asarray(img, dtype=np.float32) / 255.0


def _turbo_colormap(x: np.ndarray) -> np.ndarray:
    """Vectorised Turbo colormap (Google/Anton Mikhailov approximation).

    Perceptually uniform and dependency-free — a clear upgrade over the old
    hand-rolled blue→red ramp and OpenCV's jet, with no extra imports.
    Input/output are float arrays in [0, 1].
    """
    x = np.clip(x, 0.0, 1.0)
    r = 34.61 + x * (1172.33 - x * (10793.56 - x * (33300.12 - x * (38394.49 - x * 14825.05))))
    g = 23.31 + x * (557.33 + x * (1225.33 - x * (3574.96 - x * (1073.77 + x * 707.56))))
    b = 27.2 + x * (3211.1 - x * (15327.97 - x * (27814.0 - x * (22569.18 - x * 6838.66))))
    rgb = np.stack([r, g, b], axis=-1)
    return np.clip(rgb / 255.0, 0.0, 1.0)


def _resolve_target_layer(model):
    """Pick the last convolutional block, tolerating architecture changes."""
    layer4 = getattr(model, "layer4", None)
    if layer4 is not None and len(layer4) > 0:
        return layer4[-1]
    # Fallback: last module that produces a 4-D activation.
    last_conv = None
    import torch.nn as nn

    for module in model.modules():
        if isinstance(module, (nn.Conv2d, nn.BatchNorm2d)):
            last_conv = module
    if last_conv is None:
        raise RuntimeError("No convolutional layer found for Grad-CAM.")
    return last_conv


def _compute_cam(image: Image.Image, target_index: Optional[int]) -> CamResult:
    """Run a single forward/backward pass and return a smoothed, normalised CAM.

    Everything stays on the model's device as torch tensors until the final
    numpy hand-off, so there is only one host<->device transfer. The original
    input tensor and target-class confidence are returned alongside the CAM so
    downstream explainability (e.g. deletion faithfulness) does not have to
    re-preprocess or re-run the forward pass.
    """
    import torch
    import torch.nn.functional as F

    model = _load_model()
    model.eval()
    x = _preprocess(image)

    activations = {}
    gradients = {}
    target_layer = _resolve_target_layer(model)

    def forward_hook(_module, _inputs, output):
        activations["value"] = output

    def backward_hook(_module, _grad_input, grad_output):
        gradients["value"] = grad_output[0]

    forward_handle = target_layer.register_forward_hook(forward_hook)
    backward_handle = target_layer.register_full_backward_hook(backward_hook)
    try:
        model.zero_grad(set_to_none=True)
        logits = model(x)
        if target_index is None:
            target_index = int(torch.argmax(logits, dim=1).item())
        target_index = int(target_index)

        orig_confidence = float(F.softmax(logits, dim=1)[0, target_index].item())

        logits[:, target_index].sum().backward()

        activation = activations.get("value")
        gradient = gradients.get("value")
        if activation is None or gradient is None:
            raise RuntimeError("Grad-CAM hooks did not capture activations.")

        activation = activation.detach()
        gradient = gradient.detach()

        # Grad-CAM: channel weights are the spatially-averaged gradients.
        weights = gradient.mean(dim=(2, 3), keepdim=True)
        cam = torch.relu((weights * activation).sum(dim=1, keepdim=True))

        # Smooth on the low-res grid (cheap) then upsample — reduces the blocky
        # artefacts you get from interpolating a 7x7 map straight to 224x224.
        cam = _gaussian_blur(cam)
        cam = F.interpolate(
            cam, size=(_OUT_SIZE, _OUT_SIZE), mode="bilinear", align_corners=False
        )
        cam_np = cam[0, 0].cpu().numpy()
    finally:
        forward_handle.remove()
        backward_handle.remove()

    return CamResult(
        cam=_normalise(cam_np),
        target_index=target_index,
        x=x.detach(),
        orig_confidence=orig_confidence,
    )


def _gaussian_blur(cam, sigma: float = 1.1):
    """Separable Gaussian blur applied with two depthwise conv1d passes."""
    import torch
    import torch.nn.functional as F

    radius = max(1, int(round(sigma * 2)))
    coords = torch.arange(-radius, radius + 1, dtype=cam.dtype, device=cam.device)
    kernel = torch.exp(-(coords ** 2) / (2.0 * sigma * sigma))
    kernel = kernel / kernel.sum()

    kx = kernel.view(1, 1, 1, -1)
    ky = kernel.view(1, 1, -1, 1)
    cam = F.conv2d(cam, kx, padding=(0, radius))
    cam = F.conv2d(cam, ky, padding=(radius, 0))
    return cam


def _normalise(cam_np: np.ndarray) -> np.ndarray:
    """Percentile-clipped min/max normalisation to [0, 1]."""
    lo = float(np.percentile(cam_np, _LOW_PCT))
    hi = float(np.percentile(cam_np, _HIGH_PCT))
    if hi - lo < 1e-6:
        lo, hi = float(cam_np.min()), float(cam_np.max())
    cam_np = (cam_np - lo) / (hi - lo + 1e-8)
    return np.clip(cam_np, 0.0, 1.0)


def _render_overlay(base_rgb: np.ndarray, cam: np.ndarray) -> np.ndarray:
    """Blend the heatmap onto the MRI with attention-gated transparency.

    Low-attention regions keep the crisp original MRI; the colour ramp only
    takes over where the model actually looked, which is far more legible than
    the old uniform 58/42 blend that tinted the whole frame.
    """
    heatmap = _turbo_colormap(cam)
    alpha = (cam[..., None] ** 0.85) * _MAX_ALPHA
    overlay = base_rgb * (1.0 - alpha) + heatmap * alpha
    return np.clip(overlay * 255.0, 0, 255).astype(np.uint8)


def _encode_png(arr: np.ndarray) -> str:
    out = Image.fromarray(arr).convert("RGB")
    buf = io.BytesIO()
    out.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def generate_gradcam_base64(image: Image.Image, target_index: Optional[int] = None) -> str:
    """Generate a Grad-CAM overlay (base64 PNG) using native PyTorch hooks.

    Avoids the external `grad-cam`/OpenCV stack, which is prone to native
    library mismatches inside Docker. Returns "" on any failure so callers can
    degrade gracefully.
    """
    if not isinstance(image, Image.Image):
        return ""

    try:
        result = _compute_cam(image, target_index)
        base_rgb = _to_rgb_array_for_overlay(image)
        return _encode_png(_render_overlay(base_rgb, result.cam))
    except Exception:
        logger.exception("Grad-CAM generation failed.")
        return ""


def compute_cam_bundle(image: Image.Image, target_index: Optional[int] = None) -> Optional[CamResult]:
    """Public accessor for the raw CAM bundle (CAM + input tensor + confidence).

    Returns None on failure so callers can degrade gracefully.
    """
    if not isinstance(image, Image.Image):
        return None
    try:
        return _compute_cam(image, target_index)
    except Exception:
        logger.exception("Grad-CAM computation failed.")
        return None


def render_overlay_base64(image: Image.Image, cam: np.ndarray) -> str:
    """Render an overlay PNG (base64) from an image and a precomputed CAM."""
    try:
        base_rgb = _to_rgb_array_for_overlay(image)
        return _encode_png(_render_overlay(base_rgb, cam))
    except Exception:
        logger.exception("Grad-CAM overlay rendering failed.")
        return ""


def generate_gradcam_heatmap_base64(
    image: Image.Image, target_index: Optional[int] = None
) -> str:
    """Standalone colour heatmap (no MRI underlay) as a base64 PNG.

    Useful for a side-by-side legend/inspection view in the UI.
    """
    if not isinstance(image, Image.Image):
        return ""

    try:
        result = _compute_cam(image, target_index)
        heatmap = (_turbo_colormap(result.cam) * 255.0).astype(np.uint8)
        return _encode_png(heatmap)
    except Exception:
        logger.exception("Grad-CAM heatmap generation failed.")
        return ""
