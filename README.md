
<p align="center">
  <img src="assets/img/banner.png" width="85%">
</p>

<h1 align="center">Camera MTF Bench</h1>
<p align="center"><em>Siemens-Star MTF · Manual Focus Tuning · Autofocus & Imaging Quality Toolkit</em></p>

---

## Overview

Camera MTF Bench is an engineering-focused toolkit for analyzing imaging-system sharpness, focus behavior, and modulation transfer.
It supports both **manual-focus workflows** and **automated Z-sweeps**, and works with:

- real cameras (UVC / industrial),
- simulated focus stacks,
- manual benches,
- optional motorized stages.

The system provides:

- **Siemens-star multi-radius MTF**
- **Tenengrad / Laplacian focus metrics**
- **Autofocus sweeps**
- **Manual-focus tuning (Streamlit UI)**
- **Camera + stage abstraction layers**
- **Deterministic CLI workflows**
- **CSV/PNG/JSON artifact export**

---

## Quick Start

### Installation
```bash
git clone https://github.com/yourname/camera-mtf-bench.git
cd camera-mtf-bench
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run a demo autofocus sweep (simulated data)
```bash
python -m bench demo-af --stack "data/focus_stack/*.png" --plot
```

### Compute Siemens MTF on a single image
```bash
python -m bench mtf-siemens --image data/frame.png --out outputs/mtf
```

### Full autofocus + MTF workflow (simulated)
```bash
python -m bench focus-and-mtf --stack "data/focus_stack/*.png" --out outputs/run01
```

---

## Folder Structure

```
camera-mtf-bench/
  bench/
  docs/
      sections/
      index.md
  assets/
      img/
  data/
  outputs/
  README.md
```

---

## Full Technical Documentation

- docs/sections/section0_intro.md  
- docs/sections/section1_system_overview.md  
- docs/sections/section2_siemens_vs_edge.md  
- docs/sections/section3_autofocus_metrics.md  
- docs/sections/section4_optical_bench.md  
- docs/sections/section5_software_modules.md  
- docs/sections/section6_manual_focus.md  
- docs/sections/section7_cli.md  
- docs/sections/section8_advanced_optics.md  
- docs/sections/section9_roadmap.md  
- docs/sections/section10_appendix.md  

---

## Example Outputs

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

## Hardware Support

Camera backends:

- OpenCV UVC
- Dummy camera

Stage backends:

- Dummy
- VISA skeleton
- Kinesis skeleton

---

## Manual Focus Workflow

The Streamlit GUI provides real-time:

- live preview
- sharpness metrics
- focus-curve buildup
- best-focus visualization

---

## License

See **LICENSE**.

## Contributing

See **CONTRIBUTING.md**.

