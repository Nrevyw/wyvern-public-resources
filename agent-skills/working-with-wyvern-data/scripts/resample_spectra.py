#!/usr/bin/env python3
"""Resample a high-resolution reference spectrum onto Wyvern band centers.

Lab spectra (USGS, ECOSTRESS, EcoSIS via OpenSpecLib) are measured at 1-10 nm
resolution. Comparing them to Wyvern's ~16-32 nm bands requires convolving with each
band's spectral response, otherwise narrow absorption features are over-weighted and
detection scores are wrong.

This module is importable (use `resample()` / `load_wyvern_bands()`) and also runs as
a CLI for a quick check:

    python resample_spectra.py --item-url <STAC_ITEM_URL> --csv spectrum.csv
    python resample_spectra.py --config extended --csv spectrum.csv --out target.csv

The CSV needs two columns: wavelength and reflectance. Wavelengths in µm are detected
automatically (max < 100) and converted to nm.

Requires: numpy.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.request
from typing import Any, Optional

import numpy as np

# Nominal (center wavelength, FWHM) pairs in nm, in band order. Pairing them keeps
# the two values structurally inseparable, so a table edit cannot silently
# desynchronise centers from widths. Per-scene values from a STAC item's eo:bands or
# the GeoTIFF's own band tags are authoritative — use --item-url for a real scene.
WYVERN_BANDS: dict[str, list[tuple[float, float]]] = {
    # Dragonette-1: 23 bands, ~503-799 nm
    "standard": [
        (503, 20.1),
        (510, 20.4),
        (519, 20.8),
        (535, 21.4),
        (549, 22.0),
        (570, 22.8),
        (584, 23.4),
        (600, 24.0),
        (614, 24.6),
        (635, 25.4),
        (649, 26.0),
        (660, 26.4),
        (669, 26.8),
        (679, 27.2),
        (690, 27.6),
        (699, 28.0),
        (711, 28.4),
        (722, 28.9),
        (734, 29.4),
        (750, 30.0),
        (764, 30.6),
        (782, 31.3),
        (799, 32.0),
    ],
    # Dragonette-2/3/4: 31 bands, ~445-870 nm
    "extended": [
        (445, 15.6),
        (465, 16.3),
        (480, 16.8),
        (490, 17.2),
        (503, 17.6),
        (510, 17.9),
        (520, 18.2),
        (535, 18.7),
        (550, 19.3),
        (570, 20.0),
        (585, 20.5),
        (600, 21.0),
        (615, 21.5),
        (635, 22.2),
        (650, 22.8),
        (660, 23.1),
        (670, 23.5),
        (680, 23.8),
        (690, 24.2),
        (700, 24.5),
        (712, 24.9),
        (722, 25.3),
        (735, 25.7),
        (750, 26.3),
        (765, 26.8),
        (782, 27.4),
        (800, 28.0),
        (815, 28.5),
        (832, 29.1),
        (850, 29.8),
        (870, 30.5),
    ],
}

# Converts a Gaussian FWHM to its standard deviation: 2*sqrt(2*ln(2)).
FWHM_TO_SIGMA = 2.3548200450309493
# Wavelength arrays with a maximum below this are assumed to be in µm, not nm.
MICRON_THRESHOLD = 100.0
# Integration half-width, in sigmas, around each band center.
INTEGRATION_SIGMAS = 3.0
# The imagery CDN rejects Python-urllib's default User-Agent, so send an explicit one.
USER_AGENT = "wyvern-agent-skill/1.0"
REQUEST_TIMEOUT_SECONDS = 30
COG_ASSET_KEY = "Cloud optimized GeoTiff"


def load_wyvern_bands(
    config: Optional[str] = None, item_url: Optional[str] = None
) -> tuple[np.ndarray, np.ndarray]:
    """Load Wyvern band centers and widths, preferring a real scene's metadata.

    Args:
        config: One of the keys in `WYVERN_BANDS` (`"standard"` or `"extended"`),
            used when `item_url` is not supplied.
        item_url: A STAC item URL. When given, the exact per-scene band metadata is
            read from the item's `eo:bands` and takes precedence over `config`.

    Returns:
        A tuple of (center wavelengths, FWHM values), both in nanometres.

    Raises:
        ValueError: If neither `item_url` nor a valid `config` is provided.
    """
    if item_url:
        request = urllib.request.Request(item_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            item: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        bands = item["assets"][COG_ASSET_KEY]["eo:bands"]
        # eo:bands wavelengths are in µm.
        cwl = np.array([band["center_wavelength"] * 1000 for band in bands], float)
        fwhm = np.array([band["full_width_half_max"] * 1000 for band in bands], float)
        return cwl, fwhm
    if config not in WYVERN_BANDS:
        raise ValueError(f"config must be one of {list(WYVERN_BANDS)}, got {config!r}")
    table = np.array(WYVERN_BANDS[config], float)
    return table[:, 0], table[:, 1]


def resample(
    wavelengths_nm: np.ndarray,
    reflectance: np.ndarray,
    cwl_nm: np.ndarray,
    fwhm_nm: np.ndarray,
) -> np.ndarray:
    """Convolve a spectrum onto sensor bands using per-band Gaussian responses.

    Each band's response is approximated by a Gaussian of the given FWHM. Non-finite
    and negative reflectances (lab fill values, commonly -1.23e34) are excluded.

    Args:
        wavelengths_nm: Reference spectrum wavelengths in nanometres.
        reflectance: Reference reflectance at those wavelengths.
        cwl_nm: Sensor band center wavelengths in nanometres.
        fwhm_nm: Sensor band FWHM values in nanometres.

    Returns:
        One reflectance value per band. Bands with no valid source samples within
        `INTEGRATION_SIGMAS` are NaN rather than a fabricated value, so coverage
        gaps stay visible instead of silently biasing detection scores.

    Raises:
        ValueError: If the input spectrum contains no valid samples.
    """
    wavelengths_nm = np.asarray(wavelengths_nm, float)
    reflectance = np.asarray(reflectance, float)
    valid = np.isfinite(reflectance) & (reflectance >= 0) & np.isfinite(wavelengths_nm)
    if not valid.any():
        raise ValueError("no valid reflectance samples in input spectrum")

    out = np.full(len(cwl_nm), np.nan)
    sigma = np.asarray(fwhm_nm, float) / FWHM_TO_SIGMA
    for index, (center, sig) in enumerate(zip(cwl_nm, sigma)):
        in_range = valid & (np.abs(wavelengths_nm - center) <= INTEGRATION_SIGMAS * sig)
        if not in_range.any():
            continue
        weights = np.exp(-0.5 * ((wavelengths_nm[in_range] - center) / sig) ** 2)
        total = weights.sum()
        if total > 0:
            out[index] = float((weights * reflectance[in_range]).sum() / total)
    return out


def read_csv_spectrum(path: str) -> tuple[np.ndarray, np.ndarray]:
    """Read a two-column (wavelength, reflectance) CSV.

    Header and comment rows are skipped by attempting a float conversion and
    ignoring rows that fail.

    Args:
        path: Path to the CSV file.

    Returns:
        A tuple of (wavelengths in nanometres, reflectance). Wavelengths are
        converted from µm when the maximum value is below `MICRON_THRESHOLD`.

    Raises:
        SystemExit: If the file contains no numeric rows. This is a CLI tool, so a
            readable message beats a traceback.
    """
    wavelengths: list[float] = []
    reflectance: list[float] = []
    with open(path, newline="") as handle:
        for row in csv.reader(handle):
            if len(row) < 2:
                continue
            try:
                wavelengths.append(float(row[0]))
                reflectance.append(float(row[1]))
            except ValueError:
                continue  # header or comment line
    if not wavelengths:
        sys.exit(f"error: no numeric wavelength/reflectance rows found in {path}")
    wavelengths_nm = np.array(wavelengths, float)
    if wavelengths_nm.max() < MICRON_THRESHOLD:  # µm -> nm
        wavelengths_nm *= 1000.0
    return wavelengths_nm, np.array(reflectance, float)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv", required=True, help="two-column wavelength,reflectance CSV"
    )
    # No default: silently resampling onto the wrong product type yields a target
    # with the wrong band count, which only surfaces later as an opaque shape error.
    parser.add_argument(
        "--config",
        choices=sorted(WYVERN_BANDS),
        help="nominal band set to use when --item-url is not given",
    )
    parser.add_argument(
        "--item-url", help="STAC item URL (uses that scene's exact bands; preferred)"
    )
    parser.add_argument("--out", help="write resampled band values to this CSV")
    return parser


def main() -> None:
    """Resample a CSV spectrum onto Wyvern bands and report the result."""
    parser = build_parser()
    args = parser.parse_args()
    if not args.item_url and not args.config:
        parser.error(
            "specify --item-url (preferred: uses the scene's exact bands) or "
            "--config {standard|extended}. Standard VNIR has 23 bands and Extended "
            "has 31, so guessing produces a target of the wrong length."
        )

    wavelengths_nm, reflectance = read_csv_spectrum(args.csv)
    cwl, fwhm = load_wyvern_bands(config=args.config, item_url=args.item_url)
    resampled = resample(wavelengths_nm, reflectance, cwl, fwhm)

    rows = [
        {
            "band": index + 1,
            "cwl_nm": float(center),
            "reflectance": None if np.isnan(value) else round(float(value), 6),
        }
        for index, (center, value) in enumerate(zip(cwl, resampled))
    ]
    if args.out:
        with open(args.out, "w", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["band", "cwl_nm", "reflectance"]
            )
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(json.dumps(rows, indent=2))

    missing = int(np.isnan(resampled).sum())
    if missing:
        print(
            f"warning: {missing} of {len(cwl)} bands had no source samples (NaN) — "
            "the reference spectrum may not cover Wyvern's full VNIR range",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
