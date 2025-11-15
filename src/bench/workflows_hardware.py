"""
Hardware workflows for the Camera MTF Bench.

This module is the "glue" between the CLI and the hardware/instrument
drivers (camera, stage, etc.).

Right now my main focus is:
- Running the autofocus + MTF algorithms on **simulated** focus stacks.
- Providing a minimal hardware skeleton using DummyCamera and DummyStage.
- Optionally using a generic OpenCV camera when I want to plug in a UVC device.

Real integration with custom board cameras or production stages is intentionally
kept out of scope for this version. I plan to add that later (or in a separate
project) by swapping in real backends behind the same simple interface.

The main entry point is:

    run_focus_and_mtf_hw(config)

which is called from `bench.cli` for the `focus-and-mtf-hw` command.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING, List
import json
import time

import numpy as np
import cv2

if TYPE_CHECKING:  # for type-checkers only; avoids runtime circular import
    from .cli import FocusAndMTFHWConfig


# ---------------------------------------------------------------------------
# Dummy backends (safe for offline development)
# ---------------------------------------------------------------------------

@dataclass
class DummyCamera:
    """
    Very simple dummy camera: returns a gray ramp with noise.

    I use this as my default camera backend so that the hardware workflow
    runs on any machine, even when there is no real camera connected.
    """

    width: int = 640
    height: int = 480

    def open(self) -> None:
        print("[DummyCamera] open()")

    def close(self) -> None:
        print("[DummyCamera] close()")

    def grab_frame(self) -> np.ndarray:
        """Return a synthetic image."""
        # horizontal ramp + noise
        x = np.linspace(0, 1, self.width, dtype=np.float32)
        img = np.tile(x, (self.height, 1))
        noise = 0.03 * np.random.randn(self.height, self.width).astype(np.float32)
        img = np.clip(img + noise, 0, 1)
        return (img * 255).astype(np.uint8)


@dataclass
class OpenCVCamera:
    """
    Real camera backend using OpenCV VideoCapture.

    This works for:
      - FLIR cameras exposed as UVC / DirectShow,
      - standard USB webcams,
      - any camera accessible by cv2.VideoCapture(device_index).

    It matches the same interface as DummyCamera:
      - open()
      - close()
      - grab_frame() -> np.ndarray (uint8, BGR)

    For my v1 release I keep this backend intentionally simple; if I move to a
    dedicated SDK (e.g. Spinnaker/PySpin) I can slot that in behind the same API.
    """

    device_index: int = 0

    def __post_init__(self) -> None:
        self.cap: Optional[cv2.VideoCapture] = None

    def open(self) -> None:
        print(f"[OpenCVCamera] Opening device index {self.device_index}")
        self.cap = cv2.VideoCapture(self.device_index)
        if not self.cap.isOpened():
            raise RuntimeError(
                f"OpenCVCamera: could not open camera at index {self.device_index}"
            )

    def close(self) -> None:
        print("[OpenCVCamera] close()")
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def grab_frame(self) -> np.ndarray:
        if self.cap is None:
            raise RuntimeError("OpenCVCamera.grab_frame() called before open().")
        ok, frame = self.cap.read()
        if not ok or frame is None:
            raise RuntimeError("OpenCVCamera: failed to grab frame from camera.")
        return frame


@dataclass
class DummyStage:
    """
    Dummy stage that just tracks a current position in memory.

    This lets me exercise the sequencing logic (positions, filenames, summaries)
    without owning any physical motion hardware.
    """

    position: float = 0.0

    def move_to(self, z: float) -> None:
        print(f"[DummyStage] move_to({z})")
        self.position = z

    def get_position(self) -> float:
        return self.position


# ---------------------------------------------------------------------------
# Backend factories
# ---------------------------------------------------------------------------

def _open_camera(backend: str, config: "FocusAndMTFHWConfig") -> Any:
    """
    Return a camera object with at least:
        - open()
        - close()
        - grab_frame() -> np.ndarray

    Backends:
      - 'dummy'  : synthetic ramp image.
      - 'opencv' : cv2.VideoCapture(camera_index).
      - 'flir'   : currently identical to 'opencv', assuming FLIR is UVC/DirectShow.
                   If I move to Spinnaker/PySpin later, I will replace this mapping.

    I keep the mapping small and explicit on purpose so it's obvious where to
    plug in a future custom board-camera backend.
    """
    backend = backend.lower()

    if backend == "dummy":
        return DummyCamera()

    if backend in ("opencv", "flir"):
        # For now, both map to a generic OpenCV camera.
        # This should work for many FLIR USB/board cameras when exposed as UVC.
        return OpenCVCamera(device_index=config.camera_index)

    # Placeholder for a future dedicated FLIR/PySpin implementation:
    # if backend == "flir-spinnaker":
    #     from .instruments import flir_spinnaker
    #     return flir_spinnaker.FlirSpinnakerCamera(...)

    raise ValueError(f"Unknown camera backend: {backend!r}")


def _open_stage(backend: str, config: "FocusAndMTFHWConfig") -> Any:
    """
    Return a stage object with at least:
        - move_to(z: float)
        - get_position() -> float

    Right now I only rely on DummyStage; the VISA and Kinesis branches are
    placeholders showing where I will wire in real motion hardware later.
    """
    backend = backend.lower()
    if backend == "dummy":
        return DummyStage()

    if backend == "visa":
        # Example – probably wraps PyVISA + SCPI stage.
        # I keep this here as a hook for a future OV2311 + stage project.
        try:
            from .instruments import visa_stage
        except ImportError as exc:
            raise RuntimeError(
                "Requested stage backend 'visa' but could not import "
                "bench.instruments.visa_stage"
            ) from exc
        return visa_stage.VISAStage()  # TODO: I will adjust this to my real API.

    if backend == "kinesis":
        # Example – typical for Thorlabs stages driven by the Kinesis SDK.
        try:
            from .instruments import stage_kinesis
        except ImportError as exc:
            raise RuntimeError(
                "Requested stage backend 'kinesis' but could not import "
                "bench.instruments.stage_kinesis"
            ) from exc
        return stage_kinesis.KinesisStage()  # TODO: I will adjust this to my real API.

    raise ValueError(f"Unknown stage backend: {backend!r}")


# ---------------------------------------------------------------------------
# Core workflow
# ---------------------------------------------------------------------------

def _compute_positions(z_start: float, z_end: float, z_step: float) -> List[float]:
    if z_step == 0:
        raise ValueError("z_step must be non-zero.")
    # Include end point (within half-step tolerance)
    n_steps = int(np.floor((z_end - z_start) / z_step + 0.5)) + 1
    return [z_start + i * z_step for i in range(n_steps)]


def run_focus_and_mtf_hw(config: "FocusAndMTFHWConfig") -> int:
    """
    Hardware focus sweep + capture workflow.

    High-level steps:
      1) Create output folders.
      2) Compute stage positions.
      3) If dry_run: print plan and write JSON, then return.
      4) Open camera and stage backends.
      5) For each position:
           - move stage
           - optionally wait for settle
           - grab frames
           - save images to disk
      6) Write a simple run summary JSON.
      7) (Future) trigger Siemens/edge MTF analysis on best frame(s).

    I deliberately keep this workflow conservative and explicit. All the
    hardware-specific details are localized to `_open_camera` / `_open_stage`,
    so I can evolve drivers later without changing the control flow here.
    """
    out_dir: Path = config.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    print("[focus-and-mtf-hw] Starting hardware run.")
    print(f"[focus-and-mtf-hw] Camera backend : {config.camera_backend}")
    print(f"[focus-and-mtf-hw] Stage backend  : {config.stage_backend}")
    print(f"[focus-and-mtf-hw] z range        : [{config.z_start}, {config.z_end}]")
    print(f"[focus-and-mtf-hw] z step         : {config.z_step}")
    print(f"[focus-and-mtf-hw] frames/step    : {config.frames_per_step}")
    print(f"[focus-and-mtf-hw] exposure [ms]  : {config.exposure_ms}")
    print(f"[focus-and-mtf-hw] target         : {config.target}")
    print(f"[focus-and-mtf-hw] out_dir        : {out_dir}")
    print(f"[focus-and-mtf-hw] dry_run        : {config.dry_run}")

    positions = _compute_positions(config.z_start, config.z_end, config.z_step)
    print(f"[focus-and-mtf-hw] Planned positions ({len(positions)}): {positions}")

    # Save the planned run as JSON (useful even in dry runs)
    plan_path = out_dir / "plan_focus_sweep.json"
    plan = {
        "camera_backend": config.camera_backend,
        "stage_backend": config.stage_backend,
        "z_start": config.z_start,
        "z_end": config.z_end,
        "z_step": config.z_step,
        "positions": positions,
        "frames_per_step": config.frames_per_step,
        "exposure_ms": config.exposure_ms,
        "gain": config.gain,
        "target": config.target,
        "dry_run": config.dry_run,
    }
    with plan_path.open("w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)
    print(f"[focus-and-mtf-hw] Saved plan JSON: {plan_path}")

    if config.dry_run:
        print("[focus-and-mtf-hw] Dry run requested; not touching hardware.")
        return 0

    # --- Open hardware backends ------------------------------------------------
    camera = _open_camera(config.camera_backend, config)
    stage = _open_stage(config.stage_backend, config)

    camera.open()
    try:
        # Optional: initial move to z_start
        for idx_z, z in enumerate(positions):
            print(f"[focus-and-mtf-hw] Moving stage to z = {z}")
            stage.move_to(z)

            # I keep this settle time simple for now; if I move to a real
            # precision stage later, I can replace this with a status poll.
            time.sleep(0.1)

            for k in range(config.frames_per_step):
                frame = camera.grab_frame()
                if frame is None:
                    raise RuntimeError("grab_frame() returned None.")

                # Ensure grayscale uint8
                if frame.ndim == 3:
                    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                else:
                    frame_gray = frame

                fname = frames_dir / f"z{z:0.4f}_idx{idx_z:03d}_f{k:02d}.png"
                cv2.imwrite(str(fname), frame_gray)
                print(f"[focus-and-mtf-hw] Saved frame: {fname}")

        # Simple summary JSON (placeholder for future MTF results)
        summary = {
            "positions": positions,
            "frames_per_step": config.frames_per_step,
            "n_positions": len(positions),
            "n_frames_total": len(positions) * config.frames_per_step,
            "target": config.target,
        }
        summary_path = out_dir / "run_summary.json"
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"[focus-and-mtf-hw] Saved summary JSON: {summary_path}")

    finally:
        camera.close()

    print("[focus-and-mtf-hw] Completed hardware capture.")
    # Future: I might return nonzero here if something in the pipeline fails.
    return 0
