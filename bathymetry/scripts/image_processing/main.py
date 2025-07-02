import os
import sys
import logging

from sentinel_processor import process_sentinel_tile
from wyvern_processor import (
    process_wyvern_image,
    align_wyvern_image,
    atmospherically_correct_wyvern_image,
)
from ground_truth_processor import process_soest_ground_truth
from config import (
    IMAGES,
    SENTINEL_OUTPUT_RESOLUTION,
    WYVERN_OUTPUT_RESOLUTION,
    FORCE_DOWNLOAD,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def main():
    root_path = "data/datasets/"
    bty_path = "data/hawaii_bty_grid/hawaii_bty_5m.tif"
    os.makedirs(root_path, exist_ok=True)
    for img_key, img in IMAGES.items():
        # Process Wyvern image
        logging.info(f"Processing Wyvern image: {img_key}")
        wyvern_image_path = process_wyvern_image(
            image_id=img["wyvern_id"],
            download_path=root_path,
            output_path=root_path + img["output_filename_wyvern"],
            bbox=img["output_bounds"],
            output_crs=img["output_crs"],
            denoise=True,
            force_download=FORCE_DOWNLOAD,
        )

        logging.info(f"Processing Wyvern ground truth: {img_key}")
        wyvern_ground_truth_path = process_soest_ground_truth(
            input_path=bty_path,
            output_path=root_path
            + f"{img['output_filename_wyvern'].split('.')[0]}_ground_truth.tif",
            output_crs=img["output_crs"],
            bbox=img["output_bounds"],
            resolution=img["output_gsd_wyvern"],
        )

        # Process Sentinel-2 image
        logging.info(f"Processing Sentinel-2 image: {img_key}")
        sentinel_image_path = process_sentinel_tile(
            s2_id=img["sentinel2_id"],
            output_path=root_path + img["output_filename_sentinel"],
            bbox=img["output_bounds"],
            force_download_and_reprocess=FORCE_DOWNLOAD,
            output_resolution=SENTINEL_OUTPUT_RESOLUTION,
        )

        logging.info(f"Processing Sentinel-2 ground truth: {img_key}")
        sentinel_ground_truth_path = process_soest_ground_truth(
            input_path=bty_path,
            output_path=root_path + f"{img['sentinel2_id']}_ground_truth.tif",
            output_crs=img["output_crs"],
            bbox=img["output_bounds"],
            resolution=img["output_gsd_sentinel"],
        )

        # Align Wyvern image to Sentinel-2 image
        logging.info(f"Aligning Wyvern image to Sentinel-2 image: {img_key}")
        align_wyvern_image(
            reference_path=sentinel_image_path,
            target_path=wyvern_image_path,
            output_path=wyvern_image_path,  # Overwrites
            generate_fig=True,
        )
        atmospherically_correct_wyvern_image(
            image_path=wyvern_image_path,
            acolite_settings=img["acolite_settings"],
        )

        logging.info(
            "Image processing completed! \n"
            f"Processed Wyvern image saved at: {wyvern_image_path} \n"
            f"Wyvern ground truth saved at: {wyvern_ground_truth_path} \n"
            f"Processed Sentinel-2 image saved at: {sentinel_image_path} \n"
            f"Sentinel-2 ground truth saved at: {sentinel_ground_truth_path}"
        )


if __name__ == "__main__":
    main()
