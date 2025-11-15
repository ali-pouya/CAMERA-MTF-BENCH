"""
Manual autofocus test using a purely synthetic camera + stage.

I use this script to confirm that my autofocus implementation behaves
correctly when the focus metric is unimodal and well-behaved.

This does not depend on any real images or hardware.
"""

from __future__ import annotations

import numpy as np
import cv2

from bench.autofocus import scan_autofocus
from bench.instruments import MockStage, Camera
from bench.metrics import tenengrad


class DummyCamera(Camera):
    """
    Simple synthetic camera whose sharpness peaks at z = 200 µm.

    I simulate this with a hard edge image:
        - blur increases as |z - 200| grows
        - sigma is proportional to the distance from the true focus

    This lets me verify that the autofocus algorithm identifies the
    correct position in a controlled environment.
    """

    def __init__(self, stage: MockStage):
        self.stage = stage

    def grab(self) -> np.ndarray:
        z = self.stage.position()

        # Base synthetic 1D edge expanded into 2D
        img = np.zeros((64, 64), dtype=np.float64)
        img[:, 32:] = 255.0

        # Blur scales with distance from best focus (z = 200)
        sigma = abs(z - 200.0) / 100.0
        if sigma > 0:
            ksize = 9
            img = cv2.GaussianBlur(img, (ksize, ksize), sigmaX=sigma)

        return img.astype("uint8")


def main() -> None:
    """
    Run autofocus using the synthetic dummy camera.

    I use this as a smoke test whenever modifying autofocus logic,
    since the ground truth (best focus at z=200 µm) is known.
    """
    stage = MockStage(z0_um=0.0)
    cam = DummyCamera(stage)

    result = scan_autofocus(
        stage=stage,
        camera=cam,
        metric_fn=tenengrad,
        start_um=0.0,
        stop_um=400.0,
        step_um=50.0,
    )

    print("Positions:", result.positions_um)
    print("Metrics:", result.metrics)
    print("Best z:", result.best_z_um, "µm")


if __name__ == "__main__":
    main()
