# Camera MTF Bench — Technical Documentation

Camera MTF Bench provides a modular workflow for quantitative imaging-system evaluation using Siemens-star MTF, slanted-edge SFR, and contrast-based autofocus metrics. The software integrates image acquisition, stage control, frequency-domain analysis, and reproducible measurement pipelines.

---

## Sections

### [0 — Introduction](sections/section0_intro.md)

### [1 — System Overview](sections/section1_system_overview.md)
- Imaging geometry, sensor sampling constraints, illumination requirements, reference targets, calibration frames.
- Mechanical stack overview (focus axis, rotational alignment surfaces, target placement constraints).
- Software dataflow from acquisition → preprocessing → metric computation.

### [2 — Siemens Star vs Slanted Edge](sections/section2_siemens_vs_edge.md)
- Siemens radial sweep: radius-to-frequency mapping, angular sectoring, center bias correction.
- Slanted-edge SFR: oversampled ESF extraction, derivative normalization, LSF windowing, MTF computation per ISO 12233.
- Comparative artifacts and stability limits of both methods.

### [3 — Autofocus Metrics](sections/section3_autofocus_metrics.md)
- Spatial-gradient metrics (Tenengrad, Sobel-energy, Laplacian-variance).
- Fourier-band energy metrics and high-frequency envelope ratios.
- Behavior of focus curves under defocus, astigmatism, noise, and pixel sampling.
- Curve-shape interpretation for alignment verification.

### [4 — Optical Bench & Hardware](sections/section4_optical_bench.md)
- Target specifications (print resolution, substrate reflectance, modulation limits).
- Illumination uniformity, flicker, spectral stability, and back-illumination geometry.
- Stage motion model: commanded displacement → optical path length change.
- Mounting tolerances: tilt, yaw, roll, sensor orthogonality.
- Camera configuration: exposure linearity, gain settings, shutter timing, ADC clipping behavior.


### [5 — Software Architecture](sections/section5_software_modules.md)
- Module structure: acquisition, hardware abstraction, metric computations, reporting.
- Pixel-grid normalization, ROI stabilization, batch pipelines.
- Deterministic processing chain with reproducible configuration files.

### [6 — Manual Focus Workflow](sections/section6_manual_focus.md)
- Step size selection from lens MTF slope and DOF envelope.
- Exposure constraints to prevent saturation during focusing.
- Peak localization strategies and curve smoothing.
- Focus-curve interpretation for diagnosing tilt, decenter, or asymmetric focus lobes.

### [7 — CLI Reference](sections/section7_cli.md)
- Acquisition commands, sweep commands, batch-processing scripts, report generation.

### [8 — Advanced Optical Topics](sections/section8_advanced_optics.md)
- Pixel-integration MTF (2D sinc), sampling theory limits, PSF-to-MTF transforms.
- Defocus transfer function, aberration sensitivity, and field curvature mapping.
- Noise propagation through ESF/LSF and stability limits for MTF50 estimation.

### [9 — Roadmap & Future Work](sections/section9_roadmap.md)
- High-speed acquisition modes, GPU paths, field-MTF mapping, extended calibration.

### [10 — Appendix](sections/section10_appendix.md)
- Mathematical derivations, frequency-domain identities, geometric relations.