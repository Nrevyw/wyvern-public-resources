#!/usr/bin/env python3
"""Discover Wyvern Open Data scenes and resolve spectral bands.

Standard-library only (urllib + json) so it runs anywhere Python 3.9+ does — no pip
installs needed for discovery. Raster analysis itself needs rasterio, but you can
search the catalog and plan band math with this script alone.

Usage:
    python wyvern_stac.py search [--product-type standard|extended]
                                 [--max-cloud PCT] [--bbox W,S,E,N] [--limit N]
    python wyvern_stac.py show ITEM_URL
    python wyvern_stac.py bands ITEM_URL WAVELENGTH_NM [WAVELENGTH_NM ...]

Examples:
    python wyvern_stac.py search --product-type extended --max-cloud 10
    python wyvern_stac.py bands https://wyvern-odp.com/.../item.json 660 800
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from typing import Any, Iterator, Optional

CATALOG_ROOT = "https://wyvern-odp.com/catalog.json"
# The open-data catalog groups items under product-type collections.
PRODUCT_TYPE_COLLECTION = (
    "https://wyvern-odp.com/product-type/{product_type}/collection.json"
)
PRODUCT_TYPES = ("standard", "extended")
# Asset key for the imagery COG in Wyvern STAC items (note: contains spaces).
COG_ASSET_KEY = "Cloud optimized GeoTiff"
# The CDN in front of wyvern-odp.com returns 403 for Python-urllib's default
# User-Agent, so every request sends an explicit one (any non-default value works).
USER_AGENT = "wyvern-agent-skill/1.0"
REQUEST_TIMEOUT_SECONDS = 30


def fetch_json(url: str) -> dict[str, Any]:
    """Fetch a URL and parse the response as JSON.

    Args:
        url: The URL to fetch.

    Returns:
        The parsed JSON response.

    Raises:
        SystemExit: If the request fails or the response is not valid JSON. This is
            a CLI tool, so a readable message beats a traceback.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - single choke point for network errors
        sys.exit(f"error: could not fetch {url}: {exc}")


def iter_items(
    product_type: Optional[str] = None,
) -> Iterator[tuple[dict[str, Any], str]]:
    """Yield every STAC item in the open-data catalog.

    The catalog is small (dozens of scenes), so walking item links directly is
    simpler and more robust than requiring a STAC API client.

    Args:
        product_type: Restrict to one of `PRODUCT_TYPES`. Both are walked when
            omitted.

    Yields:
        A tuple of the parsed STAC item and the URL it was fetched from.
    """
    types = [product_type] if product_type else list(PRODUCT_TYPES)
    for ptype in types:
        collection = fetch_json(PRODUCT_TYPE_COLLECTION.format(product_type=ptype))
        for link in collection.get("links", []):
            if link.get("rel") == "item":
                yield fetch_json(link["href"]), link["href"]


def bbox_intersects(
    item_bbox: list[float], query_bbox: tuple[float, float, float, float]
) -> bool:
    """Check whether two bounding boxes overlap.

    Args:
        item_bbox: The STAC item bbox as `[west, south, east, north]`. Extra
            elements (3D bboxes carry elevation) are ignored.
        query_bbox: The query bbox as `(west, south, east, north)`.

    Returns:
        True if the boxes overlap.
    """
    west, south, east, north = query_bbox
    item_west, item_south, item_east, item_north = item_bbox[:4]
    return not (
        item_east < west or item_west > east or item_north < south or item_south > north
    )


def item_summary(item: dict[str, Any], url: str = "") -> dict[str, Any]:
    """Extract the fields most useful for choosing a scene.

    Args:
        item: A parsed STAC item.
        url: The URL the item came from, echoed back for convenience.

    Returns:
        A flat dict of scene properties, including the imagery COG's dtype,
        nodata, and scale, which are needed to load the pixels correctly.
    """
    props = item.get("properties", {})
    cog = item.get("assets", {}).get(COG_ASSET_KEY, {})
    bands = cog.get("eo:bands", [])
    raster = (cog.get("raster:bands") or [{}])[0]
    return {
        "id": item.get("id"),
        "url": url,
        "datetime": props.get("datetime") or props.get("start_datetime"),
        "platform": props.get("platform"),
        "product_type": props.get("product_type"),
        "processing_level": props.get("processing:level"),
        "epsg": props.get("proj:epsg"),
        "gsd_m": props.get("gsd"),
        "cloud_cover_pct": props.get("eo:cloud_cover"),
        "band_count": len(bands),
        "dtype": raster.get("data_type"),
        "nodata": raster.get("nodata"),
        "scale": raster.get("scale"),
        "cog_href": cog.get("href"),
        "bbox": item.get("bbox"),
    }


