"""
OpenStreetMap from a local extract instead of Overpass (added 26 Sep 2026 for Frondia, map_project).

Overpass refused both the cloud sandbox and the Mac on 26 Sep 2026, so the engine can read the same
features and the same walking network from a Geofabrik PBF. Switched on by `--pbf <path>` in
`engine.run` (or the PLANNER_PBF env var); without it nothing changes and every call goes to Overpass.

How it stays the same as the Overpass path:
  - features: osmium cuts the city's box (+1 km, `smart` strategy so multipolygons crossing the edge
    stay whole) and keeps every object carrying any key=value that ASSETS asks for, as OSM XML. OSMnx's
    `features_from_xml` then builds the GeoDataFrame through the same `_create_gdf` that
    `features_from_polygon` uses on Overpass JSON: same tag matching, same node/way/relation geometry,
    same filter to the polygon.
  - walking network: osmium keeps the highways of the box, OSMnx builds the graph with its own `walk`
    filter and `graph_from_polygon`'s order (truncate to the +500 m polygon, largest component,
    simplify, truncate to the polygon, largest component), as Fit Score's `04_graph.py --pbf` does.
The city boundary still comes from Nominatim (`geocode_to_gdf`).
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

import geopandas as gpd
import osmnx as ox

_REPO_ROOT = Path(__file__).parent.parent
_CUT_DIR = _REPO_ROOT / "cache" / "pbf"

PBF: Path | None = Path(os.environ["PLANNER_PBF"]) if os.environ.get("PLANNER_PBF") else None


def use(pbf: str | Path | None) -> None:
    """Switch the engine to a local extract (None: back to Overpass)."""
    global PBF
    PBF = Path(pbf).absolute() if pbf else None   # not resolve(): a dated symlink names the caches
    if PBF is not None and not PBF.exists():
        raise FileNotFoundError(PBF)


def describe() -> dict:
    """Where this run's OSM came from, for report.json and the Frondia manifest (added 27 Sep 2026)."""
    from datetime import date
    if PBF is None:
        return {"overpass": ox.settings.overpass_url, "fetched": date.today().isoformat()}
    ts = subprocess.run(["osmium", "fileinfo", "-g", "header.option.osmosis_replication_timestamp", str(PBF)],
                        capture_output=True, text=True).stdout.strip() or None
    return {"file": PBF.name, "osm_timestamp": ts}


def _bbox(poly, pad_deg: float = 0.015) -> str:
    x0, y0, x1, y1 = poly.bounds
    return f"{x0 - pad_deg:.6f},{y0 - pad_deg:.6f},{x1 + pad_deg:.6f},{y1 + pad_deg:.6f}"


def _cut(city_key: str, poly) -> Path:
    """The city's box cut from the extract once, reused by every kind."""
    _CUT_DIR.mkdir(parents=True, exist_ok=True)
    out = _CUT_DIR / f"{city_key}_{PBF.stem}.osm.pbf"
    if not out.exists():
        print(f"  osmium: cutting {city_key} ({_bbox(poly)}) from {PBF.name}")
        subprocess.run(["osmium", "extract", "-b", _bbox(poly), "-s", "smart", str(PBF),
                        "-o", str(out), "--overwrite"], check=True)
    return out


def _filter_expressions() -> list[str]:
    """Every key=value any kind asks for, as assets or as demand POIs, one osmium expression per key."""
    from .config import ASSETS
    wanted: dict[str, set[str]] = {}
    for cfg in ASSETS.values():
        for tags in (cfg["osm_tags"], cfg["demand_pois"]):
            for key, vals in tags.items():
                if vals is True:
                    raise ValueError(f"PBF mode expects key=value tags, got {key}=True")
                wanted.setdefault(key, set()).update([vals] if isinstance(vals, str) else vals)
    return [f"nwr/{k}={','.join(sorted(v))}" for k, v in sorted(wanted.items())]


def _features_xml(city_key: str, poly) -> Path:
    exprs = _filter_expressions()
    tag_hash = hashlib.sha1("|".join(exprs).encode()).hexdigest()[:8]
    out = _CUT_DIR / f"{city_key}_{PBF.stem}_features_{tag_hash}.osm"
    if not out.exists():
        subprocess.run(["osmium", "tags-filter", str(_cut(city_key, poly)), *exprs,
                        "-o", str(out), "--overwrite"], check=True)
    return out


def features(city_key: str, poly, tags: dict) -> gpd.GeoDataFrame:
    """`ox.features_from_polygon(poly, tags=tags)`, read from the extract."""
    return ox.features_from_xml(_features_xml(city_key, poly), polygon=poly, tags=tags)


def walk_graph(city_key: str, poly):
    """`ox.graph_from_polygon(poly, network_type="walk", retain_all=False)`, built from the extract."""
    from osmnx import _overpass, projection, simplification, truncate

    poly_proj, crs_utm = projection.project_geometry(poly)
    poly_buff, _ = projection.project_geometry(poly_proj.buffer(500), crs=crs_utm, to_latlong=True)

    osm_xml = _CUT_DIR / f"{city_key}_{PBF.stem}_highways.osm"
    if not osm_xml.exists():
        subprocess.run(["osmium", "tags-filter", str(_cut(city_key, poly)), "w/highway",
                        "-o", str(osm_xml), "--overwrite"], check=True)

    # osmnx's walk filter, e.g. ["highway"]["foot"!~"no"]: every clause but the first is a key that must not match
    clauses = re.findall(r'\["([^"]+)"!~"([^"]+)"\]', _overpass._get_network_filter("walk"))
    extra = [k for k, _ in clauses if k not in ox.settings.useful_tags_way]
    saved = list(ox.settings.useful_tags_way)
    ox.settings.useful_tags_way = saved + extra
    try:
        G = ox.graph_from_xml(osm_xml, bidirectional=True, simplify=False, retain_all=True)
    finally:
        ox.settings.useful_tags_way = saved
    drop = [(u, v, k) for u, v, k, d in G.edges(keys=True, data=True)
            if any(re.search(pat, str(d[key])) for key, pat in clauses if key in d)]
    G.remove_edges_from(drop)
    print(f"  walk filter dropped {len(drop):,} of {len(drop) + G.number_of_edges():,} directed edges")
    for _, _, d in G.edges(data=True):
        for key in extra:
            d.pop(key, None)

    G = truncate.truncate_graph_polygon(G, poly_buff)
    G = truncate.largest_component(G, strongly=False)
    G = simplification.simplify_graph(G)
    G = truncate.truncate_graph_polygon(G, poly)
    return truncate.largest_component(G, strongly=False)
