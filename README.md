<p align="center">
  <img src="assets/img/banner.png" width="85%">
</p>

<h1 align="center">Camera MTF Bench</h1>
<p align="center"><em>Siemens-Star MTF · Manual Focus Tuning · Autofocus & Imaging-Quality Toolkit</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg">
  <img src="https://img.shields.io/badge/license-MIT-green.svg">
  <img src="https://img.shields.io/badge/docs-GitHub%20Pages-lightgrey.svg">
</p>

---

## 🌟 Overview

Camera MTF Bench is an optics-focused toolkit for evaluating imaging sharpness, focus behavior, and modulation transfer.It supports:

- **Manual focus workflows** (via Streamlit)
- **Simulated autofocus sweeps**
- **Siemens-star multi-radius MTF**
- **Gradient-based focus metrics**
- **CSV / PNG / JSON artifact export**
- **Camera + stage abstraction layers**
- **Real or simulated data**

Camera MTF Bench was originally designed for manual focusing of optical assemblies during development and prototyping of imaging modules. The Siemens-star structure, combined with gradient-derived metrics, allows real-time monitoring of focus quality, enabling fine mechanical adjustments while observing the optical response.

---

## ⚙️ Quick Start

### Install
```bash
git clone https://github.com/yourname/CAMERA-MTF-BENCH.git
cd CAMERA-MTF-BENCH
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### Demo autofocus sweep (simulated data)
```bash
python -m bench demo-af --stack "data/focus_stack/*.png" --plot
```

### Compute Siemens MTF
```bash
python -m bench mtf-siemens --image data/frame.png --out outputs/mtf
```

### Full autofocus + MTF workflow
```bash
python -m bench focus-and-mtf --stack "data/focus_stack/*.png" --out outputs/run01
```

---

## 📂 Repository Structure

```text
CAMERA-MTF-BENCH/
│
├── bench/                     # Main Python package (instrumentation, metrics, workflows)
│   ├── __init__.py
│   ├── cli.py
│   ├── autofocus.py
│   ├── workflows.py
│   ├── workflows_hardware.py
│   ├── metrics/
│   ├── instruments/
│   ├── targets/
│   └── gui/
│
├── docs/                      # GitHub Pages documentation
│   ├── index.md
│   └── sections/
│       ├── index.md
│       ├── ...
│
├── assets/
│   └── img/
│       └── banner.png
│
├── data/
│   ├── charts/
│   └── focus_stack/
│
├── outputs/                   # Results from runs (gitignored)
│
├── requirements.txt
├── pyproject.toml
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

---

## 📘 Technical Documentation

Camera MTF Bench provides a modular workflow for quantitative imaging-system evaluation using Siemens-star MTF, slanted-edge SFR, and contrast-based autofocus metrics. The software integrates image acquisition, stage control, frequency-domain analysis, and reproducible measurements. All detailed technical sections live under `/docs`. 

## Sections

### [0 — Introduction](/docs/sections/section0_intro.md)

### [1 — System Overview](/docs/sections/section1_system_overview.md)
- Imaging geometry, sensor sampling constraints, illumination requirements, reference targets, calibration frames.
- Mechanical stack overview (focus axis, rotational alignment surfaces, target placement constraints).
- Software dataflow from acquisition → preprocessing → metric computation.

### [2 — Siemens Star vs Slanted Edge](/docs/sections/section2_siemens_vs_edge.md)
- Siemens radial sweep: radius-to-frequency mapping, angular sectoring, center bias correction.
- Slanted-edge SFR: oversampled ESF extraction, derivative normalization, LSF windowing, MTF computation per ISO 12233.
- Comparative artifacts and stability limits of both methods.

### [3 — Autofocus Metrics](/docs/sections/section3_autofocus_metrics.md)
- Spatial-gradient metrics (Tenengrad, Sobel-energy, Laplacian-variance).
- Fourier-band energy metrics and high-frequency envelope ratios.
- Behavior of focus curves under defocus, astigmatism, noise, and pixel sampling.
- Curve-shape interpretation for alignment verification.

### [4 — Optical Bench & Hardware](/docs/sections/section4_optical_bench.md)
- Target specifications (print resolution, substrate reflectance, modulation limits).
- Illumination uniformity, flicker, spectral stability, and back-illumination geometry.
- Stage motion model: commanded displacement → optical path length change.
- Mounting tolerances: tilt, yaw, roll, sensor orthogonality.
- Camera configuration: exposure linearity, gain settings, shutter timing, ADC clipping behavior.


### [5 — Software Architecture](/docs/sections/section5_software_modules.md)
- Module structure: acquisition, hardware abstraction, metric computations, reporting.
- Pixel-grid normalization, ROI stabilization, batch pipelines.
- Deterministic processing chain with reproducible configuration files.

### [6 — Manual Focus Workflow](/docs/sections/section6_manual_focus.md)
- Step size selection from lens MTF slope and DOF envelope.
- Exposure constraints to prevent saturation during focusing.
- Peak localization strategies and curve smoothing.
- Focus-curve interpretation for diagnosing tilt, decenter, or asymmetric focus lobes.

### [7 — CLI Reference](/docs/sections/section7_cli.md)
- Acquisition commands, sweep commands, batch-processing scripts, report generation.

### [8 — Advanced Optical Topics](/docs/sections/section8_advanced_optics.md)
- Pixel-integration MTF (2D sinc), sampling theory limits, PSF-to-MTF transforms.
- Defocus transfer function, aberration sensitivity, and field curvature mapping.
- Noise propagation through ESF/LSF and stability limits for MTF50 estimation.

### [9 — Roadmap & Future Work](/docs/sections/section9_roadmap.md)
- High-speed acquisition modes, GPU paths, field-MTF mapping, extended calibration.

### [10 — Appendix](/docs/sections/section10_appendix.md)
- Mathematical derivations, frequency-domain identities, geometric relations.

---

## 📊 Example Outputs

Typical output artifacts (simulated sweep):

```
outputs/run01/
   autofocus_curve.csv
   autofocus_curve.png
   mtf_siemens_multi_radius.csv
   mtf_siemens_multi_radius.png
   summary.json
   best_focus_frame.png
```

---

## 🖥️ Hardware Backends

### Cameras
- OpenCV UVC camera  
- Dummy camera (image stack)

### Stages
- Dummy stage for initial development  
- VISA-style motion controller (skeleton)  
- Kinesis-style stage (skeleton)  

---

## 🎛️ Manual Focus (Streamlit)

The GUI provides:

- live preview  
- Siemens focus metric  
- Tenengrad / Laplacian metrics  
- incremental focus curve  
- best-focus visualization  

Ideal for manual tuning of prototypes and lens assemblies.

---

## 📄 [License](LICENSE)

---

## 🤝 [Contributing](CONTRIBUTING.md)

---

## 👤 Ali Pouya
Optical Engineer — Optics &amp; Metrology System Design.\
GitHub: https://github.com/ali-pouya