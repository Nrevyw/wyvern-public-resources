import os
import logging

from osgeo import gdal


def process_soest_ground_truth(
    input_path: str,
    output_path: str,
    output_crs: str,
    bbox: list[float],
    resolution: float,
):
    """Processes the SOEST ground truth data by:
    - Reprojecting it to the specified CRS
    - Resampling it to the target GSD
    - Cropping it to the provided bbox

    Args:
        input_path (str): Path to the SOEST ground truth data.
        output_path (str): Path to save the processed ground truth data.
        output_crs (str): Desired output CRS in EPSG format (e.g., "EPSG:4326").
        bbox (list[float]): Bounding box for the area of interest.
        resolution: (float): Pixel resolution in output_crs units
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"SOEST ground truth data not found at {input_path}. "
            "Are you sure the dataset has been downloaded?"
        )

    logging.info(f"Processing SOEST ground truth data from {input_path}...")
    warp_options = gdal.WarpOptions(
        outputBounds=bbox,
        outputBoundsSRS="EPSG:4326",  # Assumed output bounds are in WGS84
        dstSRS=output_crs,
        xRes=resolution,
        yRes=resolution,
        targetAlignedPixels=True,  # Required so pixels align properly between images
        resampleAlg="cubic",
    )
    gdal.Warp(
        destNameOrDestDS=output_path, srcDSOrSrcDSTab=input_path, options=warp_options
    )
