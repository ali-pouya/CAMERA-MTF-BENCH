"""
Focus, contrast, and Siemens-based MTF metrics.

Exposes:
- Generic focus metrics (Tenengrad, Laplacian variance)
- Siemens-specific focus metric (Tenengrad in Siemens annulus)
- Siemens-based MTF (multi-radius curve)
- Siemens-based FFT spectrum (single-radius, debug/inspection)
"""

from .contrast import (
    tenengrad,
    laplacian_variance,
    tenengrad_in_mask,
    siemens_focus_metric,
)

from .mtf_siemens import (
    mtf_siemens_spectrum_single_radius,
    mtf_siemens_multi_radius,
)

__all__ = [
    # Focus metrics
    "tenengrad",
    "laplacian_variance",
    "tenengrad_in_mask",
    "siemens_focus_metric",

    # Siemens MTF
    "mtf_siemens_spectrum_single_radius",
    "mtf_siemens_multi_radius",
]
