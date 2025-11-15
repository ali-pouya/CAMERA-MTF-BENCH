"""
Focus and contrast metrics used throughout the Camera MTF Bench.

I keep this module intentionally lightweight:
    - A small grayscale helper so every metric starts from a clean 2D float image.
    - Two general-purpose focus metrics (Tenengrad and Laplacian variance).
    - A Siemens-specific metric that computes Tenengrad inside an annulus.

Later, if I add wavelet-based metrics or frequency-domain sharpness scores,
I will slot them into this module behind the same simple interface.
"""

from __future__ import annotations

import numpy as np
import cv2

from bench.targets import estimate_center_and_radius, make_annulus_mask


# ---------------------------------------------------------------------------
# Shared grayscale helper
# ---------------------------------------------------------------------------

def _to_float_gray(image: np.ndarray) -> np.ndarray:
    """
    Convert an image to a 2D float64 grayscale array.

    I normalize everything to a simple grayscale float representation so
    that all metrics behave consistently regardless of whether frames come
    from OpenCV cameras, simulated stacks, PNGs, or raw Bayer data.

    Parameters
    ----------
    image : np.ndarray
        2D (grayscale) or 3D (BGR/RGB/RGBA-like) image.

    Returns
    -------
    np.ndarray
        2D float64 grayscale image.
    """
    arr = np.asarray(image)

    if arr.ndim == 2:
        gray = arr
    elif arr.ndim == 3 and arr.shape[2] in (3, 4):
        # Convert using OpenCV’s BGR→gray. I cast to uint8 if needed.
        if arr.dtype != np.uint8:
            arr = arr.astype(np.uint8)
        gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
    else:
        raise ValueError(f"Unsupported image shape for grayscale conversion: {arr.shape}")

    return gray.astype(np.float64)


# ---------------------------------------------------------------------------
# 1) Tenengrad (classic gradient-energy focus metric)
# ---------------------------------------------------------------------------

def tenengrad(image: np.ndarray) -> float:
    """
    Tenengrad focus metric (global gradient energy).

    Steps I use:
        1) Convert to float64 grayscale.
        2) Compute gx = dI/dx and gy = dI/dy using numpy gradients.
        3) Compute gradient energy = gx² + gy².
        4) Return the mean energy.

    Higher values → more high-frequency structure → sharper focus.

    Returns
    -------
    float
        Tenengrad sharpness metric.
    """
    gray = _to_float_gray(image)

    gx = np.gradient(gray, axis=1)
    gy = np.gradient(gray, axis=0)

    g2 = gx * gx + gy * gy
    return float(g2.mean())


# ---------------------------------------------------------------------------
# 2) Laplacian variance
# ---------------------------------------------------------------------------

def laplacian_variance(image: np.ndarray) -> float:
    """
    Variance of Laplacian focus metric.

    This is another very common sharpness indicator:
        - Apply a Laplacian filter
        - Take the variance of the resulting image

    Higher variance → more edges → sharper image.

    Returns
    -------
    float
        Variance of Laplacian.
    """
    gray = _to_float_gray(image)
    lap = cv2.Laplacian(gray, ddepth=cv2.CV_64F)
    return float(lap.var())


# ---------------------------------------------------------------------------
# 3) Tenengrad inside a mask (annulus-aware focus metric)
# ---------------------------------------------------------------------------

def tenengrad_in_mask(image: np.ndarray, mask: np.ndarray) -> float:
    """
    Tenengrad focus metric restricted to a boolean mask.

    I use this when I only want to measure sharpness in a specific region
    (like the active Siemens spokes), rather than over the whole frame.

    Parameters
    ----------
    image : np.ndarray
        Input image.
    mask : np.ndarray of bool
        Must match the grayscale image size.

    Returns
    -------
    float
        Masked gradient energy. Returns 0.0 if mask is empty.
    """
    gray = _to_float_gray(image)

    gx = np.gradient(gray, axis=1)
    gy = np.gradient(gray, axis=0)
    g2 = gx * gx + gy * gy

    if mask.shape != g2.shape:
        raise ValueError(
            f"Mask shape {mask.shape} does not match image shape {g2.shape}."
        )

    values = g2[mask]
    if values.size == 0:
        return 0.0

    return float(values.mean())


# ---------------------------------------------------------------------------
# 4) Siemens-specific focus metric
# ---------------------------------------------------------------------------

def siemens_focus_metric(
    image: np.ndarray,
    r_inner_frac: float = 0.4,
    r_outer_frac: float = 0.8,
) -> float:
    """
    Siemens-specific focus metric.

    I compute Tenengrad only inside an annulus around the Siemens spokes.
    This region is most sensitive to blur, so the metric tends to be smooth
    and monotonic around best focus.

    Steps:
        1) Estimate Siemens center & radius.
        2) Build an annulus mask     [r_inner_frac*R, r_outer_frac*R].
        3) Compute masked Tenengrad.

    Parameters
    ----------
    image : np.ndarray
        Image containing a Siemens star.
    r_inner_frac : float
        Inner radius fraction.
    r_outer_frac : float
        Outer radius fraction.

    Returns
    -------
    float
        Siemens-targeted sharpness metric.
    """
    gray = _to_float_gray(image)

    params = estimate_center_and_radius(gray)
    r_inner = r_inner_frac * params.radius
    r_outer = r_outer_frac * params.radius

    mask = make_annulus_mask(gray.shape, (params.cx, params.cy), r_inner, r_outer)
    return tenengrad_in_mask(gray, mask)
