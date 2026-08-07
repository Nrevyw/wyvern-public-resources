# Wyvern Dragonette Band Reference

Nominal center wavelengths (CWL) and full-width-half-max (FWHM) for both band
configurations. Band numbers are **1-based** (as used by GDAL/rasterio `read(n)` and
the index library's `band_index`).

These tables are nominal design values — per-scene values in the STAC item's
`eo:bands` differ slightly (e.g. a nominal 870 nm band may report 869 nm) and are
authoritative. Use `scripts/wyvern_stac.py bands <ITEM_URL> <nm>` to resolve against
a real scene.

The index library JSON (https://knowledge.wyvern.space/hyperspectral-index-library.json)
keys its `band_mappings` by product type: `"Standard VNIR"` and `"Extended VNIR"`.

## Standard VNIR — Dragonette-1 (23 bands, 503–799 nm)

| Band | CWL (nm) | FWHM (nm) |
| ---: | ---: | ---: |
| 1 | 503 | 20.1 |
| 2 | 510 | 20.4 |
| 3 | 519 | 20.8 |
| 4 | 535 | 21.4 |
| 5 | 549 | 22.0 |
| 6 | 570 | 22.8 |
| 7 | 584 | 23.4 |
| 8 | 600 | 24.0 |
| 9 | 614 | 24.6 |
| 10 | 635 | 25.4 |
| 11 | 649 | 26.0 |
| 12 | 660 | 26.4 |
| 13 | 669 | 26.8 |
| 14 | 679 | 27.2 |
| 15 | 690 | 27.6 |
| 16 | 699 | 28.0 |
| 17 | 711 | 28.4 |
| 18 | 722 | 28.9 |
| 19 | 734 | 29.4 |
| 20 | 750 | 30.0 |
| 21 | 764 | 30.6 |
| 22 | 782 | 31.3 |
| 23 | 799 | 32.0 |

## Extended VNIR — Dragonette-2/3/4 (31 bands, 445–870 nm)

| Band | CWL (nm) | FWHM (nm) |
| ---: | ---: | ---: |
| 1 | 445 | 15.6 |
| 2 | 465 | 16.3 |
| 3 | 480 | 16.8 |
| 4 | 490 | 17.2 |
| 5 | 503 | 17.6 |
| 6 | 510 | 17.9 |
| 7 | 520 | 18.2 |
| 8 | 535 | 18.7 |
| 9 | 550 | 19.3 |
| 10 | 570 | 20.0 |
| 11 | 585 | 20.5 |
| 12 | 600 | 21.0 |
| 13 | 615 | 21.5 |
| 14 | 635 | 22.2 |
| 15 | 650 | 22.8 |
| 16 | 660 | 23.1 |
| 17 | 670 | 23.5 |
| 18 | 680 | 23.8 |
| 19 | 690 | 24.2 |
| 20 | 700 | 24.5 |
| 21 | 712 | 24.9 |
| 22 | 722 | 25.3 |
| 23 | 735 | 25.7 |
| 24 | 750 | 26.3 |
| 25 | 765 | 26.8 |
| 26 | 782 | 27.4 |
| 27 | 800 | 28.0 |
| 28 | 815 | 28.5 |
| 29 | 832 | 29.1 |
| 30 | 850 | 29.8 |
| 31 | 870 | 30.5 |

## Common wavelength → band quick reference

| Use | Wavelength | Standard VNIR band | Extended VNIR band |
| --- | --- | ---: | ---: |
| Blue (coastal) | 445–490 nm | — (not covered) | 1–4 |
| Green | 550 nm | 5 (549) | 9 (550) |
| Red | 660 nm | 12 (660) | 16 (660) |
| Red edge | 712 nm | 17 (711) | 21 (712) |
| Red edge | 750 nm | 20 (750) | 24 (750) |
| NIR | 800 nm | 23 (799) | 27 (800) |
| NIR (upper) | 870 nm | — (not covered) | 31 (870) |

Full measured relative spectral response curves per satellite:
[`relative-spectral-responses/`](https://github.com/Nrevyw/wyvern-public-resources/tree/main/relative-spectral-responses) in this repo.
