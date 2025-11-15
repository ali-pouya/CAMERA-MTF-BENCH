from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import cv2
import matplotlib.pyplot as plt  # I rely on matplotlib for quick diagnostic plots

from .autofocus import scan_autofocus_stack_siemens
from .metrics import mtf_siemens_multi_radius
from .workflows import run_focus_and_mtf


# ---------------------------------------------------------------------------
# Hardware workflow config
# ---------------------------------------------------------------------------

@dataclass
class FocusAndMTFHWConfig:
    """
    Configuration object for the hardware focus + MTF workflow.

    I pass this into `workflows_hardware.run_focus_and_mtf_hw(config)` so that
    command-line parsing stays separate from the lower-level hardware logic.
    """
    camera_backend: str
    stage_backend: str
    z_start: float
    z_end: float
    z_step: float
    frames_per_step: int
    exposure_ms: float
    gain: Optional[float]
    target: str
    out_dir: Path
    dry_run: bool
    camera_index: int


# ---------------------------------------------------------------------------
# Command implementations
# ---------------------------------------------------------------------------

def cmd_list_visa(args: argparse.Namespace) -> None:
    """
    Placeholder for future PyVISA integration.

    Right now this is just a stub; later I plan to replace it with a real
    VISA resource scan that can classify instruments (stages, scopes, etc.).
    """
    print("[list-visa] PyVISA integration is not implemented yet.")
    print("I will eventually list connected VISA instruments here.")


def cmd_demo_af(args: argparse.Namespace) -> None:
    """
    Run Siemens-based autofocus over a synthetic focus stack.

    Example:
        python -m bench demo-af --stack 'data/focus_stack/*.png' \
                                --z-start -200 --z-end 200
    """
    pattern = args.stack
    z_start = args.z_start
    z_end = args.z_end

    print(f"[demo-af] Using stack pattern: {pattern}")
    print(f"[demo-af] Simulated z range: [{z_start} µm, {z_end} µm]")

    result = scan_autofocus_stack_siemens(
        stack_pattern=pattern,
        z_start_um=z_start,
        z_end_um=z_end,
    )

    print(f"[demo-af] Best focus at z = {result.best_z_um:.2f} µm")
    print(f"[demo-af] Best metric = {result.best_metric:.3e}")

    if args.plot:
        plt.figure()
        plt.plot(result.positions_um, result.metrics, marker="o")
        plt.xlabel("Stage position [µm]")
        plt.ylabel("Siemens focus metric")
        plt.title("Autofocus scan on Siemens focus stack")
        plt.grid(True)
        plt.tight_layout()
        plt.show()


def cmd_mtf_siemens(args: argparse.Namespace) -> None:
    """
    Compute Siemens-based MTF curve by sweeping multiple radii.

    Example:
        python -m bench mtf-siemens --image data/focus_stack/frame_04.png \
                                    --out outputs/mtf_siemens
    """
    img_path = Path(args.image)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[mtf-siemens] Loading image: {img_path}")
    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {img_path}")

    freq_norm, mtf_norm = mtf_siemens_multi_radius(
        img,
        center=None,
        r_min_frac=args.r_min_frac,
        r_max_frac=args.r_max_frac,
        num_radii=args.radii,
        num_angles=args.angles,
    )

    # Save CSV
    csv_path = out_dir / "mtf_siemens_multi_radius.csv"
    data = np.column_stack([freq_norm, mtf_norm])
    header = "freq_norm,mtf_norm"
    np.savetxt(csv_path, data, delimiter=",", header=header, comments="")
    print(f"[mtf-siemens] Saved CSV: {csv_path}")

    # Optional plot
    if args.plot:
        plt.figure()
        plt.plot(freq_norm, mtf_norm, marker="o")
        plt.xlabel("Normalized spatial frequency")
        plt.ylabel("Normalized MTF (Siemens multi-radius)")
        plt.title("Siemens-based MTF (multi-radius)")
        plt.grid(True)
        plt.tight_layout()

        png_path = out_dir / "mtf_siemens_multi_radius.png"
        plt.savefig(png_path, dpi=120)
        print(f"[mtf-siemens] Saved plot: {png_path}")
        plt.show()
    else:
        print("[mtf-siemens] Plotting disabled (use --plot to view/save PNG).")


