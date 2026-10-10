# Frondia

**An evidence atlas for urban green in five Belgian cities: what actually changed, told apart from noise with a
threshold measured on the city itself.**

Live at [frondia.eu](https://frondia.eu), with the atlas at [frondia.eu/atlas](https://frondia.eu/atlas), in English,
Dutch and French. Designed and built by Elena Uvarova with Claude Code, from 31 August to 10 October 2026.

This repository is a snapshot of the code behind the site. The project's history stays in a private repository; each
commit here is the version deployed at that date (the latest: 10 October 2026).

## The idea in one step

From space, every city looks a little greener or browner every summer, because rain, heat and harvest move the whole
city at once. Compare each Brussels sector with its own past and 263 of 668 look "significantly greener" between
2017–19 and 2021–24. Compare each with the twelve sectors that looked most alike beforehand, none closer than
1.5 km, and 16 do.

- **Compare with a control, not with the past.** Difference-in-differences against 12 matched places.
- **Measure the threshold instead of choosing it.** Every sector plays a pretend intervention once. The 95 % edge of
  those effects is the threshold, computed in the same run as the effect, per city and instrument.
- **Refusal is a result.** "No fair comparison" (match gap > 0.04), "no defensible footprint", "works inside the
  windows" and "preliminary" are published in the same row as "no effect".
- **A loss needs two instruments**, NDVI and Dynamic World, and documents as a third filter.
- **The language model never computes a number.** Numbers come from a deterministic engine with tests.
- **Commit before the result.** Projects not yet started and planting priorities are registered with a geometry
  hash, a date and named control places.

The atlas asks three questions of every Statbel sector: what's missing, what to place, and what changed. Only the
third one measures change.

## Layout

| Path | What |
|---|---|
| `engine/` | the method: cities and windows (`config.py`), matching and difference-in-differences (`controls.py`), calibration, audits, manifests, city adapters, registries and pre-registration |
| `cities/<city>/` | each city's package: `manifest.json`, `layers/*.csv`, `points/*.geojson` |
| `scripts/gee/` | Google Earth Engine pipelines (Sentinel-2, Landsat, Dynamic World, WorldCover, PROBA-V) |
| `scripts/official/` | checks of the official Article 8 layers (Copernicus HRL Woody Vegetation, CLCplus) against aerial maps |
| `scripts/registry/` | registers of interventions, named points, tree priority, LLM extraction of contract texts |
| `scripts/site/` | the site's data (`site_data.py` → `site/public/data/`), downloads, proof photos |
| `site/web/` | the site: Next.js (App Router, TypeScript, next-intl), landing, atlas, dossier, commune, data, register |
| `pipelines/` | three earlier map projects merged into the atlas: City Planner, Neighbourhood Fit Score, SpotFinder |
| `tests/` | Python tests: known answers per city, visible text of the pages, rebuild from a clean folder |
| `docs/` | plans, research notes, design systems (Russian, the working language of the project) |

## Running it

```sh
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q tests                                       # engine and data
.venv/bin/python scripts/site/site_data.py                                # rebuild the site's data

cd site && npm install --include=dev
cd web && npx vitest run                                                  # site tests
NODE_ENV=development npx next dev                                         # local site
NODE_ENV=production npx next build                                        # production build
```

The Earth Engine scripts need your own Google Cloud project (`--project`, or `EE_PROJECT` for the pre-registration scripts). The report generators write finished pages to `FRONDIA_OUT` (default: a `frondia-out` folder in the system's temp dir).

## Licences

- **Code:** MIT (`LICENSE`).
- **Frondia's own layers** (effects, thresholds, verdicts, registers in `cities/` and `site/public/data/`):
  CC BY 4.0. Layers derived from OpenStreetMap are © OpenStreetMap contributors, under the ODbL.
- **Third-party data** keeps its source's licence: Copernicus (Sentinel-2, CLMS), ESA WorldCover (CC BY 4.0), Google
  Dynamic World (CC BY 4.0), USGS Landsat, Statbel, Eurostat, Digitaal Vlaanderen, Bruxelles Environnement, UrbIS,
  the cities' open-data portals.
- **Aerial photographs** in `site/public/proof/`: Flanders, "Bron: Luchtopnamen Digitaal Vlaanderen", under
  Gebruiksrecht geografische webdiensten, GDI‑Vlaanderen; Brussels, UrbIS orthophotos, CC0.
- **Fonts:** Instrument Serif and Fragment Mono (`site/web/assets/fonts/OFL.txt`) and Geist (npm `@fontsource-variable/geist`), all SIL Open Font License 1.1.
- **Icons:** Streamline Ultimate Light by [Streamline](https://streamlinehq.com), used under the author's premium
  licence. They are not covered by the MIT licence and may not be reused; see
  `site/web/icons/ultimate-light/CREDITS.md`.
