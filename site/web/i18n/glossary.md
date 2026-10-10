# Frondia glossary: English, Belgian Dutch, Belgian French

The working material for the models that translate Frondia (plan 5, tasks 10–13). It has four parts: the terms, the
drafter's brief, the reviewer's prompt, and the list of lines rewritten for a native reader.

The Regulation's wording comes from EUR-Lex, read on 2026-10-04. The excerpts used are in `sources/`, each with its
address and the date it was read:

- NL: `sources/eurlex-32024R1991-nl.txt` (https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:32024R1991)
- FR: `sources/eurlex-32024R1991-fr.txt` (https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32024R1991)

Where the official text differs from an earlier candidate in the plan, the official wording is used, and `why` says so.

## Terms

`tests/catalogues.test.ts` checks this table (parsed by `tests/glossary.ts`). A row whose first three cells are
`code` is a check. Each cell is a regular expression, matched without regard to case. Wherever the English of a
catalogue message matches the `en` cell, that message's translation must match the `nl` or `fr` cell. Inside a cell,
`\|` is the regex alternation; a bare `|` ends the cell. A row with plain cells is guidance only: the word is
polysemous, and a regex would trap good translations. Rows whose `source` starts with `EUR-Lex` are also tested
against the excerpts in `sources/`. A line kept in English with a reason in `same.json`, such as the rights holders'
credits, is not a translation, so no term applies to it.

