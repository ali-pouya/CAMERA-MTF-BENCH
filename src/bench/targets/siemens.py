"""
Utilities for Siemens star geometry and radial sampling.

I keep this module intentionally simple for v1:
    - I estimate the center and radius using only image shape.
    - I create annulus masks for quick debugging/visualization.
    - I sample circular intensity profiles using nearest-neighbor lookup.

Later, if I need subpixel interpolation or more robust center detection,
I can replace the internals here without changing the public API.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Data container for Siemens geometry
# ---------------------------------------------------------------------------

@dataclass
class SiemensParams:
    """
    Simple container for Siemens star geometry.

    I use this struct so I have a clear, typed return from the geometry
    estimator. If I later switch to a more advanced estimator (e.g.,
    gradient-based center refinement), this struct still works the same.

    Attributes
    ----------
    cx : float
        X-coordinate of center (column index, in pixels).

    cy : float
        Y-coordinate of center (row index, in pixels).

    radius : float
        Approximate usable radius of the Siemens pattern (in pixels).
    """
    cx: float
    cy: float
    radius: float


# ---------------------------------------------------------------------------
# Center + radius estimation
# ---------------------------------------------------------------------------

def estimate_center_and_radius(
    img: np.ndarray,
    center_hint: Tuple[float, float] | None = None,
    radius_frac: float = 0.45,
) -> SiemensParams:
    """
    Estimate the center and approximate outer radius of a Siemens star.

    For v1 I keep this deliberately simple:
      - assume the star is roughly centered in the image
      - optionally accept a user-provided center_hint
      - derive a radius using a fraction of the smallest dimension

    This is robust enough for synthetic data and most lab captures.
    If I need something more accurate later, I can replace only this
    function without touching the rest of the pipeline.

    Parameters
    ----------
    img : np.ndarray
        Input image (2D or 3D). Only the shape is used.

    center_hint : (cx, cy), optional
        If provided, overrides the default center.

    radius_frac : float
        Fraction of min(height, width) used as the estimated radius.

    Returns
    -------
    SiemensParams
    """
    h, w = img.shape[:2]

    if center_hint is None:
        cx = (w - 1) / 2.0
        cy = (h - 1) / 2.0
    else:
        cx, cy = center_hint

    radius = radius_frac * min(h, w)

    return SiemensParams(cx=float(cx), cy=float(cy), radius=float(radius))


# ---------------------------------------------------------------------------
# Annulus mask helper (useful for visualization/debugging)
# ---------------------------------------------------------------------------

def make_annulus_mask(
    shape: Tuple[int, int],
    center: Tuple[float, float],
    r_inner: float,
    r_outer: float,
) -> np.ndarray:
    """
    Create a boolean annulus mask for visualization/debugging.

    I use this when I want to quickly see which radial regions I'm sampling
    in the Siemens MTF routine. For performance or subpixel accuracy I can
    always replace this later.

    Returns
    -------
    mask : np.ndarray of bool
    """
    h, w = shape
    cx, cy = center

    yy, xx = np.ogrid[:h, :w]

    dist2 = (xx - cx) ** 2 + (yy - cy) ** 2
    r2_inner = r_inner * r_inner
    r2_outer = r_outer * r_outer

    mask = (dist2 >= r2_inner) & (dist2 <= r2_outer)
    return mask


# ---------------------------------------------------------------------------
# Circular sampling (core primitive used by Siemens MTF)
# ---------------------------------------------------------------------------

def sample_radial_profile(
    img: np.ndarray,
    center: Tuple[float, float],
    radius: float,
    num_angles: int = 1024,
) -> np.ndarray:
    """
    Sample image intensity along a circular path.

    For v1 I intentionally use:
        - a simple grayscale conversion (mean over channels)
        - equally spaced angles from 0 → 2π
        - nearest-neighbor sampling

    This is lightweight, fast, and fully deterministic.

    In a future update (if needed) I can:
        - switch to bilinear interpolation
        - handle color targets differently
        - refine the center more carefully
        - include anti-aliasing for small radii

    Parameters
    ----------
    img : np.ndarray
        Input image (2D or 3-channel).

    center : (cx, cy)
        Pixel coordinates of the circular sampling center.

    radius : float
        Sampling radius in pixels.

    num_angles : int
        Number of angular samples around the circle.

    Returns
    -------
    profile : np.ndarray
        1D array of intensity values sampled along the circle.
    """
    arr = np.asarray(img)

    # Convert to grayscale if needed — I keep it intentionally simple.
    if arr.ndim == 3:
        arr = arr.mean(axis=2)

    arr = arr.astype(np.float64)

    h, w = arr.shape
    cx, cy = center

    # Angular coordinates
    theta = np.linspace(0.0, 2.0 * np.pi, num_angles, endpoint=False)

    # Floating-point coordinates of the circle
    xs = cx + radius * np.cos(theta)
    ys = cy + radius * np.sin(theta)

    # Nearest-neighbor sampling (sufficient for Siemens spoke detection)
    xs_round = np.rint(xs).astype(int)
    ys_round = np.rint(ys).astype(int)

    # Clip to valid image extent
    xs_round = np.clip(xs_round, 0, w - 1)
    ys_round = np.clip(ys_round, 0, h - 1)

    profile = arr[ys_round, xs_round]
    return profile
