"""
DESCRIPTION: Python script that converts a Wyvern Dragonette Cloud Optimized
             GeoTIFF (COG) hyperspectral scene, together with its STAC JSON
             metadata sidecar, into ENVI Standard format.
"""
import json
import os

import numpy as np
import rasterio

# Hard coded constants specific to a Wyvern Dragonette STAC/COG product
FILE_TYPE = "ENVI Standard"
HEADER_OFFSET = 0
BYTE_ORDER = 0          # 0 = little-endian (Intel) - Wyvern COGs are LSF
INTERLEAVE = "bil"
WAVELENGTH_UNITS = "Nanometers"

# ENVI data type codes, keyed by the GDAL/rasterio dtype string
DATA_TYPE_CODES = {
    "uint8": 1,
    "int16": 2,
    "int32": 3,
    "float32": 4,
    "float64": 5,
    "uint16": 12,
    "uint32": 13,
    "int64": 14,
    "uint64": 15,
}


class WyvernConverter(object):
    def __init__(self, geotiff_path: str, metadata_path: str, output_dir: str):
        self.geotiff_path = geotiff_path
        self.metadata_path = metadata_path
        self.output_dir = output_dir

        # Populated while parsing the STAC JSON sidecar
        self.stac_id = None
        self.platform = None
        self.processing_level = None
        self.wavelengths = []          # nm
        self.fwhm = []                 # nm
        self.band_names = []
        self.solar_irradiance = []
        self.nodata = None
        self.scale = None
        self.offset = None
        self.sensor_mode = None
        self.sensor_type = None
        self.product_type = None
        self.acquisition_time = None
        self.sun_elevation = None
        self.sun_azimuth = None
        self.cloud_cover = None
        self.gsd = None

        # Populated while parsing the GeoTIFF
        self.map_info = ""
        self.coordinate_system_string = ""
        self.lines = 0
        self.samples = 0
        self.bands = 0
        self.data_type = -1
        self.dtype_str = None
        self.data = None

        # Fixed / derived fields
        self.wavelength_units = WAVELENGTH_UNITS
        self.file_type = FILE_TYPE
        self.header_offset = HEADER_OFFSET
        self.byte_order = BYTE_ORDER
        self.interleave = INTERLEAVE

    def convert_geotiff(self):
        print("Validating input files...")
        self.validate_input_file()
        print("Starting conversion...")
        self.parse_metadata_file()
        self.parse_geotiff_file()
        self.get_data_type()
        self.validate_wavelengths()
        print("Creating ENVI files...")
        self.create_envi_files()

    def validate_input_file(self):
        if not os.path.isfile(self.geotiff_path):
            print(f"ERROR: GeoTIFF file doesn't exist - {self.geotiff_path}")
            raise FileNotFoundError(f"{self.geotiff_path} was not found or is a directory")
        if not os.path.isfile(self.metadata_path):
            print(f"ERROR: STAC JSON Metadata file doesn't exist - {self.metadata_path}")
            raise FileNotFoundError(f"{self.metadata_path} was not found or is a directory")
        print("GeoTIFF and STAC JSON Metadata files are valid")

    @staticmethod
    def _find_imagery_asset(stac_item: dict) -> dict:
        """Locate the asset dict that carries eo:bands / raster:bands.

        Wyvern currently titles this asset 'Cloud optimized GeoTiff', but we
        search by content rather than by title so an upstream naming change
        doesn't silently break the converter.
        """
        for asset in stac_item.get("assets", {}).values():
            if "eo:bands" in asset and "raster:bands" in asset:
                return asset
        raise KeyError("No asset with 'eo:bands' / 'raster:bands' found in STAC JSON")

    def parse_metadata_file(self):
        with open(self.metadata_path, "r") as f:
            stac_item = json.load(f)

        properties = stac_item.get("properties", {})
        imagery_asset = self._find_imagery_asset(stac_item)
        eo_bands = imagery_asset["eo:bands"]
        raster_bands = imagery_asset["raster:bands"]

        self.stac_id = stac_item.get("id")
        self.platform = properties.get("platform")
        self.processing_level = properties.get("processing:level")

        for eo_band in eo_bands:
            # STAC eo:bands wavelengths/FWHM are in micrometers; ENVI wants nm
            self.wavelengths.append(round(eo_band["center_wavelength"] * 1000, 2))
            self.fwhm.append(round(eo_band["full_width_half_max"] * 1000, 2))
            self.band_names.append(eo_band["name"])
            self.solar_irradiance.append(eo_band.get("solar_illumination"))

        # nodata/scale/offset are uniform across bands for Wyvern L2A products
        # today, but we read per-band and warn rather than silently assume it.
        nodata_values = {band["nodata"] for band in raster_bands}
        scale_values = {band["scale"] for band in raster_bands}
        offset_values = {band["offset"] for band in raster_bands}
        if len(nodata_values) > 1 or len(scale_values) > 1 or len(offset_values) > 1:
            print("WARNING: raster:bands nodata/scale/offset are not uniform "
                  "across bands - using the first band's values for the header")
        self.nodata = raster_bands[0]["nodata"]
        self.scale = raster_bands[0]["scale"]
        self.offset = raster_bands[0]["offset"]

        self.sensor_mode = properties.get("sensor_mode")
        self.sensor_type = properties.get("sensor_type")
        self.product_type = properties.get("product_type")
        self.acquisition_time = properties.get("datetime")
        self.sun_elevation = properties.get("view:sun_elevation")
        self.sun_azimuth = properties.get("view:sun_azimuth")
        self.cloud_cover = properties.get("eo:cloud_cover")
        self.gsd = properties.get("gsd")

        print(f"STAC JSON Metadata file parsed ({len(eo_bands)} bands found)")

    def get_data_type(self):
        self.data_type = DATA_TYPE_CODES.get(self.dtype_str, -1)
        if self.data_type == -1:
            print(f"WARNING: Unrecognized rasterio dtype "
                  f"'{self.dtype_str}' - data type left unset")

    def parse_geotiff_file(self):
        with rasterio.open(self.geotiff_path) as src:
            self.map_info = self._build_map_info(src.crs, src.transform)
            self.coordinate_system_string = src.crs.to_wkt()
            self.dtype_str = src.dtypes[0]
            self.data = src.read()
            self.bands = self.data.shape[0]
            self.lines = self.data.shape[1]
            self.samples = self.data.shape[2]
            print(f"The dimensions of the image are: {self.data.shape}")
            print(f"Lines = {self.lines} | Samples = {self.samples} | Bands = {self.bands}")
        print("GeoTIFF file parsed")

    @staticmethod
    def _build_map_info(crs, transform) -> str:
        """Build an ENVI-compliant 'map info' value (without the enclosing
        braces - those are added by the header writer) for a WGS84 UTM
        GeoTIFF.

        ENVI expects: {Projection, tie pt x, tie pt y, tie pt easting,
        tie pt northing, x pixel size, y pixel size, zone, North/South,
        Datum, units=Meters}
        """
        epsg = crs.to_epsg()
        if epsg is None:
            print("WARNING: Could not determine EPSG code; "
                  "falling back to a generic map info string")
            return f"{crs}, 1, 1, {transform.c}, {transform.f}, {transform.a}, {abs(transform.e)}"

        # WGS84 UTM EPSG codes: 326xx = Northern Hemisphere, 327xx = Southern
        if 32601 <= epsg <= 32660:
            zone = epsg - 32600
            hemisphere = "North"
        elif 32701 <= epsg <= 32760:
            zone = epsg - 32700
            hemisphere = "South"
        else:
            print(f"WARNING: EPSG:{epsg} is not a recognized WGS84 UTM code; "
                  "falling back to a generic map info string")
            return f"EPSG:{epsg}, 1, 1, {transform.c}, {transform.f}, {transform.a}, {abs(transform.e)}"

        return (
            f"UTM, 1, 1, {transform.c}, {transform.f}, "
            f"{transform.a}, {abs(transform.e)}, {zone}, {hemisphere}, WGS-84, units=Meters"
        )

    def _build_description(self) -> str:
        parts = []
        label = " ".join(p for p in (self.platform, self.processing_level, self.product_type) if p)
        if label:
            parts.append(f"{label} surface reflectance")
        if self.stac_id:
            parts.append(f"STAC ID: {self.stac_id}")
        if self.acquisition_time:
            parts.append(f"Acquisition: {self.acquisition_time}")
        return ", ".join(parts)

    def validate_wavelengths(self):
        if len(self.wavelengths) != self.bands:
            print(f"ERROR: The number of wavelengths ({len(self.wavelengths)}) "
                  f"does not equal the number of bands ({self.bands})")
        if len(self.fwhm) != self.bands:
            print(f"ERROR: The number of fwhm ({len(self.fwhm)}) "
                  f"does not equal the number of bands ({self.bands})")
        if len(self.band_names) != self.bands:
            print(f"ERROR: The number of band names ({len(self.band_names)}) "
                  f"does not equal the number of bands ({self.bands})")

    def process_hsi_data(self):
        # Wyvern L2A data ships as unsigned 16-bit surface reflectance,
        # already in its native scale - no bit-depth remap is needed here
        # (unlike EnMap's signed-int16 -> unsigned rescale). We only reorder
        # axes from rasterio's (bands, rows, cols) to (rows, cols, bands).
        return np.transpose(self.data, [1, 2, 0])

    # ------------------------------------------------------------------
    # ENVI header / raw file writing
    #
    # Both files are written manually rather than via a library, since
    # spectral's envi.save_image() silently drops keys it doesn't
    # recognize (e.g. "reflectance scale factor" never made it into the
    # header) and formats list fields with stray spaces before commas
    # (e.g. "503.0 , 510.0") which some ENVI-based tools fail to parse.
    # This gives full, predictable control over both files.
    # ------------------------------------------------------------------

    @staticmethod
    def _format_braced(value) -> str:
        """Format a list as '{v1, v2, v3}', or wrap a comma-containing
        string value in braces - both are required by the ENVI spec
        whenever a field's value itself contains commas."""
        if isinstance(value, (list, tuple)):
            return "{" + ", ".join(str(v) for v in value) + "}"
        return "{" + str(value) + "}"

    def _img_path(self) -> str:
        base, ext = os.path.splitext(self.output_dir)
        return base + ".img" if ext.lower() == ".hdr" else self.output_dir + ".img"

    def _write_raw_data(self, hsi_data: np.ndarray):
        # hsi_data is (lines, samples, bands). On-disk BIL order is
        # (lines, bands, samples).
        bil_data = np.transpose(hsi_data, [0, 2, 1])
        bil_data.tofile(self._img_path())

    def _write_header(self, reflectance_scale_factor, reflectance_offset):
        lines = ["ENVI"]

        description = self._build_description()
        if description:
            lines.append(f"description = {self._format_braced(description)}")

        lines.append(f"samples = {self.samples}")
        lines.append(f"lines = {self.lines}")
        lines.append(f"bands = {self.bands}")
        lines.append(f"header offset = {self.header_offset}")
        lines.append(f"file type = {self.file_type}")
        lines.append(f"data type = {self.data_type}")
        lines.append(f"interleave = {self.interleave}")
        if self.sensor_mode or self.sensor_type or self.product_type:
            lines.append("sensor type = Wyvern Dragonette")
        lines.append(f"byte order = {self.byte_order}")
        lines.append(f"wavelength units = {self.wavelength_units}")

        if reflectance_scale_factor is not None:
            lines.append(f"reflectance scale factor = {reflectance_scale_factor}")
        if reflectance_offset is not None:
            lines.append(f"reflectance offset = {reflectance_offset}")

        if self.map_info:
            lines.append(f"map info = {self._format_braced(self.map_info)}")
        if self.coordinate_system_string:
            lines.append(f"coordinate system string = {self._format_braced(self.coordinate_system_string)}")

        if self.wavelengths:
            lines.append(f"wavelength = {self._format_braced(self.wavelengths)}")
        if self.fwhm:
            lines.append(f"fwhm = {self._format_braced(self.fwhm)}")
        if self.band_names:
            lines.append(f"band names = {self._format_braced(self.band_names)}")
        if self.nodata is not None:
            lines.append(f"data ignore value = {self.nodata}")
        if self.solar_irradiance and all(v is not None for v in self.solar_irradiance):
            lines.append(f"solar irradiance = {self._format_braced(self.solar_irradiance)}")
        if self.offset is not None:
            lines.append(f"data offset values = {self._format_braced([self.offset] * self.bands)}")

        if self.acquisition_time:
            lines.append(f"acquisition time = {self.acquisition_time}")
        if self.sun_elevation is not None:
            lines.append(f"sun elevation = {self.sun_elevation}")
        if self.sun_azimuth is not None:
            lines.append(f"sun azimuth = {self.sun_azimuth}")
        if self.cloud_cover is not None:
            lines.append(f"cloud cover = {self.cloud_cover}")

        with open(self.output_dir, "w") as f:
            f.write("\n".join(lines) + "\n")

    def create_envi_files(self):
        reflectance_scale_factor = round(1.0 / self.scale, 4) if self.scale else None
        reflectance_offset = self.offset

        hsi_data = self.process_hsi_data()

        self._write_raw_data(hsi_data)
        self._write_header(reflectance_scale_factor, reflectance_offset)

        if os.path.isfile(self.output_dir) and os.path.isfile(self._img_path()):
            print("ENVI Files successfully created.")
        else:
            print("ERROR: The ENVI Header or raw data file was not successfully created.")