| en | nl | fr | source | why |
|---|---|---|---|---|
| `Nature Restoration Regulation` | `natuurherstelverordening\|verordening inzake natuurherstel\|Verordening \(EU\) 2024/1991` | `règlement relatif à la restauration de la nature\|règlement \(UE\) 2024/1991` | EUR-Lex, title | NL title: «Verordening (EU) 2024/1991 … inzake natuurherstel». «Natuurherstelverordening» is not in EUR-Lex, but it is the short name the Flemish and Dutch governments use; prefer it in running text. FR title: «règlement (UE) 2024/1991 … relatif à la restauration de la nature». |
| `Regulation \(EU\) 2024/1991` | `Verordening \(EU\) 2024/1991` | `règlement \(UE\) 2024/1991` | EUR-Lex, title | The number stays. French writes «(UE)», with a lower-case «règlement» inside a sentence. |
| `\bArticle 8\b` | `\bartikel 8\b` | `\barticle 8\b` | EUR-Lex, Art. 8 | Cite paragraphs as EUR-Lex does: «Article 8(1)» becomes nl «artikel 8, lid 1» and fr «article 8, paragraphe 1». A bare «Article 8» label (nav, footer) is «Artikel 8» / «Article 8». |
| `\burban ecosystems?\b(?! areas?)` | `stedelijke? ecosyste(em\|men)` | `écosystèmes? urbains?` | EUR-Lex, Art. 8 heading | Art. 8 heading: nl «Herstel van stedelijke ecosystemen», fr «Restauration des écosystèmes urbains». |
| `\burban ecosystem areas?\b` | `stedelijke? ecosysteemgebied` | `zones? d[’']écosystème urbain` | EUR-Lex, Art. 8(1), 14(4) | nl «stedelijke ecosysteemgebieden», singular «stedelijk ecosysteemgebied». FR is singular «écosystème»: «zones d’écosystème urbain». The candidate «zones d’écosystèmes urbains» is not the official wording. |
| `\burban green space\b` | `stedelijke groene ruimte` | `espaces? verts? urbains?` | EUR-Lex, Art. 3(20) | Defined terms: nl «stedelijke groene ruimte», fr «espaces verts urbains». |
| `\burban green\b(?! space)` | `stedelijke? groen` | `verts? urbains?` | EUR-Lex, Art. 3(20) | The short form in labels and leads. nl «stedelijk groen» or the full «stedelijke groene ruimte»; fr «espaces verts urbains». |
| `\btree canopy\b` | `kroonbedekking` | `couvert arboré` | EUR-Lex, Art. 3(21) | The legal term is nl «stedelijke boomkroonbedekking», fr «couvert arboré urbain»; use it whenever the law is meant. A label for the measured layer can drop «stedelijke» / «urbain» («Boomkroonbedekking», «Couvert arboré»). |
| `\bno net loss\b` | `nettoverlies` | `pas de perte nette\|absence de perte nette` | EUR-Lex, Art. 8(1) | nl «geen nettoverlies». FR officially says «qu’il n’y ait pas de perte nette»; as a noun, «absence de perte nette». «Aucune perte nette», the plan's candidate, is not the official wording and fails the check. |
| `\bupward trend\b` | `toenemende trend` | `tendance à l[’']augmentation` | EUR-Lex, Art. 8(2), 8(3) | The law's words for what follows 2030. |
| `\burban centres and clusters\b` | `stedelijke centra en (stedelijke )?clusters` | `centres urbains et (les )?pôles urbains` | EUR-Lex, Art. 3(16), 8(1) | The 45 % / 10 % exemption is measured here. FR «pôles urbains», not «clusters». |
| `\blocal administrative units?\b\|\bLAU\b` | `\bLBE\b\|lokale bestuurlijke eenhe(id\|den)` | `\bUAL\b\|unités? administratives? locales?` | EUR-Lex, Art. 3(15) | NL officially says «lokale bestuurlijke eenheid» («LBE»), not the candidate «lokale administratieve eenheid». FR: «unité administrative locale» («UAL»). Eurostat's dataset name «LAU 2024» may be kept in brackets after the term. |
| `\bstatistical sectors?\b` | `statistische sector` | `secteurs? statistiques?` | Statbel | Statbel's own names: «statistische sector» / «secteur statistique». |
| `\bcommunes?\b` | `gemeente` | `commune` | Statbel; Belgian usage | Belgian Dutch says «gemeente», never «commune». |
| `(?<!\.)\bBrussels\b` | `Brussel` | `Bruxelles` | spec §2 | The city (site_data.py `CITY_I18N`). A web address such as «quartiers.brussels» is not the city and needs no translation. |
| `\bAntwerp\b` | `Antwerpen` | `Anvers` | spec §2 | |
| `\bGhent\b` | `\bGent\b` | `\bGand\b` | spec §2 | |
| `\bLiège\b` | `\bLuik\b` | `\bLiège\b` | spec §2 | |
| `Liège \(north\)` | `Luik \(noord\)` | `Liège \(nord\)` | site_data.py `DISTRICT_I18N` | Frondia's own district label (Task 5), not a Statbel name. |
| `Liège \(south\)` | `Luik \(zuid\)` | `Liège \(sud\)` | site_data.py `DISTRICT_I18N` | Frondia's own district label. |
| `\bHaven\b` | `\bHaven\b` | `\bPort\b` | site_data.py `DISTRICT_I18N` | Antwerp's port district: a Frondia label. |
| `\b(matched\|comparable\|control\|comparison) (control )?(places?\|sectors?)\b` | `vergelijkings(plaats\|sector)\|vergelijkbare` | `(zones?\|secteurs?) témoins?\|comparables?` | method | The 12 sectors picked by their state before the change, in every English wording (matched, comparable, control or comparison places or sectors). nl «vergelijkingsplaatsen», or «vergelijkingssectoren» where the text means sectors; «vergelijkbare» where the English says «comparable». fr «zones témoins», or «secteurs témoins» where the text means sectors: «témoin» is the control of an experiment («parcelle témoin»). «Lieux témoins» is not the idiom. |
| `significance threshold\|threshold of significance` | `significantiedrempel` | `seuil de significativité` | method | The usual statistical terms. In French, add «(plancher de bruit)» after the first use on a page, so the reader links it to the noise. «Threshold» alone stays nl «drempel», fr «seuil». |
| `\bnoise\b` | `ruis` | `bruit` | method | The signal-processing sense, used throughout: «beyond noise» = nl «boven de ruis», fr «au-delà du bruit»; «within noise» = nl «binnen de ruis», fr «dans le bruit». |
| `\bgreenness\b` | `groenheid` | `indice de végétation\|verdure` | method | NDVI: greenness, not canopy. fr: «indice de végétation (NDVI)» for the instrument, «verdure» in running text. «Verdeur» is wrong: it means tartness or vigour. nl «groenheid»; the first mention can add «(NDVI)». |
| `\bgreen(er\|ing)\b` | `groener\|vergroen` | `plus verts?e?s?\|verdi\|verdissement` | method | «Greener beyond noise» = nl «groener boven de ruis», fr «plus vert au-delà du bruit»; «greening» = nl «vergroening», fr «verdissement». A sector «verdi» / «vergroend». |
| refused, refusal (no verdict) | geweigerd, weigering («Frondia weigert een oordeel te vellen») | refusé, refus («Frondia refuse de se prononcer») | method | A refusal is an outcome in its own right, on a par with «no significant effect». Never soften it to «unknown» or «not available». Pill and table labels stay one word: «geweigerd» / «refusé». |
| intervention | ingreep (plural ingrepen) | intervention | method | What a city actually did on the ground. Dutch «interventie» sounds clinical. |
| effect against matched places | effect ten opzichte van de vergelijkingsplaatsen | effet par rapport aux zones témoins | method | The method's main quantity, never the raw change. |
| canopy | kroon, kroonbedekking | couvert arboré, canopée | method | NDVI is greenness, not canopy: keep the two apart. |
| built-up, sealed | bebouwd, verhard (verharding) | bâti, imperméabilisé (imperméabilisation) | method | «Sealed ground» = nl «verharde grond», fr «sol imperméabilisé». |
| dossier | dossier | dossier | method | The same word in all three languages. |
| audit | audit | audit | method | An audit of one project. |
| register (of interventions) | register (van ingrepen) | registre (des interventions) | method | |
| atlas | atlas | atlas | method | |
| `\blens\b` | `weergave` | `\bvues?\b` | method | A lens is one view of the atlas (what is lacking, heat, 3-30-300…). nl «weergave» is the plain word for a way of showing a map («Open deze weergave»); «invalshoek» reads as an argument, not a map view. fr «vue» («Ouvrir cette vue»), as in a map application; «lentille» is a calque, and nobody says it of a map. |
| threshold | drempel | seuil | method | |
| verdict | oordeel | verdict | method | Dutch «verdict» is legal-only. |
| sector | sector | secteur | Statbel | The statistical sector. |

