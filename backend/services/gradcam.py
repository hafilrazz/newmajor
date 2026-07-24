"""High-quality Grad-CAM++ generation for MRI explainability.

Improvements over a single-layer, single-pass Grad-CAM++ map:

1. **Multi-layer fusion** — layer3 (finer spatial detail) + layer4 (class
   semantics), both with Grad-CAM++ weights, fused after per-map normalise.
2. **LayerCAM residual** — pixel-wise ReLU(grad)·activation on layer4 adds
   local structure that pure channel-GAP maps miss.
3. **SmoothGrad-CAM++** — average maps over lightly noised inputs so noise
   spikes cancel and true attention is reinforced.
4. **Stable post-process** — float bilinear upsample, mild blur, power
   sharpen, soft threshold, re-stretch toward a readable mean (~0.25).
5. **Blue X-ray underlay + Jet heat** — navy film base so red/yellow peaks
   read clearly.

All computation is pure PyTorch / NumPy / PIL (no OpenCV / pytorch-grad-cam).
"""

from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

from backend.services.predictor import _load_model, _preprocess

logger = logging.getLogger(__name__)


@dataclass
class CamResult:
    """Everything downstream explainability needs from a single CAM pass."""

    cam: np.ndarray  # normalised attention map (H, W) in [0, 1]
    target_index: int
    x: Any  # clean preprocessed tensor (for deletion faithfulness)
    orig_confidence: float


# --- Spatial sizes ---
_OUT_SIZE = 224
_RENDER_SIZE = 448

# --- SmoothGrad-CAM++ ---
# Number of noisy copies averaged (1 = disabled). 3 balances stability vs latency.
_SMOOTH_N = 3
# Gaussian noise std on the *preprocessed* tensor (values roughly in [-1, 1]).
_SMOOTH_SIGMA = 0.06

# --- Multi-layer fusion weights (after each map is min-max normalised) ---
# Heavier layer4 Grad-CAM++ keeps class semantics; layer3 + LayerCAM add structure.
_W_LAYER4_GPP = 0.60
_W_LAYER3_GPP = 0.20
_W_LAYER4_LC = 0.20  # LayerCAM residual on layer4

# --- Post-process ---
_BLUR_PRE = 0.40
_BLUR_POST = 0.95
_CAM_POWER = 1.25
_CAM_THRESHOLD = 0.12
# Soft target for mean attention after threshold (readable without washout).
_TARGET_MEAN = 0.25
_MEAN_TOL = 0.02

# --- Overlay ---
_MAX_ALPHA = 0.64


# ---------------------------------------------------------------------------
# Colour / image helpers
# ---------------------------------------------------------------------------


def _to_rgb_array(pil_img: Image.Image, size: int) -> np.ndarray:
    img = pil_img.convert("RGB").resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(img, dtype=np.float32) / 255.0


def _xray_blue_base(base_rgb: np.ndarray) -> np.ndarray:
    """Greyscale MRI → blue X-ray / film palette (navy bg, cyan tissue)."""
    rgb = np.asarray(base_rgb, dtype=np.float32)
    luma = (
        0.299 * rgb[..., 0]
        + 0.587 * rgb[..., 1]
        + 0.114 * rgb[..., 2]
    )
    luma = np.power(np.clip(luma, 0.0, 1.0), 0.90)

    deep = np.array([0.02, 0.06, 0.18], dtype=np.float32)
    mid = np.array([0.12, 0.42, 0.72], dtype=np.float32)
    hi = np.array([0.78, 0.92, 1.00], dtype=np.float32)

    t = luma[..., None]
    split = 0.55
    u_lo = t / split
    u_hi = (t - split) / (1.0 - split + 1e-8)
    film = np.where(
        t <= split,
        deep + u_lo * (mid - deep),
        mid + np.clip(u_hi, 0.0, 1.0) * (hi - mid),
    )
    return np.clip(film, 0.0, 1.0).astype(np.float32)


def _jet_colormap(x: np.ndarray) -> np.ndarray:
    """OpenCV-style Jet colormap, float [0, 1] → RGB."""
    x = np.clip(x, 0.0, 1.0)
    r = np.clip(1.5 - np.abs(4.0 * x - 3.0), 0.0, 1.0)
    g = np.clip(1.5 - np.abs(4.0 * x - 2.0), 0.0, 1.0)
    b = np.clip(1.5 - np.abs(4.0 * x - 1.0), 0.0, 1.0)
    return np.stack([r, g, b], axis=-1).astype(np.float32)


# ---------------------------------------------------------------------------
# Model / CAM math
# ---------------------------------------------------------------------------


