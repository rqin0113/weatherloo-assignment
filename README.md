# weatherloo — Answers, run instructions, and notes

This file answers the take-home questions from `README.md`, shows how to run the visualization, and documents key prompts and issues encountered while building the project.

---
## Task 1: Chosen variable

- **Variable:** 10-meter wind speed
- **ELI5 explanation:** This measures how fast the air is moving near the ground (about the height of a flagpole). Imagine sticking a small wind vane 10 meters high — the number is how fast the wind is blowing there. It is a direct indicator of storms, breezes, and strong wind events at the surface.
- **Level:** single-level (surface)
- **Common abbreviations / names:** `10m_wind_speed`, sometimes shortened to `wind_speed_10m` or simply `wind_speed`. ERA5 also provides components: `10m_u_component_of_wind` and `10m_v_component_of_wind` (east-west and north-south components).

## Task 2: Visualization approach

- I implemented a simple, clean global animation using `xarray` + `matplotlib` + `cartopy` in `visualize_wind.py`.
- Design decisions:
  - Use the precomputed `10m_wind_speed` if available to avoid computing magnitude on the fly; fall back to components if needed.
  - Pick a 120-hour (5-day) window and animate each time slice as a colormapped global map.
  - Use `PlateCarree` for a straightforward global projection and `viridis` colormap with a sensible vmin/vmax for wind speed.

Files involved:

- `visualize_wind.py` — the main script that loads ERA5 from the public Zarr, selects a 120-hour window, computes wind speed (or uses precomputed), and animates.
- `requirements.txt` — python dependencies used to run the project.

## How to run

1. (Optional) Create and activate a virtual environment, or use conda:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If pip-installing `cartopy` fails on macOS, install via conda:

```bash
conda install -c conda-forge cartopy
```

If you see an SSL certificate verification failure while opening the ERA5 Zarr dataset, install `certifi` and make sure Python uses its certificate bundle:

```bash
pip install certifi
export SSL_CERT_FILE=$(python -m certifi)
python visualize_wind.py
```

2. Run the visualization script:

```bash
python visualize_wind.py
```

Expected behavior:

- The script will open the public ERA5 Zarr store (no local download required), select a 120-hour window in late 2021 (the dataset ends at 2021-12-31 18:00 in this Zarr), compute or use `10m_wind_speed`, and show an animated map.
- If `ffmpeg` is available, the script will attempt to save an MP4 (`wind_speed_120h.mp4`). If `ffmpeg` is not available, the script falls back to saving a GIF (`wind_speed_120h.gif`). If neither writer works, the animation will display with `plt.show()`.

## Task 3: Dataset understanding

1. **Time step of the dataset:** 6-hourly (every 6 hours). The dataset label `6h` indicates four records per day.

2. **Timezone / standard:** Times are in UTC (ISO 8601 timestamps). ERA5 uses UTC timestamps.

3. **What `1440x721` refers to:** horizontal grid resolution: 1440 longitude points (global, typically 0.25° spacing) and 721 latitude points (from -90° to 90°). This corresponds to a regular lat-lon grid covering the globe.

4. **What is Zarr:** Zarr is an on-disk (or cloud) chunked array storage format that stores multi-dimensional arrays in compressed chunks. It allows lazy, partial reads (load only needed chunks) which makes working with very large climate datasets in the cloud efficient. `xarray` can open Zarr stores as labeled `Dataset`s.
---

## Errors encountered & fixes

- **Missing Python backends:** `ModuleNotFoundError` for packages such as `zarr`, `gcsfs`, and `cartopy` occurred when opening the Zarr store or plotting.
  - Fix: add required packages to `requirements.txt` and install them (or use `conda install -c conda-forge cartopy` for `cartopy`).

- **SSL / certificate verification:** Some environments may fail to access GCS due to SSL certificate issues.
  - Fix: ensure `certifi` is present or use a conda environment with working system certificates; reinstalling dependencies typically resolved this in my environment.

- **KeyError: 'u10' (variable name mismatch):** The Zarr store uses descriptive ERA5 variable names such as `10m_u_component_of_wind`, `10m_v_component_of_wind`, and `10m_wind_speed` instead of short names like `u10`/`v10`.
  - Fix: inspect `list(ds.data_vars)` in Python to confirm names, then use `10m_wind_speed` when available or compute magnitude from the component variables.

- **Empty time selection (IndexError):** Selecting a date range outside the dataset's available time range returned an empty slice.
  - Fix: inspect `ds.time` (or `ds.sizes['time']`) to find the valid range; adjust the selected window to fall within the dataset (this Zarr ends at `2021-12-31T18:00`).

- **Animation saving errors (ffmpeg unavailable):** Attempting to save MP4 with ffmpeg failed when ffmpeg wasn't installed.
  - Fix: fall back to saving an animated GIF with `PillowWriter`, or install `ffmpeg` (e.g. `brew install ffmpeg`).


## AI usage

Tools used: Claude

What they were used for: Debugging and improving the Python visualization pipeline (`visualize_wind.py`) and writing concise documentation.

Summary of support:
- Resolved an SSL certificate verification issue when accessing the ERA5 Zarr dataset.
- Diagnosed a `KeyError: 'u10'` caused by mismatched variable names in the Zarr store and identified correct ERA5 variable names (`10m_u_component_of_wind`, `10m_v_component_of_wind`, `10m_wind_speed`).
- Suggested safer inspection patterns for `xarray.Dataset` (use `list(ds.data_vars)` in Python) and avoidance of hard-coded short names.
- Advised on fallback strategies (use precomputed `10m_wind_speed` vs compute magnitude from components) and animation writer fallbacks (GIF via PillowWriter when `ffmpeg` is not available).

Sample prompts used during the process:

- "Write a Python script using xarray to open ERA5 Zarr at gcs://gcp-public-data-arco-era5/ar/1959-2022-6h-1440x721.zarr and animate 10m wind speed over 5 days using matplotlib and cartopy. Include a fallback to GIF if ffmpeg is unavailable."
- "I got KeyError: 'u10' when running ds[['u10','v10']]. I printed ds.data_vars and see names like '10m_u_component_of_wind'. How should I robustly select the wind variable and compute wind speed? Provide code samples."
- "ModuleNotFoundError: No module named 'cartopy' — suggest clear user-facing error message and install guidance for both pip and conda users."