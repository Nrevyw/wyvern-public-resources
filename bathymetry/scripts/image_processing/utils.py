import logging
import zipfile
from urllib.request import urlretrieve

from config import BATHYMETRY_DATASET_URL


def download_soest_dataset(output_path: str):
    """Downloads the SOEST bathymetry dataset and unzips it to the specified
    output path.

    Args:
        output_path (str): Path to download files to (i.e. a directory)
    """
    logging.info("Downloading SOEST bathymetry dataset...")
    urlretrieve(BATHYMETRY_DATASET_URL, f"{output_path}/bathymetry.zip")
    logging.info("Unzipping SOEST bathymetry dataset...")
    with zipfile.ZipFile(f"{output_path}/bathymetry.zip", "r") as zip_ref:
        zip_ref.extractall(output_path)
    logging.info("SOEST bathymetry dataset download complete.")