def _resolve_target_layers(model) -> List[Tuple[str, Any]]:
    """Return named layers for multi-scale Grad-CAM++ (layer3 + layer4)."""
    layers: List[Tuple[str, Any]] = []
    layer3 = getattr(model, "layer3", None)
    layer4 = getattr(model, "layer4", None)
    if layer3 is not None and len(layer3) > 0:
        layers.append(("layer3", layer3[-1]))
    if layer4 is not None and len(layer4) > 0:
        layers.append(("layer4", layer4[-1]))
    if layers:
        return layers

    # Fallback: last Conv2d only.
    import torch.nn as nn

    last = None
    for module in model.modules():
        if isinstance(module, nn.Conv2d):
            last = module
    if last is None:
        raise RuntimeError("No convolutional layer found for Grad-CAM++.")
    return [("conv", last)]


def _gradcam_plusplus_map(activations, gradients):
    """Grad-CAM++ spatial map (B,1,H,W) from activations & gradients.

    α_ij^k = (g²) / (2 g² + (Σ A) g³)   with g = ∂Y/∂A
    w^k    = Σ_ij α_ij^k · ReLU(g_ij)
    L      = ReLU(Σ_k w^k A^k)
    """
    import torch

    grads = gradients
    grads_2 = grads.pow(2)
    grads_3 = grads_2 * grads
    sum_a = torch.clamp(activations, min=0.0).sum(dim=(2, 3), keepdim=True)

    eps = 1e-7
    denom = 2.0 * grads_2 + sum_a * grads_3 + eps
    alpha = grads_2 / denom
    alpha = torch.where(grads != 0, alpha, torch.zeros_like(alpha))
    alpha = torch.nan_to_num(alpha, nan=0.0, posinf=0.0, neginf=0.0)

    weights = (alpha * torch.relu(grads)).sum(dim=(2, 3), keepdim=True)
    if float(weights.abs().sum().item()) < 1e-12:
        weights = gradients.mean(dim=(2, 3), keepdim=True)

    return torch.relu((weights * activations).sum(dim=1, keepdim=True))


def _layercam_map(activations, gradients):
    """LayerCAM: sum_k ReLU(∂Y/∂A^k) ⊙ A^k  — keeps spatial gradient detail."""
    import torch

    return torch.relu((torch.relu(gradients) * activations).sum(dim=1, keepdim=True))


def _gaussian_blur(cam, sigma: float):
    """Separable Gaussian with reflect padding."""
    import torch
    import torch.nn.functional as F

    if sigma is None or sigma <= 0:
        return cam

    radius = max(1, int(round(sigma * 2.0)))
    coords = torch.arange(-radius, radius + 1, dtype=cam.dtype, device=cam.device)
    kernel = torch.exp(-(coords ** 2) / (2.0 * sigma * sigma))
    kernel = kernel / kernel.sum()

    cam = F.pad(cam, (radius, radius, radius, radius), mode="reflect")
    cam = F.conv2d(cam, kernel.view(1, 1, 1, -1))
    cam = F.conv2d(cam, kernel.view(1, 1, -1, 1))
    return cam


def _minmax_tensor(cam):
    """Per-map min–max to [0, 1] (tensor, keeps shape)."""
    import torch

    flat_min = cam.amin(dim=(2, 3), keepdim=True)
    flat_max = cam.amax(dim=(2, 3), keepdim=True)
    denom = (flat_max - flat_min).clamp_min(1e-8)
    return (cam - flat_min) / denom


def _fuse_layer_maps(
    maps: Dict[str, Any],
    layercam_l4: Optional[Any] = None,
):
    """Weighted fusion of multi-layer Grad-CAM++ (+ optional LayerCAM)."""
    import torch
    import torch.nn.functional as F

    parts = []
    weights = []

    if "layer4" in maps:
        parts.append(_minmax_tensor(maps["layer4"]))
        weights.append(_W_LAYER4_GPP)
    if "layer3" in maps:
        # Upsample layer3 map to layer4 spatial size before fuse if needed.
        m3 = maps["layer3"]
        ref = maps.get("layer4", m3)
        if m3.shape[-2:] != ref.shape[-2:]:
            m3 = F.interpolate(m3, size=ref.shape[-2:], mode="bilinear", align_corners=False)
        parts.append(_minmax_tensor(m3))
        weights.append(_W_LAYER3_GPP)
    if layercam_l4 is not None:
        parts.append(_minmax_tensor(layercam_l4))
        weights.append(_W_LAYER4_LC)

    if not parts:
        raise RuntimeError("No CAM maps to fuse.")

    # Renormalise weights if some layers were missing.
    wsum = float(sum(weights))
    weights = [w / wsum for w in weights]

    fused = weights[0] * parts[0]
    for w, p in zip(weights[1:], parts[1:]):
        fused = fused + w * p
    return torch.relu(fused)


