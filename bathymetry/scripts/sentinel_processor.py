import os
import logging
import tempfile
import shutil
import pystac
import rasterio
import planetary_computer

from glob import glob
from osgeo import gdal
from osgeo_utils import gdal_merge
from urllib.request import urlretrieve
from tqdm import tqdm
from pathlib import Path

from config import SENTINEL_OUTPUT_RESOLUTION, STAC_CATALOG_URL, ASSETS_TO_DOWNLOAD



def download_sentinel_tile(s2_id: str, download_path: str):
    """Downloads Sentinel-2 individual band assets. Only downloads assets
    defined in `ASSETS_TO_DOWNLOAD`

    Args:
        s2_id (str): ID for Sentinel-2 image in STAC catalog
        download_path (str): Path to download files to (i.e. a directory)
    """
    logging.info(f"Loading STAC item for: {s2_id}")
    s2_item_url = f"{STAC_CATALOG_URL}{s2_id}"
    item = pystac.Item.from_file(s2_item_url)
    signed_item = planetary_computer.sign(item)

    for asset in tqdm(ASSETS_TO_DOWNLOAD, desc="Downloading Sentinel-2 assets"):
        urlretrieve(signed_item.assets[asset].href, f"{download_path}/{asset}.tif")
    logging.info("Sentinel-2 asset download complete.")

def stack_sentinel_tile(
    images_to_stack: list[str],
    image_band_names: list[str],
    output_path: str,
    output_crs: str,
    output_bounds: list[float],
):
    # First, iterate over downloaded tiles and warp to common CRS. We have to
    # warp first because `gdal_merge` does not support specifying an output CRS.
    warp_options = gdal.WarpOptions(
        outputBounds=output_bounds,
        dstSRS=output_crs,
        xRes=SENTINEL_OUTPUT_RESOLUTION,
        yRes=SENTINEL_OUTPUT_RESOLUTION,
        targetAlignedPixels=True,  # Required so pixels align properly between images
    )
    warped_img_paths = []
    for img_path in tqdm(images_to_stack, desc="Warping Sentinel-2 assets"):
        img_path = Path(img_path)
        warp_output = img_path.parent / f"{Path(img_path).name}_warped.tif"
        warped_img_paths.append(warp_output)
        gdal.Warp(
            destNameOrDestDS=warp_output,
            srcDSOrSrcDSTab=img_path,
            options=warp_options
        )
    # Now that we've aligned our S2 bands to the same resolution and CRS, we
    # can stack 'em
    merge_params = (
        ["", "-o",  output_path] + 
        warped_img_paths + ["-separate", "-co", "COMPRESS=LZW"]
    )
    gdal_merge.main(merge_params)

    print("Adding band names!")
    with rasterio.open(output_path, "r+") as f:
        for i, band_name in enumerate(ASSETS_TO_DOWNLOAD, start=1):
            f.set_band_description(i, band_name)
    print("Band names added!")
    
    
    

def process_sentinel_tile(s2_id: str, output_path: str, epsg_code: str):
    """Downloads and processes Sentinel-2 tile for bathymetry work

    Args:
        s2_id (str): Sentinel-2 image STAC ID
        output_path (str): Full path for output geotiff
    """
    # Create temporary working directory for processing
    tempdir = tempfile.TemporaryDirectory()
    sentinel_working_folder = f"{tempdir.name}/{s2_id}"
    os.makedirs(sentinel_working_folder, exist_ok=True)

    # Download Sentinel-2 assets
    download_sentinel_tile(s2_id=s2_id, download_path=sentinel_working_folder)


