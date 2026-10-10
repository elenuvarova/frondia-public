# Pipelines run log — Liège, Charleroi, Ghent (26 Sep 2026, cloud sandbox)

Branch `cloud/wallonia-pipelines`, from `wip/three-cities` @ `b4c3739`. Raw logs: `docs/research/logs/2026-09-26/`.

**Status: done.** Fit Score, SpotFinder and City Planner ran for Liège and Charleroi, City Planner for Ghent
(all 14 kinds), and all are imported. Overpass refused the sandbox and, from about 19:13 UTC, the Mac too, so
SpotFinder and City Planner read OpenStreetMap from the 25 Sep 2026 extract (see "Method difference").

## Network

| Host | Result from the sandbox |
|---|---|
| download.geofabrik.de | refused (TLS reset after CONNECT) |
| overpass-api.de, lz4.overpass-api.de, gall.openstreetmap.de | refused (TLS reset after CONNECT) |
| z.overpass-api.de | about 1 small query in 4 answered; a city's walking network never came through (9 tries, 45 s apart) |
| overpass.kumi.systems, overpass.private.coffee | timeout; maps.mail.ru: 504 |
| nominatim.openstreetmap.org, statbel.fgov.be, opendata.tec-wl.be, raw.githubusercontent.com | reachable |

The proxy connects (it answers "Connection established") and the far end drops the TLS handshake, so these
servers refuse the sandbox's egress address; the environment is already on full network access. From
Elena's Mac, overpass-api.de answered at 17:35 UTC (endpoint gall.openstreetmap.de, 2 slots free).

## Inputs

| Input | Version | How it got here |
|---|---|---|
| OSM Belgium | `belgium-260925.osm.pbf` (Geofabrik, 25 Sep 2026), 695,068,461 bytes, sha256 `866542325f2b…d417e1` | downloaded on the Mac, passed through a draft release `osm-belgium-260925` (not committed: over GitHub's 100 MB limit); saved as `data/raw/belgium-latest.osm.pbf` |
| TEC GTFS | `TEC-GTFS.zip`, publisher OTW, `feed_start_date` 20260925, files dated 25 Sep 2026 20:36–20:43 | opendata.tec-wl.be, 78.7 MB |
| Statbel sectors 2024, population 2024 | URLs in Fit Score `config.py` | statbel.fgov.be |
| osmium | osmium-tool 1.16.0 (apt) | — |

## Neighbourhood Fit Score

| | Liège | Charleroi |
|---|---|---|
| 02 sectors (REFNIS) | 184 (62063) | 291 (52011) |
| 02 residents 2024 | 195,659 | 204,205 |
| 03 POIs from the PBF | 6,251 (3,769 inside sectors) | 3,031 (2,084 inside sectors) |
| 03 sectors with at least one POI | 177 | 256 |
| 03 TEC stops in the box / served / inside sectors | 2,633 / 2,629 / 887 | 2,131 / 2,112 / 1,039 |
| 03 service day read | Monday 20260928: 37 services, 20,933 trips (network-wide) | same |
| 04 walking graph, nodes / edges | 27,278 / 73,546 | 19,820 / 55,356 |
| 04 walk filter dropped (directed edges) | 69,148 of 461,730 | 30,108 of 265,038 |
| 05 sectors scored | 184 (552 rows, 3 scenarios) | 291 (873 rows) |
| 05 mean family / senior / remote | 0.560 / 0.421 / 0.505 | 0.463 / 0.315 / 0.385 |
| Imported | `cities/liege/layers/fit_score.csv`, 20 layers in manifest | `cities/charleroi/layers/fit_score.csv`, 20 layers |

Failures and fixes:

- **04 needs Overpass** (OSMnx `graph_from_polygon`). Retried through z.overpass-api.de: 9 failures for Liège,
  stopped. `04_graph.py` gained `--pbf`: osmium cuts the highways of the buffered box from the PBF, OSMnx
  builds the graph from that XML with its own `walk` filter and `graph_from_polygon`'s order (truncate to
  the +500 m polygon, largest component, simplify, truncate, largest component). Without `--pbf` nothing
  changes. **Method difference:** Brussels, Antwerp and Ghent were built from live Overpass; Liège and
  Charleroi from the 25 Sep extract. Same filter, so differences should be data age only.
- **05 failed** on `nearest_nodes` without scikit-learn; added to `requirements-pipeline.txt`.
- Cosmetic: 02 prints "Communes: 1 (expected 19)", the Brussels count, for every city.

## Method difference: OSM from the extract

