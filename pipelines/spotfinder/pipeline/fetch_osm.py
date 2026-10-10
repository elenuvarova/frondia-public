"""Stage 1: fetch OpenStreetMap data from Overpass for Antwerp.

Queries Overpass for the three scored business types, the attractor sets
(gastro, retail, transit, offices), and the documented diet:vegan tag, all
within the Antwerp bounding box. Emits a cleaned-but-not-yet-filtered point
layer (one record per OSM element) as GeoJSON for the next stage.

Run:  python pipeline/fetch_osm.py
Output: pipeline/data/osm_points_raw.geojson
"""

import json
import os
import time

import requests

import config


def _build_query():
    """Build a single Overpass QL query covering everything we need.

    We request nodes, ways and relations for each tag group and use `out center`
    so ways/relations collapse to a representative lon/lat. One combined query
    is far kinder to the shared Overpass service than many small ones.
    """
    bbox = config.overpass_bbox_str()

    # Collect every (key, value) selector we care about, de-duplicated.
    selectors = []

    def add(key, value):
        if value == "*":
            selectors.append(f'["{key}"]')
        else:
            selectors.append(f'["{key}"="{value}"]')

    # Scored types.
    for tags in config.OSM_TYPE_TAGS.values():
        for k, v in tags:
            add(k, v)
    # Attractors (gastro / retail / transit / offices).
    for tags in config.ATTRACTOR_TAGS.values():
        for k, v in tags:
            add(k, v)

    # De-duplicate while preserving order.
    seen = set()
    unique_selectors = []
    for sel in selectors:
        if sel not in seen:
            seen.add(sel)
            unique_selectors.append(sel)

    # Build statement lines for nodes/ways/relations for each selector.
    stmts = []
    for sel in unique_selectors:
        stmts.append(f"  node{sel}({bbox});")
        stmts.append(f"  way{sel}({bbox});")
        stmts.append(f"  relation{sel}({bbox});")

    body = "\n".join(stmts)
    query = (
        f"[out:json][timeout:{config.OVERPASS_TIMEOUT_S}];\n"
        f"(\n{body}\n);\n"
        f"out center tags;\n"
    )
    return query


def _post_with_retry(query):
    """POST the Overpass query with polite exponential backoff on 429/5xx."""
    headers = {"User-Agent": config.USER_AGENT}
    last_exc = None
    for attempt in range(config.HTTP_MAX_RETRIES + 1):
        try:
            resp = requests.post(
                config.OVERPASS_URL,
                data={"data": query},
                headers=headers,
                timeout=config.HTTP_TIMEOUT_S,
            )
        except requests.RequestException as exc:
            last_exc = exc
            wait = config.HTTP_BACKOFF_BASE_S * (2 ** attempt)
            print(f"[fetch_osm] request error ({exc}); retry in {wait:.0f}s "
                  f"(attempt {attempt + 1}/{config.HTTP_MAX_RETRIES})")
            time.sleep(wait)
            continue

        # 429 (Too Many Requests) and 504 (gateway timeout) are the common
        # Overpass throttling responses; back off and retry.
        if resp.status_code in (429, 502, 503, 504):
            # Respect Retry-After if present, else exponential backoff.
            retry_after = resp.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                wait = float(retry_after)
            else:
                wait = config.HTTP_BACKOFF_BASE_S * (2 ** attempt)
            print(f"[fetch_osm] HTTP {resp.status_code}; backing off {wait:.0f}s "
                  f"(attempt {attempt + 1}/{config.HTTP_MAX_RETRIES})")
            time.sleep(wait)
            continue

        resp.raise_for_status()
        return resp.json()

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Overpass query failed after retries (persistent throttling).")


def _element_lonlat(el):
    """Return (lon, lat) for a node, or the `center` for a way/relation."""
    if el["type"] == "node":
        return el.get("lon"), el.get("lat")
    center = el.get("center")
    if center:
        return center.get("lon"), center.get("lat")
    return None, None


def _selectors():
    """Every (key, value) the query asks for, scored types and attractors, de-duplicated in order."""
    out = []
    for group in (config.OSM_TYPE_TAGS, config.ATTRACTOR_TAGS):
        for tags in group.values():
            for kv in tags:
                if kv not in out:
                    out.append(kv)
    return out


