"""
Autofocus utilities for the Camera MTF Bench.

I keep this module intentionally small and focused:
- `scan_autofocus` handles the *general* stage+camera autofocus workflow.
- `scan_autofocus_stack_siemens` handles the *simulated* case where the
  focus sweep is represented by a folder of Siemens-star images.

Both functions return the same AFResult dataclass so that higher-level
pipelines (e.g., `workflows.py` or `workflows_hardware.py`) can treat
autofocus results uniformly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Tuple

import numpy as np

from .instruments import Stage, Camera


# ---------------------------------------------------------------------------
# Type alias for a focus metric function
# ---------------------------------------------------------------------------

# A function that takes an image and returns a scalar sharpness metric.
FocusMetric = Callable[[np.ndarray], float]


# ---------------------------------------------------------------------------
# Autofocus result dataclass
# ---------------------------------------------------------------------------

@dataclass
class AFResult:
    """
    Result of an autofocus scan.

    I always return the same structure so that downstream processing
    (e.g., plotting, selecting best-focus MTF) is consistent whether I'm
    using real hardware or a simulated focus stack.

    Attributes
    ----------
    best_z_um : float
        Stage position (in micrometers) that gave the highest focus metric.

    best_metric : float
        Maximum focus metric value.

    positions_um : np.ndarray
        1D array of all scanned positions [µm].

    metrics : np.ndarray
        1D array of focus metric values corresponding to positions_um.
    """

    best_z_um: float
    best_metric: float
    positions_um: np.ndarray
    metrics: np.ndarray


# ---------------------------------------------------------------------------
# 1) Generic autofocus (stage + camera)
# ---------------------------------------------------------------------------

def scan_autofocus(
    stage: Stage,
    camera: Camera,
    metric_fn: FocusMetric,
    start_um: float,
    stop_um: float,
    step_um: float,
    settle_callback=None,
) -> AFResult:
    """
    Simple scan-based autofocus:

        - Move stage from start_um → stop_um in increments of step_um.
        - At each position, grab an image and evaluate the focus metric.
        - Return the best metric and the full trace.

    I intentionally keep this algorithm straightforward and robust.
    Later, I can wrap smarter strategies (coarse→fine, hill climbing, golden
    section search) around the same metric_fn without changing this API.

    Parameters
    ----------
    stage : Stage
        Must implement move_to() and position().

    camera : Camera
        Must implement grab() -> np.ndarray.

    metric_fn : callable
        Function image -> scalar (e.g., Tenengrad or Siemens metric).

    start_um : float
        Starting stage position in micrometers.

    stop_um : float
        Final stage position in micrometers (inclusive-ish).

    step_um : float
        Step size in micrometers; must be non-zero.

    settle_callback : callable, optional
        If provided, I call this after each move before grabbing the image.
        For hardware this is useful for settling time; for mocks I ignore it.

    Returns
    -------
    AFResult
    """
    if step_um == 0:
        raise ValueError("step_um must be non-zero")

    # Validate that step direction actually moves toward stop_um.
    if (stop_um - start_um) * step_um < 0:
        raise ValueError("step_um sign does not move from start_um toward stop_um")

    positions = []
    metrics = []

    # Move to the starting point
    stage.move_to(start_um)
    z = stage.position()

    # Scan loop
    while True:
        # End conditions for positive/negative scanning
        if step_um > 0 and z > stop_um + 1e-9:
            break
        if step_um < 0 and z < stop_um - 1e-9:
            break

        if settle_callback is not None:
            settle_callback(stage)

        img = camera.grab()
        m = float(metric_fn(img))

        positions.append(z)
        metrics.append(m)

        # Move to the next position
        z = z + step_um
        stage.move_to(z)

    positions_arr = np.asarray(positions, dtype=float)
    metrics_arr = np.asarray(metrics, dtype=float)

    if metrics_arr.size == 0:
        raise RuntimeError("No autofocus samples were collected; check scan parameters.")

    best_idx = int(np.argmax(metrics_arr))
    best_z = float(positions_arr[best_idx])
    best_m = float(metrics_arr[best_idx])

    return AFResult(
        best_z_um=best_z,
        best_metric=best_m,
        positions_um=positions_arr,
        metrics=metrics_arr,
    )


# ---------------------------------------------------------------------------
# 2) Simulated autofocus on a Siemens focus stack
# ---------------------------------------------------------------------------

from bench.instruments import MockStage, MockCameraFocusStack
from bench.metrics import siemens_focus_metric


def scan_autofocus_stack_siemens(
    stack_pattern: str,
    z_start_um: float,
    z_end_um: float,
) -> AFResult:
    """
    Autofocus over a symmetric focus stack containing a Siemens star.

    This wrapper is designed specifically for simulation pipelines:
        - I load a stack of images from disk.
        - I map frame indices → physical z positions.
        - I evaluate a Siemens-specific focus metric at each index.
        - I return the same AFResult dataclass used for real hardware scans.

    Parameters
    ----------
    stack_pattern : str
        Glob pattern for focus stack frames, e.g. "data/focus_stack/*.png".
        Frames must be sorted in the same order as defocus.

    z_start_um : float
        Physical stage position corresponding to the first frame (index 0).

    z_end_um : float
        Physical stage position corresponding to the last frame (index N-1).

    Returns
    -------
    AFResult
        Dataclass with best focus position, best metric, and full traces.
    """
    cam = MockCameraFocusStack(stack_pattern)
    stage = MockStage(z0_um=z_start_um)

    n = cam.num_frames
    if n < 2:
        raise ValueError("Need at least two frames in the focus stack for autofocus.")

    # Map indices 0..n-1 to linearly spaced z positions
    positions = np.linspace(z_start_um, z_end_um, n)
    metrics = []

    for idx, z in enumerate(positions):
        stage.move_to(z)
        cam.set_index(idx)

        img = cam.grab()
        m = siemens_focus_metric(img)

        metrics.append(m)

    positions_arr = positions.astype(float)
    metrics_arr = np.asarray(metrics, dtype=float)

    best_idx = int(np.argmax(metrics_arr))
    best_z = float(positions_arr[best_idx])
    best_m = float(metrics_arr[best_idx])

    return AFResult(
        best_z_um=best_z,
        best_metric=best_m,
        positions_um=positions_arr,
        metrics=metrics_arr,
    )
