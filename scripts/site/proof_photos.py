#!/usr/bin/env python3
"""Снимки для полосы доказательств на лендинге: пара ортофото одного сектора в два года, с контуром сектора.

Сектор берётся из данных, а не выбирается руками: пример в `facts.json` — `editions.antwerp.aerial.example`
(наибольшее расхождение официальной кроны и аэрофото) и `be_vegetation.example` (сильнейшая потеря сверх шума по
карте Bruxelles Environnement). Рамка — квадрат вокруг сектора (+ 40 м) в EPSG:31370, контур — кремовый (#F2EADE, бренд), 4 px.

Источники и подписи (лицензии требуют назвать источник):
  · Vlaanderen, летние ортофото OMZRGB18VL / OMZRGB21VL — данные под авторским правом Digitaal Vlaanderen, доступ и
    использование по регламенту GDI-Vlaanderen («Gebruiksrecht geografische webdiensten»); предписанная ссылка дословно:
    «Bron: Luchtopnamen Digitaal Vlaanderen» (карточка набора на vlaanderen.be/datavindplaats, прочитано 09.10.2026);
  · Brussel, UrbIS Ortho2021Ns / Ortho2023 — CC0 (public domain; the service's own Fees field, read 09.10.2026);
    no credit is required, the source is named anyway: «Orthophoto UrbIS, paradigm.brussels».

    .venv/bin/python scripts/site/proof_photos.py     # после site_data.py; нужна сеть, Pillow, shapely

Пишет site/public/proof/<slug>-<год>.webp и site/public/proof/proof.json (что на каком снимке, источник).
"""
from __future__ import annotations

import hashlib
import io
import json
import subprocess
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "site/public/proof"
PAD, W, LINE, CREAM = 40, 1000, 4, (242, 234, 222)
SOURCES = {
    "antwerp": {"wms": "https://geo.api.vlaanderen.be/OMZ/wms", "layers": {2018: "OMZRGB18VL", 2021: "OMZRGB21VL"},
                "credit": "Bron: Luchtopnamen Digitaal Vlaanderen", "credit_lang": "nl",
                "licence": "Gebruiksrecht geografische webdiensten, GDI\u2011Vlaanderen"},
    "brussels": {"wms": "https://geoservices-urbis.irisnet.be/geoserver/urbisgrid/ows",
                 "layers": {2021: "Ortho2021Ns", 2023: "Ortho2023"},
                 "credit": "Orthophoto UrbIS, paradigm.brussels", "credit_lang": None, "licence": "CC0"},
}


def pair(city: str, sid: str, slug: str) -> dict:
    src = SOURCES[city]
    fc = json.loads((ROOT / f"data/{city}_sectors_31370.geojson").read_text())["features"]
    g = next(shape(f["geometry"]) for f in fc if f["properties"]["id"] == sid)
    # a square frame around the sector: both photos of a pair and both pairs share one shape, the outline whole
    x0, y0, x1, y1 = g.bounds
    cx, cy, half = (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) / 2 + PAD
    X0, Y0, X1, Y1 = cx - half, cy - half, cx + half, cy + half
    H = W
    files, sources = {}, {}
    for year, layer in src["layers"].items():
        url = (f"{src['wms']}?service=WMS&version=1.3.0&request=GetMap&layers={layer}&styles=&crs=EPSG:31370"
               f"&bbox={X0},{Y0},{X1},{Y1}&width={W}&height={H}&format=image/jpeg")
        raw = subprocess.run(["curl", "-sf", "--max-time", "120", url], capture_output=True, check=True).stdout
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        d = ImageDraw.Draw(im)
        for p in ([g] if g.geom_type == "Polygon" else list(g.geoms)):
            pts = [((x - X0) / (X1 - X0) * W, (Y1 - y) / (Y1 - Y0) * H) for x, y in p.exterior.coords]
            d.line(pts + [pts[0]], fill=CREAM, width=LINE, joint="curve")
        name = f"{slug}-{year}.webp"
        im.save(OUT / name, "WEBP", quality=80)
        files[str(year)] = name
        # what was asked and what was kept: the services are not versioned, so the request and the file's hash say which
        sources[str(year)] = {"request": url, "sha256": hashlib.sha256((OUT / name).read_bytes()).hexdigest()}
    return {"city": city, "sector": sid, "width": W, "height": H, "files": files, "sources": sources,
            "read": date.today().isoformat(),
            "credit": src["credit"], "credit_lang": src["credit_lang"], "licence": src["licence"]}


def main() -> int:
    facts = json.loads((ROOT / "site/public/data/facts.json").read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    out = {"editions": pair("antwerp", facts["editions"]["antwerp"]["aerial"]["example"]["id"], "editions"),
           "region": pair("brussels", facts["be_vegetation"]["example"]["id"], "region")}
    (OUT / "proof.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for k, v in out.items():
        print(k, v["sector"], v["files"], f"{v['width']}×{v['height']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
