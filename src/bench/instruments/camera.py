"""
Camera abstraction layer.

Right now I only need two things:
    - A base Camera interface that defines grab()
    - A MockCameraFocusStack that behaves like a real camera but reads from disk

For v1 this is perfect: I can validate the autofocus + MTF pipeline with
synthetic stacks, and later I will slot real camera drivers behind the
same interface (e.g., PySpin, UVC/OpenCV, custom board camera SDK).
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import cv2
import numpy as np
import glob


class Camera:
    """
    Abstract camera interface.

    I deliberately keep this minimal — one method:
        grab() -> np.ndarray (grayscale)
    That makes it easy to wrap any real camera SDK behind this API.
    """

    def grab(self) -> np.ndarray:  # pragma: no cover - interface
        raise NotImplementedError


class MockCameraFocusStack(Camera):
    """
    Camera backed by a folder of images forming a synthetic focus stack.

    The idea is simple:
      - I treat a folder of images as a "camera"
      - Each image is one position in the focus sweep
      - set_index(i) selects which "frame" the camera will return
      - grab() always returns the image for the current index

    This lets me test autofocus and Siemens/MTF logic end-to-end without
    touching hardware.
    """

    def __init__(self, pattern: str) -> None:
        files: List[str] = sorted(glob.glob(pattern))
        if not files:
            raise FileNotFoundError(f"No images matched pattern: {pattern}")
        self._files = [Path(f) for f in files]
        self._idx = 0

    @property
    def num_frames(self) -> int:
        """Number of frames in the focus stack."""
        return len(self._files)

    def set_index(self, idx: int) -> None:
        """
        Set the current frame index. I clamp it to [0, num_frames-1]
        so code can never request an invalid frame.
        """
        if self.num_frames == 0:
            raise RuntimeError("Focus stack is empty.")
        idx = max(0, min(idx, self.num_frames - 1))
        self._idx = idx

    def current_index(self) -> int:
        """Return the currently selected frame index."""
        return self._idx

    def grab(self) -> np.ndarray:
        """
        Return the current frame as a grayscale image.

        I keep reading as IMREAD_GRAYSCALE so all metrics are consistent
        across simulated and real cameras. Later, if I need Bayer or RGB
        handling, this is the place to extend it.
        """
        path = self._files[self._idx]
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise RuntimeError(f"Failed to read image: {path}")
        return img