def resolve_band(item: dict[str, Any], target_nm: float) -> dict[str, Any]:
    """Find the band whose center wavelength is nearest a target wavelength.

    Uses the item's own `eo:bands` metadata, which is authoritative per scene —
    band counts and exact wavelengths differ between the standard and extended
    product types.

    Args:
        item: A parsed STAC item.
        target_nm: The desired wavelength in nanometres.

    Returns:
        A dict describing the nearest band: its 1-based `band_number` (matching
        GDAL/rasterio band numbering), `name`, `center_nm`, `fwhm_nm`, and
        `distance_nm` from the target. A `warning` key is added when the
        nearest center is more than one FWHM away, which usually means the sensor
        does not cover that wavelength.
    """
    bands = item["assets"][COG_ASSET_KEY]["eo:bands"]
    best: dict[str, Any] = {}
    for index, band in enumerate(bands, start=1):  # rasterio band numbers are 1-based
        cwl_nm = band["center_wavelength"] * 1000.0  # eo:bands wavelengths are in µm
        fwhm_nm = band.get("full_width_half_max", 0) * 1000.0
        distance_nm = abs(cwl_nm - target_nm)
        if not best or distance_nm < best["distance_nm"]:
            best = {
                "band_number": index,
                "name": band.get("name"),
                "center_nm": round(cwl_nm, 1),
                "fwhm_nm": round(fwhm_nm, 1),
                "distance_nm": round(distance_nm, 1),
            }
    if best and best["fwhm_nm"] and best["distance_nm"] > best["fwhm_nm"]:
        best["warning"] = (
            f"nearest band center is {best['distance_nm']}nm from the requested "
            f"{target_nm}nm (more than one FWHM) — this scene may not cover that "
            "wavelength"
        )
    return best


def cmd_search(args: argparse.Namespace) -> None:
    """Print scenes matching the given filters as JSON.

    Args:
        args: Parsed CLI arguments for the `search` subcommand.
    """
    query_bbox = (
        tuple(float(value) for value in args.bbox.split(",")) if args.bbox else None
    )
    results: list[dict[str, Any]] = []
    for item, url in iter_items(args.product_type):
        summary = item_summary(item, url)
        if (
            args.max_cloud is not None
            and (summary["cloud_cover_pct"] or 0) > args.max_cloud
        ):
            continue
        if (
            query_bbox
            and item.get("bbox")
            and not bbox_intersects(item["bbox"], query_bbox)
        ):
            continue
        results.append(summary)
        if args.limit and len(results) >= args.limit:
            break
    print(json.dumps(results, indent=2))
    print(f"\n{len(results)} scene(s) matched", file=sys.stderr)


def cmd_show(args: argparse.Namespace) -> None:
    """Print a summary of a single STAC item as JSON.

    Args:
        args: Parsed CLI arguments for the `show` subcommand.
    """
    item = fetch_json(args.item_url)
    print(json.dumps(item_summary(item, args.item_url), indent=2))


def cmd_bands(args: argparse.Namespace) -> None:
    """Print the nearest band for each requested wavelength as JSON.

    Args:
        args: Parsed CLI arguments for the `bands` subcommand.
    """
    item = fetch_json(args.item_url)
    resolved = {str(nm): resolve_band(item, nm) for nm in args.wavelengths}
    print(json.dumps(resolved, indent=2))


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        The configured parser, with one subcommand per operation.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="list open-data scenes with filters")
    search.add_argument("--product-type", choices=PRODUCT_TYPES)
    search.add_argument("--max-cloud", type=float, help="max cloud cover percent")
    search.add_argument("--bbox", help="W,S,E,N in lon/lat")
    search.add_argument("--limit", type=int)
    search.set_defaults(func=cmd_search)

    show = subparsers.add_parser("show", help="summarize one STAC item")
    show.add_argument("item_url")
    show.set_defaults(func=cmd_show)

    bands = subparsers.add_parser("bands", help="resolve wavelengths to band numbers")
    bands.add_argument("item_url")
    bands.add_argument("wavelengths", nargs="+", type=float, metavar="WAVELENGTH_NM")
    bands.set_defaults(func=cmd_bands)

    return parser


def main() -> None:
    """Parse arguments and dispatch to the selected subcommand."""
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
