# Spectral Analysis Approaches for Wyvern Imagery

How to go beyond indices: match pixels against reference spectra, find anomalies,
unmix, and reduce dimensionality. Code uses `spectral` (SPy) and assumes an
`img` array shaped `(rows, cols, bands)` of **masked, scaled surface reflectance**
(see the main SKILL.md — mask NoData 65535 *before* applying scale 0.0001).

⚠️ **SPy cannot consume that cube directly.** Wyvern scenes are rotated swaths, so a
NoData fringe is always present. `ace`, `rx`, `mnf`, `calc_stats` and
`noise_from_diffs` raise `NaNValueError`; worse, `spectral_angles` and `smacc` do
**not** raise — they return corrupted or all-NaN output. Every snippet below therefore
routes through `valid_pixels` / `scatter_scores` from
[`scripts/spy_helpers.py`](../scripts/spy_helpers.py).

## Contents

- [Choosing an approach](#choosing-an-approach)
- [Preparing a target spectrum](#preparing-a-target-spectrum)
- [Target detection (ACE, MTMF, MF, SAM)](#target-detection)
- [Anomaly detection (RX)](#anomaly-detection)
- [Dimensionality reduction (MNF, PCA)](#dimensionality-reduction)
- [Unmixing and endmembers](#unmixing-and-endmembers)
- [Continuum removal](#continuum-removal)
- [Interpreting and verifying results](#interpreting-and-verifying-results)

## Choosing an approach

The core detection pipeline is **resample reference spectrum → ACE → verify**. The
[REE notebook](https://github.com/Nrevyw/wyvern-public-resources/tree/main/tutorial-notebooks/detecting-rare-earth-elements)
works this end to end on Dragonette-002 and is worth reading first — note it runs ACE on
plain scaled reflectance and uses continuum removal only to *inspect* absorption
features in plots, not as a detection step.

Continuum removal before ACE is optional and needs care: it must be applied to the
target as well, after resampling, and the end bands must be dropped (see
[Continuum removal](#continuum-removal)).

| Question | Approach |
| --- | --- |
| "Is material X here?" (have a reference spectrum) | **ACE** — scale-invariant, one call, and what the REE notebook uses. **MTMF** is an alternative but needs an infeasibility term SPy doesn't ship |
| "What's unusual here?" (no reference spectrum) | **RX** anomaly detection |
| "How much of X is in each pixel?" | Unmixing / MTMF infeasibility |
| "What materials are present at all?" | Endmember extraction (PPI, SMACC) → unmix |
| "Reduce noise / bands before analysis" | **MNF** (preferred over PCA for hyperspectral) |
| "Sharpen narrow absorption features" | Continuum removal |
| "Quick vegetation/water/moisture proxy" | A spectral index (see SKILL.md step 4) |

**VNIR-only caveat.** Coverage depends on the product type — **Standard VNIR is
503–799 nm, Extended VNIR 445–869 nm** — and that decides what is detectable at all.
Check the scene's band count (23 vs 31) before applying this table:

| Detectable in VNIR | Needs SWIR (not detectable) |
| --- | --- |
| Rare earth elements — Nd³⁺ has features at 585, 745, 810 and 870 nm; Standard reaches only the first two | Clays / phyllosilicates |
| Ferric iron — present on both, but *identifying* the oxide is limited (below) | Carbonates |
| Vegetation pigments, chlorophyll, stress, senescence | Hydrocarbons, most alteration minerals |
| Water constituents, chlorophyll-a, turbidity | Evaporites, sulfates |

**Detecting ferric iron and *identifying* the oxide are different claims.** Fe³⁺ has a
crystal-field band around 630–715 nm that sits inside **both** product types, so
"ferric material is present" is a supportable statement on a Standard scene.

Naming the oxide needs the longer-wavelength minimum, and that is largely out of reach:
hematite's is ~860 nm (just inside Extended's 869 nm top band, outside Standard
entirely) and goethite's is ~900–920 nm, beyond **both**. So Extended can support
"minimum at or below 870 nm, hematite-like"; it cannot locate goethite's band at all.
Coarse-grained (20–250 µm) hematite is nearly flat in VNIR regardless, so a negative
does not exclude it.

Don't over-generalize "minerals need SWIR" — REE detection in VNIR is a proven Wyvern
workflow (see [the Mountain Pass notebook](https://github.com/Nrevyw/wyvern-public-resources/tree/main/tutorial-notebooks/detecting-rare-earth-elements)).
But when a target's diagnostic features fall outside the scene's range,
say so plainly instead of reporting a weak score, and name an instrument that covers
them: [EMIT](https://earth.jpl.nasa.gov/emit/) (380–2500 nm, ~60 m),
[EnMAP](https://www.enmap.org/) or
[PRISMA](https://www.asi.it/en/earth-science/prisma/) (both to 2500 nm, ~30 m), or
[ASTER](https://asterweb.jpl.nasa.gov/) band ratios. A VNIR-detectable proxy (iron
oxides often accompany argillic alteration) can substitute only if the association is
established independently — and it maps the proxy, not the target.

⚠️ **Nothing downstream will flag an out-of-range target.** Library spectra span
350–2500 nm, so a SWIR mineral resamples onto Wyvern's bands with no NaN bands and no
warnings, and ACE returns a plausible score surface that is really ranking albedo and
background covariance. Check feasibility *before* resampling; the NaN check below only
catches the opposite problem (library not covering the sensor).

**Use L2A, not L1B, for absorption-feature work.** L1B radiance carries the solar
spectrum and atmospheric absorptions (notably the O₂ band near 760 nm) that swamp
subtle features. Convert L1B first
([`top-of-atmosphere-processing/`](https://github.com/Nrevyw/wyvern-public-resources/tree/main/top-of-atmosphere-processing)).

## Preparing a target spectrum

Reference spectra come from libraries (see [python-packages.md](python-packages.md)
for OpenSpecLib) at 1–10 nm resolution. Wyvern bands are 16–32 nm wide, so a
reference spectrum **must be convolved onto Wyvern's band response** (15.6–32 nm
FWHM) — naive interpolation over-weights narrow features and produces wrong scores.

```bash
# CSV of wavelength,reflectance -> Wyvern band values for a specific scene
python scripts/resample_spectra.py --csv hematite.csv \
    --item-url <STAC_ITEM_URL> --out target.csv
```

Or import it:

```python
import sys

sys.path.insert(0, "scripts")  # or wherever this skill's scripts/ lives
from resample_spectra import load_wyvern_bands, resample

cwl, fwhm = load_wyvern_bands(item_url=item_url)   # this scene's exact bands
target = resample(wl_nm, reflectance, cwl, fwhm)   # -> one value per band
```

Requirements for a valid comparison:

- Target and image must be the **same quantity** (surface reflectance vs surface
  reflectance). Never match a lab reflectance spectrum against L1B radiance.
- Band count must match the product type (23 standard / 31 extended).
- NaN bands in the resampled target mean the library spectrum didn't cover that
  wavelength — drop those bands from both target and image, or pick another spectrum.

An in-scene target (mean spectrum of pixels you know are the material) usually
outperforms a lab spectrum, because it already carries the scene's illumination and
residual atmospheric effects.

## Target detection

**ACE (Adaptive Cosine/Coherence Estimator)** is the recommended default here because
it is scale-invariant — it responds to spectral *shape* rather than brightness, making
it robust to illumination and albedo variation, and it normalizes against the scene's
background covariance. It is also what the REE notebook uses. **MTMF** is a reasonable
alternative but needs an infeasibility term SPy doesn't ship. These are properties of
the algorithms, not a benchmark on Wyvern data — no such comparison has been run.

```python
import numpy as np
import spectral as sp

from spy_helpers import valid_pixels, scatter_scores

px, valid = valid_pixels(img)                      # SPy rejects NaN; see below
scores = scatter_scores(sp.ace(px, target), valid)  # higher = better match
```

An ACE score is a squared cosine in whitened background space, bounded [0, 1]. It is
**not** a probability, a confidence, or an abundance, and it is not comparable across
scenes, targets, or band counts. A max of 0.94 means "this was the best match in this
scene," which is true even when the target is absent — so a high score is never
evidence on its own.

`sp.ace` accepts a single target or a list of targets and an optional `background`
(a `GaussianStats`).

⚠️ Do **not** pass `window=` alongside the `valid_pixels` column used throughout this
file. A local window estimates background from spatial neighbours, and in an
`(N, 1, bands)` array the "neighbours" are arbitrary raster-order pixels — it does not
raise, it just returns meaningless scores. The same applies to `sp.rx(window=...)`.
Local windows need a genuine NaN-free rectangle; use stratification (below) instead.

**Matched Filter (MF)** is the classic alternative; it is *not* scale-invariant, so
brightness differences leak into scores:

```python
mf = scatter_scores(sp.matched_filter(px, target), valid)
```

**MTMF** pairs the MF score with an *infeasibility* value — real detections score high
**and** are feasible, which suppresses plain MF's false positives. SPy has no `mtmf()`,
so compute MF on MNF-reduced data and threshold on both:

```python
# MTMF is conventionally run on MNF-reduced data
# noise_from_diffs needs a real 2-D, NaN-free, homogeneous patch (not px).
from spy_helpers import find_clean_patch

patch = find_clean_patch(img)   # searches; corners of a rotated swath are NoData
mnf_result = sp.mnf(sp.calc_stats(px), sp.noise_from_diffs(patch))
reduced = mnf_result.reduce(px, num=15)
target_reduced = mnf_result.get_reduction_transform(num=15)(target)
mf_scores = scatter_scores(sp.matched_filter(reduced, target_reduced), valid)
# Then: keep pixels with high mf_scores AND low infeasibility
# (infeasibility = residual distance from the MF mixing line; ENVI computes this
#  directly. If you need exact ENVI-equivalent MTMF, use ENVI or implement the
#  infeasibility term explicitly — don't report plain MF as MTMF.)
```

If you only need one detector and want defensible results with the least machinery,
**use ACE**.

**SAM (Spectral Angle Mapper)** measures the angle between pixel and target spectra —
simple, illumination-insensitive, but no background suppression, so it underperforms
ACE in cluttered scenes. Output is in **radians, where 0 = perfect match** (lower is
better — the opposite of ACE):

```python
angles = scatter_scores(sp.spectral_angles(px, target.reshape(1, -1)), valid)
```

## Anomaly detection

**RX (Reed–Xiaoli)** finds pixels that are statistically unusual versus the scene
background, with no reference spectrum needed. Good for "show me what's interesting" —
tailings, dumping, unusual materials, algal blooms.

```python
px, valid = valid_pixels(img)
anomaly = scatter_scores(sp.rx(px), valid)   # higher = more anomalous
threshold = np.nanpercentile(anomaly, 99.9)  # top 0.1% as candidates
candidates = anomaly > threshold
```

RX flags anything unusual, including clouds, shadows, sensor artifacts, and image
edges — mask those first (the `Data Mask` / `Pixel Quality Mask` assets help) or the
top hits will be junk. A local `window` makes RX sensitive to small targets against
locally-varying background.

**Stratify mixed land/water scenes, or RX just returns the shoreline.** A single
Gaussian background cannot describe land and water together, so the largest Mahalanobis
distances land on the coastline and nothing else. Split on a water mask (NDWI, or NIR
reflectance below a threshold) and run RX within each stratum:

```python
water = ndwi > 0                                   # or nir < threshold
scores = np.full(valid.shape, np.nan)
for stratum in (water & valid, ~water & valid):
    scores[stratum] = sp.rx(img[stratum].reshape(-1, 1, img.shape[2])).ravel()
```

A raw RX surface is a ranking, not a set of detections. To get usable targets, threshold
statistically, then cluster with `scipy.ndimage.label`, discard clusters below a
sensible pixel count, and convert centroids to lon/lat with the dataset transform.
Filtering clusters by size and elongation separates real objects (vessels, structures)
from speckle.

⚠️ **Moving objects have no single spectrum.** Bands are acquired at slightly
different times, so a vessel or aircraft appears at a *different position in each
band*. At a fixed pixel this reads as a huge narrow "emission line" — the band in
which the object happened to cross that pixel — and RX scores it enormously. Check any
compact, extreme anomaly by tracking its centroid across bands: a monotonic drift means
motion (or, over high-contrast point targets, residual band co-registration), not
composition. This also silently breaks the "does the hit's mean spectrum resemble the
target?" check, since the spectrum is a spatial composite.

⚠️ **Water scenes: check the deep-water NIR floor before trusting absolute values.**
Clear deep water should be near zero at 750–800 nm. If it sits at 0.05–0.07, L2A has
left residual path radiance / glint — a large additive offset that passes the
"reflectance ∈ [0, 1]" check while making every absolute water-leaving reflectance and
water-quality index wrong. Work in contrast (differences against a local water
background), not absolutes.

## Dimensionality reduction

**MNF (Minimum Noise Fraction)** is preferred over PCA for hyperspectral data because
it orders components by signal-to-noise rather than raw variance, so the leading
components are genuinely informative. Use it to denoise before detection, or to
compress 31 bands to ~10–15 components.

```python
from spy_helpers import find_clean_patch, valid_pixels

px, valid = valid_pixels(img)
signal = sp.calc_stats(px)
# Noise needs a 2-D, NaN-free, spatially homogeneous patch (uniform water, a bare
# field). Passing px raises NaNValueError; a heterogeneous patch treats real
# spectral variation as noise and degrades everything downstream.
noise = sp.noise_from_diffs(find_clean_patch(img))
mnfr = sp.mnf(signal, noise)
denoised = scatter_scores(mnfr.denoise(px, num=10), valid)
reduced = scatter_scores(mnfr.reduce(px, num=10), valid)   # MNF space
```

The noise estimate must come from a **homogeneous** region (uniform water, bare
field). Estimating noise from a heterogeneous patch treats real spectral variation as
noise and degrades everything downstream.

**PCA** is fine for visualization (see the QGIS PCA tutorial in the knowledge centre):

```python
pc = sp.principal_components(px)
top = scatter_scores(pc.reduce(num=3).transform(px), valid)   # for an RGB composite
```

## Unmixing and endmembers

At 5 m GSD most pixels are mixtures. To estimate fractional abundance:

```python
members = sp.smacc(px, min_endmembers=5)[0]    # or sp.ppi(px, niters=1000)
abundances = scatter_scores(sp.unmix(px, members), valid)   # -> (rows, cols, k)
```

`unmix` is unconstrained least squares — abundances can fall outside [0, 1] and won't
sum to 1. Treat them as relative indicators, not physical fractions. Keep the endmember
count well below the band count.

## Continuum removal

Normalizes broad brightness/albedo shape so narrow absorption features stand out. For
mineral and REE targets this belongs **before** detection, not as an afterthought —
apply it to both the image and the reference spectrum so they're comparable.

⚠️ **Continuum removal breaks ACE unless you drop the end bands.**
`remove_continuum` pins the first and last band to exactly 1.0 (they are the hull
anchors), so those bands have zero variance, the background covariance is singular, and
`sp.ace` raises `LinAlgError: SVD did not converge`. Slice both the cube and the target
identically:

```python
from spectral import remove_continuum

cr = remove_continuum(px, cwl)                 # cwl = band centers in nm; px from above
cr_target = remove_continuum(target.reshape(1, 1, -1), cwl).ravel()

# Drop the pinned hull anchors (first/last band) from BOTH cube and target.
scores = scatter_scores(sp.ace(cr[..., 1:-1], cr_target[1:-1]), valid)
```

With only 23–31 broad VNIR bands, absorption features must be wide to survive
convolution; don't expect SWIR-style diagnostic band depths.

## Interpreting and verifying results

Detection scores are **relative to the scene** — never report an absolute threshold as
if it were physically meaningful. Concretely:

1. **Threshold statistically** (e.g. `nanpercentile(scores, 99.9)`), and state the
   threshold and how many pixels passed.
2. **Sanity-check the hits**: plot the mean spectrum of detected pixels against the
   target. If shapes disagree, it's a false positive regardless of score.
3. **Verify with a second method** — ACE plus RX, or ACE plus a relevant index.
   Agreement is much stronger evidence than one detector's ranking.
4. **Rule out artifacts** — clouds, shadows, water glint, scene edges, and NoData
   fringes drive most spurious detections. Confirm hits fall inside valid data.
   In coastal scenes the dominant false positive is **land–water mixing along the
   shoreline**, which manufactures convincing spectral slopes: erode the land mask a
   few pixels and re-test on interior pixels only. If the hits vanish, they were
   mixtures. Confirm by fitting a two-endmember (land + water) mixture — if that
   explains the spectrum better than your target does, it isn't your target.
5. **Run a null control.** Repeat the identical pipeline with a target you know is
   undetectable (a SWIR-only mineral such as kaolinite). If it scores comparably to
   your real target, the pipeline is ranking brightness and covariance, not
   composition — the strongest single check available, and cheap.
6. **Report uncertainty honestly**: state the product type and band count used,
   whether the target came from a lab library or the scene, and whether the
   material's diagnostic wavelengths are inside **this product type's** range
   (Standard 503–799 nm, Extended 445–869 nm). If they aren't, the result is not
   evidence of that material.
7. **Nothing found is a valid answer.** Say the target wasn't detected rather than
   lowering the threshold until something appears.
