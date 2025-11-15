"""
High-level simulated workflow for autofocus + Siemens-based MTF.

This file is intentionally focused on the *simulation* pipeline:
    - I load a Siemens focus stack from disk.
    - I run my autofocus metric over the entire sweep.
    - I select the best-focus frame.
    - I compute Siemens multi-radius MTF on that frame.
    - I write CSV and PNG artifacts, plus a summary.json.

For hardware workflows I use `workflows_hardware.py`. Here I keep the
logic clean and image-based so it's always runnable on any machine.

Later, if I add real-camera backends or replace the focus stack loader
with a physical capture, this high-level pipeline stays the same.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

import numpy as np
import cv2
import matplotlib.pyplot as plt

from bench.autofocus import scan_autofocus_stack_siemens
from bench.instruments import MockCameraFocusStack
from bench.metrics import mtf_siemens_multi_radius


def run_focus_and_mtf(
    stack_pattern: str,
    z_start_um: float,
    z_end_um: float,
    out_dir: Path,
    angles: int = 2048,
    r_min_frac: float = 0.2,
    r_max_frac: float = 0.9,
    num_radii: int = 20,
    make_plots: bool = True,
) -> Dict[str, Any]:
    """
    End-to-end workflow (simulation mode):

        1) Run Siemens-based autofocus over a focus stack.
        2) Pick best-focus frame.
        3) Compute Siemens-based MTF (multi-radius) at the best focus.
        4) Save CSV/PNG artifacts and a JSON summary.

    This workflow has zero hardware dependencies. Everything runs on disk
    images. This lets me validate the autofocus and MTF logic anywhere,
    and later I can re-use this exact chain once real hardware capture is wired in.

    Parameters
    ----------
    stack_pattern : str
        Glob pattern for the focus stack, e.g. "data/focus_stack/*.png".
    z_start_um : float
        Starting z position in micrometers. Only used for labeling.
    z_end_um : float
        Ending z position in micrometers. Only used for labeling.
    out_dir : Path
        Output directory for all artifacts.
    angles : int
        Number of angular samples per radius for MTF estimation.
    r_min_frac : float
        Inner radius fraction (highest spatial frequency).
    r_max_frac : float
        Outer radius fraction (lowest spatial frequency).
    num_radii : int
        Number of radii to sample between r_max and r_min.
    make_plots : bool
        If True, save PNG plots in addition to CSVs.

    Returns
    -------
    summary : dict
        Dictionary with key results (best_z, best_index, file paths, etc.).
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1) Siemens autofocus
    # ------------------------------------------------------------------
    # I compute a focus metric (Siemens-based) across the entire stack.
    af_result = scan_autofocus_stack_siemens(
        stack_pattern=stack_pattern,
        z_start_um=z_start_um,
        z_end_um=z_end_um,
    )

    positions = af_result.positions_um
    metrics = af_result.metrics

    # Best index
    best_idx = int(np.argmax(metrics))
    best_z = float(positions[best_idx])
    best_metric = float(metrics[best_idx])

    # Save autofocus CSV
    af_csv = out_dir / "autofocus_curve.csv"
    af_data = np.column_stack([positions, metrics])
    np.savetxt(
        af_csv,
        af_data,
        delimiter=",",
        header="z_um,siemens_focus_metric",
        comments="",
    )

    # Save autofocus plot
    af_plot = None
    if make_plots:
        plt.figure()
        plt.plot(positions, metrics, marker="o")
        plt.xlabel("Stage position [µm]")
        plt.ylabel("Siemens focus metric")
        plt.title("Autofocus scan on Siemens focus stack")
        plt.grid(True)
        plt.tight_layout()
        af_plot = out_dir / "autofocus_curve.png"
        plt.savefig(af_plot, dpi=120)
        plt.close()

    # ------------------------------------------------------------------
    # 2) Grab best-focus frame from stack
    # ------------------------------------------------------------------
    # I use a simple mock-camera abstraction so that the autofocus pipeline
    # behaves the same whether images come from disk, a frame grabber,
    # or a real camera later.
    cam = MockCameraFocusStack(stack_pattern)
    cam.set_index(best_idx)
    best_img = cam.grab()

    best_img_path = out_dir / f"best_focus_frame_{best_idx:02d}.png"
    cv2.imwrite(str(best_img_path), best_img)

    # ------------------------------------------------------------------
    # 3) Siemens MTF (multi-radius) at best focus
    # ------------------------------------------------------------------
    # This step is the same whether the image came from disk or a physical camera.
    freq_norm, mtf_norm = mtf_siemens_multi_radius(
        best_img,
        center=None,
        r_min_frac=r_min_frac,
        r_max_frac=r_max_frac,
        num_radii=num_radii,
        num_angles=angles,
    )

    mtf_csv = out_dir / "mtf_siemens_multi_radius.csv"
    mtf_data = np.column_stack([freq_norm, mtf_norm])
    np.savetxt(
        mtf_csv,
        mtf_data,
        delimiter=",",
        header="freq_norm,mtf_norm",
        comments="",
    )

    mtf_plot = None
    if make_plots:
        plt.figure()
        plt.plot(freq_norm, mtf_norm, marker="o")
        plt.xlabel("Normalized spatial frequency")
        plt.ylabel("Normalized MTF (Siemens multi-radius)")
        plt.title("Siemens-based MTF at best focus")
        plt.grid(True)
        plt.tight_layout()
        mtf_plot = out_dir / "mtf_siemens_multi_radius.png"
        plt.savefig(mtf_plot, dpi=120)
        plt.close()

    # ------------------------------------------------------------------
    # 4) Summary JSON
    # ------------------------------------------------------------------
    summary: Dict[str, Any] = {
        "stack_pattern": stack_pattern,
        "z_start_um": float(z_start_um),
        "z_end_um": float(z_end_um),
        "best_index": best_idx,
        "best_z_um": best_z,
        "best_metric": best_metric,
        "autofocus_csv": str(af_csv),
        "autofocus_plot": str(af_plot) if af_plot is not None else None,
        "best_focus_image": str(best_img_path),
        "mtf_csv": str(mtf_csv),
        "mtf_plot": str(mtf_plot) if mtf_plot is not None else None,
        "angles": int(angles),
        "r_min_frac": float(r_min_frac),
        "r_max_frac": float(r_max_frac),
        "num_radii": int(num_radii),
    }

    summary_path = out_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Store the JSON path for convenience
    summary["summary_json"] = str(summary_path)

    return summary