def _elements_from_pbf(pbf):
    """The elements Overpass returns for `_build_query()`, read from a local extract.

    Added 26 Sep 2026 for Frondia (map_project): Overpass refused the sandbox and the Mac. osmium cuts
    the same box (ways with a node in it, multipolygons completed), keeps the objects carrying one of
    the selectors and exports them with their OSM type and id. As with `out center tags`, a node keeps
    its own position and a way or multipolygon relation gets the centre of its bounding box. Relations
    other than multipolygons are not exported by osmium; they are counted and reported.
    """
    import subprocess
    import tempfile

    s, w, n, e = config.BBOX
    sels = _selectors()
    wanted = {}
    for k, v in sels:
        wanted.setdefault(k, set()).add(v)
    exprs = [f"nwr/{k}" if "*" in vs else f"nwr/{k}={','.join(sorted(vs))}" for k, vs in wanted.items()]

    with tempfile.TemporaryDirectory() as tmp:
        cut, filt, seq = (os.path.join(tmp, f) for f in ("cut.osm.pbf", "f.osm.pbf", "f.geojsonseq"))
        subprocess.run(["osmium", "extract", "-b", f"{w},{s},{e},{n}", "-s", "smart", pbf,
                        "-o", cut, "--overwrite"], check=True)
        subprocess.run(["osmium", "tags-filter", cut, *exprs, "-o", filt, "--overwrite"], check=True)
        subprocess.run(["osmium", "export", filt, "-f", "geojsonseq", "-a", "type,id",
                        "-o", seq, "--overwrite"], check=True)
        # relations matching a selector that osmium export leaves out (not multipolygons)
        rel = subprocess.run(["osmium", "tags-filter", "-R", filt, *[x.replace("nwr/", "r/") for x in exprs],
                              "-f", "opl", "-o", "-"], check=True, capture_output=True, text=True).stdout
        n_rel = sum(1 for line in rel.splitlines() if line.startswith("r"))

        def matches(tags):
            return any(k in tags and (v == "*" or tags[k] == v) for k, v in sels)

        def coords(g):
            c = g["coordinates"]
            while isinstance(c[0], list) and isinstance(c[0][0], list):
                c = [p for part in c for p in part]
            return c if isinstance(c[0], list) else [c]

        elements, seen = [], set()
        with open(seq, encoding="utf-8") as fh:
            for line in fh:
                f = json.loads(line.strip("\x1e\n"))
                props = dict(f["properties"])
                typ, oid = props.pop("@type"), props.pop("@id")
                if (typ, oid) in seen or not matches(props):
                    continue
                pts = coords(f["geometry"])
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                if typ == "node":
                    if not (w <= xs[0] <= e and s <= ys[0] <= n):
                        continue   # a node outside the box, pulled in by a way
                    el = {"type": "node", "id": oid, "lon": xs[0], "lat": ys[0], "tags": props}
                else:
                    el = {"type": typ, "id": oid, "tags": props,
                          "center": {"lon": (min(xs) + max(xs)) / 2, "lat": (min(ys) + max(ys)) / 2}}
                seen.add((typ, oid))
                elements.append(el)

    exported_rel = sum(1 for t, _ in seen if t == "relation")
    print(f"[fetch_osm] relations matching a selector: {n_rel}, exported as multipolygons: {exported_rel}")
    return elements


def fetch_osm(pbf=None):
    """Query Overpass (or read the local extract `pbf`) and write the raw point layer as GeoJSON."""
    os.makedirs(config.DATA_DIR, exist_ok=True)

    if pbf:
        import subprocess
        print(f"[fetch_osm] reading {config.CITY_NAME} from {pbf} (local extract, no Overpass) ...")
        elements = _elements_from_pbf(pbf)
        ts = subprocess.run(["osmium", "fileinfo", "-g", "header.option.osmosis_replication_timestamp", pbf],
                            capture_output=True, text=True).stdout.strip() or None
        provenance = {"file": os.path.basename(pbf), "osm_timestamp": ts}
    else:
        provenance = {"overpass": config.OVERPASS_URL, "fetched": time.strftime("%Y-%m-%d")}
        query = _build_query()
        print(f"[fetch_osm] querying Overpass for {config.CITY_NAME} ...")
        data = _post_with_retry(query)
        elements = data.get("elements", [])
    print(f"[fetch_osm] received {len(elements)} raw OSM elements")

    features = []
    skipped_no_geom = 0
    for el in elements:
        lon, lat = _element_lonlat(el)
        if lon is None or lat is None:
            skipped_no_geom += 1
            continue
        tags = el.get("tags", {}) or {}
        # Carry the OSM id/type so downstream stages can deduplicate if a single
        # real-world place is mapped as both a node and an enclosing way.
        props = {
            "osm_type": el["type"],
            "osm_id": el["id"],
        }
        # Flatten tags as plain properties (clean.py reads these directly).
        props.update(tags)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": props,
        })

    if skipped_no_geom:
        print(f"[fetch_osm] skipped {skipped_no_geom} elements without geometry")

    fc = {"type": "FeatureCollection", "features": features}
    with open(config.OSM_POINTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(fc, fh, ensure_ascii=False)

    print(f"[fetch_osm] wrote {len(features)} points -> {config.OSM_POINTS_PATH}")
    # where the points came from, read by Frondia's importer for the manifest (added 27 Sep 2026)
    with open(config.OSM_POINTS_PATH.replace("_osm_points_raw.geojson", "_osm_source.json"), "w") as fh:
        json.dump(provenance, fh)
    return config.OSM_POINTS_PATH


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--pbf", default=os.environ.get("SF_PBF"),
                    help="read OSM from this local extract instead of Overpass (or set SF_PBF)")
    fetch_osm(ap.parse_args().pbf)
