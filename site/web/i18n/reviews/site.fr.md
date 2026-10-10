# Review: part `site` (common, privacy, landing), Belgian French (fr-BE)

- Part: `site`, sections `common`, `privacy`, `landing`
- Language: fr-BE
- Drafting model: `claude-opus-5-5`
- Reviewing model: `claude-sonnet-5-5`
- Date: 2026-10-04
- Keys read: 331 (every key of the three sections, English against French; `tests/catalogues.test.ts` passes, 28 tests)

## What was checked

- Sense, key by key against `en.json`. No claim the site never makes was added. The cooling key (`landing.refusals.0.text`) still denies the claim, but its word order needs fixing (finding below). Refusals stay full outcomes («refuse de se prononcer», «ne reçoivent aucun verdict», «pas de comparaison équitable»). Every change is stated «par rapport aux zones témoins» or labelled as the raw «avant / après». Causes are named «documents à l’appui» or not at all.
- Numbers, years, percentages, ± and × signs, the 3-30-300 code: identical, in French notation (`0,29`, `45 %`, `95 %`, plain space before `%`, no plain space inside numbers). Script check of arguments and tags (`<em>`, `<b>`, `<a>`, `<mail>`): identical to English in all keys.
- Glossary: all terms follow the table (couvert arboré, espaces verts urbains, perte nette, tendance à l’augmentation, zones témoins, seuil, bruit, plancher de bruit, verdure, verdissement, secteur statistique, commune, Région, article 8, règlement (UE) 2024/1991). The EUR-Lex wording in `landing.law.p1` matches the French excerpt in `sources/`.
- Belgian usage and register: «vous» throughout, «chantier», «Anvers / Gand», «Autorité de protection des données», «introduire une réclamation», «Bruxelles Environnement», «SPW», «SNCB»; nothing France-only found, no «tu».
- Typography: « » only, ’ only, no straight or “ ” quotes, no U+00A0, a plain space before `; : ! ?` and inside « », no `1 000` typed with a plain space. Clean.
- `same.json`, French block: every key identical to English has an entry and every entry is identical (no missing, no stale). All reasons hold.
- Retold keys under «For a native reader», French rows: the ones listed are justified. Two keys were rewritten for the language but are not in the table: `landing.refusals.0.text` (word order, see below) and `landing.audiences.2.text` («draw the result to fit» became «ajuster le tracé au résultat»; this is a good reading, it echoes the FAQ question, but it should be listed).

## Findings

