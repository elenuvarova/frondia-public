# Pipelines of the merged projects

Frondia absorbed three of Elena's earlier map projects (docs/07-unified-frondia.md). Their pipelines
live here so that every layer on the site can be rebuilt from this repository. The code arrived on
26 Sep 2026. It carries the ports made for Frondia, which were never committed in the source repositories.

| Folder | Source repository, base commit | Ported for Frondia | Feeds |
|---|---|---|---|
| `city_planner/engine` | `public_realm_planner_multicity` @ `fd7f9a6` | Brussels: `adapters/brussels.py` (new), `adapters/__init__.py`, `config.py` (city `brussels`, CRS 31370, 14 kinds of object), `deprivation.py` (shared Belgian BIMD loaders, commune prefixes as a parameter) | `cities/<city>/points/*.geojson`, the planner layers and `data/registry/named_points_<city>.json` |
| `neighbourhood_fit_score/pipeline` | `neighbourhood_fit_score` (`backend/pipeline`) @ `b094ac2` | Antwerp: `config.py` (16 REFNIS, bbox, 458 sectors, transit from De Lijn), `02_sectors.py` (`ONLY_SECTORS`), `03_pois.py` (De Lijn GTFS read as a stream) | `cities/<city>/layers/fit_score.csv` |
| `spotfinder/pipeline` | `spot-finder-geo` (`pipeline`) @ `d1daaa1` | Brussels: a `brussels` entry in `config.py` | `cities/<city>/layers/shops_access.csv` |

Only code is kept. What the pipelines download and write — OSM extracts, GTFS feeds, Statbel tables,
caches, their own outputs — stays local and is ignored by git (see `.gitignore`), and so do `.env`
files: Fit Score's step 8 reads `GROQ_API_KEY` from `neighbourhood_fit_score/pipeline/.env`
(template: `.env.example`). Step 8 writes narratives and is not used by Frondia.

## Running

Each pipeline keeps its own folder layout, so its relative paths resolve inside `pipelines/<name>/`.

- **City Planner:** from `pipelines/city_planner/`, `python -m engine.run --city brussels --asset toilets --budget 40`.
  Output lands in `frontend/public/data/<city>/<asset>/`. Deprivation inputs download into `cache/`.
- **Fit Score:** from `pipelines/neighbourhood_fit_score/pipeline/`, run `01_download.py`, then `02_sectors.py`
  to `05_score.py` in order, each with `--city antwerp` (or `brussels`). `06_seed.py` and `08_narratives.py`
  feed the original app and are not needed for Frondia. Output lands in `data/processed/<city>/scores.csv`.
  For Antwerp, De Lijn's GTFS (`delijn_gtfs.zip`, 2.3 GB unpacked) goes into `data/raw/`.
- **SpotFinder:** from `pipelines/spotfinder/pipeline/`, `SF_CITY=brussels` and then `fetch_osm`, `fetch_statbel`,
  `clean`, `build_grid`, `compute`. Output lands in `../backend/data/<city>.geojson`.

### From a local OSM extract instead of Overpass

On 26 Sep 2026 Overpass refused both the cloud sandbox and the Mac, so each pipeline can read OpenStreetMap
from a Geofabrik PBF instead (needs the osmium CLI). Without the flag nothing changes:

- **City Planner:** `python -m engine.run ... --pbf <belgium.osm.pbf>` (or `PLANNER_PBF`). Features go through
  osmnx's `features_from_xml`, the same `_create_gdf` as the Overpass path; the walk graph is cached apart.
- **Fit Score:** `04_graph.py --city <city> --pbf <belgium.osm.pbf>` (step 03 always read the PBF).
- **SpotFinder:** `fetch_osm.py --pbf <belgium.osm.pbf>` (or `SF_PBF`): nodes at their position, ways and
  multipolygons at their bounding-box centre, as Overpass's `out center`.

**Where each city's OSM came from.** Ghent, Liège and Charleroi: City Planner from the extract
`belgium-260925.osm.pbf` (Geofabrik, 25 Sep 2026), and so are Liège's and Charleroi's SpotFinder and Fit Score
walking graph. Brussels and Antwerp: live Overpass, earlier in September; Ghent's SpotFinder and Fit Score were
made on the Mac on 26 Sep. Known answers: Ghent's seven kinds run both ways agree to the unit on existing assets
and demand POIs (`docs/research/2026-09-26-pipelines-runlog.md`).

**Provenance (since 27 Sep 2026).** Each pipeline records where its OSM came from: a Geofabrik extract with the
data's timestamp from the PBF header (`osmosis_replication_timestamp`), or live Overpass with the day. City
Planner puts it in `report.json` (`osm_source`); SpotFinder writes `pipeline/data/<city>_osm_source.json`; Fit
Score's steps 03 and 04 write `data/processed/<city>/provenance.json` (with the GTFS feed and the Monday read).
The importer copies it into the manifest's `source`; a run made before then says the source was not recorded.

Then `python scripts/report/import_projects.py --city <city> --what <planner|fitscore|spotfinder>`
brings the result into the city bundle and registers it in the manifest. The importer reads these
folders first and falls back to the sibling repositories under `~/git projects/`.

Each pipeline needs its own environment (`requirements*.txt` in its folder). Their dependencies
(geopandas, osmnx, networkx…) are heavier than Frondia's own.
