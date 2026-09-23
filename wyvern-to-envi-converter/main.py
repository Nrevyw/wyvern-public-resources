"""
DESCRIPTION: The main python file to be executed.
"""
from convert_wyvern_geotiff_to_envi import WyvernConverter
import constants
import time

print("==============================================")
print("         WYVERN GEOTIFF CONVERSION")
print("==============================================")

start_time = time.time()

converter = WyvernConverter(constants.GEOTIFF_FILE_PATH, constants.JSON_METADATA_FILE_PATH, constants.OUTPUT_HDR_FILE_PATH)
converter.convert_geotiff()

end_time = time.time()
total_time = end_time - start_time

print("")
print("Done!")
print(f"Script completed in {total_time:.3f} seconds")
print("==============================================")
