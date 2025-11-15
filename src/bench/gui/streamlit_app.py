from __future__ import annotations
import streamlit as st
import numpy as np
import cv2
from pathlib import Path
import glob

import matplotlib.pyplot as plt
from bench.workflows import run_focus_and_mtf


def show_image(title: str, img: np.ndarray):
    st.subheader(title)
    if img is None:
        st.write("⚠ No image loaded.")
        return
    if img.ndim == 2:
        st.image(img, clamp=True, use_container_width=True)
    else:
        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)


def main():
    st.set_page_config(page_title="Camera MTF & Autofocus Bench", layout="wide")

    # ---------- Global style tweak: slightly larger body text ----------
    st.markdown(
        """
        <style>
        /* Make normal paragraph text a bit larger for readability */
        div.block-container p {
            font-size: 1.05rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("📷 Automated Camera MTF & Autofocus Bench")

    st.markdown(
        """
        This GUI runs a **full bench pipeline**:

        1. Siemens-based autofocus over a focus stack  
        2. Extract the best-focus frame  
        3. Compute Siemens-based MTF (multi-radius)  

        All artifacts are saved to the chosen output folder.
        """
    )

    # Sidebar controls
    with st.sidebar:
        st.header("Settings")

        stack_pattern = st.text_input(
            "Focus stack pattern",
            value="data/focus_stack/*.png",
            help="Glob pattern for frames (e.g. data/focus_stack/*.png)",
        )

        out_dir = st.text_input(
            "Output directory",
            value="outputs/gui_run",
        )

        z_start = st.number_input("Z start (µm)", value=-200.0)
        z_end = st.number_input("Z end (µm)", value=200.0)

        st.markdown("---")
        angles = st.number_input("Angular samples", value=2048)
        r_min_frac = st.number_input("Inner radius fraction", value=0.2)
        r_max_frac = st.number_input("Outer radius fraction", value=0.9)
        num_radii = st.number_input("Number of radii", value=20)

        run_btn = st.button("▶ Run autofocus + MTF")

    col1, col2 = st.columns([1, 1])
    col3 = st.container()

    if run_btn:
        out_path = Path(out_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        with st.spinner("Running autofocus and MTF analysis..."):
            summary = run_focus_and_mtf(
                stack_pattern=stack_pattern,
                z_start_um=float(z_start),
                z_end_um=float(z_end),
                out_dir=out_path,
                angles=int(angles),
                r_min_frac=float(r_min_frac),
                r_max_frac=float(r_max_frac),
                num_radii=int(num_radii),
                make_plots=True,
            )

        st.success("Done!")

        # --------------------------------------------------
        # Focus stack thumbnails (defocus sweep)
        # --------------------------------------------------
        st.subheader("Focus stack (defocus sweep)")

        frame_paths = sorted(glob.glob(stack_pattern))
        if not frame_paths:
            st.write("⚠ No frames found for pattern:", stack_pattern)
        else:
            max_per_row = 15
            n = len(frame_paths)
            for row_start in range(0, n, max_per_row):
                row_paths = frame_paths[row_start : row_start + max_per_row]
                cols = st.columns(len(row_paths))
                for col, fp in zip(cols, row_paths):
                    with col:
                        img = cv2.imread(fp, cv2.IMREAD_GRAYSCALE)
                        if img is not None:
                            st.image(img, use_container_width=True)
                            st.caption(Path(fp).name)
                        else:
                            st.write("Failed to load")
                            st.caption(Path(fp).name)

        # --------------------------------------------------
        # Autofocus curve
        # --------------------------------------------------
        with col1:
            st.subheader("Autofocus curve")
            af_plot_path = summary.get("autofocus_plot")
            if af_plot_path and Path(af_plot_path).is_file():
                af_img = plt.imread(af_plot_path)
                st.image(af_img, use_container_width=True)
            else:
                st.write("No autofocus plot found.")

        # --------------------------------------------------
        # Best-focus image
        # --------------------------------------------------
        with col2:
            img_path = summary.get("best_focus_image")
            if img_path and Path(img_path).is_file():
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                show_image("Best-focus frame", img)
            else:
                show_image("Best-focus frame", None)

        # --------------------------------------------------
        # MTF curve
        # --------------------------------------------------
        with col3:
            st.subheader("Siemens MTF (multi-radius)")
            mtf_plot_path = summary.get("mtf_plot")
            if mtf_plot_path and Path(mtf_plot_path).is_file():
                mtf_img = plt.imread(mtf_plot_path)
                st.image(mtf_img, use_container_width=True)
            else:
                st.write("No MTF plot found.")

        # --------------------------------------------------
        # Summary
        # --------------------------------------------------
        st.markdown("### Run Summary")
        st.json(summary)


if __name__ == "__main__":
    main()
