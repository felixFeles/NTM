# Dossiers d’adaptation par chapitre

Cette couche transforme un chapitre importé en un dossier de travail **sans
modifier le canon**. Elle enregistre des décisions éditoriales courtes,
contrôlables et reliées à des localisateurs de source; elle ne stocke pas de
chaîne de raisonnement privée exhaustive.

## Initialisation

```python
from ntm.adaptation import initialize_chapter_adaptation

initialize_chapter_adaptation("src/ntm/adaptation", "chapter_001")
```

L’appel crée, sans écraser les fichiers existants,
`src/ntm/adaptation/chapter_001/` avec :

| Fichier | Contenu attendu |
| --- | --- |
| `summary.md` | Résumé fidèle, exclusivement appuyé par le texte source. |
| `narrative_breakdown.json` | Séquences, enjeux, tournants et ordre narratif. |
| `explicit_facts.json` | Faits formulés explicitement, avec leurs localisateurs. |
| `inferences.json` | Inférences séparées des faits, avec confiance et validation humaine si nécessaire. |
| `visual_hypotheses.json` | Hypothèses de mise en image qui ne deviennent pas des traits canoniques. |
| `dialogue_proposals.json` | Répliques proposées, bornées par les connaissances publiées du personnage. |
| `added_scenes.json` | Scènes ou transitions ajoutées, chacune reliée à une décision. |
| `offscreen_elements.json` | Éléments plausibles hors champ, explicitement non affirmés comme faits. |
| `continuity_risks.json` | Risques, sources concernées et résolution ou revue requise. |
| `adaptation_decision.json` | Registre des ajouts créatifs et de leur approbation. |

Les artefacts JSON doivent avoir `chapter_id` et leurs entrées doivent référencer
les localisateurs stables de l’ingestion (`fichier:p<paragraphe>:s<phrase>`).
Toute proposition de dialogue reste soumise à
`facts_available_for_dialogue`; une source privée ne peut pas révéler de canon
au lecteur.

## Registre des décisions

`adaptation_decision.json` suit
[`adaptation_decision.schema.json`](adaptation_decision.schema.json). Le modèle
prêt à copier est [`adaptation_decision.json`](adaptation_decision.json).
Chaque ajout de tenue non décrite, décoration, dialogue supplémentaire ou
transition doit avoir :

- un `decision_id` unique et un `addition_type`;
- ses `source_locators` et son statut : `proposed`, `approved` ou `rejected`;
- `adaptation_only: true`;
- une `editorial_justification` concise : `sources_used`, règle canonique,
  hypothèse, niveau de confiance, alternatives rejetées et besoin de validation
  humaine.

`approved` signifie seulement « autorisé dans cette adaptation ». La règle
`canonization_rule`, imposée par le schéma et
`validate_adaptation_decisions`, interdit de faire d’une inférence du canon par
défaut. Une modification canonique exige un document
`editorial_decision` sourcé dans `canon/sources/`.
