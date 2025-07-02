import os
import sys
import glob
import rasterio
import logging
import pystac
import requests
import shutil
import tempfile
import numpy as np
import xarray as xr

from osgeo import gdal
from pathlib import Path
from arosics import COREG_LOCAL
from scipy.signal import medfilt2d

from config import WYVERN_STAC_CATALOG_URL, TARGET_CRS, WYVERN_OUTPUT_RESOLUTION

# NOTE: Sys path modification is necessary to import ACOLITE. It is not an installable
# package so we must fall back to blecherous hackery to get it working.
# DOUBLE NOTE: We assume ACOLITE is present in the parent directory above this project.
sys.path.append("../../acolite")
import acolite as ac


def download_wyvern_image(image_id: str, download_path: str):
    """Downloads Wyvern image by ID.

    Args:
        image_id (str): Wyvern image ID.
        download_path (str): Path to download the image and metadata to.
    """
    item_url = f"{WYVERN_STAC_CATALOG_URL}{image_id}/{image_id}.json"
    pystac_item = pystac.Item.from_file(item_url)

    # Download image from STAC item
    logging.info(f"Downloading Wyvern image: {image_id} to {download_path}")
    with requests.get(
        pystac_item.assets["Cloud optimized GeoTiff"].href, stream=True
    ) as r:
        with open(f"{download_path}{image_id}.tiff", "wb") as f:
            shutil.copyfileobj(r.raw, f)

    logging.info("Downloading Wyvern metadata")
    with requests.get(pystac_item.assets["stac_metadata"].href, stream=True) as r:
        with open(f"{download_path}{image_id}.json", "wb") as f:
            shutil.copyfileobj(r.raw, f)

    logging.info("Wyvern image download complete.")


def reproject_wyvern_image(
    image_path: str, output_crs: str, bbox: list[float], output_path: str
):
    """Reprojects Wyvern image to specified CRS.

    Args:
        image_path (str): Path to the downloaded Wyvern image.
        output_crs (str): Desired output CRS in EPSG format (e.g., "EPSG:4326").
        bbox: list[float]: Bounding box for the output image in EPSG:4326 decimal lat/lon degrees
        output_path (str): Path to save the reprojected image.
    """
    logging.info(
        f"Reprojecting Wyvern image {image_path} to {output_crs}"
        f" w/ {WYVERN_OUTPUT_RESOLUTION} resolution"
    )
    warp_options = gdal.WarpOptions(
        outputBounds=bbox,
        outputBoundsSRS="EPSG:4326",  # Assumed output bounds are in WGS84
        dstSRS=output_crs,
        xRes=WYVERN_OUTPUT_RESOLUTION,
        yRes=WYVERN_OUTPUT_RESOLUTION,
        targetAlignedPixels=True,  # Required so pixels align properly between images
    )
    gdal.Warp(
        destNameOrDestDS=output_path, srcDSOrSrcDSTab=image_path, options=warp_options
    )
    logging.info(f"Reprojected Wyvern image saved to {output_path}")


def denoise_wyvern_image(image_path: str, output_path: str):
    """Applies a denoising filter to the Wyvern image.

    Args:
        image_path (str): Path to the Wyvern image.
        output_path (str): Path to save the denoised image.
    """
    logging.info(f"Denoising Wyvern image {image_path}")
    src = rasterio.open(image_path)
    dst = rasterio.open(output_path, "w", **src.profile)

    for band in range(1, src.count + 1):
        logging.info(f"Processing band {band}")
        band_data = src.read(band)
        dst.write_band(band, medfilt2d(band_data, kernel_size=3))
        dst.set_band_description(band, src.descriptions[band - 1])

    logging.info(f"Denoised Wyvern image saved to {output_path}")


def process_wyvern_image(
    image_id: str,
    download_path: str,
    output_path: str,
    bbox: list[float],
    output_crs: str,
    denoise: bool,
    force_download: bool = True,
) -> str:
    """Processes a Wyvern image by downloading, reprojecting, and optionally denoising it.

    Args:
        image_id (str): Wyvern image ID.
        download_path (str): Path to download the image and metadata to.
        bbox (list[float]): Bounding box for the area of interest in EPSG:4326 decimal lat/lon degrees.
        output_crs (str): Desired output CRS in EPSG format (e.g., "EPSG:4326").
        denoise (bool): Whether to apply a denoising filter to the image.

    Returns:
        str: Path to the processed Wyvern image.
    """
    # Download Wyvern image
    logging.info(f"Downloading Wyvern image: {image_id}")
    raw_path = download_path + "raws/"
    os.makedirs(raw_path, exist_ok=True)

    downloaded_file_path = f"{download_path}raws/{image_id}.tiff"

    if force_download or not os.path.isfile(downloaded_file_path):
        logging.info(
            "Downloaded raw file doesn't exist, or `FORCE_DOWNLOAD` is True. Downloading image!"
        )
        download_wyvern_image(image_id, raw_path)
    else:
        logging.info("Skipping download, file already exists.")

    # Reproject Wyvern image
    logging.info(f"Reprojecting Wyvern image: {image_id} to {output_crs}")
    processed_path = f"{download_path}{image_id}_reprojected.tiff"
    reproject_wyvern_image(downloaded_file_path, output_crs, bbox, processed_path)

    # Optionally denoise the image
    if denoise:
        logging.info(f"Denoising Wyvern image: {image_id}")
        denoised_image_path = f"{download_path}{image_id}_denoised.tiff"
        denoise_wyvern_image(processed_path, denoised_image_path)

        # Overwrite processed path and remove reprojected image
        logging.info("Removing reprojected image...")
        os.remove(processed_path)
        processed_path = denoised_image_path

    # Finally, remove the original downloaded image and rename the processed image
    logging.info(f"Cleaning up files for Wyvern image: {image_id}")
    os.rename(processed_path, output_path)
    output_json_path = output_path.split(".")[0] + ".json"
    shutil.copy(f"{download_path}raws/{image_id}.json", output_json_path)
    logging.info(f"Wyvern image {image_id} processed!")
    logging.info(f"Return file path: {output_path}")
    return output_path


