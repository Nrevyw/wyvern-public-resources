#!/usr/bin/env python3
"""Run Spectral Python (SPy) algorithms on cubes that contain NoData.

SPy's `ace`, `rx`, `mnf`, `calc_stats` and friends raise `NaNValueError` when any
pixel is NaN. Wyvern scenes are rotated swaths stored in a north-up grid, so a real
cube always has a NoData fringe — often a third of the raster — and masking NoData to
NaN is exactly what the loading step produces.

The fix is to hand SPy only the valid pixels, shaped as a degenerate (N, 1, bands)
image, then scatter the per-pixel results back onto the raster grid. Results are
numerically identical to running on a NaN-free rectangle.

    from spy_helpers import valid_pixels, scatter_scores

    px, valid = valid_pixels(img)
    scores = scatter_scores(sp.ace(px, target), valid)

Requires: numpy.
"""

from __future__ import annotations

import numpy as np


def valid_pixels(img: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Extract finite pixels from a cube as an SPy-safe image.

    Args:
        img: Cube shaped (rows, cols, bands), typically with NaN where NoData was
            masked.

    Returns:
        A tuple of (pixels, valid) where pixels is shaped (N, 1, bands) — the
        degenerate image layout SPy accepts — and valid is the (rows, cols) boolean
        mask identifying which pixels were kept.

    Raises:
        ValueError: If the cube has no fully finite pixels, which usually means the
            window landed entirely on NoData.
    """
    valid = np.isfinite(img).all(axis=2)
    if not valid.any():
        raise ValueError(
            "no valid pixels in this cube — the window may be entirely NoData"
        )
    return img[valid].reshape(-1, 1, img.shape[2]), valid


def scatter_scores(scores: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Place per-pixel results back onto the raster grid.

    Args:
        scores: Output of an SPy call on the (N, 1, bands) image. Trailing
            singleton dimensions are squeezed, so both (N, 1) score maps and
            (N, 1, k) multi-band outputs are accepted.
        valid: The boolean mask returned by `valid_pixels`.

    Returns:
        An array shaped like `valid` (or (rows, cols, k) for multi-band results),
        with NaN wherever the input pixel was NoData.
    """
    scores = np.asarray(scores)
    flat = scores.reshape(scores.shape[0], -1)
    if flat.shape[1] == 1:
        out = np.full(valid.shape, np.nan)
        out[valid] = flat[:, 0]
        return out
    out = np.full((*valid.shape, flat.shape[1]), np.nan)
    out[valid] = flat
    return out
