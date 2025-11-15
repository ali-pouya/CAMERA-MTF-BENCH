"""
Siemens-star–based MTF estimation.

I keep this file focused on two things:
- A legacy/debug spectrum function for inspecting angular FFTs.
- A practical multi-radius Siemens-star MTF proxy used in my pipeline.

This is not a classical ISO 12233 slanted-edge MTF. Instead I treat the
Siemens star as a radial pattern whose angular modulation decreases with
defocus. This gives me an intuitive and robust "MTF-like" curve that is
often good enough for quick optical validation.

All math is intentionally simple and self-contained.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

from bench.targets import estimate_center_and_radius, sample_radial_profile


# ---------------------------------------------------------------------------
# 1) Legacy/debug FFT spectrum
# ---------------------------------------------------------------------------

def mtf_siemens_spectrum_single_radius(
    img: np.ndarray,
    center: Tuple[float, float] | None = None,
    radius: float | None = None,
    num_angles: int = 2048,
) -> tuple[np.ndarray, np.ndarray]:
    """
    DEBUG / LEGACY:
        Compute the full FFT magnitude of a single angular profile.

    This is NOT a classical MTF curve — it's mostly for inspection and
    troubleshooting. Sometimes I use it to confirm that the Siemens spokes
    have the expected harmonic structure before running the full algorithm.

    Returns
    -------
    freq_norm : np.ndarray
        Normalized frequency axis for the angular FFT.

    mtf_norm : np.ndarray
        Normalized FFT magnitude.
    """
    arr = np.asarray(img)

    params = estimate_center_and_radius(arr)
    cx, cy, r_est = params.cx, params.cy, params.radius

    if center is not None:
        cx, cy = center
    if radius is None:
        radius = 0.7 * r_est  # simple default to avoid clipping

    profile = sample_radial_profile(arr, (cx, cy), radius=radius, num_angles=num_angles)

    # Remove DC component
    profile = profile.astype(np.float64)
    profile = profile - profile.mean()

    fft_vals = np.fft.rfft(profile)
    mag = np.abs(fft_vals)

    freqs = np.fft.rfftfreq(num_angles, d=1.0)

    # Normalize axes
    if freqs.max() > 0:
        freq_norm = freqs / freqs.max()
    else:
        freq_norm = freqs

    if mag.max() > 0:
        mtf_norm = mag / mag.max()
    else:
        mtf_norm = mag

    return freq_norm, mtf_norm


# ---------------------------------------------------------------------------
# 2) Siemens multi-radius MTF proxy
# ---------------------------------------------------------------------------

def mtf_siemens_multi_radius(
    img: np.ndarray,
    center: Tuple[float, float] | None = None,
    r_min_frac: float = 0.2,
    r_max_frac: float = 0.9,
    num_radii: int = 20,
    num_angles: int = 2048,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Estimate a Siemens-based MTF curve by sweeping multiple radii.

    Concept
    -------
    A Siemens star has a fixed angular spoke frequency (k0 cycles/revolution).
    When sampled along a circle of radius r:

        linear spatial frequency  f(r) ∝ k0 / (2πr)

    So:
        - smaller radii → higher spatial frequencies
        - larger radii  → lower spatial frequencies

    The algorithm:
      1) Determine the center and approximate Siemens radius.
      2) Sweep radii from outer (low freq) to inner (high freq).
      3) At each radius:
           * sample angular profile (num_angles samples)
           * subtract mean (remove DC)
           * take FFT
           * extract magnitude at the fundamental spoke harmonic (k0)
      4) Convert radius → normalized spatial frequency
      5) Normalize modulation → [0, 1]
      6) Return a smooth MTF-like curve

    This gives me a very intuitive MTF proxy that responds cleanly to
    sharpening/blur and is easy to plot across different lenses.

    Parameters
    ----------
    img : np.ndarray
        Input image containing a Siemens star, roughly centered.

    center : (cx, cy) tuple, optional
        Manually override the center. If None, I estimate it.

    r_min_frac : float
        Smallest radius as a fraction of the estimated Siemens radius.
        This corresponds to the highest spatial frequencies.

    r_max_frac : float
        Largest radius as a fraction of the estimated Siemens radius.
        This corresponds to the lowest spatial frequencies.

    num_radii : int
        Number of radii to sweep between r_max_frac*R and r_min_frac*R.

    num_angles : int
        Number of angular samples per radius.

    Returns
    -------
    freq_norm : np.ndarray
        Spatial frequency axis, normalized to [0, 1].

    mtf_norm : np.ndarray
        Normalized modulation (proxy for MTF) at each frequency.
    """

    arr = np.asarray(img)

    # Step 0: find center & radius
    params = estimate_center_and_radius(arr)
    cx, cy, r_est = params.cx, params.cy, params.radius

    if center is not None:
        cx, cy = center

    # Radii from outer (low freq) → inner (high freq)
    r_outer = r_max_frac * r_est
    r_inner = r_min_frac * r_est
    radii = np.linspace(r_outer, r_inner, num_radii)

    # Step 1: determine fundamental harmonic k0 at a reference radius
    r_ref = r_outer
    prof_ref = sample_radial_profile(arr, (cx, cy), radius=r_ref, num_angles=num_angles)
    prof_ref = prof_ref.astype(np.float64)
    prof_ref = prof_ref - prof_ref.mean()

    fft_ref = np.fft.rfft(prof_ref)
    mag_ref = np.abs(fft_ref)

    if mag_ref.size < 2:
        raise RuntimeError("FFT spectrum too small to estimate fundamental harmonic.")

    # I ignore DC (index 0) and take the largest remaining peak as the fundamental
    k0 = 1 + int(np.argmax(mag_ref[1:]))

    # Step 2: sweep radii and measure amplitude at k0
    freqs_linear = []
    mods = []

    for r in radii:
        profile = sample_radial_profile(arr, (cx, cy), radius=r, num_angles=num_angles)
        profile = profile.astype(np.float64)
        profile = profile - profile.mean()

        fft_vals = np.fft.rfft(profile)
        mag = np.abs(fft_vals)

        if k0 >= mag.size:
            # At very small radii, angular sampling may undersample k0
            # I skip those safely. This is rare unless the image is tiny.
            continue

        # Modulation amplitude at fundamental harmonic
        M = mag[k0]

        # Linear spatial frequency (up to a constant factor)
        f_linear = k0 / (2.0 * np.pi * r)

        freqs_linear.append(f_linear)
        mods.append(M)

    freqs_linear = np.asarray(freqs_linear, dtype=float)
    mods = np.asarray(mods, dtype=float)

    if freqs_linear.size == 0:
        raise RuntimeError("No valid radii found for Siemens MTF estimation.")

    # Step 3: sort by increasing frequency
    order = np.argsort(freqs_linear)
    freqs_linear = freqs_linear[order]
    mods = mods[order]

    # Step 4: normalize frequency to [0, 1]
    f_max = freqs_linear.max()
    if f_max > 0:
        freq_norm = freqs_linear / f_max
    else:
        freq_norm = freqs_linear

    # Step 5: normalize modulation to [0, 1]
    M_max = mods.max()
    if M_max > 0:
        mtf_norm = mods / M_max
    else:
        mtf_norm = mods

    return freq_norm, mtf_norm
