# NTM — Novel To Manhwa

**NTM is a Codex plugin that gives every Codex agent the same canon-first workflow for turning a long novel into a continuity-safe manhwa production pipeline.** It does not pretend that an LLM's memory is the source of truth, nor does it lock you into a particular image, OCR, vision, or LLM provider.

## Install for any Codex agent

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL> ntm
cd ntm
codex plugin marketplace add .
```

Then install **Novel To Manhwa** from the Codex plugin marketplace and open Codex in this cloned directory. The plugin supplies the `novel-to-manhwa` skill automatically, so every agent gets the same operating rules and project structure.

> The marketplace command is intentionally repository-local: contributors clone the same repository, install the same plugin version, and work from the same repeatable instructions. If your Codex build uses a graphical plugin installer, select the cloned repository's `.agents/plugins/marketplace.json` instead.

## What the plugin enforces

- **Canonical single source of truth:** typed, immutable entity IDs and sourced facts.
- **Long-distance continuity:** retrieval of prior entity appearances and state before new scenes are planned.
- **Temporal safety:** deterministic checks for ownership, location, injuries, wardrobe, life status, knowledge, and powers.
- **Visual consistency:** canonical image/reference metadata is attached to generation requests rather than recreated from prose.
- **Honest QA:** visual checks are only marked passed when a configured vision provider actually runs; otherwise they remain `not_run`.
- **Auditable completion:** a chapter cannot be `final` with unresolved blocking findings.

The governing priority is:

```text
CANON > CONTINUITY > STORYBOARD > AESTHETICS > SPEED
```

## Use in a project

Once the plugin is installed, ask Codex:

```text
Initialize a canon-first Novel To Manhwa project in ./my-series.
Inspect existing files first, propose the architecture, then build one tested prototype chapter.
```

Codex follows the bundled phased workflow: inspect → architecture → schemas/canon → extraction → resolved scene state → storyboard → provider-neutral generation request → QA report → finalization gate.

To initialize manually without overwriting existing work:

```bash
python3 plugins/novel-to-manhwa/scripts/init_project.py ./my-series
```

The initialized project separates `canon`, `story`, `storyboard`, `visual_bible`, `references`, `generation`, `validation`, `chapters`, `reports`, and `tools`.

## Included plugin contents

| Path | Purpose |
| --- | --- |
| `plugins/novel-to-manhwa/skills/novel-to-manhwa/SKILL.md` | Rules and production workflow applied by Codex agents. |
| `plugins/novel-to-manhwa/templates/` | Provider-neutral JSON Schema contracts for entities, events, scene states, and reports. |
| `plugins/novel-to-manhwa/scripts/init_project.py` | Non-destructive project initializer. |
| `plugins/novel-to-manhwa/scripts/check_reports.py` | Finalization gate for continuity reports. |
| `.agents/plugins/marketplace.json` | Repository-local Codex marketplace entry. |

## Validate the plugin

```bash
python3 /opt/codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/novel-to-manhwa
python3 plugins/novel-to-manhwa/scripts/init_project.py /tmp/ntm-smoke-test
python3 plugins/novel-to-manhwa/scripts/check_reports.py plugins/novel-to-manhwa/examples
```

The first command requires Python's `PyYAML` module because it belongs to Codex's plugin validator.

## Boundaries

NTM designs and orchestrates the production workflow; it does not bundle commercial model credentials or falsely promise flawless art generation. Configure actual LLM, image-generation, OCR, and vision adapters in your series project, retain their request/output metadata, and keep human review for ambiguous or creative decisions.
