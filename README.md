# NTM
Novel To Manhwa

## Continuité narrative

Les chapitres Markdown ou texte placés dans `story/source/` sont importés avec
`StoryIngestor`. Chaque occurrence conserve un localisateur stable
`fichier:p<paragraphe>:s<phrase>` et le manifeste contient le SHA-256 de chaque
source. Le front matter optionnel distingue explicitement `publication_order`,
`chronological_order`, `flashback` et `flashback_of`.

`HybridStoryIndex` combine une recherche lexicale, une similarité TF-IDF, un
graphe d'entités/événements et les deux timelines. Après avoir enregistré les
entités et événements, utilisez `retrieve_entity_context(entity_id, chapter_id,
direction)` ou `retrieve_chapter_context(chapter_id)`. Les résultats séparent
les occurrences antérieures et postérieures, événements causaux, contradictions
potentielles et sources auditables.
