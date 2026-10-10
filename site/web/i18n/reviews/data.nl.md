# Review: part `data` (the 554 data-text units of /data and /register), Belgian Dutch (nl-BE)

- Part: `data`: `scripts/site/i18n/nl.json` (554 units), rendered as `site/public/data/downloads.nl.json` and `register.nl.json`
- Language: nl-BE
- Drafting model: `claude-opus-5-5` (draft commit `2f9b8b7`)
- Reviewing model: `claude-sonnet-5-5`
- Date: 2026-10-04
- Units read: 554, every one, with its English template (collected with `i18n_sync.collect()`, hash-checked against the catalogue). The rendered files were compared with the English `downloads.json` and `register.json`.

## What was checked

- **Structure of the rendered files.** `downloads.nl.json` and `register.nl.json` have exactly the English keys; no non-text value differs (ids, counts, hashes, dates, urls, thresholds, `gold`/`label`/`rule` codes, CSV `columns[].name`, `file`, `key`, `group`, `licence`, credits). Strings left identical to English are only credits, licence names, file and column names, identifiers and the contracts' French quotes, as L6 says. All 14 commune names of the contracts are named in Dutch (Sint-Jans-Molenbeek, Elsene, Schaarbeek, Vorst, Sint-Gillis, Sint-Joost-ten-Node, Sint-Agatha-Berchem, Brussel).
- **Quotes from the contracts.** Every quoted span of the 98 reasons was compared with its English source after turning straight apostrophes into ’ (controller ruling): all are character-for-character the same, including the contracts' own slips («la création d’une espace vert», «d’ilot»), the «...» ellipsis and the nested «liaison douce». The only spans not found are the label codes «weak» and «state» (translated on purpose) and `5 Pocket Park` (choice 5).
- **The register describes what a model read.** No unit suggests the model counts or measures: the model «las», «vindt», «noemt», «beschrijft», the rule baseline is a rule, and the numbers stay with code («elk getal … blijft bij de rekenmotor» is on the page itself). «telt als maatregel» (`why.10`) means «qualifies», as in the English.
- **Commitment strength is neither softened nor strengthened.** «vaste verbintenis» / «vast toegezegde» for the English «firm commitment» / «firmly committed»; «een doel» for the weak label (an aim), «geen maatregel» for no; the reasons keep the English argument for each label («alleen als behoefte of doel», «geen verbindend werkwoord»). `register.check_why.7` («doit» = a stated need, no commitment verb) and `register.model_why.7` are faithful.
- **Cooling and causes.** `layer.heat_2022_2025.limits.1` keeps the denial («niet voor ‘het werd koeler’ … dus afkoeling wordt niet gemeten»). `layer.monitoring_*.limits.1` keeps «zonder document blijft ze onbekend». `graden` appears only for coordinate degrees (`layer.sectors.unit`). No «door/dankzij» as a cause.
- **Dynamic World is a probability.** «kans per klasse», «Klassewaarden zijn kansen, geen gedeelten van de grond», «de klasse met de hoogste gemiddelde kans» (the hard class picked from the probability), «Harde klassen tegenover de kansen van Dynamic World» (WorldCover).
- **Effect against matched places; budget per project, effect per footprint.** Every effect, column and verdict is stated against «vergelijkingsplaatsen» (or «vergelijkbare»); `layer.*.column.*_raw` and `ndvi_raw` are labelled «zonder aftrek / zonder vergelijkingsplaatsen». The only budgets in the units are the contract pages' own «budgetcijfers»; nothing compares a price with an effect.
- **Licence wording.** `CC BY 4.0` and `ODbL` appear only in the untranslated credits and `licence` fields; none of the 554 units rewords a licence.
- **Proper names untranslated.** Statbel, VITO, Proba-V, Copernicus, Landsat, Sentinel-2, Dynamic World, ESA WorldCover, Groenkaart Vlaanderen, ANB, quartiers.brussels, Parc de l’Ouest, square Jacques Frank, Place Desmet, Parc de Résédas, rue Vandenbranden and the other project and street names are as written.
- **Glossary, numbers, typography.** All terms as the table says (vergelijkingsplaatsen, ruis, drempel, significantiedrempel, groenheid, oordeel, geweigerd, ingreep, nulverdeling, nulmeting, basisjaar, LBE, artikel 3, punt 20, kroonbedekking, verhard/onthard, ontharding). Numbers and dates are copied, with decimal commas from `texts.nums`; `0,04`, `1,32 °C`, `1,5 km` agree. Script check: ‘ ’ only, no straight or “ ” quotes, no straight apostrophe between letters, no `%` with a space. `tests/test_texts.py` and the catalogue test pass per the drafter's report.
- **Belgian usage and register.** `bv.`, «Pijplijn», «aanbestedingsfeed», «voetgangersnetwerk», «gelijkaardige», «volkstelling», «Leefmilieu»-style names are Flemish; no Netherlands-only forms. Imperatives are impersonal («koppel op id», «download ze bij Statbel»).

