# Satellite Derived Bathymetry with the Dragonette Constellation

> [!CAUTION]
> Final adjustments and additions are still being made on this code.
> It is not particularly clean yet, please be advised that I'm still
> working on it :).

Presented at JACIE 2025 and Living Planet Symposium 2025

**Authors:** Ellie Jones, Chad Bryant

## Data Sources
- University of Hawai'i's [SOEST 5m Bathymetry Synthesis Grid](https://www.soest.hawaii.edu/hmrg/multibeam/bathymetry.php)
- Wyvern's [Open Data Program](https://opendata.wyvern.space/#/?.language=en)

# Project Structure

- `data`: Folder that holds all data for the project, including AOIs, raw & processed imagery, and results.
    - `aois`: GeoJSON files for train/test, validation, and multi-image AOIs. Corresponds to specific images, and matches the image's CRS.
    - `datasets`: All imagery, processed and raw. Will contain imagery from Sentinel-2 and Wyvern, as well as ground truth data.
        - `raws`: Area to store raw Wyvern data. Saves having to download the imagery over and over again
    - `results`:
- `notebooks`: Directory containing all notebooks for the project.
- `scripts`: Directory containing all relevant code for the project.
- `Makefile`: Contains all of the relevant commands for project setup, data processing, and experiment running.

# Getting Started

1. Ensure you are running a Mac or Linux based operating system. You _can_ make this work using Windows, but it is painful and not recommended. If on Windows, ensure you are running Windows Subsystem for Linux
2. Ensure you have `conda` (or miniconda/etc) installed
3. Clone down this repository and `cd` into the `bathymetry` directory
4. Call `make build-env` to create a `conda` environment for this project. It will install all relevant dependencies.
5. Call `make install-dependencies` to install the relevant projects that are required to process our data (ACOLITE).
6. Call `make download-soest` to download the ground truth dataset. _This will take a while, the SOEST server is very slow_
7. Call `make process-datasets` to download and process all Wyvern and Sentinel-2 imagery. _This will also take a while, particularly the first time when all of the Wyvern data is downloaded._
8. Call `make run-experiments` to run all relevant experiments. Results will be placed in the `data/results/` directory.

_Note: We must install ACOLITE in the parent directory above `wyvern-public-resources`. This ensures it exists in a known place and we can successfully use it to process imagery.

# Caveats and TODOs

# Contributing