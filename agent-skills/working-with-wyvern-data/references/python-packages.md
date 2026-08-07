# Python Packages for Wyvern Hyperspectral Analysis

Recommended defaults, not an exhaustive menu. Install what the task needs.

## Core stack

| Package | Use | Notes |
| --- | --- | --- |
| `rasterio` | Read/write COGs, windowed reads, reprojection | The default for loading Wyvern imagery. GDAL-backed. |
| `numpy` | Band math, index calculation, masking | Everything is an ndarray. |
| `pystac` | Parse STAC items/collections | `pystac.Item.from_file(url)` works against the Open Data catalog. |
| `pystac-client` | Query a STAC **API** | Only useful for STAC APIs; the Wyvern open-data catalog is static JSON, so walk `rel: item` links or use `scripts/wyvern_stac.py`. |
| `requests` | HTTP fetches | Its default User-Agent avoids the CDN's 403 on Python-urllib. |
| `shapely` + `pyproj` | AOI geometry, CRS transforms | Needed because each scene has its own UTM zone. |

```bash
pip install rasterio numpy pystac requests shapely pyproj scipy
```

## Hyperspectral-specific

| Package | Use | Notes |
| --- | --- | --- |
| `spectral` (Spectral Python / SPy) | **Target detection (ACE, matched filter), anomaly detection (RX), SAM, MNF, PCA, endmember extraction, continuum removal** | The workhorse for the analysis in [spectral-analysis.md](spectral-analysis.md). Verified against v0.25. |
| `scikit-learn` | Classification, clustering, dimensionality reduction | Pair with SPy for supervised workflows. |
| `xarray` + `rioxarray` | Labeled dimensions, keeping wavelength as a coordinate | Helpful for multi-scene/time-series work. |
| `dask` | Out-of-core processing | For scenes or stacks too large for memory. |
| `matplotlib` | Spectral plots, index maps | |
| `geopandas` | Vector AOIs, zonal workflows | |

```bash
pip install spectral scikit-learn matplotlib
```

**On `pysptools`:** often cited for hyperspectral work, but it fails to import on
current Python versions (broken `detection` submodule). Prefer `spectral` — it covers
the same detection and unmixing algorithms and is maintained.

## Spectral libraries: OpenSpecLib

[OpenSpecLib](https://github.com/null-jones/openspeclib) (a third-party project, not
Wyvern-maintained — hence the pinned tag below) amalgamates USGS Spectral Library 7,
ECOSTRESS, and EcoSIS into one schema-validated structure. **v0.0.6** — the release the
[REE notebook](https://github.com/Nrevyw/wyvern-public-resources/tree/main/tutorial-notebooks/detecting-rare-earth-elements)
also pins — holds 32,940 spectra: 26,780 vegetation, 2,885 mineral, 1,410 water, 470
rock, 440 man-made, 360 organic compounds. This is the practical way to get reference
spectra for target detection.

**Get the data** — download release assets directly (no install needed):

```bash
BASE=https://github.com/null-jones/openspeclib/releases/download/v0.0.6
curl -sLO $BASE/usgs_splib07.parquet     #  38 MB — minerals/rocks (best for detection)
curl -sLO $BASE/wavelengths.parquet      # 0.3 MB — REQUIRED: wavelength grids
curl -sLO $BASE/ecostress.parquet        #  30 MB — optional
curl -sLO $BASE/ecosis.parquet           # 307 MB — optional; vegetation, large
```

Pin the version. Counts, sizes and grid layout all shift between releases, so an
unpinned URL will silently change the data underneath your analysis.

Prefer the Parquet files over `openspeclib-catalog-*.json` — that catalog is a ~100 MB
metadata index and is rarely what you want.

**Two schema details that will burn you:**

1. Spectra store `spectral_data.values` but *not* their wavelengths. Those live in
   `wavelengths.parquet`, joined `spectral_data.wavelength_grid_id` → `grid_id` (the
   column names differ on each side).
2. **Units are not uniform.** usgs_splib07 (4 grids) and ecostress (65) are µm, but
   all 43 **ecosis grids are nm** — and ecosis is where the 26,780 vegetation spectra
   live. Read `wavelength_unit` per grid (also on each row as
   `spectral_data.wavelength_unit`) instead of hardcoding `* 1000`.

Lab fill values for bad bands are large negatives (e.g. `-1.23e34`) and must be
masked.

```python
import pyarrow.parquet as pq
import numpy as np

spectra = pq.read_table("usgs_splib07.parquet", columns=[
    "name", "material.category",
    "spectral_data.wavelength_grid_id", "spectral_data.values",
]).to_pylist()

grids = {r["grid_id"]: r for r in pq.read_table("wavelengths.parquet").to_pylist()}

match = next(r for r in spectra
             if "hematite" in r["name"].lower() and r["spectral_data.values"])
grid = grids[match["spectral_data.wavelength_grid_id"]]

wl_nm = np.array(grid["wavelengths"], float) * 1000   # µm -> nm
refl = np.array(match["spectral_data.values"], float) # mask negatives before use
```

For ad-hoc search, DuckDB queries the Parquet in place:

```sql
SELECT id, name, "material.formula"
FROM 'usgs_splib07.parquet'
WHERE "material.category" = 'mineral' AND lower(name) LIKE '%hematite%';
```

There is also a no-install [browser viewer](https://null-jones.github.io/openspeclib/)
that can search, plot, simulate Wyvern-band downsampling, and export CSV or ENVI
`.sli` — useful for picking a target spectrum before writing code.

**Always resample lab spectra to Wyvern bands** before comparing them to imagery.
Use `scripts/resample_spectra.py` (FWHM-weighted convolution); see
[spectral-analysis.md](spectral-analysis.md) for why this matters. The
[REE notebook](https://github.com/Nrevyw/wyvern-public-resources/tree/main/tutorial-notebooks/detecting-rare-earth-elements) shows the
same convolution applied to a USGS bastnaesite spectrum end to end.

Note the USGS `splib07a` grid is 2151 samples at 1 nm spacing over 350–2500 nm, so a
USGS spectrum covers Wyvern's full VNIR range with room to spare.
