# Review: part `documents` (dossier, commune, data, register), Belgian Dutch (nl-BE)

- Part: `documents`, sections `dossier`, `commune`, `data`, `register`
- Language: nl-BE
- Drafting model: `claude-opus-5-5` (draft commit `b12c9c1`)
- Reviewing model: `claude-sonnet-5-5`
- Date: 2026-10-04
- Keys read: 418 (every key of the four sections, English against Dutch; `tests/catalogues.test.ts`, `messages.test.ts` and `icu.test.ts` pass)

## What was checked

- **Sense and the never-claim rules.** No key adds or drops a claim. Cooling is denied in all four places it appears (`dossier.fair.rule.body`, `dossier.cases.left.body`, `dossier.limits.items.0`, and the data layer texts), never promised; no «door» or «dankzij» is used as a cause. Causes stay with documents (`dossier.limits.items.3`, `commune.limits.3`: «niet waarom. De oorzaak komt uit documenten»). Every change is stated against the vergelijkingsplaatsen / vergelijkbare sectoren (`dossier.trend.*`, `commune.change.*`), and the raw shift appears only as the explicitly labelled thing that is subtracted (`dossier.trend.background`). Refusals stay full outcomes («geen oordeel», «weigert de audit te rekenen», «als weigering geregistreerd», «geweigerd vóór de werken»). Scattered street planting is stated as lost at sector level (`dossier.trend.notProof.body`, `dossier.limits.items.2`, `register.limits.items.0`), not verified.
- **Register: a model reading contracts.** Nothing suggests the model counts. `register.method.rules.0` says it plainly («Het telt, schat en rangschikt nooit: elk getal op deze site blijft bij de rekenmotor»). The «model» only «vindt», «las», «somde op»; the rule baseline is «de regel als referentie» throughout; the check is called «een tweede model, geen mens». Model names, `greening_v1`, `greening_check_v1`, file names and the seed stay as written. `who`, `k` and `key` values are untouched (they match `lib/pseudo.ts` `ID`).
- **Dynamic World.** Class values are «kans per klasse» / «waarschijnlijkheden» (`dossier.passport.*`, `dossier.scale.note`), never a share; `commune.balance.note` says hectares as Dynamic World classifies the ground, not the official layers.
- **Article 8 terms** against `sources/`: «artikel 8, lid 1», «artikel 3, punt 20», «stedelijke centra en clusters», «Stedelijk ecosysteem», «nettoverlies», «boomkroonbedekking»/«kroonbedekking», «LBE», «Verordening (EU) 2024/1991», «natuurherstelverordening», «gewest» all match.
- **Glossary table and numbers.** Every term is used as the table says (vergelijkingsplaatsen/-sectoren, significantiedrempel, ruis, groenheid, oordeel, ingreep, register van ingrepen, stedelijke groene ruimte). Numbers, units, years, `1,32 °C`, `45%`, `10%`, `95%-interval`, `600`, `30`, `98` all agree with English in Dutch notation; the licence codes «CC BY 4.0», «ODbL 1.0» and «VN-indicator 11.7» keep their points under the controller's ruling. «quartiers.brussels» is left alone, as ruled. Script check: arguments, tags, select and plural keywords match English in every key.
- **Typography.** ‘ ’ only, no straight or “ ” quotes (the ICU `'<'…'>'` escapes in `data.colophon.1.v` are intact), no U+00A0, no space before punctuation, no `1.5` decimals.
- **Belgian usage and register.** «u» throughout, «gemeente», «gewest», «wijkcontract», «Leefmilieu»-style names, «onthard», «bouwwerf», «databank», «oplaadt» (Flemish for uploads), «Gegevens», «stadsbosbouw», «nulmeting» are Flemish. `€ {v}` with a space is the Dutch form.
- **`same.json`.** No key in these sections is identical to English without an entry, and no entry is stale. Reasons hold.
- **Retold keys, Dutch rows of «For a native reader»:** all justified (`steekkaart`, `kans per klasse`, `Vanzelf wordt het niet beter`, `Er voldoen er {n}`, the commune-name and «haar» rows, the `door hitte bedreigd` avoidance, `meet niet of een ingreep afkoeling brengt`, `commune.law.reading`, `commune.balance.title`). One note on the fair-rule row: «meet niet of een ingreep afkoeling brengt» is a faithful denial («the project does not measure cooling from an intervention»), and it is followed by the reason, so it does not hint that cooling exists. Two rewritten keys are not in the list: see the note below the table.

## Findings