def cmd_focus_and_mtf(args: argparse.Namespace) -> None:
    """
    Run the full **simulated** pipeline:

      1) Siemens-based autofocus over a focus stack.
      2) Siemens-based MTF (multi-radius) at the best-focus frame.
      3) Save all artifacts (CSV/PNG/JSON) into the output folder.
    """
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[focus-and-mtf] Stack pattern : {args.stack}")
    print(f"[focus-and-mtf] z range      : [{args.z_start} µm, {args.z_end} µm]")
    print(f"[focus-and-mtf] Output folder: {out_dir}")

    summary = run_focus_and_mtf(
        stack_pattern=args.stack,
        z_start_um=args.z_start,
        z_end_um=args.z_end,
        out_dir=out_dir,
        angles=args.angles,
        r_min_frac=args.r_min_frac,
        r_max_frac=args.r_max_frac,
        num_radii=args.radii,
        make_plots=(not args.no_plot),
    )

    print("[focus-and-mtf] Done.")
    print(
        f"[focus-and-mtf] Best focus at z = {summary['best_z_um']:.2f} µm "
        f"(frame index = {summary['best_index']})"
    )
    print(f"[focus-and-mtf] Summary JSON: {summary['summary_json']}")


def cmd_focus_and_mtf_hw(args: argparse.Namespace) -> None:
    """
    Hardware bench entry point.

    This is where I sequence the physical stage and camera for a focus sweep.
    To keep things maintainable, I only handle configuration and logging here
    and push all hardware details into `workflows_hardware.py`.
    """
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    config = FocusAndMTFHWConfig(
        camera_backend=args.camera,
        stage_backend=args.stage,
        z_start=args.z_start,
        z_end=args.z_end,
        z_step=args.z_step,
        frames_per_step=args.frames_per_step,
        exposure_ms=args.exposure_ms,
        gain=args.gain,
        target=args.target,
        out_dir=out_dir,
        dry_run=args.dry_run,
        camera_index=args.camera_index,
    )

    print("[focus-and-mtf-hw] Configuration:")
    print(config)

    try:
        from . import workflows_hardware
    except ImportError as exc:
        print(
            "[focus-and-mtf-hw] ERROR: Could not import `bench.workflows_hardware`.\n"
            f"Underlying error: {exc}\n"
            "I expect `src/bench/workflows_hardware.py` to exist in this project."
        )
        return

    if not hasattr(workflows_hardware, "run_focus_and_mtf_hw"):
        print(
            "[focus-and-mtf-hw] ERROR: `workflows_hardware` does not define "
            "`run_focus_and_mtf_hw(config)`."
        )
        return

    workflows_hardware.run_focus_and_mtf_hw(config)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bench",
        description="Automated Camera MTF & Autofocus Bench (PyVISA + OpenCV)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # -------------------------------------------------------------------------
    # list-visa
    # -------------------------------------------------------------------------
    p_visa = subparsers.add_parser(
        "list-visa",
        help="List VISA instruments (placeholder; PyVISA integration TBD).",
    )
    p_visa.set_defaults(func=cmd_list_visa)

    # -------------------------------------------------------------------------
    # demo-af  (Siemens-based autofocus over focus stack)
    # -------------------------------------------------------------------------
    p_af = subparsers.add_parser(
        "demo-af",
        help="Run Siemens-based autofocus over a synthetic focus stack.",
    )
    p_af.add_argument(
        "--stack",
        required=True,
        help="Glob pattern for focus stack frames, e.g. 'data/focus_stack/*.png'.",
    )
    p_af.add_argument(
        "--z-start",
        type=float,
        default=-200.0,
        help="Starting z position in micrometers (default: -200).",
    )
    p_af.add_argument(
        "--z-end",
        type=float,
        default=200.0,
        help="Ending z position in micrometers (default: 200).",
    )
    p_af.add_argument(
        "--no-plot",
        dest="plot",
        action="store_false",
        help="Disable plotting of autofocus metric vs z.",
    )
    p_af.set_defaults(func=cmd_demo_af, plot=True)

    # -------------------------------------------------------------------------
    # mtf-siemens  (Siemens-based MTF, multi-radius)
    # -------------------------------------------------------------------------
    p_mtf = subparsers.add_parser(
        "mtf-siemens",
        help="Compute Siemens-based MTF from a single image (multi-radius).",
    )
    p_mtf.add_argument(
        "--image",
        required=True,
        help="Input image file (best-focus Siemens star).",
    )
    p_mtf.add_argument(
        "--out",
        required=True,
        help="Output directory for CSV/plots.",
    )
    p_mtf.add_argument(
        "--angles",
        type=int,
        default=2048,
        help="Number of angular samples per radius (default: 2048).",
    )
    p_mtf.add_argument(
        "--r-min-frac",
        type=float,
        default=0.2,
        help="Inner radius fraction (highest spatial frequency, default: 0.2).",
    )
    p_mtf.add_argument(
        "--r-max-frac",
        type=float,
        default=0.9,
        help="Outer radius fraction (lowest spatial frequency, default: 0.9).",
    )
    p_mtf.add_argument(
        "--radii",
        type=int,
        default=20,
        help="Number of radii to sample between r_max and r_min (default: 20).",
    )
    p_mtf.add_argument(
        "--no-plot",
        dest="plot",
        action="store_false",
        help="Disable plotting; still writes CSV.",
    )
    p_mtf.set_defaults(func=cmd_mtf_siemens, plot=True)

    # -------------------------------------------------------------------------
    # focus-and-mtf  (full pipeline: autofocus + MTF, simulated stack)
    # -------------------------------------------------------------------------
    p_fm = subparsers.add_parser(
        "focus-and-mtf",
        help="Run autofocus on a Siemens focus stack, then Siemens-based MTF at best focus.",
    )
    p_fm.add_argument(
        "--stack",
        required=True,
        help="Glob pattern for focus stack frames, e.g. 'data/focus_stack/*.png'.",
    )
    p_fm.add_argument(
        "--out",
        required=True,
        help="Output directory for CSV/PNG/JSON artifacts.",
    )
    p_fm.add_argument(
        "--z-start",
        type=float,
        default=-200.0,
        help="Starting z position in micrometers (default: -200).",
    )
    p_fm.add_argument(
        "--z-end",
        type=float,
        default=200.0,
        help="Ending z position in micrometers (default: 200).",
    )
    p_fm.add_argument(
        "--angles",
        type=int,
        default=2048,
        help="Number of angular samples per radius for MTF (default: 2048).",
    )
    p_fm.add_argument(
        "--r-min-frac",
        type=float,
        default=0.2,
        help="Inner radius fraction (highest spatial frequency, default: 0.2).",
    )
    p_fm.add_argument(
        "--r-max-frac",
        type=float,
        default=0.9,
        help="Outer radius fraction (lowest spatial frequency, default: 0.9).",
    )
    p_fm.add_argument(
        "--radii",
        type=int,
        default=20,
        help="Number of radii to sample between r_max and r_min (default: 20).",
    )
    p_fm.add_argument(
        "--no-plot",
        action="store_true",
        help="Disable PNG plotting (only CSV/JSON).",
    )
    p_fm.set_defaults(func=cmd_focus_and_mtf)

    # -------------------------------------------------------------------------
    # focus-and-mtf-hw  (hardware sweep + capture)
    # -------------------------------------------------------------------------
    p_hw = subparsers.add_parser(
        "focus-and-mtf-hw",
        help="Run hardware focus sweep and capture data for MTF analysis.",
    )
    p_hw.add_argument(
        "--camera",
        type=str,
        default="dummy",
        help="Camera backend: 'dummy' (default), 'opencv', or future backends.",
    )
    p_hw.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Camera index for OpenCV/FLIR (default: 0).",
    )
    p_hw.add_argument(
        "--stage",
        type=str,
        default="dummy",
        help="Stage backend: 'dummy' (default) or future hardware backends.",
    )
    p_hw.add_argument(
        "--z-start",
        type=float,
        required=True,
        help="Stage start position (e.g. in mm).",
    )
    p_hw.add_argument(
        "--z-end",
        type=float,
        required=True,
        help="Stage end position (e.g. in mm).",
    )
    p_hw.add_argument(
        "--z-step",
        type=float,
        required=True,
        help="Stage step size between positions (e.g. in mm).",
    )
    p_hw.add_argument(
        "--frames-per-step",
        type=int,
        default=1,
        help="Number of frames to capture at each focus position.",
    )
    p_hw.add_argument(
        "--exposure-ms",
        type=float,
        default=10.0,
        help="Camera exposure time in milliseconds.",
    )
    p_hw.add_argument(
        "--gain",
        type=float,
        default=None,
        help="Optional camera gain setting.",
    )
    p_hw.add_argument(
        "--target",
        type=str,
        default="siemens",
        choices=["siemens", "slanted-edge"],
        help="Imaging target used for the test.",
    )
    p_hw.add_argument(
        "--out",
        type=str,
        default="outputs/run_hw_001",
        help="Directory to store captured images and logs.",
    )
    p_hw.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned sweep but do not move hardware or capture images.",
    )
    p_hw.set_defaults(func=cmd_focus_and_mtf_hw)

    # GUI commands are intentionally kept out of v1 CLI.
    # If I revive a GUI later, I will add a separate `bench-gui` entry point
    # instead of packing it into this script.

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
