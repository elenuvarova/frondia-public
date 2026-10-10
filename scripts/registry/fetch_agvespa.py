"""Реестр проектов AG Vespa (Антверпен): статус, тема, хронология, год сдачи.

Что это: антверпенский аналог реестра Beliris. Список `agvespa.be/projecten`
отдаёт все проекты одной страницей с координатами маркеров; страница проекта —
Drupal-поля: статус (`In realisatie` / `Gerealiseerd`), тема, адрес, партнёры и
хронологию событий (дата · заголовок · текст).

Год сдачи берётся из хронологии, не из статуса: последнее событие со словами
открытия/сдачи (opening, geopend, ingehuldigd, oplevering, afgewerkt, klaar,
in gebruik, einde van de werken). Если таких нет, а статус «Gerealiseerd» —
год последнего события, с пометкой `completed_basis = last_event`.
Без хронологии — `completed_year = None`: срок неизвестен, не угадывается.

Привязка к паркам — по расстоянию от маркера до центроида именованного парка
OSM ≥ 1 га (`data/perimeters/parks_antwerp.geojson`) в пределах 400 м И по
совпадению слова названия. Как показал Beliris, точка рядом с чужим парком —
не след; поэтому расстояние без совпадения имени печатается как «кандидат».

    python scripts/registry/fetch_agvespa.py            # → data/registry/agvespa_projects.json,
                                                        #   data/registry/agvespa_park_links.csv
"""
from __future__ import annotations

import csv
import html
import json
import math
import re
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BASE = "https://www.agvespa.be"
UA = {"User-Agent": "Mozilla/5.0 (research; frondia; contact via github)"}
OUT = Path("data/registry/agvespa_projects.json")
LINKS = Path("data/registry/agvespa_park_links.csv")
PARKS = Path("data/perimeters/parks_antwerp.geojson")

DONE_WORDS = re.compile(r"\b(opening|geopend|open(t|de)?\b|ingehuldigd|inhuldiging|oplevering|opgeleverd|"
                        r"afgewerkt|afgerond|klaar|in gebruik|einde (van de )?werken|voltooid|feestelijk)", re.I)