def _single_pass_cam(
    model,
    x,
    target_index: int,
    named_layers: Sequence[Tuple[str, Any]],
):
    """One forward/backward → fused multi-layer Grad-CAM++ (+ LayerCAM) map."""
    import torch
    import torch.nn.functional as F

    acts: Dict[str, Any] = {}
    grads: Dict[str, Any] = {}
    handles = []

    for name, layer in named_layers:
        def _fwd(module, inputs, output, n=name):
            acts[n] = output

        def _bwd(module, grad_input, grad_output, n=name):
            grads[n] = grad_output[0]

        handles.append(layer.register_forward_hook(_fwd))
        handles.append(layer.register_full_backward_hook(_bwd))

    try:
        model.zero_grad(set_to_none=True)
        # Fresh graph each SmoothGrad sample.
        logits = model(x)
        logits[0, target_index].backward()

        gpp_maps: Dict[str, Any] = {}
        layercam_l4 = None
        for name, _layer in named_layers:
            a = acts.get(name)
            g = grads.get(name)
            if a is None or g is None:
                continue
            a = a.detach()
            g = g.detach()
            gpp_maps[name] = _gradcam_plusplus_map(a, g)
            if name == "layer4":
                layercam_l4 = _layercam_map(a, g)

        if not gpp_maps:
            raise RuntimeError("Grad-CAM++ hooks did not capture activations.")

        fused = _fuse_layer_maps(gpp_maps, layercam_l4=layercam_l4)
        # Mild blur on the coarse feature grid before upsample.
        fused = _gaussian_blur(fused, sigma=_BLUR_PRE)
        fused = F.interpolate(
            fused,
            size=(_OUT_SIZE, _OUT_SIZE),
            mode="bilinear",
            align_corners=False,
        )
        fused = torch.relu(fused)
        return fused
    finally:
        for h in handles:
            h.remove()


def _apply_threshold(cam: np.ndarray, thr: float) -> np.ndarray:
    thr = float(np.clip(thr, 0.0, 0.85))
    if thr <= 0.0:
        out = cam.copy()
    else:
        out = np.clip((cam - thr) / (1.0 - thr + 1e-8), 0.0, 1.0)
    peak = float(out.max())
    if peak > 1e-8:
        out = out / peak
    return out


def _normalise_and_sharpen(cam_np: np.ndarray) -> np.ndarray:
    """Min–max, power, soft threshold; iterative threshold toward _TARGET_MEAN."""
    cam = np.asarray(cam_np, dtype=np.float32)
    cam = np.maximum(cam, 0.0)
    lo = float(cam.min())
    hi = float(cam.max())
    if hi - lo < 1e-8:
        return np.zeros_like(cam, dtype=np.float32)

    cam = (cam - lo) / (hi - lo)
    cam = np.power(cam, _CAM_POWER)

    thr = float(_CAM_THRESHOLD)
    out = _apply_threshold(cam, thr)

    # Binary-search a threshold so mean sits near the target (more reliable than
    # power-only adjustment on sparse maps).
    target = float(_TARGET_MEAN)
    mean = float(out.mean())
    if abs(mean - target) > _MEAN_TOL:
        lo_t, hi_t = 0.0, 0.75
        best = out
        for _ in range(10):
            mid = 0.5 * (lo_t + hi_t)
            cand = _apply_threshold(cam, mid)
            m = float(cand.mean())
            best = cand
            if abs(m - target) <= _MEAN_TOL:
                break
            if m > target:
                lo_t = mid  # need more suppression
            else:
                hi_t = mid
        out = best

    return out.astype(np.float32)


def _resize_cam_float(cam: np.ndarray, size: int) -> np.ndarray:
    import torch
    import torch.nn.functional as F

    t = torch.from_numpy(np.asarray(cam, dtype=np.float32))[None, None]
    t = F.interpolate(t, size=(size, size), mode="bilinear", align_corners=False)
    return t[0, 0].numpy().astype(np.float32)