City Planner and SpotFinder gained a PBF mode (`engine.run --pbf`, `fetch_osm.py --pbf`; details in
`pipelines/README.md`). **Ghent, Liège and Charleroi's planner points, and Liège and Charleroi's SpotFinder
layer and Fit Score walking graph, come from `belgium-260925.osm.pbf` (25 Sep 2026). Brussels and Antwerp came
from live Overpass earlier in September;** Ghent's SpotFinder and Fit Score from the Mac on 26 Sep.

### Known answers: Ghent, Overpass on the Mac (26 Sep) against the extract

| Kind | Overpass (Mac): assets / demand | Extract: assets / demand | Overpass coverage % | Extract coverage % |
|---|---|---|---|---|
| toilets | 144 / 1,634 | 144 / 1,634 | 27.8 → 51.6 | 27.8 → 51.6 |
| benches | 2,098 / 1,576 | 2,098 / 1,576 | 61.2 → 76.0 | 61.2 → 76.0 |
| waste_bins | 972 / 2,387 | 972 / 2,387 | 47.4 → 60.6 | 47.4 → 60.7 |
| drinking_water | 27 / 2,176 | 27 / 2,176 | 7.2 → 40.3 | 7.2 → 40.3 |
| fitness_stations | 31 / 439 | 31 / 439 | 8.0 → 43.6 | 8.0 → 43.6 |
| bike_parking | 3,333 / 1,634 | 3,333 / 1,634 | 65.9 → 78.2 | 65.9 → 78.2 |
| defibrillators | 142 / 1,491 | 142 / 1,491 | 28.8 → 51.7 | 28.8 → 51.7 |

Equal to the unit on every count. The one difference is waste_bins after placement, 60.7 against 60.6 %:
the greedy solver's last pick on a tie, not the data. City Planner's own tests: 19 passed.

## SpotFinder

`fetch_statbel`: boxes kept 524 sectors around Liège and 503 around Charleroi (of 19,795). Income merge fails
for 3,184 of 19,795 sectors nationally (16.1 %), population merge for none. SpotFinder reads the **2022**
sector geometry (`sh_statbel_statistical_sectors_31370_20220101`), not the 2024 register.

| | Liège | Charleroi |
|---|---|---|
| `fetch_osm --pbf`: points (relations matching / exported) | 4,458 (3 / 3) | 2,680 (2 / 2) |
| `clean`: cafe / bakery / confectionery | 104 / 109 / 21 | 58 / 39 / 3 |
| `clean`: gastro / retail / transit / offices | 812 / 578 / 2,291 / 543 | 256 / 290 / 1,876 / 158 |
| `build_grid`: sectors, scorable (≥ 1 food place) | 524, 393 | 503, 232 |
| `compute`: sectors with scores | 388 | 226 |
| Imported: sectors kept / left out of the box | 184 / 340 | 291 / 212 |

No known answer exists for SpotFinder from the extract; its reading follows Overpass's `out center tags`
(node position, bounding-box centre for ways and multipolygons). Charleroi's confectionery (3) is too thin to
rank; SpotFinder already flags that type as low-confidence.

## City Planner

All 42 runs, budget 40, one at a time, logs checked for "fetch warning", zero demand POIs and zero existing
assets: none. Deprivation (BIMD 2011) joined 184 zones in Ghent, 175 in Liège, 273 in Charleroi. Walking graph
from the extract: the walk filter dropped 60,678 of 362,446 directed edges in Liège, 26,952 of 224,964 in
Charleroi. Existing assets / demand POIs / coverage before → after (%):

