# Registre des sources canoniques

Chaque document source est un JSON validé par l'un des schémas de ce dossier. Les
sept catégories acceptées sont : `published_chapter`, `author_note`,
`worldbuilding_draft`, `outline`, `visual_reference`, `editorial_decision` et
`superseded_material`. Chaque élément de `facts` référence `fact.schema.json`.

## Métadonnées obligatoires sur chaque fait

- `canon_status` : `published`, `approved_private`, `provisional`,
  `superseded` ou `non_canon` ;
- `audience_visibility` : `author_only`, `reader_hidden` ou `reader_known` ;
- `character_knowledge` : dictionnaire par identifiant de personnage, dont
  l'état est `unknown`, `suspects` ou `knows`.

## Politique de résolution

1. Un fait `published` provenant d'un `published_chapter` est prioritaire sur
   tout matériel non publié.
2. Les données privées (`author_only` et `reader_hidden`) peuvent informer les
   choix d'adaptation, mais ne sont jamais proposées pour une réplique tant
   qu'une révélation canonique publiée ne les rend pas `reader_known`.
3. Deux faits actifs qui portent la même `claim_key` avec des affirmations
   différentes créent un conflit **bloquant**. Aucun choix automatique n'est
   effectué : une `editorial_decision` doit le résoudre explicitement.
4. Les faits `superseded` et `non_canon` ne participent pas aux adaptations.
   `superseded_material` conserve la traçabilité, sans redevenir une source
   d'autorité.

L'importeur applique ces garde-fous et produit les conflits destinés à
`reports/conflict_review.html`.
