---
name: working-with-wyvern-data
description: Find, load, and analyze Wyvern hyperspectral satellite imagery — STAC discovery, correct scaling/masking, wavelength-to-band resolution, spectral indices, and spectral analysis (ACE/MTMF target detection, RX anomaly detection, MNF, unmixing, spectral libraries). Use whenever a task involves Wyvern imagery, Dragonette satellites, Wyvern Open Data, or hyperspectral material detection, even if the user just says "this satellite image" and the file or URL matches wyvern_dragonette-*.
---

# Working with Wyvern Hyperspectral Data

Wyvern's Dragonette satellites produce hyperspectral imagery (23–31 narrow VNIR bands)
delivered as Cloud-Optimized GeoTIFFs with STAC metadata. The Open Data Program
(CC-BY-4.0) provides free scenes used throughout this skill.

## Data products at a glance

Both L2A and L1B are purchasable. Open Data currently publishes L2A; an
[L1B collection](https://wyvern-odp.com/l1b/collection.json) exists and will be
populated later (it returns zero items today).

| | L2A surface reflectance | L1B top-of-atmosphere radiance |
| --- | --- | --- |
| Dtype / units | `uint16`, **multiply by `scale` (0.0001) → reflectance 0–1** | `float32`, W·m⁻²·sr⁻¹·µm⁻¹ (no scaling) |
| NoData | **65535** (mask *before* scaling) | −9999 |
| CRS | Per-scene UTM zone (`proj:epsg` e.g. 32639) | EPSG:4326 with non-square pixels (sized to 5 m at scene-centre latitude) |
| Ready for analysis? | Yes | No — convert first |

Read `raster:bands` from the item's COG asset for the authoritative
`data_type` / `nodata` / `scale` rather than assuming the values above.

**For L1B**, convert to top-of-atmosphere reflectance with
[`top-of-atmosphere-processing/`](https://github.com/Nrevyw/wyvern-public-resources/tree/main/top-of-atmosphere-processing) in this repo,
or atmospherically correct to surface reflectance for quantitative work (see the
[knowledge centre](https://knowledge.wyvern.space/docs/documentation/getting_started/atmospheric_correction)).
Prefer L2A whenever the analysis depends on absorption-feature shape: L1B radiance
carries the solar spectrum and atmospheric features (e.g. the O₂ band near 760 nm)
that will swamp subtle targets.

## Workflow

- [ ] **Feasibility first:** for a named material, confirm its diagnostic absorptions
      fall inside **this scene's** range — Standard VNIR is **503–799 nm**, Extended
      VNIR is **445–870 nm**. Check the product type before the range; 445–870 is the
      widest case, not the guarantee. If the features fall outside, stop and say so —
      no amount of processing recovers what the sensor never measured (see step 5)
- [ ] Discover scenes (STAC catalog)
- [ ] Resolve wavelengths → band numbers from the item's `eo:bands`
- [ ] Load: window/mask → apply scale → verify value ranges
- [ ] Analyze: indices, and/or spectral detection & anomaly methods
- [ ] Verify output ranges before reporting results

Feasibility is step 0 because everything downstream succeeds for an undetectable
target — you get a meaningless map after paying the full (rate-limited) cost.

## Python packages

Default stack: `rasterio` (load COGs), `numpy` (band math), `pystac` (parse items),
`requests`, plus `pyproj`/`shapely` for AOIs. For spectral analysis add `spectral`
(SPy) — it provides ACE, matched filter, RX, SAM, MNF, and unmixing.

```bash
pip install rasterio numpy pystac requests pyproj shapely spectral scipy matplotlib
```

Full rationale, the OpenSpecLib spectral-library workflow (~27,000 reference spectra),
and packages to avoid: [references/python-packages.md](references/python-packages.md).

## 1. Discover scenes

Run `scripts/wyvern_stac.py` (stdlib-only, no pip installs needed):

```bash
python scripts/wyvern_stac.py search --product-type extended --max-cloud 10
python scripts/wyvern_stac.py search --bbox -114.5,50.7,-113.5,51.3   # W,S,E,N lon/lat
python scripts/wyvern_stac.py show  <ITEM_URL>
python scripts/wyvern_stac.py bands <ITEM_URL> 660 800   # wavelengths in nm
```

Or walk the catalog directly — root `https://wyvern-odp.com/catalog.json` (STAC 1.0.0),
with child catalogs by `year/`, `application/` (agriculture, mining, coastal, …), and
`product-type/{standard,extended}` whose `rel: item` links are the scenes.
Human-browsable mirror: https://opendata.wyvern.space/

Useful item properties for filtering: `eo:cloud_cover`, `datetime`, `platform`,
`view:sun_elevation`, `proj:epsg`, plus the item `bbox`.

⚠️ `product_type` is `"hyperspectral"` on every item and does **not** tell you the band
configuration. Determine it from the band count — 23 = Standard VNIR, 31 = Extended
VNIR — or from the catalog path. The index library keys its `band_mappings` on the
strings `"Standard VNIR"` / `"Extended VNIR"`, which appear nowhere in the item JSON.

**HTTP gotcha:** the CDN returns 403 to some default User-Agents — Python-urllib's,
and some agent HTTP tools. Send an explicit custom `User-Agent` header (the `requests`
library's default works, `curl` works, and the bundled script already handles this).
If a fetch 403s, set the header before assuming the URL is wrong.

## 2. Resolve bands

Band counts and wavelengths differ by product type — never hardcode band numbers
across scenes:

- **Standard VNIR** (Dragonette-1): 23 bands, ~503–799 nm
- **Extended VNIR** (Dragonette-2/3/4): 31 bands, ~445–870 nm

There are two authoritative sources, both per-scene — use either:

**The GeoTIFF's own band tags** (simplest, works offline once downloaded, already in
nm):

```python
with rasterio.open(path) as src:
    cwl = [float(src.tags(b)["wavelength"]) for b in range(1, src.count + 1)]
    fwhm = [float(src.tags(b)["FWHM"]) for b in range(1, src.count + 1)]
    nodata = src.nodata          # 65535, read from the file — don't hardcode
```

**The STAC item's `eo:bands`**, at
`item["assets"]["Cloud optimized GeoTiff"]["eo:bands"]` — on the asset, *not* under
`properties`. Order = 1-based GeoTIFF band numbers, but `center_wavelength` /
`full_width_half_max` are in **µm**, not nm. Ignore `common_name`: it is coarse and ambiguous
here — seven separate bands are labelled `"red"` on Standard VNIR (six on Extended),
and the labels shift between product types. Always resolve by `center_wavelength`.

⚠️ `src.scales` is **1.0** — the GeoTIFF does *not* carry the 0.0001 reflectance
scale. Take `scale` from STAC `raster:bands`, or hardcode 0.0001 for L2A after
verifying. Trusting `src.scales` silently leaves values unscaled.

Nominal tables for both configurations are in
[references/band-reference.md](references/band-reference.md) — use them to reason
about coverage, but read the actual values per scene, since individual bands can
report slightly off-nominal centers (a nominal 870 nm band may report 869 nm). If a
requested wavelength is farther than one FWHM from the nearest band center, the sensor
doesn't cover it — say so rather than silently substituting.

## 3. Load and scale correctly

The imagery asset key is `"Cloud optimized GeoTiff"` (with spaces). Try a windowed read
first — it avoids pulling a multi-GB file — and fall back to downloading the asset if
streaming fails (see the rate-limit note below):

```python
import rasterio
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds
import numpy as np

with rasterio.open(cog_href) as src:
    # Reproject a lon/lat AOI into the scene's UTM CRS, then read only that window.
    bounds = transform_bounds("EPSG:4326", src.crs, *aoi_lonlat_bounds)
    window = from_bounds(*bounds, src.transform).round_offsets().round_lengths()
    cube = src.read(window=window).astype("float64")   # all bands: (bands, rows, cols)
    nodata = src.nodata                                # 65535, from the file

cube = np.where(cube == nodata, np.nan, cube) * 0.0001  # mask BEFORE scaling
img = np.moveaxis(cube, 0, -1)                          # -> (rows, cols, bands) for SPy
```

⚠️ **That recipe is L2A-only. Check `processing:level` first.** Applying it to an L1B
scene fails *silently*: the 0.0001 cancels in any normalized-difference index, so you
get an index computed on radiance, biased by the red/NIR solar-irradiance ratio. It
passes every range check in step 6 — measured on a known-truth scene, bare soil read
−0.06 instead of +0.15, flipping sign and reading as water.

For L1B (`float32`, NoData **−9999**, no scale factor), convert radiance to
top-of-atmosphere reflectance first. The per-band solar irradiance is in the STAC
asset's `eo:bands` as `solar_illumination`, and the item JSON is a hard prerequisite:

```python
# cube here is the L1B read: float32 radiance, shape (bands, rows, cols)
radiance = np.where(cube == -9999, np.nan, cube)   # L1B NoData; no scale factor

day_of_year = 180        # from properties["datetime"]
sun_elev_deg = 60.2      # properties["view:sun_elevation"] — an elevation, so sin()

# Real per-band irradiance. If you read a band subset, subset e0 the same way,
# or the broadcast fails.
e0 = np.array([b["solar_illumination"] for b in eo_bands])

d = 1 - 0.01672 * np.cos(np.deg2rad(0.9856 * (day_of_year - 4)))   # sun-earth AU
reflectance = (radiance * np.pi * d**2) / (
    e0[:, None, None] * np.sin(np.deg2rad(sun_elev_deg))
)
```

⚠️ `solar_illumination` must be the **real per-band values**. A single constant across
bands cancels out of any normalized-difference index, silently reproducing the exact
unconverted-radiance error above. Note this field lives only in the STAC item, so
unlike L2A the item JSON is required, not optional.

`view:sun_elevation` is an *elevation*, so it takes `sin`, not `cos`. Full worked
example:
[top-of-atmosphere-processing/](https://github.com/Nrevyw/wyvern-public-resources/tree/main/top-of-atmosphere-processing).
For quantitative work, atmospherically correct beyond TOA.

Read all bands at once for spectral analysis — one pass over the file, and it's the
layout `spectral` expects. For a two-band index, read just those two —
`src.read([red_b, nir_b], window=...)` — whether local or remote: it is one request
either way and ~11× fewer bytes, which matters against the rate limiter. Resolve
`red_b`/`nir_b` per scene (step 2); never paste literal band numbers, since they
differ between product types. Scenes in different UTM zones must be reprojected to a common CRS before
mosaicking or cross-scene comparison.

**Picking an AOI when the user didn't give one:** survey cheaply first using the COG's
overviews, then read one full-resolution window over the interesting area:

```python
with rasterio.open(path) as src:
    # red_b / nir_b resolved from THIS scene's metadata (step 2), not hardcoded
    small = src.read([red_b, nir_b], out_shape=(2, src.height // 8, src.width // 8))
```

Items also ship `"Data Mask"` and `"Pixel Quality Mask"` COG assets for cloud/quality
screening.

**Rate limiting.** Metadata is on `wyvern-odp.com`, but imagery COGs are on
`wyvern-data.com`, which returns **HTTP 429** under repeated access. GDAL usually
reports this as `Range downloading not supported by this server!` — treat that as "back
off and retry", not a missing feature. Minimize requests (one windowed read beats
many):

```python
import os
os.environ["GDAL_HTTP_USERAGENT"] = "your-tool/1.0"
os.environ["GDAL_HTTP_MAX_RETRY"] = "5"
os.environ["GDAL_HTTP_RETRY_DELAY"] = "15"   # seconds; set before opening
```

If streaming keeps failing, download the asset once (or the `zip_file` asset) and work
locally.

## 4. Compute indices

The Wyvern index library defines 34 indices with per-product-type band mappings
(1-based `band_index`, matching `src.read(n)`):

- JSON: https://knowledge.wyvern.space/hyperspectral-index-library.json — source data
  also at
  [index-library/](https://github.com/Nrevyw/wyvern-public-resources/tree/main/index-library)
- Human reference: https://knowledge.wyvern.space/hyperspectral_library

```python
ndvi = (nir - red) / (nir + red)   # bands resolved per scene, reflectance-scaled
```

For narrowband indices (RENDVI, NDRE, MTCI, …) use the library's band mappings rather
than multispectral conventions — red-edge placement matters at these bandwidths.

## 5. Spectral analysis beyond indices

For material identification and discovery, use `spectral` (SPy) on masked, scaled
reflectance shaped `(rows, cols, bands)`:

| Goal | Method |
| --- | --- |
| "Is material X here?" (have a reference spectrum) | **ACE** — `sp.ace(img, target)`; best results on Wyvern data, scale-invariant. **MTMF** also performs well but needs an infeasibility term SPy doesn't ship. |
| "What's unusual here?" (no reference spectrum) | **RX** — `sp.rx(img)` |
| Denoise / compress bands | **MNF** — preferred over PCA for hyperspectral |
| Fractional abundance | endmember extraction (`smacc`/`ppi`) → `sp.unmix` |

⚠️ **SPy rejects NaN.** `rx`, `ace`, `mnf`, and `calc_stats` all raise `NaNValueError`
on the NaN-masked cube step 3 produces — and Wyvern scenes are rotated swaths, so a
third of a raster can be NoData. Score only the valid pixels and scatter the results
back (numerically identical to running on a clean rectangle):

```python
valid = np.isfinite(img).all(axis=2)
scores = np.full(valid.shape, np.nan)
scores[valid] = sp.rx(img[valid].reshape(-1, 1, img.shape[2])).ravel()
```

The house pattern for material detection is **resample reference → continuum removal →
ACE → verify hits resemble the reference**. Resampling comes first: continuum removal
needs the target already expressed on the scene's band centers. Reference spectra (OpenSpecLib, USGS,
ECOSTRESS) are measured at 1–10 nm and **must be convolved onto Wyvern's 16–32 nm
bands** — naive interpolation over-weights narrow features and yields wrong scores:

```bash
python scripts/resample_spectra.py --csv spectrum.csv --item-url <ITEM_URL> --out target.csv
```

**Worked end-to-end example:**
[`tutorial-notebooks/detecting-rare-earth-elements/`](https://github.com/Nrevyw/wyvern-public-resources/tree/main/tutorial-notebooks/detecting-rare-earth-elements)
detects neodymium at Mountain Pass using exactly this pipeline — read it before writing
a new detection workflow.

**Wyvern is VNIR-only**, which determines what is detectable. Mind the product type:
Extended VNIR spans 445–870 nm, but **Standard VNIR only 503–799 nm** — a target at
460 nm or 860 nm is undetectable on a Standard scene even though it is inside the
constellation's overall envelope:

- **Works:** rare earth elements (Nd has sharp VNIR features — see the notebook above),
  vegetation pigments and stress, chlorophyll, water constituents
- **Extended VNIR only:** iron oxides. The Fe³⁺ minimum that separates hematite from
  goethite/jarosite is at ~860–900 nm, so a Standard scene (799 nm) can suggest
  "ferric material" but never say which oxide
- **Does not work:** clays, carbonates, evaporites, hydrocarbons, sulfates, and most
  alteration minerals generally. Their diagnostic absorptions are in the SWIR —
  kaolinite's Al-OH doublet is at ~2160/2200 nm and alunite's at ~2170/2210 nm, roughly
  **1300 nm past Wyvern's reddest band**, not a marginal miss. When a target isn't on
  either list, check where its diagnostic features actually sit rather than assuming
  the list is exhaustive. Report that limitation
  rather than presenting a weak score as a detection.

⚠️ **No pipeline check will catch this for you.** A SWIR mineral's library spectrum
resamples onto Wyvern's bands cleanly (USGS splib07 spans 350–2500 nm, so there are no
NaN bands to warn you), and ACE will happily return a plausible-looking score surface —
one that is ranking albedo and background covariance, not the mineral. The only defence
is the feasibility check before you start.

When a target needs SWIR, say so and point at an instrument that covers it:
[**EMIT**](https://earth.jpl.nasa.gov/emit/) (380–2500 nm, ~60 m),
[**EnMAP**](https://www.enmap.org/) or [**PRISMA**](https://www.asi.it/en/earth-science/prisma/)
(both to 2500 nm, ~30 m), or [**ASTER**](https://asterweb.jpl.nasa.gov/) band ratios.
A VNIR-detectable proxy can still help if the association is established independently
(iron oxides often accompany argillic alteration), but that maps the proxy, not the
target — label it as such.

Method details, thresholding, MTMF workflow, and interpretation rules:
[references/spectral-analysis.md](references/spectral-analysis.md).

## 6. Verify before reporting

- **If the product is L1B, confirm you actually converted it.** An unconverted L1B
  scene passes every check below — the scale cancels in a normalized difference — while
  every value is wrong. Check `processing:level` before trusting an in-range result
- Reflectance after masking+scaling ∈ [0, ~1] (small excursions over bright targets
  are normal; values of 6.5 mean you forgot the scale, NaN-everything means you
  masked after scaling)
- Normalized-difference indices ∈ [−1, 1]
- Band CWLs you actually read match the index definition (print them)
- Reprojection preserved the AOI (compare bounds)
- Detection scores are scene-relative: threshold statistically (e.g. 99.9th
  percentile), confirm hits aren't clouds/shadows/edges, and check the detected
  pixels' mean spectrum actually resembles the target. "Not detected" is a valid
  finding — don't lower the threshold until something appears.

## More resources

- Reference files in this skill: [python-packages.md](references/python-packages.md),
  [spectral-analysis.md](references/spectral-analysis.md),
  [band-reference.md](references/band-reference.md)
- Worked notebooks on the same data:
  [REE detection](https://github.com/Nrevyw/wyvern-public-resources/tree/main/tutorial-notebooks/detecting-rare-earth-elements),
  [water quality indices](https://github.com/Nrevyw/wyvern-public-resources/tree/main/tutorial-notebooks/water-quality-indices-maracaibo),
  [L1B → ToA reflectance](https://github.com/Nrevyw/wyvern-public-resources/tree/main/top-of-atmosphere-processing),
  [visualizing Wyvern data](https://github.com/Nrevyw/wyvern-public-resources/tree/main/visualizing-wyvern-data)
- [Sensor relative spectral response curves](https://github.com/Nrevyw/wyvern-public-resources/tree/main/relative-spectral-responses)
- Everything for agents, condensed: https://knowledge.wyvern.space/AGENTS.md and
  https://knowledge.wyvern.space/llms.txt (full docs text: `llms-full.txt`)