## How to translate

You draft one part of the site's catalogue (`messages/<lang>.json`) or of the data texts
(`scripts/site/i18n/<lang>.json`) into Belgian Dutch (nl-BE) or Belgian French (fr-BE). A second model reviews it with
the prompt under «Review».

1. **Language.** Dutch as written in Flanders: «gemeente», «gewest» (Brussels Hoofdstedelijk Gewest, Vlaams Gewest),
   and the «u» form when the reader is addressed. French as written in Belgium. Numbers are digits, so «septante» and
   «nonante» never come up. The tone is calm and exact, never promotional.
2. **Sense before words.** Translate what the English means, not its word order. **Headings and the landing's main
   lines are rewritten for the language, not calqued.** Every key you rewrite this way goes into «For a native reader»,
   with one line on what you changed and why.
3. **Terms.** Use the table above. The Regulation's terms are the official EUR-Lex wording. The method's terms are the
   chosen translations, kept the same on every page. A term not in the table stays the same through the whole part.
4. **The ICU shape stays.** Same arguments (`{city}`), same `select` and `plural` keywords and options, and the same
   tags (`<em>`, `<a>`, `<b>`, `<mail>`), placed where the sense needs them. Every `plural` keeps at least `one` and
   `other`. In French, `one` covers 0 and 1 («0 secteur»). Do not write a number where the English has an argument.
   Never translate a key named `id` or `key`, or a register filter's `k` (`lib/pseudo.ts` `ID`): code reads them.
5. **Numbers.** Copy every number, year, code and percentage exactly; never compute one. Write it in the language's
   notation:
   - Dutch: groups with «.» («1.246.136»), decimals with «,» («0,0373»), percent without a space («39%»).
   - French: groups with **U+202F, the narrow no-break space** («1 246 136», «1 000»), decimals with «,» («0,0373»),
     percent after a **plain space** («39 %»; `tie()` makes it narrow). A plain space inside a number is wrong: the
     test reads «1 000» typed with a plain space as two numbers.
   - Ranges with «–» («2017–2024»), and «3-30-300» as is.
   The test (`scripts/numbers.mjs`) compares each message's numbers with the English ones, so «1.5 km» in Dutch fails.
6. **Quotes and spaces.** Dutch uses ‘ ’, French « », both with the apostrophe ’, never a straight ' or ".
   - French: put a **plain** space before ; : ! ? and inside « » («« mot »»). Do not type U+00A0 anywhere: `tie()` sets
     the no-break spaces when the page renders.
   - Neither language uses “ ”.
7. **What stays as written.** Keep these untranslated:
   - place names as Statbel spells them in the language (the data supplies sector and commune names);
   - project and contract names, and quotations, in their original language;
   - the rights holders' credits (`credits`, `credit`) and licence names;
   - brands and product names (Sentinel-2, Landsat, Dynamic World, Copernicus, OpenStreetMap, Frondia);
   - codes («NDVI», «3-30-300», «LAU 2024» when it names the dataset).
   Codes keep their owners' spelling in every language, point included: «CC BY 4.0», «ODbL 1.0», the UN «indicator 11.7»
   (nl «VN-indicator 11.7», fr «l’indicateur 11.7»). They are names, not quantities, so the number check leaves them out
   (`tests/catalogues.test.ts` `CODES`).
   A key left identical to the English needs an entry in `i18n/same.json` with the reason.
8. **Never add a claim.** The site never promises cooling («minus X degrees»), never names a cause without a document,
   and never claims to verify scattered street planting at sector level. A translation must not add such a claim, or
   make a refusal sound softer than the English. Two more method rules hold in every language: a
   change is always the **effect against the matched places**, never the raw change; and a **refusal is an outcome** («the
   comparison does not hold», «no defensible footprint»), never a missing value. The method's rules in the project's `CLAUDE.md` hold in every
   language. Numbers come from the engine; the text only reads them.
9. **Length.** Dutch and French run 20–35 % longer. Keep buttons, pills and table headings short; where the English is
   one word, look for one word.

## Review

The reviewer subagent receives this prompt word for word, with the part, the language and the files.

