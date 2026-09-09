---
name: novel-to-manhwa
version: 0.1.0
description: Use when building or operating a long-form novel-to-manhwa pipeline that needs strict narrative, temporal, material, and visual continuity.
---

# Novel To Manhwa: canon-first production skill

Build a production system, not a one-shot image prompt. The source of truth is structured project data; a model's context window and memory are never canon.

## Non-negotiable rules

1. **Priority:** `CANON > CONTINUITY > STORYBOARD > AESTHETICS > SPEED`.
2. Give every entity an immutable typed ID (`character_grey`, `item_ring_001`, `location_city_014`). Never key data only by display name.
3. Do not silently repair, retcon, or invent a fact to resolve a contradiction. Record sources, report the conflict, and request an explicit canon decision.
4. Before planning or generating a scene, resolve the scene state from canon at its timeline position.
5. Before an entity appears again, retrieve its prior appearances, current state, visual reference, ownership, and applicable rules.
6. Treat image generation and vision checks as replaceable adapters. Do not claim an image has been generated or visually verified when no configured provider has done so.
7. A chapter is final only when every blocking validation finding is resolved or explicitly waived with an audit trail.

## First-turn protocol

When a user starts a project, do these in order:

1. Inspect the repository and identify existing story, canon, asset, and tooling files.
2. Preserve existing work; do not overwrite canonical data.
3. Explain the proposed architecture and the phased delivery plan **before** implementing a full pipeline.
4. Initialize the standard structure with `scripts/init_project.py` only after choosing the project root. Existing files are preserved unless `--force` is intentionally supplied.
5. Start with one small, end-to-end prototype chapter. Add tests and reports before scaling to more chapters.

## Standard project layout

Use this layout inside the target work root:

```text
canon/                 # canonical entities, events, world rules, timeline
story/source/          # immutable imported novel source
story/extractions/     # chapter-level facts extracted from source
storyboard/            # scenes, panels, dialogue, generation briefs
visual_bible/          # stable design rules and reference metadata
references/            # canonical images/sheets, addressed by entity ID
generation/            # provider-neutral requests, outputs, and manifests
validation/            # validators, policies, and fixture data
chapters/              # assembled, approved chapter artifacts
reports/               # continuity reports and review queues
tools/                 # project-local automation
```

The bundled schemas are deliberately provider-neutral JSON templates. Convert to YAML only if the project has a validated YAML parser and tests; keep the schema meaning identical.

## Required production flow per chapter

1. **Ingest:** retain immutable source text plus source locator(s).
2. **Extract:** identify events, entity mentions, new claims, dialogue knowledge, and proposed state changes. Every extracted claim must retain chapter/source evidence.
3. **Resolve:** load the canon slice for the chapter's timeline position, including entity history and visual references.
4. **Validate before generation:** reject unavailable items, impossible locations, unrevealed knowledge, invalid abilities, unhealed injuries, ownership conflicts, and unapproved wardrobe changes.
5. **Storyboard:** create scene/panel specifications that refer to IDs—not only free-form names—and bind each panel to a scene state.
6. **Generate:** create provider-neutral generation requests containing prompt, negative constraints, entity references, and expected scene state. A provider adapter may then produce assets.
7. **Inspect:** use a vision/OCR provider adapter when configured to compare panels against scene state and visual reference requirements. Otherwise report visual checks as `not_run`, never `pass`.
8. **Report:** write `reports/chapter_<id>_continuity_report.json` with findings, evidence, severity, and disposition.
9. **Finalize:** publish only when blocking findings are zero. Preserve all intermediate artifacts and hashes for reproducibility.

## Canon data model

Use templates in `templates/` as the minimum contract:

- `entity.template.json` and `event.template.json`: compatibility entry points to the versioned `schemas/v1/` entity and append-only state-transition contracts.
- Entity state uses named compartments: `physical_state`, `health_state`, `appearance_state`, `wardrobe_state`, `inventory_state`, `ownership_state`, `location_state`, `knowledge_state`, `ability_state`, `material_state`, `texture_state`, and `energy_state`.
- Each event has a dated timeline coordinate (`date`, `order`, `scene_id`), source evidence, and complete compartment replacements. Reconstruct prior scenes by replaying events rather than changing prior state.
- `scene-state.template.json`: resolved input contract for each scene.
- `continuity-report.template.json`: machine-readable QA output.

Every mutable fact must be represented as a sourced event or state transition. Examples: acquiring `item_ring_001`, changing its owner, receiving a scar, changing outfits, learning a secret, or dying. Use `ntm.continuity.CanonStateResolver(...).resolve_entity_state(entity_id, timeline_position)` to reconstruct the state supplied to a scene; this returns a detached snapshot and never mutates history.

## Visual bible rules

For important entities, retain reference metadata and image files under `references/<entity_id>/`. Include a canonical sheet plus angle/state variants where relevant. Store immutable design constraints (geometry, materials, markings, proportions) in canon and bind each panel request to the reference paths.

For a recurring ring, the canonical geometry and markings stay invariant unless a specifically sourced event modifies them. Normal wear must be modeled as a state transition, not prompt improvisation.

## Validation rules

Implement deterministic checks before model-assisted checks whenever possible:

- timeline ordering and simultaneous-location conflicts;
- item acquisition, ownership, and inventory availability;
- life status, injury persistence, wardrobe state, and ability acquisition;
- character and reader knowledge boundaries;
- scene entities, references, and required visual constraints;
- event/source provenance;
- report status and blocking-finalization gate.

Use model/vision checks for fuzzy visual questions only. Record model/provider, prompt/version, reference IDs, output hashes, timestamps, and confidence; a low-confidence result must become a review finding, not an automatic approval.

## Safe contradiction handling

When a contradiction is found:

1. preserve both claims and their source evidence;
2. emit a blocking report finding with a stable ID;
3. state why the claims conflict and list viable resolutions;
4. wait for an explicit decision or an already documented priority policy;
5. append a decision event—never rewrite history without an audit record.

## Completion checklist

Before saying a project phase is complete, confirm:

- schemas validate;
- a prototype chapter has extracted facts, a resolved scene state, storyboard artifact, and report;
- automated continuity tests ran;
- no blocker is hidden or silently ignored;
- external provider steps are either reproducibly configured or marked unexecuted.
