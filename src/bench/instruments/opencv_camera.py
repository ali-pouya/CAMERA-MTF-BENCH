from __future__ import annotations

import cv2
import numpy as np

from bench.instruments.camera import Camera


class OpenCVCamera(Camera):
    """
    Real camera backend using cv2.VideoCapture.

    This backend works for:
        - Standard UVC webcams
        - Many FLIR / Point Grey cameras in USB3 (UVC/DirectShow) mode
        - Any device that OpenCV can open via an integer device index

    I treat this as my "minimal real camera" option. If I need a custom
    SDK (e.g. PySpin/Spinnaker for FLIR, or a board-camera vendor SDK),
    I will wrap those behind this same Camera interface later.
    """

    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        self.cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        """
        Open the camera device.

        I do not set exposure, gain, or resolution here — OpenCV is too
        inconsistent across platforms. Instead, I treat those as optional
        hardware-stage responsibilities, and in v1 I keep this super simple.
        """
        print(f"[OpenCVCamera] Opening device index {self.device_index}")
        self.cap = cv2.VideoCapture(self.device_index)
        if not self.cap.isOpened():
            raise RuntimeError(
                f"OpenCVCamera: could not open camera at index {self.device_index}"
            )

    def close(self) -> None:
        """
        Release the underlying device.
        """
        print("[OpenCVCamera] close()")
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def grab(self) -> np.ndarray:
        """
        Grab a single frame from the camera as a grayscale uint8 image.

        I convert color frames to grayscale for consistency with the
        rest of the MTF/autofocus pipeline.
        """
        if self.cap is None:
            raise RuntimeError("OpenCVCamera.grab() called before open().")

        ok, frame = self.cap.read()
        if not ok or frame is None:
            raise RuntimeError("OpenCVCamera: failed to grab frame from camera.")

        if frame.ndim == 3:
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            frame_gray = frame

        return frame_gray
