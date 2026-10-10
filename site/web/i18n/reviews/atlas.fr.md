# Review: part `atlas`, Belgian French (fr-BE)

- Part: `atlas` (the `atlas` section of the catalogue)
- Language: fr-BE
- Drafting model: `claude-opus-5-5` (draft commit `915b08c`)
- Reviewing model: `claude-sonnet-5-5`
- Date: 2026-10-04
- Keys read: 328 (325 strings and 3 `null` legend gaps), plus all 538 rendered lines of `task-12-report.md` (269 French, read in full); `tests/catalogues.test.ts`, `messages.test.ts` and `icu.test.ts` pass

## What was checked

- **Agreement in the rendered lines (French).** All 14 objects × `place.register.at` (1/0 and 2/3), `place.register.none` («il n’y a aucun banc» / «aucune poubelle» / «aucun WC public»), `place.title`, `tip` and `passport` roles («banc · #3 · point nommé», the participle carried by «point»); all 4 groups × `equity.ages.*`; `equity.livesIn` with and without a cut; `equity.reading.shops` («plus loin d’une boulangerie / d’un café / d’une confiserie»); `equity.byIncome.*`; `place.register.gap` and `caution`; `more.who` at 0, 1 and 2 (`one` covers 0 and 1: «0 se trouve», «2 se trouvent»); `more.whoOne`; the count lines at 0, 1 and 2 (counts follow their labels: «habitants : 1», «secteurs : 0»); `registered.lede` for Brussels («Projets Beliris à Bruxelles»), Ghent, Antwerp; `change.threshold`; `communes.unstable.other` with Ixelles, Elsene, Watermael-Boitsfort, Anderlecht. No agreement error found; no «de Anvers» / «de Ixelles» anywhere («à {city}», «Pour {name},»; «hors d’Anvers» is correct). One sentence that agrees but cannot be parsed easily: the first finding.
- **Temperature is a state.** The heat lens says «De combien le sol est plus chaud en été que dans le secteur médian», `equity.reading.heat` says «vit sur un sol plus chaud / moins chaud», the passport says «par rapport à la ville»: where it is hotter, never an effect of greening. `need.lenses.heat.limit` denies cooling in the conditional («la méthode ne peut pas mesurer le refroidissement qu’apporterait un parc (plancher de bruit 1,32 °C)»); `place.limit` keeps «Une recommandation, pas un effet».
- **«What changed».** Counts are «en verdissement au-delà du bruit» / «en perte au-delà du bruit» against zones témoins; the raw view is «d’aspect plus vert» / «Paraît plus vert» and the subtraction is explicit (`change.subtract`, `change.background`, `balance.raw`). `built.rawOff`: «Affiché uniquement par rapport aux zones témoins».
- **Refusal.** «Aucune zone comparable — refusé», `passport.refused` («C’est un résultat, pas une lacune»), `registered.refused`, `built.word.refused` are all full outcomes.
- **Dynamic World.** «une probabilité de classe, pas une part du sol» (`built.limit`); hectares «selon la classification du sol de Dynamic World» (`balance.lede`); never a share.
- **Tooltips and short labels.** «Manque», «Placer», «Changé», «Affichage», «Zoomer/Dézoomer», «point nommé / point de comparaison / autre candidat» are clear; «Manque» for «Missing» works with «Ce qui manque» one tap away.
- **Article 8 terms** against the French EUR-Lex text: «article 8, paragraphe 1», «article 3, point 20», «centres urbains et pôles urbains», «UAL (LAU 2024)», «AEE», «absence de perte nette»/«perte nette», «couvert arboré», «règlement», «tendance»; the EEA/JRC method line is faithful.
- **Glossary, numbers, typography.** Every term follows the table (zones témoins, bruit, seuil, plancher de bruit, verdure, verdissement, verdict, imperméabilisé/désimperméabilisé, vue for the lens). Numbers agree in French notation (`1,32 °C`, `0,0458`, `19 000 €`, `45 %`, plain space before `%` and `:`). Script check: arguments, tags, select and plural keywords match English in every key; « » with plain spaces inside, ’ only, no straight or “ ” quotes, no U+00A0.
- **`same.json`.** Every French key identical to English has an entry, and no entry is stale. Reasons hold.
- **Belgian usage and register.** «vous»/impersonal, «crèche», «épicerie», «médecin généraliste», «transports en commun», «Aînés», «WC public», «Confiserie», «AEE». Nothing France-only that Belgium avoids.
- **Retold keys, French rows of «For a native reader»:** all justified, including `registered.lede` («Projets Beliris à Bruxelles»), `communes.unstable.*` («bénéficierait de l’exemption», no gender needed), `change.threshold` («à {city}»), `pts` («pt» at every count, accepted in the documents round), `equity.reading.r3` («Le tiers … se trouve plus souvent … là où …»).

## Findings

| severity | key | problem | suggestion | response |
|---|---|---|---|---|
| major | `atlas.equity.ages.one`, `atlas.equity.ages.split`, `atlas.equity.ages.both` | With the 3-30-300 group the rendered lines read «Les enfants vivent plus souvent dans les secteurs qui ne respectent aucune des deux parties que l’ensemble des habitants»: the comparison «que l’ensemble des habitants» lands right after «aucune des deux parties», so «que» can be taken as the relative of the negation («aucune des deux parties que …»). The line is long and ambiguous in 6 of the 24 rendered sentences of each key (and clumsy in the others). Putting the comparison before the group removes the collision for all four groups and keeps every argument. | `ages.one`: {who, select, kid {Les enfants} other {Les personnes de 65 ans et plus}} vivent {more, select, yes {plus} other {moins}} souvent que l’ensemble des habitants dans {group} : {x} contre {all}. `ages.split`: {more, select, kid {Les enfants} other {Les personnes de 65 ans et plus}} vivent plus souvent que l’ensemble des habitants dans {group}, {more, select, kid {les personnes de 65 ans et plus} other {les enfants}} moins souvent : {x} et {y} contre {all}. `ages.both`: Les enfants et les personnes de 65 ans et plus vivent tous deux {more, select, yes {plus} other {moins}} souvent que l’ensemble des habitants dans {group} : {x} et {y} contre {all}. | Fixed as suggested: the comparison now comes before {group} in all three keys. The 32 re-rendered lines (4 groups × every branch) are in the task report, under «Round 1 fixes». |
| minor | `atlas.need.lenses.services.lede` | «l’un de trois modes de vie» is not French; it is «l’un des trois modes de vie». | Dans quelle mesure un secteur répond à la vie quotidienne, d’une école et d’un médecin généraliste à un parc et un arrêt de tram, pondéré selon l’un des trois modes de vie. | Fixed as suggested. |
| minor | `atlas.communes.leaveOut` | «L’obligation d’absence de perte nette» is a noun pile; the glossary form «qu’il n’y ait pas de perte nette» (EUR-Lex wording) reads better and passes the term check. | Exclure les {n} retirerait du décompte {area} de la superficie de la région et {res} de ses habitants, mais {woody} de sa végétation ligneuse. L’obligation qu’il n’y ait pas de perte nette reposerait sur {rest} communes denses, avec en moyenne {restGreen} d’espaces verts. | Fixed, worded differently: «Ce seraient alors {rest} communes denses, avec en moyenne {restGreen} d’espaces verts, qui devraient garantir qu’il n’y ait pas de perte nette.» The obligation becomes a verb phrase, so no noun pile is left, and the EUR-Lex wording «qu’il n’y ait pas de perte nette» stays. |
| minor | `atlas.zoom.reset` | «Réinitialiser la vue» now clashes with «vue» as the lens (glossary) and with the new «Affichage» for the View switch; the English means the map view. | Réinitialiser l’affichage | Fixed as suggested. |

## Notes on the source (English), not counted in the verdict

- `atlas.need.lenses.heat.lede` says «Canopy is the strongest shield»; the French («le meilleur bouclier») follows it, with «à {city}, les deux sont liés avec r = {r}» saying only that the two move together. «Shield» is protective, causal language next to a lens that is explicitly a state. Not a translation fault, but the English could drop or soften it.

Verdict: 0 blocker, 1 major, 3 minor

## Round 2

Reviewed: the 6 keys changed between `915b08c` and `227460e` in `fr.json` (`git diff` confirms 6), and all 32 re-rendered lines of «Round 1 fixes» in `task-12-report.md` (`equity.ages.one`, `split` and `both` × the four groups × every branch). `tests/catalogues.test.ts`, `messages.test.ts` and `icu.test.ts` pass. Arguments, select keywords, numbers and typography (« » spacing, plain space before `:` and `%`) of the changed keys are unchanged.

| severity | key | problem | suggestion |
|---|---|---|---|
| resolved | `atlas.equity.ages.one`, `atlas.equity.ages.split`, `atlas.equity.ages.both` | Fixed. All 32 rendered lines are grammatical and unambiguous: with the comparison before the group, «que l’ensemble des habitants dans les secteurs qui ne respectent aucune des deux parties : 31 % contre 24 %» has no «que» collision, and the other three groups («le tiers le moins bien desservi», «le tiers le plus éloigné», «le tiers le plus chaud») read as well as before. `ages.none` is untouched and was already correct. The heat sentences still describe where people live, never an effect. | none |
| resolved | `atlas.need.lenses.services.lede` | Fixed: «l’un des trois modes de vie». | none |
| resolved | `atlas.zoom.reset` | Fixed: «Réinitialiser l’affichage» no longer collides with «vue» as the lens and matches «Affichage». | none |
| accepted | `atlas.communes.leaveOut` | The drafter's own wording, «Ce seraient alors {rest} communes denses, avec en moyenne {restGreen} d’espaces verts, qui devraient garantir qu’il n’y ait pas de perte nette», is acceptable: the noun pile is gone, the glossary term «pas de perte nette» is present (the term check passes), «devraient garantir» keeps the duty on those communes and claims nothing the English does not, and the sentence agrees for the Brussels values the page shows (several dense communes). A reading nit, not counted: EUR-Lex itself says «veillent à ce qu’il n’y ait pas de perte nette», and «garantir qu’il n’y ait» takes the subjunctive only loosely; «veiller à ce qu’il n’y ait» would be the more exact verb. | none |

Open issues: none.

Verdict: 0 blocker, 0 major, 0 minor