> You review a machine translation of one part of the Frondia site from English into Belgian Dutch (nl-BE) or
> Belgian French (fr-BE). You are a different model from the one that drafted it. Read `site/web/i18n/glossary.md`
> first: its «Terms» table and «How to translate» are the rules the drafter followed.
>
> Read the English and the translation key by key, the whole part, and check each key for:
>
> 1. **Sense.** Does it say what the English says? Look for anything omitted, anything added (above all a claim the
>    English does not make: cooling, a cause, a softer refusal), and anything turned around.
> 2. **Numbers.** Are they the same, in the language's notation (nl «1.246.136», «0,0373», «39%»; fr «1 246 136» with
>    U+202F, «0,0373», «39 %»)?
> 3. **Glossary.** Is every term from the table translated as the table says, and the same way throughout?
> 4. **Belgian usage.** Is it Flemish Dutch («gemeente», «gewest», «u») or Belgian French, not Netherlands Dutch or
>    French from France where the two differ?
> 5. **Agreement with real values.** For each message with arguments, substitute real values (a city, a commune, 0, 1, 2,
>    1000) and read the result aloud: do gender, number and articles agree?
> 6. **Headings.** Is each heading as short as the English one, and natural?
> 7. **Claims the site never makes.** Flag as `blocker` any text that promises cooling, names a cause without a
>    document, or reads raw change as an effect. Red-flag words: fr «à cause de», «grâce à», «degrés», «rafraîchit»,
>    «refroidit», «fraîcheur»; nl «door» or «dankzij» (as a cause), «graden», «koelt», «verkoelt», «afkoeling». The test
>    fails cooling words where the English key has none; causes and degrees are yours to catch.
> 8. **Register and tone.** Is it calm and exact, never promotional? Do the quotes, apostrophes and spaces follow the brief?
>
> Write `site/web/i18n/reviews/<part>.<lang>.md`:
>
> - A header with the part, the language, the drafting model (`claude-opus-5-5`), the reviewing model (your own model
>   identifier), the date, and the number of keys read.
> - A table `| severity | key | problem | suggestion |`. The severities:
>   - `blocker`: the sense is distorted, a number or a term is wrong, or a text is in another language;
>   - `major`: unnatural for a native speaker, the wrong register, or the wrong method term;
>   - `minor`: style.
>   Write the suggestion as the full corrected text of the key.
> - The last line: `Verdict: N blocker, N major, N minor`.
>
> Round 2: read only the keys changed since round 1, and add a new table under `## Round 2` in the same file, ending
> with its own `Verdict:` line.
>
> Report what you find; do not edit the catalogue.

## For a native reader

The keys rewritten for the language rather than translated, for a future review by a native speaker. Tasks 10–12 fill
this list: `key`, language, the English, the translation, and what changed.

