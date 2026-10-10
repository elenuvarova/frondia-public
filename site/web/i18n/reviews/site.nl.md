# Review: part `site` (common, privacy, landing), Belgian Dutch (nl-BE)

- Part: `site`, sections `common`, `privacy`, `landing`
- Language: nl-BE
- Drafting model: `claude-opus-5-5`
- Reviewing model: `claude-sonnet-5-5`
- Date: 2026-10-04
- Keys read: 331 (every key of the three sections, English against Dutch; `tests/catalogues.test.ts` passes, 28 tests)

## What was checked

- Sense, key by key against `en.json`: nothing added or dropped that matters. Every claim the site never makes is kept out: the cooling key (`landing.refusals.0.text`) still says the site does not claim cooling; refusals stay full outcomes («geen oordeel», «weigert Frondia een oordeel te vellen», «zonder eerlijke vergelijking»); every change is stated against «vergelijkingsplaatsen» or labelled as the raw «voor en na»; causes are named «met documenten» or not at all.
- Numbers, years, percentages, ± and × signs, the 3-30-300 code: identical in Dutch notation (`0,29`, `45%`, `95%`, no space before `%`). Script check of arguments (`{city}`, `{k}`, ...) and tags (`<em>`, `<b>`, `<a>`, `<mail>`): identical to English in all keys.
- Glossary: every term in the table is used as the table says and the same way throughout (ruis, drempel, vergelijkingsplaatsen, groenheid, oordeel / weigeren, ingreep not needed, nettoverlies, toenemende trend, stedelijke groene ruimte, kroonbedekking, gemeente, gewest, artikel 8). EUR-Lex wording in `landing.law.p1` matches the Dutch excerpt in `sources/`.
- Belgian usage and register: «u» throughout, «gemeente», «gewest», «aanvaarden» for Accept, «gelijkaardig», «bouwwerf», «braakland», «Leefmilieu Brussel», «Gegevensbeschermingsautoriteit» are all Flemish; no Netherlands-only forms found. One generic «je» (below).
- Typography: ‘ ’ only, no straight or “ ” quotes, no U+00A0, no space before punctuation, no `1.5`-style decimals. Clean.
- `same.json`, Dutch block: every key that is identical to English has an entry and every entry is identical (no missing, no stale). All reasons hold. One optional comment on a place name is in the table.
- Retold keys under «For a native reader», Dutch rows: all justified. `landing.audits.controls` («Vergelijking») loses the word «plaatsen» but reads fine above «12 benoemd».

## Findings

