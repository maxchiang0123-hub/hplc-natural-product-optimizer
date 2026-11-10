# HPLC Natural Product Method Explorer

An offline, Agilent-compatible **CSV export** chromatogram analyzer and gradient screening assistant. It **does not connect to or control** an HPLC instrument.

## Install and launch

Python 3.10+ recommended.

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

A browser window opens. Demo chromatogram data are included automatically. For real Agilent OpenLab / ChemStation data, **export a chromatogram to CSV or TXT** with a time column in minutes and a detector-response column. Agilent export formats vary; if your export isn't tabular, first convert it to a two-column CSV.

## How to use

1. Enter your actual linear-gradient settings (%B, times, flow, column).
2. Upload a CSV with time and signal columns (or use the synthetic demo).
3. Select time and signal columns, adjust peak detection parameters.
4. Review the chromatogram, detected peaks, approximate FWHM-based resolution, and critical peak pair.
5. Download candidate gradient methods as CSV and test them under approved lab procedures.
6. Import subsequent experimental chromatograms to evaluate improvement.

## Important limitations

- Candidate gradients are **heuristics**, not quantitatively predicted retention times or an AI-trained optimizer.
- Approximate resolution is computed from adjacent peak retention-time difference and Gaussian-equivalent FWHM: Rs ≈ 2 ΔtR / [1.699 (FWHM1 + FWHM2)].
- The baseline is a simple low-quantile estimate; overlapping peaks, drift, shoulders, and irregular sampling can bias results.
- Peak area/purity and compound identity are **not** established by this prototype.
- Do not load the generated CSV into Agilent software as an instrument-ready method. It is an experiment planning table only.
- Verify pressure, solvent miscibility, detector compatibility, column limits, sample stability, injection load, and lab SOPs.