| severity | key | problem | suggestion | response |
|---|---|---|---|---|
| major | `landing.anyway.body` | «et ils ne sont plus que {k}»: the nearest plural masculine noun is «douze lieux», so «ils» reads as the twelve places («they are no more than 16»), not the sectors that still look greener. The sentence is one of the landing's central claims. | Comparez chaque secteur à son propre passé, et {share} de la ville semble « significativement plus verte ». Comparez-le à douze lieux qui lui ressemblaient au départ, et il n’en reste que {k}. | Fixed as suggested. |
| major | `common.charts.series.aria` | «pendant {above} étés sur {n}» gives «1 étés» (and «0 étés») when the count is 0 or 1; the series for audits within noise show exactly those values. | Effet par été, {from}–{to} : au-dessus du seuil pendant {above} des {n} étés | Fixed as suggested. |
| major | `common.charts.series.caption` | Same agreement fault: «<b>{above} étés sur {n}</b>» gives «1 étés». | Au-delà du bruit pendant <b>{above} des {n} étés</b>, {from}–{to}{opened, select, none {} other { · ouvert en {opened}}}{gap, select, none {} other { · aucun été dans la série : {gap}}} | Fixed as suggested. |
| major | `landing.refusals.0.text` | This is the key that must say the site never claims cooling. «Nulle part sur ce site, donc, un parc ne « rafraîchit la rue d’un degré »» is broken syntax (a stray «donc» after the fronted negation); a hurried reader or a text scraper can take the quoted phrase as a claim. «réalistement» is a calque. The denial must be unmistakable. | Notre plancher de bruit pour la température de surface est supérieur à l’effet qu’un nouveau parc peut raisonnablement avoir sur elle. C’est pourquoi aucun passage de ce site ne dit qu’un parc « rafraîchit la rue d’un degré ». | Fixed as suggested; listed under «For a native reader». |
| minor | `landing.audiences.0.who` | «rendent compte de l’article 8» means «give an account of the article»; the English means reporting under it. | Les Régions qui font rapport au titre de l’article 8 | Fixed as suggested. |
| minor | `landing.audiences.0.text` | «après l’état de référence de 2024»: one measures change «depuis» a baseline. | Si les espaces verts et le couvert arboré ont progressé ou reculé depuis l’état de référence de 2024, secteur par secteur, avec le bruit mesuré et chaque perte nommée. Bruxelles Environnement à Bruxelles ; en Flandre, l’ANB et l’INBO, qui assure le suivi ; en Wallonie, le SPW. | Fixed as suggested. |
| minor | `landing.law.title` | «la loi européenne compte les espaces verts urbains» can be read as «the law contains urban green spaces» (like «la loi compte 12 articles»). The drafter was right that «compter par la loi» is not French, but the replacement is ambiguous. | Depuis 2024, l’Europe est tenue de <em>compter ses espaces verts urbains.</em> | Fixed differently: «Depuis 2024, la loi oblige l’Europe à <em>compter ses espaces verts urbains.</em>», which keeps the law as the agent and is unambiguous. |
| minor | `landing.three.1.title` | «Quoi placer» is a colloquial question next to «Ce qui manque» and «Ce qui a changé»; the three headings should be one pattern. | Ce qu’il faut placer | Fixed as suggested. |
| minor | `landing.three.2.text` | «douze lieux qui se ressemblaient au départ» says the places looked like each other; the English means they looked like the sector (as `landing.anyway.body` says correctly). | Plus vert ou plus brun au-delà du bruit propre de la ville, par rapport à douze lieux d’aspect identique au départ. Seule cette étape mesure un changement ; les deux autres décrivent et recommandent. | Fixed with «douze lieux qui lui ressemblaient au départ», the same wording as `landing.anyway.body`, so the places resemble the sector. |
| minor | `landing.threshold.steps.1` | «qui avaient … et assez éloignés» drops the verb in the second branch. | Il est apparié à douze secteurs qui avaient au départ la même verdure et la même chaleur estivale, et qui sont assez éloignés pour ne pas partager ses chantiers. | Fixed as suggested. |
| minor | `landing.threshold.steps.2` | English says «all {n} effects»; the French drops «all», which is the point (every sector takes a turn). | Son « effet » est enregistré. Rien ne s’y est passé : la dispersion de l’ensemble des {n} effets est donc le bruit propre de la méthode. Le seuil de la ville est là où s’arrêtent 95 % de cette dispersion : ±{thr} à {city}. | Fixed as suggested. |
| minor | `landing.refusals.2.text` | «Un été brun» drops «single»; the heading says one season and the sentence is about exactly one. | Un seul été brun, c’est plus souvent la météo qu’une perte. Une baisse n’est publiée que si un second instrument indépendant voit le couvert arboré disparaître et qu’aucun chantier n’apparaît. | Fixed as suggested. |
| minor | `landing.law.stats.cityExemptWater` | «sans l’eau» is not idiomatic for the Regulation's «urban green space» without ponds and watercourses. | {city} : plus de 45 %, exemption · {v} hors plans d’eau | Fixed as suggested. |
| minor | `landing.anyway.effectCap` | «{refused} hachurés» does not agree if the count is 0 or 1 (and the ICU rule treats 0 and 1 alike in French). An invariable wording avoids it. | plus verts au-delà du bruit par rapport à 12 zones témoins · {down} en perte · {refused} sous hachures : pas de comparaison équitable | Fixed as suggested. |
| minor | `common.objects.one.toilets`, `common.objects.a.toilets`, `common.objects.no.toilets` | French has «toilettes» in the plural; «une toilette publique» and «aucune toilette publique» sound odd. «WC public» works in the singular (the plural key «Toilettes publiques» is right). | one: WC public; a: un WC public; no: aucun WC public | Fixed as suggested. |
| minor | `landing.showcase.maps.need` | «le cinquième le moins bien desservi en plus foncé» is a heavy tail. | Services du quotidien pour une famille, Bruxelles : le cinquième le moins bien desservi, en plus foncé | Fixed as suggested. |
| minor | `landing.cases.spoor-noord.story` | Title says «gare de triage», story says «gare de formation»: one place, two names. | La gare de triage de la SNCB a ouvert comme parc en 2008–2009. Sentinel-2 n’existait pas encore : l’audit utilise donc Landsat, qui remonte à 2006. | Fixed as suggested. |
| minor | `landing.faq.6.a` | «étalonnage» here, «calibré» in `landing.audits.p2`: two words for one idea. | {cities}. Le seuil appartient au couple formé par la ville et l’instrument : {wider}. Une nouvelle ville reçoit sa propre calibration. | Fixed the other way: «étalonnage» stays, and `landing.audits.p2` now says «étalonné», the usual French for calibrating an instrument. |
| minor | `common.charts.rings.aria` | «{summers} étés» gives «1 étés» for a park with a single summer; the English has the same flaw. Restructuring avoids it. | {place} : depuis {completed}, au-delà du bruit pendant {above} des {summers} étés. La largeur d’un anneau est l’effet par rapport à {n} zones témoins, seuil {thr}. | Fixed as suggested. |
| minor | `landing.showcase.notes.2` | «douze lieux» is the control set; every other page calls it «zones témoins». The English drops the adjective here, but a reader should not wonder whether these are different places. | <b>L’audit.</b> {effect} par rapport à douze zones témoins, chacune avec son nom et sa distance, pour que chacun puisse vérifier. | Fixed as suggested. |
| minor | `landing.showcase.alt` | Same: «douze lieux nommés» are the control places. | L’atlas Frondia sur l’audit de la Porte de Ninove : le panneau de la vue avec {up} secteurs plus verts et {down} en perte au-delà du bruit, la carte de Bruxelles avec des secteurs hachurés sans comparaison équitable, et la fiche d’audit avec un effet de {effect} par rapport à douze zones témoins nommées. | Fixed as suggested. |

