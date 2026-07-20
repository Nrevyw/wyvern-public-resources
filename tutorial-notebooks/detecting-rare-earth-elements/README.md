# Detecting Rare Earth Elements (Neodymium)

Detect neodymium (Nd), a rare earth element, in Wyvern Dragonette hyperspectral imagery,
using the Mountain Pass REE mine in California as the example scene.

The notebook walks through three small, standard steps:

1. **Continuum removal**: isolate absorption features from overall brightness.
2. **Spectral resampling**: resample a real USGS bastnaesite reference spectrum onto Wyvern's
   bands (convolved with each band's response function).
3. **ACE** (Adaptive Cosine Estimator): a matched-filter-style detector that maps Nd-bearing
   pixels, plus a sanity-check of the high-scoring spectra against the reference.

To follow along with the write-up, visit the knowledge centre:
https://knowledge.wyvern.space/docs/tutorials/python/detecting_rare_earth_elements

This tutorial is inspired by Asadzadeh, Koellner & Chabrillat (2024), *Detecting rare earth
elements using EnMAP hyperspectral satellite data: a case study from Mountain Pass, California*
(Scientific Reports 14:20766, https://doi.org/10.1038/s41598-024-71395-2), adapted to Wyvern's
Extended VNIR bands.

## Data

- **Imagery:** a Wyvern Dragonette-002 L2A surface-reflectance scene over Mountain Pass, from the
  [Wyvern Open Data Program](https://opendata.wyvern.space/#/?.language=en). The notebook downloads
  it automatically from the STAC item.
- **Reference spectrum:** USGS splib07 bastnaesite, from
  [OpenSpecLib v0.0.6](https://github.com/null-jones/openspeclib/releases/tag/v0.0.6)
  (downloaded automatically).

> **Use L2A surface reflectance.** REE absorptions are subtle; L1B top-of-atmosphere radiance
> mixes in the solar spectrum and the O2 band near 760 nm and will not work for this analysis.

## Running the notebook

The notebook is self-contained and installs its own dependencies with a `%pip install` cell, so
there is no environment to set up.

- **Google Colab (easiest):** open the notebook with the "Open in Colab" badge at the top of it, or
  go to [colab.research.google.com](https://colab.research.google.com/) and open the notebook from
  this GitHub repo, then run the cells top to bottom.
- **Local Jupyter:** open `detecting_rare_earth_elements.ipynb` in JupyterLab or VS Code and run it.
  The first cell installs `rasterio`, `spectral`, `scipy`, and `pyarrow` into your active
  environment (Python 3.10+; the rest of the packages ship with most scientific Python installs).

## Output

A georeferenced ACE detection GeoTIFF (`mountain_pass_nd_ace.tif`) you can open in QGIS, ArcGIS,
or ENVI, plus inline spectral and map figures.
