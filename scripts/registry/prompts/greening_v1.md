You read the description of a Brussels neighbourhood contract (contrat de quartier, written in French) and list every greening measure it mentions, then label the whole contract.

A greening measure is anything that would change vegetation cover or sealed ground: creating or redesigning a park or a green space, restoring one, removing paving (déminéralisation, désimperméabilisation), planting trees or hedges, greening a street (a "rue parc", a green street), community, school or shared gardens and urban agriculture, green roofs or green façades. Housing, schools, sports halls, mobility, social and economic projects are not greening measures, even when they sit next to a park.

For every mention, copy the exact words from the text into "quote": one clause or one sentence, character for character, keeping spelling, accents, apostrophes and punctuation, and never joining separate sentences. Never paraphrase or translate the quote.

Give each measure a status:
- "action": the contract commits to it: it plans, finances or carries it out (future tense or a firm plan: "prévoit", "sera réaménagé", "seront plantés", "création de", "transformée en", "le programme comprend"). The verb of commitment decides, not the purpose clause: "le pôle prévoit des interventions dans certains espaces publics afin d'améliorer leur verdurisation" is an action, because interventions are foreseen. Quote the clause together with its verb of commitment.
- "intention": greening is named only as an aim, a need or better access, without a commitment to change the cover ("améliorer l'accès aux espaces verts", "la création d'espaces verts s'avérera nécessaire", "favoriser la verdurisation").
- "state": it describes what already exists, a place name, or a diagnosed problem ("le quartier manque d'espaces verts", "bordées par le parc Maximilien", "une forte imperméabilisation").

Give each measure a kind: new_green_space, park_redesign, restoration, unsealing, street_greening, gardens_agriculture, green_roofs_facades or other_greening. "place" is the named park, street or site the measure concerns, as written in the text, or null.

Label the whole contract:
- "yes": at least one measure with status "action" that changes vegetation cover;
- "weak": greening appears only as an intention or as access to green space;
- "no": no greening measure: only a description of the state, a diagnosis, a place name, or a greening word in an unrelated context (for example "implantation" is not "plantation", and "parcelle" is not "parc").

"why": one sentence in English that names the decisive quote and why it decides the label.

Do not count, estimate or add anything that is not in the text. If the text has no greening at all, return an empty list of measures and the label "no".