def align_wyvern_image(
    reference_path: str,
    target_path: str,
    output_path: str,
    generate_fig: bool = True,
):
    """Aligns a Wyvern image to the specified reference image using AROSICS.

    Args:
        reference_path (str): Path to reference image (e.g., Sentinel-2).
        target_path (str): Path to Wyvern image to be aligned.
        output_path (str): Output path for the aligned Wyvern image.
        generate_fig (bool, Optional): If True, generates a figure showing the
            co-registration points.
    """
    kwargs = {
        "grid_res": 50,
        "window_size": (256, 256),
        "path_out": output_path,
        "q": False,
        "fmt_out": "GTIFF",
        "r_b4match": 5,
        "s_b4match": 15,
    }
    logging.info(
        f"Aligning Wyvern image {target_path} to reference image {reference_path}"
    )
    CRL = COREG_LOCAL(reference_path, target_path, **kwargs)
    CRL.correct_shifts()

    if generate_fig:
        logging.info("Generating co-registration points figure...")
        fig, axs = CRL.view_CoRegPoints(
            figsize=(15, 15), backgroundIm="ref", return_map=True
        )
        figure_path = Path(output_path).parent / "wyvern_co_registration_points.png"
        fig.savefig(figure_path, dpi=150, bbox_inches="tight")
        logging.info("Co-registration points figure saved.")


def atmospherically_correct_wyvern_image(
    image_path: str,
    acolite_settings: dict,
):
    """Applies atmospheric correction to the Wyvern image.

    Args:
        image_path (str): Path to the Wyvern image.
    """
    from netCDF4 import Dataset
    import h5py

    temp_working_dir = (
        Path(image_path).parent / "temp_dir"
    )  # tempfile.TemporaryDirectory()
    os.makedirs(temp_working_dir, exist_ok=True)
    output_path = temp_working_dir  # .name
    logging.info(f"Creating temporary working directory at {output_path}")

    # Ensure absolute paths are used
    image_path = os.path.abspath(image_path)
    logging.info(f"Atmospherically correcting Wyvern image: {image_path}")

    logging.info(f"Applying atmospheric correction to Wyvern image: {image_path}")
    settings = {
        "inputfile": image_path,
        "output": output_path,
        # "l1r_delete_netcdf": True,
        **acolite_settings,  # Unpack additional settings
    }
    ac.acolite.acolite_run(settings)

    logging.info("Extracting ACOLITE output...")
    matching_files = glob.glob(f"{output_path}/*_L2R.nc")
    if len(matching_files) == 0:
        raise FileNotFoundError(
            "No ACOLITE output files found. Check if ACOLITE ran successfully."
        )

    # Read in required metadata prior to GeoTIFF creation
    logging.info("Reading metadata from input GeoTIFF")
    input_file = rasterio.open(image_path)
    output_meta = input_file.meta.copy()
    output_band_descs = input_file.descriptions
    input_file.close()

    # Load HDF5 and gather rhos variables
    h5_ds = xr.open_dataset(matching_files[0])
    rhos_vars = [x for x in list(h5_ds.data_vars) if "rhos" in x]

    # Now we're ready to create the GeoTIFF
    logging.info("Creating GeoTIFF from ACOLITE output")
    temp_geotiff_path = f"{output_path}/acolite_surf.tiff"
    with rasterio.open(temp_geotiff_path, "w", **output_meta) as f:
        for i, (band, band_name) in enumerate(zip(rhos_vars, output_band_descs), 1):
            arr = h5_ds[band].values
            arr = np.where(arr > 1, np.nan, arr)
            f.write(arr, i)
            f.set_band_description(i, band_name)

    logging.info("Removing input file and replacing with ACOLITE GeoTIFF")
    os.remove(image_path)
    shutil.move(temp_geotiff_path, image_path)
    logging.info(f"Atmospherically corrected Wyvern image saved to {image_path}")

    logging.info("Cleaning up temporary files...")
    # temp_working_dir.close()
    shutil.rmtree(temp_working_dir, ignore_errors=True)
    logging.info("Atmospheric correction complete.")
