"""
Manual autofocus test using a Siemens focus stack.

I keep this script as a minimal, direct example of how to run autofocus
on a set of Siemens-star images without going through the CLI.

Example usage:
    python -m bench.manual_af_siemens_stack
"""

from __future__ import annotations

import numpy as np
from bench.autofocus import scan_autofocus_stack_siemens


def main() -> None:
    """
    Run autofocus over a synthetic Siemens focus stack on disk.

    I use this script whenever I want to sanity-check the autofocus
    algorithm or quickly visualize the metric curve.
    """
    pattern = "data/focus_stack/*.png"
    z_start_um = -200.0
    z_end_um = 200.0

    result = scan_autofocus_stack_siemens(
        stack_pattern=pattern,
        z_start_um=z_start_um,
        z_end_um=z_end_um,
    )

    print("Best z [µm]:", result.best_z_um)
    print("Best metric:", result.best_metric)
    print("All positions:", result.positions_um)
    print("All metrics:", result.metrics)

    # Optional: visualize the autofocus curve
    try:
        import matplotlib.pyplot as plt

        plt.figure()
        plt.plot(result.positions_um, result.metrics, marker="o")
        plt.xlabel("Stage position [µm]")
        plt.ylabel("Siemens focus metric")
        plt.title("Autofocus scan on Siemens focus stack")
        plt.grid(True)
        plt.show()

    except ImportError:
        # I allow this to run even if matplotlib is not installed
        pass


if __name__ == "__main__":
    main()
