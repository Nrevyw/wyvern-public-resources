# All image type configuration
TARGET_CRS = "EPSG:32604"  # UTM Zone 4N, Hawaii

# Sentinel-2 download configuration
ASSETS_TO_DOWNLOAD = [
    "B01",
    "B02",
    "B03",
    "B04",
    "B05",
    "B06",
    "B07",
    "B08",
    "B8A",
    "B09",
    "B11",
    "B12",
]
SENTINEL_STAC_CATALOG_URL = "https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-2-l2a/items/"
SENTINEL_OUTPUT_RESOLUTION = 10  # Metres

# Wyvern download configuration
WYVERN_STAC_CATALOG_URL = "https://wyvern-prod-public-open-data-program.s3.ca-central-1.amazonaws.com/industry/coastal/"
WYVERN_OUTPUT_RESOLUTION = 5  # Metres

# Ground truth dataset URL.
#  See https://www.soest.hawaii.edu/hmrg/multibeam/bathymetry.php for more info
BATHYMETRY_DATASET_URL = (
    "https://www.soest.hawaii.edu/hmrg/multibeam/all_Hawaii/hawaii_bty_5m.zip"
)

# If True, will force re-downloading of raw files even if they already exist.
# You have been warned, it will take a long time.
FORCE_DOWNLOAD = False

# This dictionary contains every matching Wyvern/Sentinel-2 image pair that requires
# downloading and processing.
IMAGES = {
    # "molokai_d1_01": {
    #     "wyvern_id": "wyvern_dragonette-001_20250101T201001_5dc97ba2",
    #     "sentinel2_id": "S2A_MSIL2A_20250114T210921_R057_T04QFJ_20250114T231353",
    #     "output_bounds": [-157.10671255019022396, 21.04393380062705887, -156.98104215818889884, 21.10384496549667688],
    #     "output_crs": TARGET_CRS,
    #     "output_gsd_wyvern": WYVERN_OUTPUT_RESOLUTION,
    #     "output_gsd_sentinel": SENTINEL_OUTPUT_RESOLUTION,
    #     "output_filename_wyvern": "wyvern_dragonette-001_20250101T201001_5dc97ba2.tiff",
    #     "output_filename_sentinel": "S2A_MSIL2A_20250114T210921_R057_T04QFJ_20250114T231353.tiff",
    #     "acolite_settings": {},
    # },
    "molokai_d2_01": {
        "wyvern_id": "wyvern_dragonette-002_20250225T004037_4788dc6b",
        "sentinel2_id": "S2B_MSIL2A_20250228T210929_R057_T04QGJ_20250228T230046",
        "output_bounds": [
            -156.96035934644146437,
            20.98364355956388749,
            -156.76075901017460978,
            21.08208310067092128,
        ],
        "output_crs": TARGET_CRS,
        "output_gsd_wyvern": WYVERN_OUTPUT_RESOLUTION,
        "output_gsd_sentinel": SENTINEL_OUTPUT_RESOLUTION,
        "output_filename_wyvern": "wyvern_dragonette-002_20250225T004037_4788dc6b.tiff",
        "output_filename_sentinel": "S2B_MSIL2A_20250228T210929_R057_T04QGJ_20250228T230046.tiff",
        "acolite_settings": {
            # "dsf_residual_glint_wave_range": [800, 900],
            # "glint_mask_rhos_band": 865,
            # "dsf_residual_glint_correction": True,
            # "dsf_residual_glint_correction_method": "alternative",
            # "glint_mask_rhos_threshold": 0.15
        },
    },
    # "oahu_d2_01": {
    #     "wyvern_id": "wyvern_dragonette-002_20250203T005242_1eaa2a96",
    #     "sentinel2_id": "S2B_MSIL2A_20250102T211919_R100_T04QFJ_20250103T004642",
    #     "output_bounds": [-157.92620878934624784, 21.23127167811359683, -157.67012482448828337, 21.49327588172029735],
    #     "output_crs": TARGET_CRS,
    #     "output_gsd_wyvern": WYVERN_OUTPUT_RESOLUTION,
    #     "output_gsd_sentinel": SENTINEL_OUTPUT_RESOLUTION,
    #     "output_filename_wyvern": "wyvern_dragonette-002_20250203T005242_1eaa2a96.tiff",
    #     "output_filename_sentinel": "S2B_MSIL2A_20250102T211919_R100_T04QFJ_20250103T004642.tiff",
    #     "acolite_settings": {},
    # },
    # "molokai_d3_01": {
    #     "wyvern_id": "wyvern_dragonette-003_20250508T203730_3cb1306b",
    #     "sentinel2_id": "S2B_MSIL2A_20250228T210929_R057_T04QFJ_20250228T230046",
    #     "output_bounds": [-157.10671255019022396, 21.04393380062705887, -156.98104215818889884, 21.10384496549667688],
    #     "output_crs": TARGET_CRS,
    #     "output_gsd_wyvern": WYVERN_OUTPUT_RESOLUTION,
    #     "output_gsd_sentinel": SENTINEL_OUTPUT_RESOLUTION,
    #     "output_filename_wyvern": "wyvern_dragonette-003_20250508T203730_3cb1306b.tiff",
    #     "output_filename_sentinel": "S2B_MSIL2A_20250228T210929_R057_T04QFJ_20250228T230046.tiff",
    #     "acolite_settings": {
    #         "dsf_residual_glint_wave_range": [800, 900],
    #         "glint_mask_rhos_band": 865,
    #         "dsf_residual_glint_correction": True,
    #         "dsf_residual_glint_correction_method": "alternative",
    #         "glint_mask_rhos_threshold": 0.15
    #     },
    # },
    # "maui_d3_01": {
    #     "wyvern_id": "wyvern_dragonette-003_20241206T203812_64e116d6",
    #     "sentinel2_id": "S2A_MSIL2A_20241205T210921_R057_T04QGJ_20241205T231445",
    #     "output_bounds": [-156.56120473401617232, 20.64869369579713876, -156.43304793929041807, 20.80562531586762631],
    #     "output_crs": TARGET_CRS,
    #     "output_gsd_wyvern": WYVERN_OUTPUT_RESOLUTION,
    #     "output_gsd_sentinel": SENTINEL_OUTPUT_RESOLUTION,
    #     "output_filename_wyvern": "wyvern_dragonette-003_20241206T203812_64e116d6.tiff",
    #     "output_filename_sentinel": "S2A_MSIL2A_20241205T210921_R057_T04QGJ_20241205T231445.tiff",
    #     "acolite_settings": {},
    # },
}
