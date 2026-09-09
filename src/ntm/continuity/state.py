"""Replay sourced state-transition events without modifying canonical history."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, Mapping

STATE_FIELDS = frozenset(
    {
        "physical_state", "health_state", "appearance_state", "wardrobe_state",
        "inventory_state", "ownership_state", "location_state", "knowledge_state",
        "ability_state", "material_state", "texture_state", "energy_state",
    }
)


@dataclass(frozen=True, order=True)
class _EventPosition:
    date: str
    order: int


def _event_position(event: Mapping[str, Any]) -> _EventPosition:
    timeline = event.get("timeline")
    if not isinstance(timeline, Mapping):
        raise ValueError(f"event {event.get('id', '<unknown>')} has no timeline")
    event_date, order = timeline.get("date"), timeline.get("order")
    if not isinstance(event_date, str) or not isinstance(order, int):
        raise ValueError(f"event {event.get('id', '<unknown>')} has an invalid timeline")
    date.fromisoformat(event_date)
    return _EventPosition(event_date, order)


def _requested_position(position: int | str | Mapping[str, Any]) -> _EventPosition:
    if isinstance(position, int):
        return _EventPosition("9999-12-31", position)
    if isinstance(position, str):
        date.fromisoformat(position)
        return _EventPosition(position, 2**63 - 1)
    if isinstance(position, Mapping):
        event_date, order = position.get("date"), position.get("order")
        if not isinstance(event_date, str) or not isinstance(order, int):
            raise ValueError("timeline_position must contain a date and integer order")
        date.fromisoformat(event_date)
        return _EventPosition(event_date, order)
    raise TypeError("timeline_position must be an integer order, ISO date, or timeline mapping")


class CanonStateResolver:
    """Resolve entity state by replaying immutable, sourced canonical events.

    State patches replace complete named state compartments.  Thus an event never
    edits a previous snapshot: resolving an earlier timeline position simply
    replays a shorter prefix of the same append-only event log.
    """

    def __init__(self, entities: Iterable[Mapping[str, Any]], events: Iterable[Mapping[str, Any]]) -> None:
        self._entities = {entity["id"]: deepcopy(dict(entity)) for entity in entities}
        self._events = tuple(sorted((deepcopy(dict(event)) for event in events), key=lambda event: (_event_position(event), event.get("id", ""))))

    def resolve_entity_state(self, entity_id: str, timeline_position: int | str | Mapping[str, Any]) -> dict[str, Any]:
        """Return a new state snapshot valid at ``timeline_position``.

        The returned object includes the entity id and resolved timeline marker;
        changing it cannot alter entities, events, or future resolutions.
        """
        try:
            entity = self._entities[entity_id]
        except KeyError as exc:
            raise KeyError(f"unknown entity: {entity_id}") from exc
        requested = _requested_position(timeline_position)
        state = deepcopy(entity.get("initial_state", {}))
        for event in self._events:
            event_position = _event_position(event)
            # An integer denotes the project-wide sequence number. A dated
            # position compares the full (date, order) timeline coordinate.
            if isinstance(timeline_position, int):
                if event_position.order > timeline_position:
                    continue
            elif event_position > requested:
                break
            for change in event.get("changes", ()):
                if change.get("entity_id") != entity_id:
                    continue
                patch = change.get("state")
                if not isinstance(patch, Mapping):
                    raise ValueError(f"event {event.get('id', '<unknown>')} has an invalid state patch")
                unknown = set(patch) - STATE_FIELDS
                if unknown:
                    raise ValueError(f"event {event.get('id', '<unknown>')} changes unsupported state fields: {sorted(unknown)}")
                state.update(deepcopy(dict(patch)))
        return {"entity_id": entity_id, "timeline_position": {"date": requested.date, "order": requested.order}, "state": state}


def resolve_entity_state(
    entity_id: str,
    timeline_position: int | str | Mapping[str, Any],
    *,
    entities: Iterable[Mapping[str, Any]],
    events: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Convenience API for one-off immutable state reconstruction."""
    return CanonStateResolver(entities, events).resolve_entity_state(entity_id, timeline_position)
