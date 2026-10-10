# Wyvern Dragonette GeoTIFF Converter

This module converts a Wyvern Dragonette Hyperspectral Cloud Optimized GeoTIFF (COG), along with its associated STAC JSON metadata, into an ENVI Standard file.

## Directory Contents

| File | Description |
|---|---|
| `README.md` | Documentation and instructions for using the converter |
| `main.py` | Main Python script used to execute the converter |
| `constants.py` | Configuration file containing the input and output paths that need to be updated by the user |
| `convert_wyvern_geotiff_to_envi.py` | Contains the conversion logic for converting the COG and STAC JSON metadata to ENVI format |
| `requirements.in` | List of Python packages required by the converter |
| `requirements.txt` | Auto-generated dependency list used by `pip` to install the required packages |

## Using the Module

Before running the converter, ensure that all required third-party Python packages are installed.

It is recommended to run the converter inside a Python virtual environment to avoid conflicts with packages installed in your existing Python environment.

### Python Version

The converter was tested using **Python 3.13.5**.

## Setting Up a Python Virtual Environment (Optional)

If you want to keep your existing Python environment unchanged, you can create and use a virtual environment.

Make sure Python is installed on your system, then follow these steps:

1. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the converter as described in the [Running the Wyvern to ENVI Converter](#running-the-wyvern-to-envi-converter) section.

5. When finished, deactivate the virtual environment:

   ```bash
   deactivate
   ```

6. Optionally, remove the virtual environment:

   ```bash
   rm -r .venv
   ```

## Running the Wyvern to ENVI Converter

Before running the converter, make sure that all required third-party packages have been installed. If you are using a virtual environment, activate it before proceeding.

### 1. Configure the Input and Output Paths

Open `constants.py` and update the following values:

- `GEOTIFF_FILE_PATH` — Path to the Wyvern Dragonette Cloud Optimized GeoTIFF (`.tif` or `.tiff`).
- `JSON_METADATA_FILE_PATH` — Path to the corresponding STAC metadata JSON file (`.json`).
- `OUTPUT_HDR_FILE_PATH` — Path where the output ENVI header file (`.hdr`) should be created.

### 2. Run the Converter

From the project directory, run:

```bash
python main.py
```

### 3. Verify the Output

After the conversion completes successfully, verify that the following ENVI files have been generated at the specified output location:

- `.hdr` — ENVI header file containing metadata and image information.
- `.img` — ENVI image data file.

### 4. Use the ENVI Files

The generated `.hdr` and `.img` files can be uploaded to and opened in a compatible GIS or remote-sensing platform.

## Example Workflow

The overall workflow is:

```text
Wyvern Dragonette COG (.tif/.tiff)
              +
       STAC Metadata (.json)
              |
              v
      Wyvern ENVI Converter
              |
              v
        ENVI Standard
         /          \
      .hdr          .img
```

## Notes

- Ensure that the STAC JSON metadata corresponds to the input Dragonette GeoTIFF.
- Verify that the input file paths specified in `constants.py` are correct before running the converter.
- The `.hdr` and `.img` files should be kept together, as the ENVI header references the associated image data file.
- If using a virtual environment, activate it before installing dependencies or running the converter.