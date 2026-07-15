"""Deterministic exercise library lookup (no embeddings).

Use for SELECTION (filter by muscle/equipment/modality/difficulty/contraindications).
Use semantic RAG for EXPLANATION (cues, technique, science).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from langsmith import traceable

from app.tracing import annotate_run, exercise_tool_outputs

DIFFICULTY_RANK = {"beginner": 1, "intermediate": 2, "advanced": 3}
DEFAULT_LIBRARY = Path("data/knowledge_base/exercise_library.json")


@lru_cache(maxsize=1)
def _load_library(path: str = str(DEFAULT_LIBRARY)) -> dict[str, dict]:
    data = json.loads(Path(path).read_text())
    exercises = data.get("exercises") or []
    return {ex["id"]: ex for ex in exercises if isinstance(ex, dict) and ex.get("id")}


def get_exercise(exercise_id: str) -> dict | None:
    return _load_library().get(exercise_id)


@traceable(
    name="find_exercises",
    run_type="tool",
    process_outputs=exercise_tool_outputs,
)
def find_exercises(
    muscle: str | None = None,
    equipment_available: list[str] | None = None,
    modality: str | None = None,
    difficulty_max: str | None = None,
    exclude_contraindications: list[str] | None = None,
) -> list[dict]:
    """Filter the exercise index. Returns matching exercise records."""
    annotate_run(inputs={
        "muscle": muscle,
        "equipment_available": equipment_available,
        "modality": modality,
        "difficulty_max": difficulty_max,
        "exclude_contraindications": exclude_contraindications,
    })
    library = _load_library()
    max_rank = DIFFICULTY_RANK.get((difficulty_max or "advanced").lower(), 99)
    exclude = {c.lower() for c in (exclude_contraindications or [])}
    muscle_q = (muscle or "").lower().strip()
    modality_q = (modality or "").lower().strip()
    filter_equipment = equipment_available is not None
    avail = {e.lower() for e in (equipment_available or [])}

    results: list[dict] = []
    for ex in library.values():
        name = (ex.get("name") or "").lower()
        eid = (ex.get("id") or "").lower()
        muscles = [m.lower() for m in (ex.get("muscle_primary") or [])]

        if muscle_q:
            ok = (
                any(muscle_q in m or m in muscle_q for m in muscles)
                or muscle_q in name
                or eid.startswith(muscle_q + "_")
                or muscle_q in eid
            )
            if not ok:
                continue

        mods = [m.lower() for m in (ex.get("modality") or [])]
        if modality_q and modality_q not in mods:
            continue

        diff = (ex.get("difficulty") or "beginner").lower()
        if DIFFICULTY_RANK.get(diff, 99) > max_rank:
            continue

        contra = [c.lower() for c in (ex.get("contraindications") or [])]
        if exclude and any(
            any(e in c or c in e for e in exclude) for c in contra
        ):
            continue

        eq = [x.lower() for x in (ex.get("equipment") or [])]
        if filter_equipment:
            if eq and not avail:
                continue  # needs gear; caller has none
            if eq and avail and not set(eq).issubset(avail):
                continue

        results.append(ex)
    return results


@traceable(
    name="get_substitutions",
    run_type="tool",
    process_outputs=exercise_tool_outputs,
)
def get_substitutions(exercise_id: str, constraint: str) -> list[dict]:
    """Resolve substitutions map entries to full exercise records.

    Example: get_substitutions('chest_001', 'home_only') → [{chest_010}, {chest_011}]
    """
    annotate_run(inputs={"exercise_id": exercise_id, "constraint": constraint})
    library = _load_library()
    ex = library.get(exercise_id)
    if not ex:
        return []
    subs = ex.get("substitutions") or {}
    ids = subs.get(constraint) or subs.get(constraint.lower()) or []
    if not ids and constraint:
        for key, val in subs.items():
            if constraint.lower() in key.lower() or key.lower() in constraint.lower():
                ids = val
                break
    out: list[dict] = []
    for sid in ids:
        found = library.get(sid)
        if found:
            out.append(found)
    return out
