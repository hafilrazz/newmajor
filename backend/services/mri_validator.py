from dataclasses import dataclass
from typing import List

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class MRIValidationResult:
    accepted: bool
    reasons: List[str]


def validate_mri_image(image: Image.Image) -> MRIValidationResult:
    """
    Reject obvious out-of-domain uploads before MRI stage classification.

    Plausibility check for exported 2D brain MRI slices — not a diagnostic
    OOD detector. Thresholds are intentionally moderate so typical clinical
    PNG/JPEG exports are accepted.
    """
    if not isinstance(image, Image.Image):
        return MRIValidationResult(False, ["The upload is not a readable image."])

    if image.width < 64 or image.height < 64:
        return MRIValidationResult(False, ["The image is too small for MRI analysis."])

    rgb = np.asarray(image.convert("RGB").resize((224, 224)), dtype=np.float32)
    gray = np.asarray(image.convert("L").resize((224, 224)), dtype=np.float32)
    reasons = []

    # Colorfulness: real MRI exports are near-grayscale, but allow slight tint/compression.
    channel_range = rgb.max(axis=2) - rgb.min(axis=2)
    color_pixel_ratio = float(np.mean(channel_range > 18.0))
    mean_channel_range = float(np.mean(channel_range))
    if color_pixel_ratio > 0.22 and mean_channel_range > 12.0:
        reasons.append("The uploaded image looks too colorful for a brain MRI slice.")

    # Require some contrast (reject near-blank images).
    if float(gray.std()) < 8.0:
        reasons.append("The image does not contain enough scan contrast.")

    # Dark frame is common but not universal (some cropped exports omit borders).
    border_width = max(6, int(min(gray.shape) * 0.08))
    border = np.concatenate(
        (
            gray[:border_width, :].ravel(),
            gray[-border_width:, :].ravel(),
            gray[:, :border_width].ravel(),
            gray[:, -border_width:].ravel(),
        )
    )
    dark_border_ratio = float(np.mean(border < 50.0))
    if dark_border_ratio < 0.22:
        reasons.append("The image does not have the expected dark MRI background.")

    # Foreground area: reject empty or nearly full-frame photos.
    foreground = gray > 28.0
    foreground_ratio = float(np.mean(foreground))
    if foreground_ratio < 0.04 or foreground_ratio > 0.90:
        reasons.append("The visible anatomy area is not consistent with a brain MRI slice.")

    return MRIValidationResult(not reasons, reasons)
