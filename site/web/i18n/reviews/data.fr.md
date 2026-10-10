# Review: part `data` (the 554 data-text units of /data and /register), Belgian French (fr-BE)

- Part: `data`: `scripts/site/i18n/fr.json` (554 units), rendered as `site/public/data/downloads.fr.json` and `register.fr.json`
- Language: fr-BE
- Drafting model: `claude-opus-5-5` (draft commit `2f9b8b7`)
- Reviewing model: `claude-sonnet-5-5`
- Date: 2026-10-04
- Units read: 554, every one, with its English template (collected with `i18n_sync.collect()`, hash-checked against the catalogue). The rendered files were compared with the English `downloads.json` and `register.json`.

## What was checked

- **Structure of the rendered files.** `downloads.fr.json` and `register.fr.json` have exactly the English keys; no non-text value differs. Strings left identical to English are credits, licence names, file and column names, identifiers and the contracts' French quotes (L6). All 14 commune names are in French form (Molenbeek-Saint-Jean, Saint-Josse-ten-Noode, Berchem-Sainte-Agathe…), and the 11 kept units (`commune` ×6, the two WGS 84 lines, `°C`, `km²` ×2) are rightly the same word or a unit.
- **Quotes from the contracts.** Every quoted span of the 98 reasons was compared with its English source after turning straight apostrophes into ’ (controller ruling): all are character-for-character the same, including the contracts' own slips and the nested «liaison douce». The colon without a space inside «intervenir sur les espaces publics: plantation…» (`why.51`, `why.52`) is the contract's own punctuation and stays. The only spans not found are the label codes «weak» and «state» (translated on purpose) and `5 Pocket Park` (choice 5).
- **The register describes what a model read.** No unit suggests the model counts or measures: «a lu», «relève», «cite», «décrit»; the rule baseline is «la règle»; «rien ne compte donc comme mesure» (`why.10`) means «qualifies». The page's own sentence is explicit («chaque chiffre de ce site reste l’affaire du moteur de calcul»).
- **Commitment strength is neither softened nor strengthened.** «engagement ferme» / «fermement engagés» for «firm commitment»; «un objectif» for the weak label, «aucune mesure» for no; the reasons keep each English argument («seulement comme objectif», «ni verbe d’engagement ni projet précis»). `register.check_why.7` («doit» = a stated need, no engagement verb) and `register.model_why.7` are faithful.
- **Cooling and causes.** The one cooling sentence is the finding below (major). Elsewhere: `layer.monitoring_*.limits.1` keeps «sans document elle reste inconnue»; «degrés» appears only for coordinate degrees; no «à cause de» / «grâce à».
- **Dynamic World is a probability.** «probabilité de classe», «Les valeurs de classe sont des probabilités, pas des parts du sol», «la classe dont la probabilité moyenne … est la plus élevée» (the hard class picked from the probability), «Des classes strictes face aux probabilités de Dynamic World» (WorldCover).
- **Effect against matched places; budget per project, effect per footprint.** Every effect, column and verdict is stated «par rapport aux zones témoins» (or «comparables»); the raw columns say «sans soustraire les zones témoins». The only budgets in the units are the contract pages' own «chiffres de budget».
- **Licence wording.** `CC BY 4.0` and `ODbL` appear only in the untranslated credits and `licence` fields; no unit rewords a licence.
- **Proper names untranslated.** Statbel, VITO, Proba-V, Copernicus, Landsat, Sentinel-2, Dynamic World, ESA WorldCover, Groenkaart Vlaanderen, ANB, quartiers.brussels, Parc de l’Ouest, square Jacques Frank, Place Desmet, rue Vandenbranden and the other project and street names are as written.
- **Glossary, numbers, typography.** All terms as the table says (zones témoins, bruit, seuil, indice de végétation / verdure, verdict, refusé, intervention, distribution sous hypothèse nulle, état zéro, année de référence, UAL, article 3, point 20, couvert arboré, imperméabilisé / désimperméabilisé). The glossary's «(plancher de bruit)» is on `data.noThreshold`, the first use on the page, so omitting it from `threshold.*` is correct. Numbers and dates are copied, with decimal commas; `0,04`, `1,32 °C`, `1,5 km` agree. Script check: « » and ’ only, no straight or “ ” quotes, no straight apostrophe between letters, plain space before `%`.
- **Belgian usage and register.** `p. ex.`, «crèche», «Chaîne de traitement», «centile», «empreinte (hash)», «vous» imperatives («téléchargez-les», «faites la jointure»). Nothing France-only that Belgium avoids.

## The drafter's five choices