| severity | key | problem | suggestion | response |
|---|---|---|---|---|
| minor | `dossier.scale.note` | «geen aandelen van de grond»: «aandelen» also means company shares, and the next clause says «percentages van de oppervlakte», so the first half reads like a pun. | Het streepje is de mediaan van de stad, de balk de sector. Klassewaarden zijn waarschijnlijkheden, geen gedeelten van de grond: vergelijk ze tussen sectoren, maar lees ze niet als percentages van de oppervlakte. | Fixed as suggested. |
| minor | `dossier.noPick` | «vrijgesteld onder artikel 8, lid 1»: one is exempt «op grond van» or «krachtens» an article; `dossier.trend.law.*` use «komt in aanmerking voor de vrijstelling van artikel 8, lid 1». | De openbare regel kiest in {city} geen sector. Hij vraagt een gemeente die de wet meetelt, en {city} is vrijgesteld op grond van artikel 8, lid 1: {green} groen in de stedelijke centra en clusters. Elke sector heeft wel zijn dossier; kies er een in de atlas. | Fixed as suggested. |
| minor | `commune.trees.reading` | «dicht bebouwd» says the sectors are densely built; the English «dense» explains why per-hectare numbers are higher while per-resident numbers are lower, which is population density. | Per inwoner gingen er minder bomen naar het derde met de minste kroonbedekking: {resIn} per 1.000 inwoners, tegenover {resOut} in de rest. Per hectare gingen er meer naartoe: {haIn} per 10 ha, tegenover {haOut}. Die sectoren zijn dicht bevolkt, dus beide lezingen kloppen; geen van beide zegt of de bomen daar meer nodig waren. | Fixed as suggested. |
| minor | `register.limits.items.0` | «een omtrek van ongeveer een hectare»: an outline (perimeter) is not measured in hectares; the English «footprint» is the area. The sentence is the key limit (small planting is not verified), so the dimension should be right. (`landing.audits.p1` already says «terrein».) | ‘Verbindt zich’ legt een belofte uit een contract vast. Of het terrein veranderde, is de vraag van de atlas, en die kan hij alleen beantwoorden waar een gebied van ongeveer een hectare bestaat; de meeste van deze maatregelen zijn straten, binnenplaatsen en pleinen die kleiner zijn. | Fixed as suggested: «gebied» is an area, so the hectare now measures the right thing. |
| minor | `dossier.colophon.0.v` | «de auditdossiers» for «the audit cases»: «dossier» is the sector page of this site, so a reader meets two things under one word. | De laag artikel 8 van het stadspakket (niveaus van 2024 en de trend ten opzichte van de vergelijkingsplaatsen), het stadsmanifest (drempels en hun herkomst), de auditgevallen, het register van benoemde punten, Statbel (sectoren, bevolking, inkomen, de volkstelling van 2021). Beelden: Copernicus Sentinel-2 met het Cloud Score+-masker, Google Dynamic World V1. | Fixed as suggested. |
| minor | `register.colophon.reader.v` | «één oproep per contract»: a call to a model API is an «aanroep»; «oproep» is a summons or a phone call. | Claude Sonnet 5 via Claude Code in printmodus, één aanroep per contract, {to}. | Fixed as suggested. |
| minor | `dossier.commitment.items.3.lead` | «vertrekt van de opleveringsdatum» is a stilted calque of «is built from». | Het vergelijkingsvenster wordt opgebouwd vanaf de opleveringsdatum: | Fixed as suggested. |
| minor | `dossier.fair.kids.body` | «In de sector wonen {k} kinderen» prints «1 kinderen» for a count of 1 (the English has the same flaw: «1 children»). Naming the quantity first avoids agreement without changing the arguments. | Kinderen onder 15 in de sector: {k} ({kp} van de inwoners); mensen van 65 jaar en ouder: {o} ({op}), van wie {o80} ouder dan 80. Dat zijn de groepen voor wie hitte het gevaarlijkst is. In de hele stad woont {third} van alle kinderen in het derde van de sectoren met de minste kroonbedekking{hardest, select, yes {, dus het tekort aan schaduw is niet gelijk verdeeld, en het treft hen het hardst} other {, ongeveer hun aandeel in de stad}}. | Fixed as suggested; the row under «For a native reader» is updated. |

Note on «For a native reader»: two Dutch keys were rewritten for the language but are not in the list: `register.ref.person.lede` («Bij een controle met de hand van {n} contracten wijkt zijn label in {k} gevallen af») and `dossier.standfirst`. Neither is wrong; they should be listed.

Verdict: 0 blocker, 0 major, 8 minor

Drafter’s response (round 1): every minor is fixed as the table’s `response` column says; the missing «For a native reader» rows are added.

## Round 2

Reviewed: the 8 keys changed between `b12c9c1` and `9b1dd0a` in `nl.json` (`git diff` confirms 8), one per round-1 minor. `tests/catalogues.test.ts`, `messages.test.ts` and `icu.test.ts` pass. Arguments, tags, select keywords, numbers (`1.000`, `10 ha`, `2021`, `Cloud Score+`) and quotes of the changed keys are unchanged; no never-claim rule is touched.

| severity | key | problem | suggestion |
|---|---|---|---|
| resolved | `dossier.scale.note` | Fixed: «gedeelten van de grond» removes the «aandelen» pun; Dynamic World class values are still «waarschijnlijkheden», not shares. | none |
| resolved | `dossier.noPick` | Fixed: «op grond van artikel 8, lid 1» (the citation form is unchanged). | none |
| resolved | `commune.trees.reading` | Fixed: «dicht bevolkt» is the density that explains the per-resident and per-hectare readings. | none |
| resolved | `register.limits.items.0` | Fixed: «een gebied van ongeveer een hectare» has the right dimension and still states that the atlas answers only where such an area exists (small planting is not verified). | none |
| resolved | `dossier.colophon.0.v` | Fixed: «de auditgevallen» no longer collides with «dossier». | none |
| resolved | `register.colophon.reader.v` | Fixed: «aanroep». | none |
| resolved | `dossier.commitment.items.3.lead` | Fixed: «wordt opgebouwd vanaf de opleveringsdatum:» joins the following body («een nulmeting voordat de werken beginnen, …») correctly. | none |
| resolved | `dossier.fair.kids.body` | Fixed: quantity first, so «1 kinderen» cannot occur; the `hardest` select, the numbers and the claim («de groepen voor wie hitte het gevaarlijkst is», no cause) are unchanged, and the new sentence order reads naturally. | none |

Open issues: none.

Verdict: 0 blocker, 0 major, 0 minor
