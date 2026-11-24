# ==================================================================================
#                           CONSTANTS FILE
#
# DESCRIPTION: This file contains all the variables that need to be updated for
#              the conversion of a Wyvern Dragonette GeoTIFF to ENVI to work.
#
# VARIABLES:
#   GEOTIFF_FILE_PATH      - Location of the Wyvern Cloud Optimized GeoTIFF
#                            (COG) to be converted
#   JSON_METADATA_FILE_PATH - Location of the Wyvern STAC JSON metadata file
#                             that ships alongside the COG. Contains the
#                             per-band wavelength/FWHM/solar-irradiance info.
#   OUTPUT_HDR_FILE_PATH   - Location of the ENVI output. This file path MUST be
#                            the .hdr file, the .raw file will automatically be
#                            created in the same dir
# ==================================================================================

GEOTIFF_FILE_PATH = "wyvern_dragonette-001_20250526T081429_123b53d7_l2a.tiff"
JSON_METADATA_FILE_PATH = "wyvern_dragonette-001_20250526T081429_123b53d7_l2a.json"
OUTPUT_HDR_FILE_PATH = "wyvern_dragonette-001_20250526T081429_123b53d7_l2a.hdr"
