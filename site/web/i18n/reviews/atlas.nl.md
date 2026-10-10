# Review: part `atlas`, Belgian Dutch (nl-BE)

- Part: `atlas` (the `atlas` section of the catalogue)
- Language: nl-BE
- Drafting model: `claude-opus-5-5` (draft commit `915b08c`)
- Reviewing model: `claude-sonnet-5-5`
- Date: 2026-10-04
- Keys read: 328 (325 strings and 3 `null` legend gaps), plus all 538 rendered lines of `task-12-report.md` (269 Dutch, read in full); `tests/catalogues.test.ts`, `messages.test.ts` and `icu.test.ts` pass

## What was checked

- **Agreement in the rendered lines (Dutch).** All 14 objects × `place.register.at` (1/0 and 2/3), `place.register.none`, `place.title`, `tip` and `passport` roles; all 4 groups × `equity.ages.none/one/split/both`; `equity.livesIn` with and without a cut; `equity.reading.*` in both directions with all three shops; `equity.byIncome.*`; `place.register.gap` and `caution`; `more.who` at 0, 1 and 2; `more.whoOne`; the count lines at 0, 1 and 2; `registered.lede` for Brussels, Ghent, Antwerp; `change.threshold`; `communes.unstable.other` with Ixelles, Elsene, Watermael-Boitsfort, Anderlecht. Every line is grammatical: articles agree («een zitbank», «een hondenweide», «het dichtstbijzijnde café», «de dichtstbijzijnde bakkerij»), «er is geen …» fits all 14 objects, the counts follow their labels so «1 inwoners» cannot occur, and `more.who` correctly switches «staat er 1» / «staan er 2» (and «staan er 0»). No agreement error found.
- **Temperature is a state.** The heat lens, `byIncome.heat`, `equity.reading.heat` and the passport say «hoeveel warmer de grond … wordt dan in de mediane sector», «woont op warmere grond» and «t.o.v. de stad»: where it is hotter, never an effect of greening. `need.lenses.heat.limit` denies cooling («Een toestand, geen effect: of een park afkoeling brengt, kan de methode niet meten (ruisvloer 1,32 °C)»); `place.limit` («Een aanbeveling, geen effect») keeps the same line for City Planner.
- **«What changed».** Counts are «groener boven de ruis» / «verlies boven de ruis» against vergelijkingsplaatsen; the raw view is labelled «schijnbaar groener» / «Lijkt groener» and the subtraction is explicit (`change.subtract`, `change.background`, `balance.raw`). `built.rawOff` states «alleen getoond ten opzichte van de vergelijkingsplaatsen».
- **Refusal.** «Geen vergelijkbare plaatsen — geweigerd», `passport.refused` («Dat is een resultaat, geen leemte»), `registered.refused`, `built.word.refused` are all full outcomes.
- **Dynamic World.** «kans per klasse, geen aandeel van de grond» (`built.limit`), hectares «zoals Dynamic World de grond indeelt» (`balance.lede`); never a share.
- **Tooltips and short labels.** «Tekort», «Plaatsen», «Veranderd» (the three questions), «Beeld» for the switch, «Inzoomen/Uitzoomen», «benoemd punt» / «vergelijkingspunt» / «verdere kandidaat» are clear. «Tekort» for «Missing» works, with the full «Wat ontbreekt» one tap away.
- **Article 8 terms** against `sources/`: «artikel 8, lid 1», «artikel 3, punt 20», «stedelijke centra en clusters», «LBE (LAU 2024)», «nettoverlies», «kroonbedekking», «Verordening»/«verordening»; the EEA/JRC method line is faithful.
- **Glossary, numbers, typography.** Every term follows the table (vergelijkingsplaatsen, ruis, drempel, groenheid, oordeel, ingreep, verhard/onthard, weergave for the lens). Numbers, units and years agree in Dutch notation (`1,32 °C`, `0,0458`, `€ 19.000`, `45%`, `1,5 tot 2,5 km`, `1,7 hectare`). Script check: arguments, tags, select and plural keywords match English in every key; no straight or “ ” quotes, no U+00A0, no spaces before punctuation.
- **`same.json`.** Every Dutch key identical to English has an entry, and no entry is stale. Reasons hold (credits, head titles, units, «Object», «Sector», «Effect», «Audit»).
- **Belgian usage and register.** «u»/impersonal throughout, «telewerk», «kinderopvang», «buurtwinkel», «huisarts», «openbaar vervoer», «Snoepwinkel» for OpenStreetMap's confectionery, «gemeente», «gewest». Nothing Netherlands-only.
- **Retold keys, Dutch rows of «For a native reader»:** all justified. «Beeld» for `change.view` does not clash with `zoom.reset` («Beeld herstellen» means the same view); «Wie komt tekort» is the right idiom.

## Findings

| severity | key | problem | suggestion | response |
|---|---|---|---|---|
| minor | `atlas.communes.leaveOut` | «De plicht van geen nettoverlies» is a noun pile (the same pattern the documents round fixed in `dossier.trend.law.counted.body`), and «dichte stedelijke gemeenten» is not the Dutch for «dense communes» (densely populated: «dichtbevolkt»). | Als alle {n} wegvallen, verdwijnt {area} van de oppervlakte van het gewest en {res} van zijn inwoners uit de telling, maar {woody} van zijn houtige vegetatie. De plicht om geen nettoverlies te lijden zou dan rusten op {rest} dichtbevolkte gemeenten, met gemiddeld {restGreen} groen. | Fixed as suggested: «De plicht om geen nettoverlies te lijden», «dichtbevolkte gemeenten». |
| minor | `atlas.equity.reading.r3` | «woont vaker dan het rijkste waar aan geen van beide delen voldaan is» puts the comparison before its place clause; it parses, but reads heavily. | Het armste derde woont {worse, select, yes {vaker} other {minder vaak}} waar aan geen van beide delen voldaan is dan het rijkste: {p} tegenover {r}. | Fixed as suggested: the place clause now comes before «dan het rijkste». |

## Notes on the source (English), not counted in the verdict

- `atlas.need.lenses.heat.lede` says «Canopy is the strongest shield»; the Dutch («het sterkste schild») and French («le meilleur bouclier») follow it, with «in {city} hangen de twee samen met r = {r}» saying only that the two move together. «Shield» is protective, causal language next to a lens that is explicitly a state. It is not a translation fault, but the English could say «Canopy is the factor that moves with it most closely», or drop the sentence's first half.

Verdict: 0 blocker, 0 major, 2 minor

## Round 2

Reviewed: the 2 keys changed between `915b08c` and `227460e` in `nl.json` (`git diff` confirms 2), and the 2 re-rendered Dutch lines of «Round 1 fixes» in `task-12-report.md`. `tests/catalogues.test.ts`, `messages.test.ts` and `icu.test.ts` pass. Arguments, select keywords, numbers and typography of both keys are unchanged.

| severity | key | problem | suggestion |
|---|---|---|---|
| resolved | `atlas.equity.reading.r3` | Fixed: «Het armste derde woont vaker waar aan geen van beide delen voldaan is dan het rijkste: 38 % tegenover 21 %.» (and «minder vaak») reads naturally, and the claim is unchanged. | none |
| resolved | `atlas.communes.leaveOut` | Fixed: «De plicht om geen nettoverlies te lijden» and «dichtbevolkte gemeenten» are idiomatic; «nettoverlies» is the glossary term and the sense is unchanged. | none |

Open issues: none.

Verdict: 0 blocker, 0 major, 0 minor