## The drafter's five choices

1. **CSV codes stay English with a gloss.** Accepted: the files stay English, so the reader meets the code and its meaning together. One refinement is in the findings (the balance verdict columns gloss 4 codes with 3 phrases).
2. **Elliptical descriptions spelled out.** Accepted: «in de stedelijke centra en clusters», «met de gemeente opgebouwd uit Statbel-sectoren» are correct and read alone.
3. **yes / weak / no become the page's filter names.** Accepted: ‘verbindt zich’, ‘een doel’, ‘geen maatregel’ are the names on `/register`, so no bare English code appears, and the strength is the same.
4. **Quoted French keeps its wording.** Accepted under the ruling: only the apostrophe changed.
5. **`5` outside the quote in `register.why.72`.** Accepted: «5 ‘Pocket Park’» reads as «five Pocket Parks», which is what the contract says.

## Findings

| severity | key | problem | suggestion | response |
|---|---|---|---|---|
| blocker | `register.why.57` | «nieuwe begroeide of **bebouwde** grond» for «vegetated/cultivated ground»: on this site «bebouwd» means built-up (glossary; `built`), so the reason says the opposite of what the English means for a commitment to urban vegetable gardens. A wrong term in a commitment reason. | Het citaat ‘implanter des potagers urbains sur plusieurs sites du périmètre’ is een vaste verbintenis (een van de projecten die het contract ‘va développer’) die nieuwe begroeide of beteelde grond creëert, en die beslist het label ‘verbindt zich’. | Fixed as suggested: «beteelde». |
| minor | `layer.art8_balance_2025.column.built_verdict`, `…green_verdict`, `…trees_verdict`, and the same three keys of `layer.art8_balance_2026` | «up, down, noise of refused (meer of minder boven de ruis, binnen de ruis, geweigerd)» glosses four codes with three phrases, so the reader has to guess which is which; `layer.article8_2024.column.*_verdict` pairs each code with its gloss. | `built_verdict`: bebouwd: up (meer bebouwd boven de ruis: verhard), down (minder bebouwd boven de ruis: onthard), noise (binnen de ruis) of refused (geweigerd). `green_verdict`: stedelijk groen: up (meer boven de ruis), down (minder boven de ruis), noise (binnen de ruis) of refused (geweigerd). `trees_verdict`: kroonbedekking: up (meer boven de ruis), down (minder boven de ruis), noise (binnen de ruis) of refused (geweigerd). | Fixed as suggested: each code with its own gloss, in all six keys. |
| minor | `layer.groenkaart_2018_2024.limits.1` | «In de zomer van 2018 was het droog» is weaker than «was a drought» and does not say why low green reads low. | De zomer van 2018 was een droogtezomer: laag groen valt in die editie laag uit. | Fixed as suggested. |
| minor | `layer.fit_score.limits.0` | «meng ze nooit» has no clear antecedent for «ze» (the layer or the scores); the English «it» is the layer's values. | Een toestand, geen gemeten verandering: meng deze laag nooit met de effecten hierboven. | Fixed as suggested. |
| minor | `layer.fit_score.column.playground` | «speelplein» (also a summer-camp word in Flanders) where the catalogue and the atlas say «speeltuin». | deelscore speeltuin, 0–1 | Fixed as suggested: «speeltuin», as in the atlas. |
| minor | `threshold.level` | The pointer to the section reads «‘Wat veranderde’», but the page's heading is «Wat er veranderde». | Geen significantiedrempel: een niveau voor één jaar, geen verandering. Ook het eigen formaat van de Commissie heeft geen drempel; of er iets boven de ruis veranderde, staat in de laag onder ‘Wat er veranderde’. | Kept. The pointer names the group on the data page itself, whose label is `data.groups.changed.label` «Wat veranderde». «Wat er veranderde» is the atlas heading, not this page’s. |
| minor | `threshold.article8`, `threshold.balance`, `layer.planner_coverage.method` | «run» is English; the atlas uses «doorrekening» for the same word (`atlas.built.rawOff`). | `threshold.article8`: Groenheid {ndvi}, kroonbedekking {trees}, bebouwd {built}: het 95e percentiel van de eigen nulverdeling van deze doorrekening — elk van de {n} vergelijkbare sectoren speelt één keer ‘ingreep’ tegenover zijn eigen {controls} vergelijkingsplaatsen, en de effecten die daaruit komen, zijn pure ruis. `threshold.balance`: Groen {green}, kroonbedekking {trees}, bebouwd {built} (aandeel van de oppervlakte van de sector): het 95e percentiel van de eigen nulverdeling van deze doorrekening, voor elke klasse en elk seizoen apart — elke sector speelt één keer ‘ingreep’ tegenover zijn {controls} vergelijkingsplaatsen. `layer.planner_coverage.method`: Uit dezelfde doorrekening van City Planner als de gerangschikte plaatsen. | Fixed as suggested: «doorrekening» in all three keys, as in `atlas.built.rawOff`. |