| key | lang | English | translation | what changed |
|---|---|---|---|---|
| `landing.meta.title` | nl | Frondia — what actually changed | Frondia — wat er echt veranderd is | Dutch says what has changed in the perfect tense; the simple past reads as a story. |
| `landing.meta.title` | fr | Frondia — what actually changed | Frondia — ce qui a vraiment changé | «Ce qui a changé» is the French turn; «actually» becomes «vraiment». |
| `landing.hero.title` | nl | What actually <em>changed.</em> | Wat er echt <em>veranderd is.</em> | Perfect tense, as in the title; the stress falls on the participle and its verb. |
| `landing.hero.title` | fr | What actually <em>changed.</em> | Ce qui a vraiment <em>changé.</em> | The French relative turn; the stress stays on the participle. |
| `landing.hero.lede` | nl | Every summer the city’s green rustles — a little greener, a little browner. Frondia tells the rustle from the growth, measured against places that stayed the same. | Elke zomer ritselt het groen van de stad — wat groener, wat bruiner. Frondia onderscheidt het geritsel van de groei, gemeten tegen plaatsen die hetzelfde bleven. | The rustle is «ritselen / geritsel» (leaves), kept through the page and the motto; «tells … from» becomes «onderscheidt … van». |
| `landing.hero.lede` | fr | (as above) | Chaque été, la verdure de la ville bruisse — un peu plus verte, un peu plus brune. Frondia distingue le bruissement de la croissance, en mesurant par rapport à des lieux restés les mêmes. | The rustle is «bruisser / bruissement» (leaves), which also echoes «bruit», the method’s noise; «green» in running text is «verdure» (glossary). |
| `common.footer.motto` | nl | , the growth, not the rustle. | , de groei, niet het geritsel. | Follows «frondia»; the same rustle word as the hero. |
| `common.footer.motto` | fr | , the growth, not the rustle. | , la croissance, pas le bruissement. | Follows «frondia»; the same rustle word as the hero. |
| `landing.anyway.title` | nl | Between 2017 and 2024 all of Brussels got greener. <em>{words} places grew.</em> | Tussen 2017 en 2024 werd heel Brussel groener. <em>{words} plaatsen groeiden echt.</em> | «Echt» carries the contrast that English gets from the bare second sentence. |
| `landing.anyway.title` | fr | (as above) | Entre 2017 et 2024, tout Bruxelles a verdi. <em>{words} zones ont vraiment poussé.</em> | «Pousser» is what plants do; «vraiment» carries the contrast. «Zones» is feminine so that `landing.words.1` («Une») agrees, as it does with «villes» and «saisons» elsewhere. |
| `landing.anyway.body` | nl | … and {k} do. | … en dan zijn het er nog {k}. | English ends on an elliptic «do»; Dutch needs the count said outright. |
| `landing.anyway.body` | fr | … and {k} do. | … et il n’en reste que {k}. | Same reason: French cannot end on an auxiliary; the impersonal «il n’en reste» cannot be read as the twelve places. |
| `landing.anyway.tiles.threshold` | fr | {city} city threshold · {other}’s is {p}% wider | seuil à {city} · {p} % plus large à {other} | «celui de {other}» would print «de Anvers»; «à» needs no elision for any of the five cities. |
| `landing.questions.widerFirst`, `narrowerFirst`, `wider`, `narrower` | fr | {name}’s is {p}% wider than Brussels’ | à {name}, il est {p} % plus large qu’à Bruxelles | Same elision reason («de Anvers»); «il» is the threshold of the sentence before. |
| `landing.law.title` | fr | Since 2024, Europe counts urban green <em>by law.</em> | Depuis 2024, la loi oblige l’Europe à <em>compter ses espaces verts urbains.</em> | «Compter par la loi» is not French; the law becomes the subject and the stress moves to what Europe must count. |
| `landing.law.close`, `landing.faq.1.a` (trees) | fr | By rank the two agree | En corrélation de rang, les deux concordent | «Par rang» means nothing on its own in French; the statistical name says what is compared. |
| `landing.audits.title` | nl | … each with its caveat printed. | … elk met zijn voorbehoud erbij. | «Gedrukt» would be literal; «erbij» says it comes with the number. |
| `landing.audits.title` | fr | … each with its caveat printed. | … chacun avec ses réserves noir sur blanc. | «Noir sur blanc» is the French idiom for printed, stated openly. |
| `landing.three.1.title` | nl | What to place | Wat waar komt | «Wat plaatsen» is not a Dutch heading; «what goes where» is. |
| `landing.cases.droogdokkenpark.reading` | nl | … half the headline … | … de helft van het getal op papier … | Ties back to the case title «+0,29 op papier»; «koppengetal» is jargon. |
| `landing.cases.spoor-noord.title` | nl | A rail yard became <em>nineteen hectares</em> of grass. | Een rangeerterrein werd <em>negentien hectare</em> gras. | «Spoorwegemplacement» did not fit a 320 px screen; «rangeerterrein» is the common word. |
| `landing.audits.controls` | nl | Controls | Vergelijking | A label above «12 benoemd»; «Vergelijkingsplaatsen» (the glossary term) did not fit the card from 320 to 1280 px. |
| `landing.words.1` | nl | One | Één | Written with both accents so that the code’s lower-casing gives «één». |
| `landing.refusals.0.text` | fr | Our noise floor for surface temperature is larger than what a new park realistically does to it. So nowhere on this site does a park “cool the street by a degree”. | Notre plancher de bruit pour la température de surface est supérieur à l’effet qu’un nouveau parc peut raisonnablement avoir sur elle. C’est pourquoi aucun passage de ce site ne dit qu’un parc « rafraîchit la rue d’un degré ». | The denial of cooling: French cannot front «nulle part» before a quoted claim without the quote reading as a statement, so the sentence says outright that no passage makes the claim. |
| `landing.audiences.2.text` | fr | … so nobody can draw the result to fit afterwards. | … pour que personne ne puisse, après coup, ajuster le tracé au résultat. | «Dessiner le résultat» is not French; what could be drawn to fit is the outline, as the FAQ question says. |
| `landing.cases.ninove.place` (and the same name in `threshold.hist.marker`, `anyway.tiles.ninove`, `showcase.browserAria`, `showcase.alt`, `cases.ninove.story`) | nl | Porte de Ninove | Porte de Ninove | Kept as the project’s French name (How to translate 7). A Flemish reader knows the site as «Ninoofsepoort»: Elena’s call whether to switch. |
| `dossier.passport.eyebrow` | nl | Passport | Steekkaart | «Paspoort» reads as a travel document; «steekkaart» is the Flemish word for a fact card. |
| `dossier.passport.eyebrow` | fr | Passport | Fiche d’identité | «Passeport» reads as a travel document; a sector’s card is a «fiche d’identité». |
| `dossier.passport.canopy`, `dossier.passport.built` | nl | …, class probability | …, kans per klasse | «Klassewaarschijnlijkheid» is one 24-letter word that pushed the 320 px page sideways. |
| `dossier.trend.title` | nl | It will not improve by itself | Vanzelf wordt het niet beter | Dutch puts «vanzelf» first for the stress; the literal order reads flat. |
| `dossier.picked` | nl | … {n} sectors fit; … | … Er voldoen er {n}; … | The count is said without a noun, so 1 never reads «1 sectoren». |
| `dossier.picked` | fr | … {n} sectors fit; … | … Secteurs retenus : {n} ; … | Same reason: no agreement at 0 or 1. |
| `dossier.place.lede` | nl, fr | {n} of the planner’s ranked points fall in this sector. | Gerangschikte punten van de planner in deze sector: {n}. / Points classés du planificateur situés dans ce secteur : {n}. | A label and a count, so the verb never disagrees with 1. |
| `dossier.noPick` | fr | … {city} is exempt under Article 8(1) … | … {city} bénéficie de l’exemption de l’article 8, paragraphe 1 … | «Exempté(e)» would need a gender for a city name; the noun turn needs none. |
| `dossier.trend.law.counted.body`, `dossier.trend.law.exempt.body` | nl | {commune} does / passes … | De gemeente {commune} … | Dutch names the kind of place before a commune’s name («de gemeente Elsene»); it also gives «haar» an antecedent. |
| `dossier.trend.law.counted.body` | nl, fr | … enters the national count of no net loss. | … telt mee in het nationale totaal, dat geen nettoverlies mag lijden. / … entre dans le total national, qui doit respecter l’absence de perte nette. | «The count of no net loss» is a noun pile in both; the total is named and the rule follows it. |
| `dossier.fair.kids.body` | nl | {k} children under 15 live in the sector … the groups heat endangers most. | Kinderen onder 15 in de sector: {k} (…); mensen van 65 jaar en ouder: {o} (…). Dat zijn de groepen voor wie hitte het gevaarlijkst is. … | The counts follow their labels, so 1 never reads «1 kinderen»; «voor wie hitte het gevaarlijkst is» avoids «door hitte bedreigd», where «door» could read as a cause. |
| `dossier.fair.rule.body` | nl | … does not measure cooling from an intervention … | … meet niet of een ingreep afkoeling brengt … | The denial of cooling, said as a question the project does not measure; no «door». |
| `dossier.cases.left.body` | fr | … so there are no claims about degrees here. | … ce tableau n’avance donc aucun chiffre en degrés. | The denial of cooling made unmistakable: the table states no figure in degrees. |
| `commune.find.placeholder`, `commune.find.nis`, `commune.kicker` | fr | NIS code | code INS | Belgian French calls Statbel’s code by its French initials, «INS». |
| `commune.title`, `commune.law.title` | fr | counted in Article 8’s total; Under both lines: counted | dans le décompte de l’article 8; Sous les deux seuils : dans le décompte | «Comptée» after a commune’s name needs an agreement the heading cannot carry; «dans le décompte» is invariable. |
| `commune.law.reading` | nl | Its urban centres and clusters are {green}% green and {canopy}% tree canopy. | In haar stedelijke centra en clusters is {green}% groen en bedraagt de boomkroonbedekking {canopy}%. | Dutch says the shares with a verb; the first draft glued «20,0% uit boomkroonbedekking» into one unbreakable run at 320 px. |
| `commune.balance.title` | nl | Tree canopy {v} beyond noise by summer {s} | {v} kroonbedekking boven de ruis tot zomer {s} | The value comes first: after the long «Boomkroonbedekking» it wrapped to a line starting with «+» or «−», and with «boom-» the glued value ran off the 320 px screen. |
| `commune.change.title` | fr | {up} {n, plural, one {sector} other {sectors}} greener and {down} lost beyond noise, of {m} measured | {up} {n, plural, one {secteur plus vert} other {secteurs plus verts}} et {down} en perte au-delà du bruit ; secteurs mesurés : {m} | The adjective sits inside the plural so that it agrees; the measured count follows a label, so «sur 1 mesurés» cannot occur. |
| `commune.change.counts` | fr | Built-up ground: {up} sealed and {down} unsealed beyond noise. | Sol bâti, au-delà du bruit : {up} en imperméabilisation, {down} en désimperméabilisation. | Invariable nouns, so 0 and 1 read right. |
| `commune.base.eyebrow` (and «zero measurement» on the commune and data pages) | fr | The zero measurement | L’état zéro | The PBL’s «nulmeting» is an «état zéro» in French environmental reporting; «état de référence» is kept for the 2024 baseline. |
| `register.list.title` | fr | Ninety-eight contracts, in their own words | Nonante-huit contrats, dans leurs propres termes | A number written in words: Belgian French says «nonante». |
| `register.ref.model.lede` | fr | Read again by another model …, the two readings differ … | Une relecture par un autre modèle, qui n’a jamais vu ses réponses, diverge de la première … | The English opens on a participle with no subject of its own; French makes the re-reading the subject. |
| `register.method.rules.5` | fr | … on the author’s own account … | … depuis le compte personnel de l’autrice … | The author is Elena; Belgian French uses the feminine «autrice»; «compte personnel» keeps «sur le compte de» from reading as «about her». |
| `dossier.standfirst` | nl | Why money for greening should come to this sector, and how the result will be checked with the same method that measured its state. | Waarom geld voor vergroening naar deze sector moet gaan, en hoe het resultaat getoetst wordt met dezelfde methode die de toestand ervan mat. | «Getoetst» (tested against a standard) for «checked», and «ervan» for «its», the Dutch way to point back to the sector. |
| `register.ref.person.lede` | nl | Checked by hand on {n} contracts, its label differs on {k}. | Bij een controle met de hand van {n} contracten wijkt zijn label in {k} gevallen af. | Dutch cannot open on a participle with no subject of its own; the check becomes a phrase and «gevallen» names what {k} counts. |
| `register.ref.person.lede` | fr | Checked by hand on {n} contracts, its label differs on {k}. | Après vérification à la main de {n} contrats, son étiquette diffère pour {k} d’entre eux. | Same reason: «Vérifié à la main, son étiquette…» would make the label the thing checked; «d’entre eux» names what {k} counts without agreement. |
| `dossier.fair.kids.body` | fr | {k} children under 15 live in the sector (…) and {o} people aged 65 and over (…), {o80} of them over 80: … | Enfants de moins de 15 ans dans le secteur : {k} (…) ; personnes de 65 ans et plus : {o} (…), dont {o80} de plus de 80 ans. Ce sont les groupes … | Counts follow their labels, so 1 never reads «1 enfants»; «dont» replaces the English «of them». |
| `commune.law.title`, `commune.law.vsLine`, `commune.law.vsRegion` | fr | {p} points … | {p} pt … | {p} is a decimal: French takes the singular below 2 («1,5 point»), so the abbreviation «pt» avoids agreement. |
| `atlas.change.view` | nl, fr | View | Beeld / Affichage | «Weergave» and «vue» are taken by «lens» (glossary); the switch between sectors, communes, field and photos needs its own word. |
| `atlas.need.lenses.heat.limit` | nl | A state, not an effect: the method cannot measure a park’s cooling (noise floor 1.32 °C). | Een toestand, geen effect: of een park afkoeling brengt, kan de methode niet meten (ruisvloer 1,32 °C). | The denial of cooling, said as a question the method cannot answer, as in `dossier.fair.rule.body`; «afkoeling» is never the subject of a claim. |
| `atlas.need.lenses.heat.limit` | fr | (as above) | Un état, pas un effet : la méthode ne peut pas mesurer le refroidissement qu’apporterait un parc (plancher de bruit 1,32 °C). | The conditional «qu’apporterait» keeps the cooling hypothetical, as in `dossier.fair.rule.body`. |
| `atlas.equity.title` | nl, fr | Who is short | Wie komt tekort / Qui en manque | The idioms for being short of something; a literal «court» or «kort» means nothing here. |
| `atlas.equity.reading.heat` | nl, fr | The poorest third is hotter than the richest | Het armste derde woont op warmere grond … / Le tiers le plus pauvre vit sur un sol plus chaud … | A third of residents is not «warmer» or «plus chaud» itself; the measure is the summer ground temperature (`equity.byIncome.heat`), so the ground carries the comparison. |
| `atlas.equity.reading.r3` | fr | The poorest third misses both parts more often … | Le tiers le plus pauvre se trouve plus souvent que le plus riche là où aucune des deux parties n’est respectée … | «Manquer les deux parties» is not French; the sentence says where the third lives. |
| `atlas.equity.pts` | nl, fr | {n} pt / pts | {n} pt | A percentage-point difference beside a percentage; «pt» stays the same at every count, so no agreement turns on the number. |
| `atlas.place.register.at`, `atlas.place.register.gap` | nl, fr | … within 50 m of {named} named and {control} comparison points …; {named} of {namedN} named … have one … | … (benoemde punten: {named}; vergelijkingspunten: {control}) … / … (points nommés : {named} ; points de comparaison : {control}) …; Punten met … zo’n object …: {named} van de {namedN} … / Points ayant … un objet de ce type … : {named} sur {namedN} … | The counts follow their labels, so 0 and 1 never meet a plural noun or verb; the object comes as the city register’s «er is {a}» / «il y a {a}», which agrees with every one of the 14 objects. |
| `atlas.place.register.none` | nl, fr | {no} stands within 50 m … | er is {no} binnen 50 m … / il n’y a {no} à moins de 50 m … | «Staan» does not suit a dog area or a recycling point; «er is» / «il n’y a» fits all 14 objects and their «geen» / «aucun(e)». |
| `atlas.more.title` | nl, fr | What if {k} more? | En met nog {k}? / Et avec {k} de plus ? | «Als er {k} bijkomen» needs a verb that agrees with 1; this turn has none. |
| `atlas.more.whoOne` | nl, fr | It stands / does not stand … | Dit object staat … / Cet objet se trouve … | «It» would need the object’s gender in both languages; «dit object» / «cet objet» names it. |
| `atlas.need.few`, `atlas.tip.residents`, `atlas.passport.people` | nl, fr | {n} sectors / {n} residents | sectoren: {n} / inwoners: {n}; secteurs : {n} / habitants : {n} | The count follows its label, so 0 and 1 read right («0 habitant» is French). |
| `atlas.registered.lede` | nl, fr | {n} … projects were fixed on {date} … | {…projecten} die op {date} werden vastgelegd …: {n}. / {Projets …} fixés le {date} … : {n}. | The count follows the label, so one project never reads with a plural verb. fr «Projets Beliris à Bruxelles»: the city named where the English option key alone carried it (the glossary’s Brussels check). |
| `atlas.meta.sectorDescription` | nl | {name}, {commune}, {city}: … | {name}, gemeente {commune}, {city}: … | Dutch names the kind of place before a commune’s name, as in `dossier.trend.law.*`. |
| `atlas.tip.named`, `atlas.tip.control`, `atlas.passport.role.named` | fr | named, comparison | point nommé, point de comparaison | «Nommé» after a feminine object («poubelle · #3 · nommé») would disagree; the noun «point» carries the participle for every object. nl «benoemd punt» for the tip, to match. |
| `atlas.change.counts.*`, `atlas.built.counts.*` | fr | greener / look greener / sealed beyond noise (under a count) | en verdissement / d’aspect plus vert / en imperméabilisation au-delà du bruit | Invariable phrases under the number, so 0 and 1 read right, as in `commune.change.counts`. nl «schijnbaar groener» for «look greener»: no verb to agree with 1. |
| `atlas.communes.unstable.*` | fr | {name} would be exempt; {name}’s verdict … | {name} bénéficierait de l’exemption; Pour {name}, le verdict … | «Exemptée» needs a gender for the name, and «de {name}» would print «de Ixelles»; both turns need neither. |
| `atlas.change.threshold`, `atlas.built.threshold`, `atlas.change.background` | fr | … sectors of {city} … | … mesuré à {city} … / À {city}, … | «de {city}» would print «de Anvers»; «à» needs no elision for any of the five cities (as on the landing). |
| `atlas.need.shop.confectionery` (and every «confectionery») | nl | Confectionery | Snoepwinkel | OpenStreetMap’s shop=confectionery is a sweet shop; «banketbakkerij» would be a pastry baker. |
| `atlas.q.need.short` | nl | Missing | Tekort | The bar’s short label at 320 px: «Ontbreekt» pushed the three questions 7 px past the screen; «tekort» (shortage) is the noun the panel already uses. |
| `atlas.equity.ages.one`, `split`, `both` | fr | … live in {group} more often than residents overall … | … vivent plus souvent que l’ensemble des habitants dans {group} … | The comparison comes before the group: after «les secteurs qui ne respectent aucune des deux parties», a trailing «que …» read as a relative clause (review round 1). |
| `atlas.communes.leaveOut` | fr | The duty of no net loss would rest on {rest} dense communes … | Ce seraient alors {rest} communes denses, … qui devraient garantir qu’il n’y ait pas de perte nette. | The duty becomes a verb phrase, in the EUR-Lex wording, so there is no noun pile. |
| `commune.find.placeholder` | nl, fr | Commune name or NIS code | Gemeente of NIS-code / Commune ou code INS | Without «naam van de» / «nom de la»: the full placeholder was cut in the 320 px finder (re-check 1 after plan 5, 5 Oct). English followed on 5 Oct (design wave): «Commune or NIS code». |
| `atlas.passport.r3Value.1` | nl | meets one of the two | voldoet aan één | «aan een van de twee» is five short words that the typography ties into one 164-px run; in the sector card’s 125-px column it ran 23 px out of the card at every width (re-check 2 after plan 5, 5 Oct). «Voldoet aan één» sits between «voldoet aan geen van beide» and «voldoet aan beide», and the card’s label (3-30-300, two parts measured) says one of what. |
| `atlas.place.allPlaced` | fr | with all {n} placed | tous les {n} en place | Was «avec les {n} en place». tie() glues «avec les 40 en place» into one 134-px run (avec, les and en are short words), wider than a count's 111-px column at 1440, so the two counts stacked; «tous» may end a line, so the longest run is «les 40 en place» (≈ 100 px) and the counts share a row again. «En place» keeps the agreement-free form (objects are masculine or feminine). Design wave, 5 Oct 2026. |
