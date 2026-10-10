"""
Build the OSMnx walking graph for Brussels + 2 km buffer.
Adds travel_time (default adult 1.33 m/s) and travel_time_senior (1.0 m/s) to every edge.

Output:
  data/processed/brussels_walk.graphml   (~50-150 MB, reusable)
  data/processed/graph_stats.json

Run:
  cd backend/pipeline
  python 04_graph.py

Notes:
  - First run queries Overpass API (~2-5 min); cached in data/raw/osmnx_cache/.
  - Requires sectors.geojson from step 02.
  - The +2 km buffer reduces edge effects when scoring border sectors.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import osmnx as ox
import pyproj
from shapely.ops import transform

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    CITY_CONFIG, CRS_LAMBERT, CRS_WGS84, DATA_PROCESSED, DATA_RAW,
    WALK_SPEED_DEFAULT, WALK_SPEED_SENIOR,
)

import argparse as _ap
_p = _ap.ArgumentParser(); _p.add_argument("--city", default="brussels", choices=list(CITY_CONFIG))
# added 26 Sep 2026 for Frondia: build the network from a local OSM extract instead of Overpass
# (e.g. --pbf data/raw/belgium-latest.osm.pbf), for when Overpass refuses the connection
_p.add_argument("--pbf", type=Path, default=None)
_args = _p.parse_known_args()[0]
CITY = _args.city
PBF = _args.pbf

if CITY == "brussels":
    SECTORS_PATH = DATA_PROCESSED / "sectors.geojson"
    GRAPH_PATH   = DATA_PROCESSED / "brussels_walk.graphml"
    STATS_PATH   = DATA_PROCESSED / "graph_stats.json"
else:
    _city_dir    = DATA_PROCESSED / CITY
    SECTORS_PATH = _city_dir / "sectors.geojson"
    GRAPH_PATH   = _city_dir / f"{CITY}_walk.graphml"
    STATS_PATH   = _city_dir / "graph_stats.json"


def build_brussels_polygon(buffer_m: float = 2000.0):
    """
    Load sector boundaries → union → buffer in Lambert (metres) → WGS84.
    Returns a Shapely polygon suitable for osmnx.graph_from_polygon().
    """
    if not SECTORS_PATH.exists():
        raise FileNotFoundError(
            f"{SECTORS_PATH} not found.\n"
            "Run: python 02_sectors.py first."
        )

    print("  Loading sector boundaries …")
    sectors = gpd.read_file(SECTORS_PATH).to_crs(CRS_LAMBERT)

    # geopandas ≥1.0: union_all(); older: unary_union
    try:
        brussels = sectors.union_all()
    except AttributeError:
        brussels = sectors.unary_union

    # Buffer 2 km in projected metres
    brussels_buffered = brussels.buffer(buffer_m)
    print(f"  Brussels polygon buffered +{buffer_m:.0f} m")

    # Project to WGS84 for osmnx
    proj = pyproj.Transformer.from_crs(CRS_LAMBERT, CRS_WGS84, always_xy=True)
    return transform(proj.transform, brussels_buffered)


def graph_from_pbf(polygon_wgs84, pbf: Path):
    """
    The same walking graph graph_from_polygon(network_type="walk") builds, read from a local PBF:
    osmium cuts the highways of the polygon's box (+500 m, as osmnx buffers) to OSM XML, osmnx's own
    walk filter is applied to the ways, then osmnx's order: truncate to the buffered polygon, largest
    component, simplify, truncate to the polygon, largest component.
    """
    import re
    import subprocess

    from osmnx import _overpass, projection, simplification, truncate

    poly_proj, crs_utm = projection.project_geometry(polygon_wgs84)
    poly_buff, _ = projection.project_geometry(poly_proj.buffer(500), crs=crs_utm, to_latlong=True)

    cut_pbf = DATA_RAW / f"{CITY}_walk_cut.osm.pbf"
    osm_xml = DATA_RAW / f"{CITY}_walk_highways.osm"
    bbox = ",".join(f"{v:.6f}" for v in poly_buff.bounds)
    print(f"  osmium: {pbf.name} → box {bbox} → highways → {osm_xml.name}")
    subprocess.run(["osmium", "extract", "-b", bbox, "-s", "complete_ways", str(pbf),
                    "-o", str(cut_pbf), "--overwrite"], check=True)
    subprocess.run(["osmium", "tags-filter", str(cut_pbf), "w/highway",
                    "-o", str(osm_xml), "--overwrite"], check=True)

    # osmnx's walk filter, e.g. ["highway"]["foot"!~"no"]: every clause but the first is a key that must not match
    walk_filter = _overpass._get_network_filter("walk")
    clauses = re.findall(r'\["([^"]+)"!~"([^"]+)"\]', walk_filter)
    extra_tags = [k for k, _ in clauses if k not in ox.settings.useful_tags_way]
    ox.settings.useful_tags_way = list(ox.settings.useful_tags_way) + extra_tags

    G = ox.graph_from_xml(osm_xml, bidirectional=True, simplify=False, retain_all=True)
    drop = [(u, v, k) for u, v, k, d in G.edges(keys=True, data=True)
            if any(re.search(pat, str(d[key])) for key, pat in clauses if key in d)]
    G.remove_edges_from(drop)
    print(f"  walk filter dropped {len(drop):,} of {len(drop) + G.number_of_edges():,} directed edges")
    for _, _, d in G.edges(data=True):
        for key in extra_tags:
            d.pop(key, None)

    G = truncate.truncate_graph_polygon(G, poly_buff)
    G = truncate.largest_component(G, strongly=False)
    G = simplification.simplify_graph(G)
    G = truncate.truncate_graph_polygon(G, polygon_wgs84)
    G = truncate.largest_component(G, strongly=False)
    return G


def main() -> None:
    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)

    if GRAPH_PATH.exists():
        print(f"  ✓ {GRAPH_PATH.name} already exists — delete to regenerate")
        if STATS_PATH.exists():
            stats = json.loads(STATS_PATH.read_text())
            print(f"  Nodes: {stats.get('nodes', '?'):,}  Edges: {stats.get('edges', '?'):,}")
        return

    # Configure osmnx caching
    cache_dir = DATA_RAW / "osmnx_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    ox.settings.use_cache = True
    ox.settings.cache_folder = str(cache_dir)
    ox.settings.log_console = False

    print(f"─── Building {CITY} boundary ───")
    polygon_wgs84 = build_brussels_polygon(buffer_m=2000.0)

    if PBF is not None:
        print(f"\n─── Building walking network from {PBF} ───")
        G = graph_from_pbf(polygon_wgs84, PBF)
    else:
        print("\n─── Downloading walking network from Overpass API ───")
        print("  (first run: 2–5 min; subsequent runs use cache)")
        print("  Cache:", cache_dir)

        G = ox.graph_from_polygon(
            polygon_wgs84,
            network_type="walk",
            simplify=True,
            retain_all=False,
        )

    # Add travel_time to every edge
    print("\n─── Adding travel_time attributes ───")
    for u, v, k, d in G.edges(keys=True, data=True):
        length = d.get("length", 0)
        d["travel_time"]        = round(length / WALK_SPEED_DEFAULT, 1)
        d["travel_time_senior"] = round(length / WALK_SPEED_SENIOR,  1)

    # Stats
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    print(f"  Nodes: {n_nodes:,}")
    print(f"  Edges: {n_edges:,}")

    edge_lengths = [d.get("length", 0) for _, _, d in G.edges(data=True)]
    avg_len = sum(edge_lengths) / max(len(edge_lengths), 1)
    print(f"  Avg edge length: {avg_len:.1f} m")

    print(f"\n─── Saving {GRAPH_PATH.name} ───")
    ox.save_graphml(G, filepath=str(GRAPH_PATH))
    size_mb = GRAPH_PATH.stat().st_size / 1_048_576
    print(f"  ✓ {size_mb:.1f} MB")

    stats = {
        "nodes": n_nodes,
        "edges": n_edges,
        "avg_edge_length_m": round(avg_len, 1),
        "walk_speed_default": WALK_SPEED_DEFAULT,
        "walk_speed_senior": WALK_SPEED_SENIOR,
        "buffer_m": 2000,
        "crs_source": CRS_LAMBERT,
    }
    STATS_PATH.write_text(json.dumps(stats, indent=2))

    # where the network came from, for the importer's manifest entry (added 27 Sep 2026)
    prov_path = STATS_PATH.parent / "provenance.json"
    prov = json.loads(prov_path.read_text()) if prov_path.exists() else {}
    if PBF is not None:
        import subprocess
        ts = subprocess.run(["osmium", "fileinfo", "-g", "header.option.osmosis_replication_timestamp", str(PBF)],
                            capture_output=True, text=True).stdout.strip() or None
        prov["osm_graph"] = {"file": PBF.name, "osm_timestamp": ts}
    else:
        prov["osm_graph"] = {"overpass": ox.settings.overpass_url, "fetched": date.today().isoformat()}
    prov_path.write_text(json.dumps(prov, indent=2, ensure_ascii=False))
    print(f"  ✓ Stats written to {STATS_PATH.name}")

    print("\nNext steps complete!")
    print(f"Next: python 05_score.py --city {CITY}")


if __name__ == "__main__":
    main()