## Notes on the source (English), not counted in the verdict

- `landing.law.close` says Frondia tells «whether it changed beyond noise, and why». `landing.faq.4.a` says «with documents, why», and the site's rule is that no cause is named without a document. The French follows the English faithfully («et pourquoi»), so this is not a translation fault, but the English should say «and, with documents, why». French then: «Frondia dit si cela a <em>changé</em> au-delà du bruit, et, documents à l’appui, pourquoi.»
- `landing.anyway.title`: «ont vraiment poussé» is fine as a retold line (the drafter lists it); «vraiment» carries the contrast the English gets from its bare second sentence.

Verdict: 0 blocker, 4 major, 17 minor

## Round 2

Reviewed: the 23 keys changed between `4208fa9` and `5964a22` in `fr.json` (`git diff` confirms 23, including `landing.audits.p2`, which was changed as part of the answer on «calibré / étalonnage»). `tests/catalogues.test.ts`, `messages.test.ts` and `icu.test.ts` pass. Arguments, tags, numbers (`12`, `95 %`, `±{thr}`), «  » quotes, plain spaces before `: ; !` and the ’ apostrophe of the changed keys are as the brief asks; no change adds or weakens a never-claim rule.

| severity | key | problem | suggestion |
|---|---|---|---|
| resolved | `landing.refusals.0.text` | Fixed. «C’est pourquoi aucun passage de ce site ne dit qu’un parc « rafraîchit la rue d’un degré »» is an unmistakable denial of cooling (same strength as the English «nowhere on this site»); «supérieur à» and «raisonnablement» are idiomatic and keep the sense (the noise floor is larger than the realistic effect). The key is now listed under «For a native reader». | none |
| resolved | `landing.anyway.body` | Fixed: «il n’en reste que {k}» cannot be taken as the twelve places. | none |
| resolved | `common.charts.series.aria`, `common.charts.series.caption`, `common.charts.rings.aria` | Fixed: «{above} des {n} étés» and «{above} des {summers} étés» agree for 0, 1 and any larger count. Select branches of the caption unchanged. | none |
| resolved | `landing.audiences.0.who`, `landing.audiences.0.text` | Fixed: «font rapport au titre de l’article 8», «depuis l’état de référence de 2024». | none |
| resolved | `landing.law.title` | Fixed differently, and acceptably: «la loi oblige l’Europe à compter ses espaces verts urbains» keeps «by law» as the agent, is unambiguous, and adds no claim the English does not make. The «For a native reader» row is updated. | none |
| resolved | `landing.three.1.title` | Fixed: «Ce qu’il faut placer» matches «Ce qui manque» and «Ce qui a changé». Also reads correctly inside `landing.showcase.threeAria` («… : ouvrir les points dans l’atlas»). | none |
| resolved | `landing.threshold.steps.1`, `landing.threshold.steps.2` | Fixed: «et qui sont assez éloignés», «de l’ensemble des {n} effets». | none |
| resolved | `landing.refusals.2.text` | Fixed: «Un seul été brun». | none |
| resolved | `landing.law.stats.cityExemptWater` | Fixed: «hors plans d’eau». | none |
| resolved | `landing.anyway.effectCap` | Fixed: «{refused} sous hachures» is invariable. | none |
| resolved | `common.objects.one.toilets`, `common.objects.a.toilets`, `common.objects.no.toilets` | Fixed: «WC public», «un WC public», «aucun WC public» (the plural key keeps «Toilettes publiques»). | none |
| resolved | `landing.showcase.maps.need` | Fixed: comma before «en plus foncé». | none |
| resolved | `landing.cases.spoor-noord.story` | Fixed: «gare de triage» in title and story. | none |
| resolved | `landing.faq.6.a`, `landing.audits.p2` | Fixed the other way, and acceptably: «étalonnage» and «étalonné» are the usual French for calibrating an instrument, and the two keys now agree. | none |
| resolved | `landing.showcase.notes.2`, `landing.showcase.alt` | Fixed: «zones témoins», with the feminine agreement («chacune», «nommées») correct. | none |
| open | `landing.three.2.text` | The fix «douze lieux qui lui ressemblaient au départ» leaves «lui» without an antecedent: unlike `landing.anyway.body`, this sentence has no noun («Plus vert ou plus brun …») that «lui» can refer to, so the reader asks «lui = qui ?». The English is itself vague, but French needs the point of comparison named or left out. | Plus vert ou plus brun au-delà du bruit propre de la ville, par rapport à douze lieux d’aspect identique au départ. Seule cette étape mesure un changement ; les deux autres décrivent et recommandent. |

Open issues: one minor.

Verdict: 0 blocker, 0 major, 1 minor

Drafter’s response to round 2: `landing.three.2.text` now reads «par rapport à douze lieux qui ressemblaient au secteur au départ», which names the antecedent and keeps the sense (the places looked like the sector before), rather than «d’aspect identique», which would drop the comparison with the sector.