1. **CSV codes stay English with a gloss.** Accepted: the files stay English, so the reader meets the code and its meaning together. One refinement is in the findings (the balance verdict columns gloss four codes with three phrases).
2. **Elliptical descriptions spelled out.** Accepted: «dans les centres urbains et pôles urbains», «avec la commune reconstituée à partir des secteurs Statbel» are correct and read alone.
3. **yes / weak / no become the page's filter names.** Accepted: « s’engage », « un objectif », « aucune mesure » are the names on `/registre`, so no bare English code appears, and the strength is the same.
4. **Quoted French keeps its wording.** Accepted under the ruling: only the apostrophe changed.
5. **`5` outside the quote in `register.why.72`.** Accepted: «5 « Pocket Park »» reads as «five Pocket Parks», which is what the contract says.
6. Not a choice but worth a word: `layer.planner_points.limits.1` «ils sont prudents» for «conservative» is acceptable (the group biases against finding an effect); «conservateurs» would be the calque.

## Findings

| severity | key | problem | suggestion | response |
|---|---|---|---|---|
| major | `layer.heat_2022_2025.limits.1` | The English denies «“it got cooler”» (a change in temperature, the cooling claim the site never makes). «pour dire « il fait plus frais »» denies a different sentence: a state («it is cooler»), which is what this layer legitimately ranks. «Frais» is also one of the red-flag words, and the sentence is the data page's only cooling denial, so the sense must be exact. | Utile pour classer les secteurs entre eux ; pas pour dire « la température a baissé » : le seuil pour un changement de température est ressorti à 1,32 °C, plus qu’un effet réaliste d’un parc, si bien que le refroidissement n’est pas mesuré. | Fixed as suggested: «pas pour dire « la température a baissé »». |
| minor | `layer.art8_balance_2025.column.built_verdict`, `…green_verdict`, `…trees_verdict`, and the same three keys of `layer.art8_balance_2026` | «up, down, noise ou refused (en hausse ou en baisse au-delà du bruit, dans le bruit, refusé)» glosses four codes with three phrases, so the reader has to guess which is which; `layer.article8_2024.column.*_verdict` pairs each code with its gloss. | `built_verdict`: bâti : up (plus de bâti au-delà du bruit : imperméabilisé), down (moins de bâti au-delà du bruit : désimperméabilisé), noise (dans le bruit) ou refused (refusé). `green_verdict`: espaces verts urbains : up (en hausse au-delà du bruit), down (en baisse au-delà du bruit), noise (dans le bruit) ou refused (refusé). `trees_verdict`: couvert arboré : up (en hausse au-delà du bruit), down (en baisse au-delà du bruit), noise (dans le bruit) ou refused (refusé). | Fixed as suggested: each code with its own gloss, in all six keys. |
| minor | `layer.fit_score.column.childcare`, `layer.fit_score.column.convenience`, `layer.fit_score.column.scenario`, `layer.fit_score.measures` | The same things are named differently in the atlas (`atlas.need.service.childcare` «crèche», `convenience` «épicerie», scenario «Aînés») and in the data («garde d’enfants», «commerce de proximité», «seniors»). | `childcare`: sous-score crèche, 0–1. `convenience`: sous-score épicerie, 0–1. `scenario`: family, remote ou senior (famille, télétravail, aînés). `measures`: Dans quelle mesure un secteur répond à trois modes de vie — une famille avec enfants, le télétravail, les aînés — par l’accès à pied à quatorze services du quotidien. | Fixed as suggested: «crèche», «épicerie», «aînés», as in the atlas. |

Verdict: 0 blocker, 1 major, 2 minor

Drafter’s response (claude-opus-5-5): 1 major and 2 minors fixed.

## Round 2

Reviewed: the 11 units changed between `2f9b8b7` and `d3af467` in `scripts/site/i18n/fr.json` (the diff confirms 11). Numbers (`1,32 °C`, `0–1`, `quatorze`), « » spacing, plain space before `:` and `;` and the ’ apostrophe of the changed units are intact.

| severity | key | problem | suggestion |
|---|---|---|---|
| resolved | `layer.heat_2022_2025.limits.1` | Major fixed: «pas pour dire « la température a baissé »» now denies the change the English denies («it got cooler»), «frais» is gone, and the sentence still ends on the denial of cooling («le refroidissement n’est pas mesuré»), with the 1,32 °C threshold unchanged. No new claim. | none |
| resolved | `layer.art8_balance_2025.column.{built,green,trees}_verdict`, `layer.art8_balance_2026.column.{built,green,trees}_verdict` | Each code now has its own gloss. `built_verdict` says up «plus de bâti au-delà du bruit : imperméabilisé», down «moins de bâti … : désimperméabilisé», which is the English up/down for built-up; green and trees say «en hausse / en baisse au-delà du bruit». Nothing is softened. | none |
| resolved | `layer.fit_score.column.childcare`, `layer.fit_score.column.convenience`, `layer.fit_score.column.scenario`, `layer.fit_score.measures` | «crèche», «épicerie» and «aînés» now match `atlas.need.service.*` and the atlas scenario label. | none |

Open issues: none.

Verdict: 0 blocker, 0 major, 0 minor