MONTHS = {m: i for i, m in enumerate(
    ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"], 1)}


def get(url: str) -> str:
    with urlopen(Request(url, headers=UA), timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def text(s: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def field(page: str, name: str) -> str | None:
    m = re.search(rf'field--name-{name}[^>]*>(.*?)</div>\s*</div>', page, re.S)
    if not m:
        m = re.search(rf'field--name-{name}[^>]*>(.*?)</div>', page, re.S)
    if not m:
        return None
    t = text(m.group(1))
    for lab in ("Status", "Thema", "Adres", "Partners", "Architect", "Aannemer", "Rol AG Vespa"):
        if t.startswith(lab + " "):
            t = t[len(lab) + 1:]
    return t or None


def timeline(page: str) -> list[dict]:
    ev = []
    for m in re.finditer(r'paragraph--type--timeline-events.*?field--name-field-time-upper-title[^>]*>(.*?)</div>'
                         r'(?:.*?field--name-field-time-title[^>]*>(.*?)</div>)?(?:.*?field--name-field-time-body[^>]*>(.*?)</div>)?',
                         page, re.S):
        when, title, body = text(m.group(1)), text(m.group(2) or ""), text(m.group(3) or "")
        ev.append({"when": when, "title": title, "body": body[:400], "year": year_of(when)})
    return ev


def year_of(when: str) -> int | None:
    ys = re.findall(r"\b(19[89]\d|20[0-4]\d)\b", when)
    return int(ys[-1]) if ys else None


def completion(events: list[dict], status: str | None) -> tuple[int | None, str]:
    done = [e for e in events if e["year"] and DONE_WORDS.search(e["title"] + " " + e["body"][:120])]
    if done:
        return max(e["year"] for e in done), "done_event"
    if status and status.lower().startswith("gerealiseerd"):
        ys = [e["year"] for e in events if e["year"]]
        if ys:
            return max(ys), "last_event"
    return None, "unknown"


def list_projects() -> list[dict]:
    h = get(BASE + "/projecten")
    rows = re.findall(r'data-lat="([\d.]+)" data-lng="([\d.]+)"[^>]*data-icon="([^"]+)".*?<h4 class="field-content">\s*(.*?)\s*</h4>.*?href="(/projecten/[^"]+)"', h, re.S)
    out, seen = [], set()
    for lat, lng, icon, title, href in rows:
        if href in seen:
            continue
        seen.add(href)
        out.append({"title": text(title), "url": BASE + href, "slug": href.rsplit("/", 1)[-1],
                    "lat": float(lat), "lon": float(lng), "marker": icon.rsplit("/", 1)[-1]})
    return out


def dist_m(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def centroid(geom) -> tuple[float, float]:
    pts = []
    def walk(c):
        if isinstance(c[0], (int, float)):
            pts.append(c[:2])
        else:
            for x in c:
                walk(x)
    walk(geom["coordinates"])
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


STOP = {"park", "plein", "de", "het", "van", "en", "site", "nieuw", "nieuwe", "stad", "antwerpen", "tuin", "straat", "kaai", "brug"}


def words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-zà-ÿ]{4,}", s.lower()) if w not in STOP}


def stems_match(a: set[str], b: set[str]) -> set[str]:
    """Совпадение по основе: droogdokkeneiland ~ droogdokkenpark, sorghvliedt = sorghvliedt.
    Общий префикс ≥ 6 букв — чтобы «park»/«plein» не склеивали полгорода."""
    out = a & b                      # точное совпадение слова (≥ 4 букв, стоп-слова уже сняты)
    for x in a:
        for y in b:
            n = 0
            while n < min(len(x), len(y)) and x[n] == y[n]:
                n += 1
            if n >= 6:
                out.add(x[:n])
    return out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--relink", action="store_true", help="только привязка к паркам из сохранённого JSON")
    args = ap.parse_args()
    if args.relink and OUT.exists():
        projects = json.loads(OUT.read_text())
        print(f"проектов из {OUT}: {len(projects)}")
        return link(projects)
    projects = list_projects()
    print(f"проектов в списке: {len(projects)}")
    for i, p in enumerate(projects, 1):
        try:
            page = get(p["url"])
        except Exception as e:  # noqa: BLE001
            p["error"] = str(e); continue
        p["status"] = field(page, "field-project-status")
        p["theme"] = field(page, "field-project-theme")
        p["address"] = field(page, "field-project-address-sidebar")
        p["partners"] = field(page, "field-project-partners")
        p["description"] = (field(page, "field-project-description") or "")[:600]
        p["timeline"] = timeline(page)
        p["completed_year"], p["completed_basis"] = completion(p["timeline"], p["status"])
        if i % 25 == 0:
            print(f"  {i}/{len(projects)}")
        time.sleep(0.4)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(projects, ensure_ascii=False, indent=1))
    st = {}
    for p in projects:
        st[p.get("status")] = st.get(p.get("status"), 0) + 1
    basis = {}
    for p in projects:
        basis[p.get("completed_basis")] = basis.get(p.get("completed_basis"), 0) + 1
    print("статусы:", st); print("основание года сдачи:", basis)
    return link(projects)


def link(projects: list[dict]) -> int:
    parks = [f for f in json.load(PARKS.open())["features"] if f["properties"].get("in_city", True)]
    rows = []
    for p in projects:
        pw = words(p["title"])
        for f in parks:
            pr = f["properties"]; c = centroid(f["geometry"]); d = dist_m((p["lon"], p["lat"]), c)
            if d > 400:
                continue
            common = stems_match(pw, words(pr.get("name", "")))
            rows.append({"project": p["title"], "slug": p["slug"], "status": p.get("status"), "theme": p.get("theme"),
                         "completed_year": p.get("completed_year"), "completed_basis": p.get("completed_basis"),
                         "park": pr.get("name"), "park_area_ha": round(float(pr.get("area_ha", 0)), 2), "dist_m": round(d),
                         "name_match": bool(common), "link": "след" if common else "кандидат"})
    rows.sort(key=lambda r: (r["link"] != "след", r["dist_m"]))
    with LINKS.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["project"]); w.writeheader(); w.writerows(rows)
    print(f"связей с парками ≤ 400 м: {len(rows)}, из них по имени: {sum(r['name_match'] for r in rows)} → {LINKS}")
    for r in rows:
        if r["name_match"]:
            print(f"  {r['completed_year'] or '----'} {r['completed_basis']:<10} {r['status'] or '?':<14} {r['project'][:38]:<40} → {r['park'][:30]:<32} {r['park_area_ha']:>6} га  {r['dist_m']} м")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
