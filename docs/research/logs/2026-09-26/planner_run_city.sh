#!/bin/bash
# One city, the given kinds, one run at a time, from the 25 Sep 2026 extract. A log with a fetch
# warning or zero demand POIs is a failed run; zero existing assets is flagged for a look.
cd "$(dirname "$0")/.."
PBF=../neighbourhood_fit_score/pipeline/data/raw/belgium-260925.osm.pbf
city=$1; shift
for kind in "$@"; do
  log=runlogs/${city}_${kind}.log
  echo "source: $PBF (local extract, no Overpass)" > "$log"
  .venv/bin/python -m engine.run --city $city --asset $kind --budget 40 --pbf $PBF >> "$log" 2>&1
  code=$?
  a=$(grep -oP 'loaded \K[0-9]+(?= existing assets)' "$log"); d=$(grep -oP 'loaded \K[0-9]+(?= demand POIs)' "$log")
  cov=$(grep -oP 'Coverage: \K.*' "$log")
  if [ $code -ne 0 ] || grep -q "fetch warning" "$log" || [ "$d" = "0" ]; then st=FAIL; elif [ "$a" = "0" ]; then st=CHECK; else st=OK; fi
  echo "$st $city $kind exit=$code assets=$a demand=$d coverage=$cov"
done
