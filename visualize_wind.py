import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

try:
    import cartopy.crs as ccrs
except ImportError as exc:
    raise ImportError(
        "cartopy is required for this script. Install it with `pip install cartopy` "
        "or `conda install -c conda-forge cartopy` and then rerun the script."
    ) from exc

# Public ERA5 Zarr URL for 10-meter winds
ZARR_URL = (
    "gcs://gcp-public-data-arco-era5/ar/1959-2022-6h-1440x721.zarr"
)

WIND_SPEED_VAR = "10m_wind_speed"
U10_VAR = "10m_u_component_of_wind"
V10_VAR = "10m_v_component_of_wind"


def load_era5_wind(zarr_url: str) -> xr.Dataset:
    """Load the ERA5 Zarr dataset from Google Cloud Storage."""
    ds = xr.open_zarr(
        zarr_url,
        consolidated=True,
        storage_options={"token": "anon"},
    )

    # Debug: print the variables present in the dataset.
    print("Available variables:", list(ds.data_vars))

    # This specific dataset uses descriptive spaCy-like ERA5 names.
    if WIND_SPEED_VAR in ds.data_vars:
        ds = ds[[WIND_SPEED_VAR]]
    elif U10_VAR in ds.data_vars and V10_VAR in ds.data_vars:
        ds = ds[[U10_VAR, V10_VAR]]
    else:
        raise KeyError(
            f"Expected {WIND_SPEED_VAR} or both {U10_VAR}/{V10_VAR}, but found: "
            f"{list(ds.data_vars)}"
        )

    # Keep only the relevant 10m wind data to reduce memory use.
    return ds


def select_time_window(ds: xr.Dataset, start: str, end: str) -> xr.Dataset:
    """Select a 120-hour window from the dataset by date range."""
    window = ds.sel(time=slice(start, end))
    return window


def compute_wind_speed(ds: xr.Dataset) -> xr.DataArray:
    """Compute 10-meter wind speed from u10 and v10 wind components."""
    if WIND_SPEED_VAR in ds.data_vars:
        return ds[WIND_SPEED_VAR].rename("wind_speed_10m")

    u10 = ds[U10_VAR]
    v10 = ds[V10_VAR]
    wind_speed = np.sqrt(u10**2 + v10**2)
    wind_speed = wind_speed.rename("wind_speed_10m")
    return wind_speed


def plot_wind_frame(ax, data, vmin=0, vmax=25):
    """Draw one wind speed map frame on the provided axes."""
    mesh = ax.pcolormesh(
        data.longitude,
        data.latitude,
        data,
        transform=ccrs.PlateCarree(),
        cmap="viridis",
        shading="auto",
        vmin=vmin,
        vmax=vmax,
    )
    return mesh


def create_animation(wind_speed: xr.DataArray, output_path: str = None):
    """Create and optionally save an animation of 10m wind speed."""
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.coastlines(linewidth=0.6)
    ax.set_global()
    ax.set_title("10m Wind Speed (m/s)")

    # Use the first time slice as the initial frame.
    initial = wind_speed.isel(time=0)
    mesh = plot_wind_frame(ax, initial)
    cbar = plt.colorbar(mesh, ax=ax, orientation="horizontal", pad=0.05)
    cbar.set_label("Wind speed (m/s)")

    time_text = ax.text(
        0.02,
        0.95,
        str(initial.time.values),
        transform=ax.transAxes,
        fontsize=12,
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", pad=4),
    )

    def update_frame(frame_index: int):
        data = wind_speed.isel(time=frame_index)
        mesh.set_array(data.values.ravel())
        time_text.set_text(str(data.time.values))
        return mesh, time_text

    anim = FuncAnimation(
        fig,
        update_frame,
        frames=wind_speed.sizes["time"],
        interval=500,
        blit=False,
    )

    if output_path:
        try:
            anim.save(output_path, fps=2, dpi=150, writer="ffmpeg")
            print(f"Saved animation to {output_path}")
        except Exception as exc:
            # Fallback: try saving as GIF with Pillow writer if ffmpeg/mp4 fails
            print("ffmpeg save failed, attempting GIF fallback...")
            try:
                from matplotlib.animation import PillowWriter

                gif_path = output_path.rsplit('.', 1)[0] + '.gif'
                anim.save(gif_path, fps=2, dpi=150, writer=PillowWriter(fps=2))
                print(f"Saved animation to {gif_path}")
            except Exception as exc2:
                print("Unable to save animation automatically.")
                print("Install ffmpeg or ensure the output extension matches an available writer.")
                print(exc)
                print(exc2)

    plt.show()
    return anim


if __name__ == "__main__":
    print("Loading ERA5 10-meter wind components...")
    ds = load_era5_wind(ZARR_URL)

    # Choose a 120-hour window that exists in this Zarr (ends 2021-12-31 18:00).
    # Use a 5-day window in late 2021 to ensure the range is present.
    start_date = "2021-12-27"
    end_date = "2021-12-31T18:00"
    ds_window = select_time_window(ds, start_date, end_date)

    print(
        f"Selected time window: {ds_window.time.values[0]} to {ds_window.time.values[-1]}"
    )
    print("Computing wind speed magnitude...")
    wind_speed = compute_wind_speed(ds_window)

    print("Creating animation...")
    create_animation(wind_speed, output_path="wind_speed_120h.mp4")