Verdict: 1 blocker, 0 major, 6 minor

Drafter’s response (claude-opus-5-5): 1 blocker and 5 minors fixed, 1 minor answered (`threshold.level`).

## Round 2

Reviewed: the 13 units changed between `2f9b8b7` and `d3af467` in `scripts/site/i18n/nl.json` (the diff confirms 13), plus the drafter's answer on `threshold.level`. Placeholders (`{ndvi}`, `{trees}`, `{built}`, `{green}`, `{n}`, `{controls}`), numbers (`0/1`, `95e`) and typography (‘ ’, no straight apostrophes) of the changed units are intact.

| severity | key | problem | suggestion |
|---|---|---|---|
| resolved | `register.why.57` | Blocker fixed: «nieuwe begroeide of beteelde grond» says vegetated or cultivated ground; «bebouwd» no longer appears. The quote, «vaste verbintenis» and the label ‘verbindt zich’ are unchanged. | none |
| resolved | `layer.art8_balance_2025.column.{built,green,trees}_verdict`, `layer.art8_balance_2026.column.{built,green,trees}_verdict` | Each code now has its own gloss, as in `layer.article8_2024`. `built_verdict` explains up as «meer bebouwd … verhard» and down as «minder bebouwd … onthard», which is exactly the English up/down for built-up; green and trees say «meer / minder boven de ruis». Nothing is softened. | none |
| resolved | `layer.groenkaart_2018_2024.limits.1` | «De zomer van 2018 was een droogtezomer» keeps the drought of the English. | none |
| resolved | `layer.fit_score.limits.0` | «meng deze laag nooit …» gives the pronoun its antecedent. | none |
| resolved | `layer.fit_score.column.playground` | «speeltuin», as in the atlas. | none |
| resolved | `threshold.article8`, `threshold.balance`, `layer.planner_coverage.method` | «doorrekening» replaces «run» and matches `atlas.built.rawOff`; the rest of each text is unchanged. | none |
| accepted | `threshold.level` (not changed) | The drafter is right and my round-1 finding was wrong: the pointer «onder ‘Wat veranderde’» names the group on the data page itself, whose label is `data.groups.changed.label` «Wat veranderde»; «Wat er veranderde» is the atlas heading. Keeping «Wat veranderde» is the correct match. | none |

Open issues: none.

Verdict: 0 blocker, 0 major, 0 minor
