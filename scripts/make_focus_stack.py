#!/usr/bin/env python3
"""
Generating a synthetic, *symmetric* focus stack from a single sharp source image.

Physical interpretation:
- The middle frame corresponds to best focus (defocus sigma = 0).
- Frames towards either end correspond to increasing defocus in +/– directions.
- The ends of the stack have the maximum blur sigma (sigma_max).

Usage example:
    python scripts/make_focus_stack.py \
        --input data/charts/slanted_edge.png \
        --out data/focus_stack \
        --frames  nine \
        --sigma-max 6.0
"""

import argparse
from pathlib import Path

import cv2
import numpy as np


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def symmetric_gaussian_blur_stack(
    image: np.ndarray, frames: int, sigma_max: float
) -> tuple[list[np.ndarray], np.ndarray]:
    """
    Creating a list of images with blur sigma ranging from sigma_max at the ends
    down to 0 at the center frame.

    For frames > 1:
        index i = 0 .. frames-1
        center  = (frames - 1) / 2
        normalized distance d(i) = |i - center| / center   in [0, 1]
        sigma(i) = d(i) * sigma_max

    - If frames is odd, the center index has sigma = 0 (exact best focus).
    - If frames is even, there are two closest-to-focus frames with the smallest sigma.

    Returns
    -------
    stack : list of np.ndarray
        Blurred frames in order.
    sigmas : np.ndarray
        Array of sigma values used for each frame.
    """
    if frames <= 0:
        raise ValueError("frames must be >= 1")

    if frames == 1:
        return [image.copy()], np.array([0.0], dtype=float)

    center = (frames - 1) / 2.0
    sigmas = np.empty(frames, dtype=float)
    stack: list[np.ndarray] = []

    for i in range(frames):
        d = abs(i - center) / center  # normalized distance from the middle [0, 1]
        sigma = d * sigma_max
        sigmas[i] = sigma

        if sigma == 0:
            blurred = image.copy()
        else:
            # kernel size ~ 6*sigma, at least 3, odd
            k = int(max(3, 6 * sigma))
            if k % 2 == 0:
                k += 1
            blurred = cv2.GaussianBlur(image, (k, k), sigmaX=sigma)

        stack.append(blurred)

    return stack, sigmas


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate a symmetric focus stack from a sharp source image. "
            "Middle frame is best focus; ends are most defocused."
        )
    )
    parser.add_argument("--input", required=True, help="Sharp source image file.")
    parser.add_argument("--out", required=True, help="Output folder for focus stack.")
    parser.add_argument(
        "--frames",
        type=int,
        default= 9,
        help="Number of frames in the stack (default: nine).",
    )
    parser.add_argument(
        "--sigma-max",
        type=float,
        default=6.0,
        help="Maximum blur sigma at the farthest defocus (default: 6.0).",
    )
    args = parser.parse_args()

    in_path = Path(args.input)
    out_dir = Path(args.out)
    ensure_dir(out_dir)

    img = cv2.imread(str(in_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Could not read input image: {in_path}")

    stack, sigmas = symmetric_gaussian_blur_stack(img, args.frames, args.sigma_max)

    index_sigma_lines = []

    for i, (frame, sigma) in enumerate(zip(stack, sigmas)):
        out_path = out_dir / f"frame_{i:02d}.png"
        cv2.imwrite(str(out_path), frame)
        index_sigma_lines.append(f"{i:02d}, {sigma:.4f}, {out_path.name}")

    # Optional: write a small metadata file with sigma per frame
    meta_path = out_dir / "focus_stack_metadata.txt"
    meta_path.write_text(
        "index, sigma, filename\n" + "\n".join(index_sigma_lines),
        encoding="utf-8",
    )

    print(f"[OK] Generated {len(stack)} frames (symmetric defocus).")
    print("Sigmas per frame:", sigmas)
    print(f"Middle frame index ≈ {(args.frames - 1) / 2:.2f}")
    print(f"Metadata written to: {meta_path.resolve()}")
    print(f"Output images in:   {out_dir.resolve()}")


if __name__ == "__main__":
    main()