| severity | key | problem | suggestion | response |
|---|---|---|---|---|
| minor | `landing.hero.lede` | «gemeten tegen plaatsen» is a calque of «measured against»; Dutch says «afgezet tegen» (or «gemeten aan»). It is the first sentence a reader meets. | Elke zomer ritselt het groen van de stad — wat groener, wat bruiner. Frondia onderscheidt het geritsel van de groei, afgezet tegen plaatsen die hetzelfde bleven. | Fixed as suggested. |
| minor | `landing.showcase.body` | «toetst, tegen de eigen ruis» is the same calque; Dutch says «toetst aan». | De atlas brengt vier eerdere tools samen op één eenheid, de statistische sector van Statbel: wat een buurt mist, wat waar moet komen, en of er echt iets veranderde. De eerste twee beschrijven en bevelen aan. De derde toetst aan de eigen ruis van de stad. | Fixed as suggested. |
| minor | `landing.faq.0.a` | «verandering tegen de eigen ruis» again a calque of «against». | Nee. De atlas toont ook wat elke sector mist, van dagelijkse diensten en winkels binnen bereik tot zomerhitte en de 3-30-300-regel, en waar het volgende van veertien soorten openbare objecten moet komen. Alleen groenheid wordt gemeten als verandering ten opzichte van de eigen ruis van de stad; de rest zijn toestanden en aanbevelingen, en de atlas noemt ze ook zo. | Fixed as suggested. |
| minor | `landing.audits.p1` | «voetafdruk van de werken» sounds like an ecological footprint to a Dutch reader; the text means the area the works cover. «tegen twaalf sectoren» is the «against» calque again. | Een audit meet het terrein van de werken zelf ten opzichte van twaalf sectoren die in de atlas benoemd zijn, en volgt het effect daarna zomer na zomer, want een park dat één keer groener werd en weer vervaagde, is een ander verhaal. | Fixed as suggested. |
| minor | `landing.audiences.2.text` | «het resultaat op maat kan intekenen»: in Flemish «intekenen» mostly means «to subscribe». The sentence is understood, but it is odd, and it does not echo the FAQ question («Kan die naar het resultaat worden getekend?»). | Een toets die in de subsidie wordt vastgelegd voordat de werken beginnen. De omtrek, de nulmeting en de vergelijkingsplaatsen worden met een datum vastgelegd, zodat niemand achteraf de omtrek naar het resultaat kan tekenen. | Fixed as suggested. |
| minor | `landing.refuse.title` | The drafted aphorism «Wie op alles een getal heeft, zegt niets» is not an existing saying, moves the subject from the tool to a person, and turns «useless» into «says nothing». The sense is kept, but the English shape is closer and just as natural. | Een tool die op alles met een getal antwoordt, is nutteloos. <em>Deze zegt waar hij ophoudt.</em> | Fixed as suggested; the row is removed from «For a native reader», since the line now follows the English. |
| minor | `landing.law.close` | «kroonlaag» can be read as the forest canopy layer instead of a data layer; «kroon-instrumenten» is an awkward hyphen compound. | Officiële lagen zeggen <em>hoeveel</em>. Frondia zegt of het boven de ruis <em>veranderd</em> is, en waarom. In rangorde stemmen ze overeen: de officiële laag voor kroonbedekking en de drie instrumenten voor kroonbedekking die Frondia gebruikt, correleren met r = {lo}–{hi} over de {count} steden. (The «en waarom» is the English's own wording; see the note on the source below.) | Fixed as suggested. |
| minor | `privacy.lede` | «hoe u van gedachten verandert» says how you do change your mind; the English means how you can. | Wat deze site vastlegt, waar dat terechtkomt en hoe u van gedachten kunt veranderen. | Fixed as suggested. |
| minor | `privacy.meta.description` | Same as `privacy.lede`. | Wat deze site vastlegt, waar dat terechtkomt en hoe u van gedachten kunt veranderen. | Fixed as suggested. |
| minor | `landing.refusals.3.text` | One generic «zie je» in a page that addresses the reader with «u» everywhere else, and the clause order is heavy. An impersonal form avoids the clash. | Paden, vijvers en fonteinen herstellen in een park dat al groen is, is vanuit de ruimte niet te zien. Oudere parkprojecten, waaronder zeven grote renovaties, elk gemeten met een eigen venster en een eigen drempel, blijven binnen de ruis. | Fixed as suggested. |
| minor | `landing.cases.droogdokkenpark.story` | «ving de werken in volle gang» is stilted. | Het Belvédère opende in september 2018 op de oude droogdokken van het Eilandje. Het standaardvenster ‘voor’ viel midden in de werken. | Fixed as suggested. |
| minor | `landing.faq.6.a` | «kalibratie» here, «geijkt» in `landing.audits.p2`: two words for one idea on the same page. | {cities}. De drempel hoort bij het paar stad en instrument: {wider}. Een nieuwe stad krijgt haar eigen ijking. | Fixed as suggested. |
| minor | `landing.cases.spoor-noord.story` | Title says «rangeerterrein», story says «rangeerstation»: the same place under two names. | Het rangeerterrein van de NMBS werd in 2008–2009 als park geopend. Sentinel-2 bestond toen nog niet, dus de audit gebruikt Landsat, dat teruggaat tot 2006. | Fixed as suggested. |
| minor | `landing.cases.droogdokkenpark.reading` | «scènes» for satellite scenes is remote-sensing jargon; in running prose «opnamen» is plainer. (The chart tooltips in `common.charts.*` may keep «scènes».) | Met een nulmeting van vóór de werken is het verdedigbare effect de helft van het getal op papier, en nog altijd driemaal de drempel. Die nulmeting steunt op de twee bruikbare opnamen van de zomer van 2016. | Fixed as suggested. |
| minor | `landing.faq.5.a` | «een halve hectare kroon» reads as «crown»; the term is «kroonbedekking». | Onder ongeveer een hectare verdrinkt het signaal: vier beplante straten in een sector van 19 hectare voegen ruwweg een halve hectare kroonbedekking toe, veertig keer verdund. Voor kleine dingen toetst Frondia iets anders: of het object verscheen op punten die vooraf benoemd waren, met niet-benoemde punten als vergelijking. | Fixed as suggested. |
| minor | `common.charts.rings.aria` | «{summers} zomers» is wrong for 1 («1 zomers»); the English has the same flaw. Restructuring avoids it without changing the ICU shape. | {place}: sinds {completed}, boven de ruis in {above} van {summers} zomers. De breedte van een ring is het effect ten opzichte van {n} vergelijkingsplaatsen, drempel {thr}. | Fixed as suggested. |
| minor | `landing.cases.ninove.place` | A Flemish reader knows this Brussels site as «Ninoofsepoort». Keeping the French project name is allowed by the brief and `same.json` states why, so this is Elena's call, not an error. If the Dutch name is adopted, change the same name in `landing.threshold.hist.marker`, `landing.anyway.tiles.ninove`, `landing.showcase.browserAria`, `landing.showcase.alt`, `landing.cases.ninove.story` and the `same.json` entries. | Ninoofsepoort | Kept as the French project name (brief §7); noted under «For a native reader» as Elena’s call, with «Ninoofsepoort» as the Flemish alternative. |

## Notes on the source (English), not counted in the verdict

- `landing.law.close` says Frondia tells «whether it changed beyond noise, and why». `landing.faq.4.a` says «with documents, why», and the site's rule is that no cause is named without a document. The Dutch follows the English faithfully, so this is not a translation fault, but the English should say «and, with documents, why». Dutch then: «Frondia zegt of het boven de ruis <em>veranderd</em> is, en, met documenten, waarom.» (French below in its own file.)
- `common.charts.rings.aria` has «{summers} summers» without singular handling in English too.

Verdict: 0 blocker, 0 major, 17 minor

## Round 2

Reviewed: the 16 keys changed between `4208fa9` and `5964a22` in `nl.json` (`git diff` confirms 16), plus the drafter's `response` to the one minor that was not changed (`landing.cases.ninove.place`). `tests/catalogues.test.ts`, `messages.test.ts` and `icu.test.ts` pass. Arguments, tags, numbers (`19`, `2016`, `{lo}–{hi}`), quotes and spaces of the changed keys are unchanged from English; no never-claim rule is touched (the cooling key `landing.refusals.0.text` is not among the changed Dutch keys).

| severity | key | problem | suggestion |
|---|---|---|---|
| resolved | `common.charts.rings.aria` | Fixed: «boven de ruis in {above} van {summers} zomers» no longer prints «1 zomers»; sense kept (the rings above the threshold are a subset of the summers). | none |
| resolved | `privacy.lede`, `privacy.meta.description` | Fixed: «kunt veranderen». | none |
| resolved | `landing.hero.lede`, `landing.showcase.body`, `landing.faq.0.a`, `landing.audits.p1` | Fixed: «afgezet tegen», «toetst aan», «ten opzichte van», «het terrein van de werken». The glossary terms (vergelijkingsplaatsen, ruis, drempel) are intact. | none |
| resolved | `landing.law.close` | Fixed: «de officiële laag voor kroonbedekking» and «instrumenten voor kroonbedekking» (glossary term). «En waarom» is still the English's own wording (see the note on the source in round 1). | none |
| resolved | `landing.audiences.2.text` | Fixed: «de omtrek naar het resultaat kan tekenen» echoes the FAQ question and is idiomatic. | none |
| resolved | `landing.refuse.title` | Fixed: closer to the English, and the row is correctly removed from «For a native reader». | none |
| resolved | `landing.refusals.3.text` | Fixed: impersonal, no generic «je». | none |
| resolved | `landing.cases.droogdokkenpark.story`, `landing.cases.droogdokkenpark.reading` | Fixed: «viel midden in de werken», «opnamen». | none |
| resolved | `landing.cases.spoor-noord.story` | Fixed: «rangeerterrein» in title and story. | none |
| resolved | `landing.faq.5.a` | Fixed: «kroonbedekking». | none |
| resolved | `landing.faq.6.a` | Fixed: «ijking» is consistent with «geijkt» in `landing.audits.p2`. | none |
| accepted | `landing.cases.ninove.place` (not changed) | The response keeps the French project name per the brief and notes «Ninoofsepoort» for Elena under «For a native reader». That is what I asked for; it is her decision, not an open fault. | none |

Open issues: none.

Verdict: 0 blocker, 0 major, 0 minor