def _compute_cam(image: Image.Image, target_index: Optional[int]) -> CamResult:
    """SmoothGrad multi-layer Grad-CAM++ → sharpened map in [0, 1]."""
    import torch
    import torch.nn.functional as F

    model = _load_model()
    model.eval()
    x = _preprocess(image)
    named_layers = _resolve_target_layers(model)

    # Clean forward for class + confidence (no noise).
    with torch.no_grad():
        logits = model(x)
        if target_index is None:
            target_index = int(torch.argmax(logits, dim=1).item())
        target_index = int(target_index)
        orig_confidence = float(F.softmax(logits, dim=1)[0, target_index].item())

    n = max(1, int(_SMOOTH_N))
    sigma = float(_SMOOTH_SIGMA)
    acc = None

    for i in range(n):
        if i == 0 or sigma <= 0:
            xi = x
        else:
            noise = torch.randn_like(x) * sigma
            xi = (x + noise).clamp(-1.0, 1.0)

        # Need grad enabled on the input path; model params stay frozen via eval.
        cam_i = _single_pass_cam(model, xi, target_index, named_layers)
        acc = cam_i if acc is None else acc + cam_i

    cam = acc / float(n)
    cam = _gaussian_blur(cam, sigma=_BLUR_POST)
    cam_np = cam[0, 0].detach().cpu().numpy().astype(np.float32)

    return CamResult(
        cam=_normalise_and_sharpen(cam_np),
        target_index=target_index,
        x=x.detach(),
        orig_confidence=orig_confidence,
    )


# ---------------------------------------------------------------------------
# Rendering / public API
# ---------------------------------------------------------------------------


def _render_overlay(base_rgb: np.ndarray, cam: np.ndarray) -> np.ndarray:
    """Jet heat on blue X-ray base; alpha gated by attention only."""
    h, w = base_rgb.shape[:2]
    if cam.shape[0] != h or cam.shape[1] != w:
        cam = _resize_cam_float(cam, size=h if h == w else max(h, w))
        if cam.shape[0] != h or cam.shape[1] != w:
            import torch
            import torch.nn.functional as F

            t = torch.from_numpy(cam)[None, None]
            cam = F.interpolate(t, size=(h, w), mode="bilinear", align_corners=False)[
                0, 0
            ].numpy()

    cam = np.clip(cam, 0.0, 1.0).astype(np.float32)
    film = _xray_blue_base(base_rgb)
    heatmap = _jet_colormap(cam)

    # Slightly super-linear alpha so peaks punch through the blue film.
    alpha = (cam[..., None] ** 0.90) * _MAX_ALPHA

    overlay = film * (1.0 - alpha) + heatmap * alpha
    return np.clip(overlay * 255.0, 0, 255).astype(np.uint8)


def _encode_png(arr: np.ndarray) -> str:
    out = Image.fromarray(arr).convert("RGB")
    buf = io.BytesIO()
    out.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def generate_gradcam_base64(image: Image.Image, target_index: Optional[int] = None) -> str:
    """Generate a Grad-CAM++ overlay (base64 PNG). Returns \"\" on failure."""
    if not isinstance(image, Image.Image):
        return ""
    try:
        result = _compute_cam(image, target_index)
        base_rgb = _to_rgb_array(image, _RENDER_SIZE)
        return _encode_png(_render_overlay(base_rgb, result.cam))
    except Exception:
        logger.exception("Grad-CAM++ generation failed.")
        return ""


def compute_cam_bundle(image: Image.Image, target_index: Optional[int] = None) -> Optional[CamResult]:
    """Public accessor for the raw CAM bundle. Returns None on failure."""
    if not isinstance(image, Image.Image):
        return None
    try:
        return _compute_cam(image, target_index)
    except Exception:
        logger.exception("Grad-CAM++ computation failed.")
        return None


def render_overlay_base64(image: Image.Image, cam: np.ndarray) -> str:
    """Render an overlay PNG (base64) from an image and a precomputed CAM."""
    try:
        base_rgb = _to_rgb_array(image, _RENDER_SIZE)
        return _encode_png(_render_overlay(base_rgb, cam))
    except Exception:
        logger.exception("Grad-CAM++ overlay rendering failed.")
        return ""


def generate_gradcam_heatmap_base64(
    image: Image.Image, target_index: Optional[int] = None
) -> str:
    """Standalone Jet heatmap (no MRI underlay) as a base64 PNG."""
    if not isinstance(image, Image.Image):
        return ""
    try:
        result = _compute_cam(image, target_index)
        cam = _resize_cam_float(result.cam, _RENDER_SIZE)
        heatmap = (_jet_colormap(cam) * 255.0).astype(np.uint8)
        return _encode_png(heatmap)
    except Exception:
        logger.exception("Grad-CAM++ heatmap generation failed.")
        return ""