| Kind | Ghent: assets / demand / coverage % | Liège | Charleroi |
|---|---|---|---|
| toilets | 144 / 1,634 / 27.8 → 51.6 | 52 / 1,210 / 19.4 → 64.2 | 11 / 1,336 / 3.6 → 41.2 |
| benches | 2,098 / 1,576 / 61.2 → 76.0 | 1,373 / 1,163 / 67.7 → 90.6 | 162 / 1,188 / 18.7 → 52.4 |
| waste_bins | 972 / 2,387 / 47.4 → 60.7 | 708 / 1,575 / 55.2 → 82.5 | 44 / 1,386 / 10.3 → 46.3 |
| drinking_water | 27 / 2,176 / 7.2 → 40.3 | 31 / 1,476 / 16.1 → 62.4 | 1 / 1,500 / 0.9 → 38.8 |
| fitness_stations | 31 / 439 / 8.0 → 43.6 | 8 / 236 / 4.8 → 61.8 | 2 / 134 / 0.7 → 46.6 |
| bike_parking | 3,333 / 1,634 / 65.9 → 78.2 | 653 / 1,210 / 55.2 → 83.0 | 61 / 1,336 / 16.8 → 49.3 |
| defibrillators | 142 / 1,491 / 28.8 → 51.7 | 62 / 1,179 / 28.3 → 69.1 | 6 / 1,303 / 2.2 → 40.1 |
| dog_areas | 27 / 337 / 10.0 → 43.2 | 2 / 127 / 1.6 → 57.2 | 1 / 109 / 0.2 → 50.0 |
| playgrounds | 234 / 622 / 43.5 → 62.2 | 62 / 318 / 32.5 → 71.5 | 29 / 267 / 14.9 → 53.8 |
| shelters | 415 / 1,324 / 55.8 → 69.8 | 187 / 1,103 / 52.6 → 83.4 | 178 / 1,240 / 44.2 → 72.2 |
| recycling | 191 / 783 / 32.8 → 57.4 | 192 / 440 / 61.9 → 84.6 | 8 / 339 / 4.1 → 47.8 |
| bicycle_repair | 39 / 4,714 / 12.2 → 46.7 | 4 / 1,756 / 3.9 → 58.1 | 1 / 1,302 / 1.0 → 38.4 |
| public_bookcases | 83 / 762 / 20.5 → 47.4 | 41 / 404 / 24.9 → 67.6 | 2 / 312 / 1.8 → 42.1 |
| picnic_tables | 414 / 6,693 / 23.9 → 55.0 | 127 / 409 / 16.7 → 67.5 | 16 / 377 / 2.4 → 44.4 |

Read with care:
- **Charleroi's OSM is thin**: 11 toilets, 6 defibrillators, 1 drinking fountain, 1 bicycle repair stand for
  ~204,000 residents. Its low "before" coverage partly measures the map, not the city.
- Ghent's picnic_tables demand (6,693) and bicycle_repair demand (4,714) dwarf Liège's: `leisure=garden` and
  `amenity=bicycle_parking` are mapped far more densely in Flanders. Same config for every city.

Imported: 560 points in each of `cities/{ghent,liege,charleroi}/points/` (35 layers per manifest).
Ghent's points were named for the execution line (`scripts/registry/name_points_planner.py --city ghent`:
140 named, 140 control → `data/registry/named_points_ghent.json`); Liège and Charleroi are not on the site
yet and were not named. `scripts/site/site_data.py` regenerated `points-ghent.json` (14 kinds, 560 points,
none outside sectors) and Ghent's downloads; `facts.json` now counts 35 layers for Ghent (was 20).

## Also on the branch

- `cities/ghent/manifest.json`: the heat layer `heat_2022_2025` was committed without its manifest entry;
  registered with `heat_exposure.py`'s fields (canopy cross-check r = −0.531, 23 sectors hot and under
  10 % canopy, 42,315 residents).

## Provenance in the manifests (27 Sep 2026)

The pipelines now record where their OSM came from and the importer writes it into each layer's `source`
(details in `pipelines/README.md`). For the runs above, made before that, the records were written afterwards
from this log: City Planner's 42 `report.json`, SpotFinder's two `<city>_osm_source.json`, Fit Score's two
`provenance.json` (TEC, Monday 20260928, feed of 20260925; OSM data as of 2026-09-25T20:24:36Z, read from the
PBF header). Liège and Charleroi's Fit Score and SpotFinder and the three cities' planner points were then
re-imported; the points' coordinates and `named_at` (2026-09-26) did not change, and `computed` keeps the day
of the run. Layers whose outputs are not in this sandbox (Brussels, Antwerp, Ghent's Fit Score and SpotFinder)
say that the source was not recorded, with "live Overpass, on or before <computed>" where only Overpass could
have been read; Antwerp's toilets name the city's open-data portal.

Found on the way: the Fit Score entry of Ghent, Liège and Charleroi was Antwerp's text ("--city antwerp",
De Lijn on 8 June 2026). Liège and Charleroi now read TEC, Monday 28 Sep 2026; Ghent De Lijn, day not recorded.
The site's downloads said "STIB-MIVB and De Lijn timetables" for every city; each city now names its operator
and its OSM source. Tests: 176 passed; City Planner's 19 passed.

## Tests

`pytest -q tests` on Python 3.13: **135 passed.** Ghent's two planner tests pass once its points are named.
On Python 3.11 five tests fail: `article8_html.py` and `audit_html.py` put backslashes inside f-string
expressions, which needs Python 3.12+. The repository does not state its Python version. `site_data.py`
also needs `shapely` in Facta's own environment (the README's install line lists only earthengine-api and
pytest).
