"""Tests for KB YAML chunking and exercise substitutions."""
from app.rag.ingest_kb import chunk_kb_markdown, parse_yaml_block, as_list
from app.tools.exercise_lookup import find_exercises, get_substitutions
from pathlib import Path


SAMPLE = """## Push-Up Standard
```yaml
id: chest_010
name: Push-Up Standard
muscle_primary: [pectoralis_major_sternal]
equipment: []
difficulty: beginner
modality: [home, hotel, gym]
contraindications: []
```

Do a proper push-up with a rigid plank.
"""


def test_parse_yaml_block_well_formed():
    meta = parse_yaml_block(SAMPLE)
    assert meta is not None
    assert meta["id"] == "chest_010"
    assert as_list(meta["modality"]) == ["home", "hotel", "gym"]


def test_parse_yaml_block_malformed():
    bad = "## X\n```yaml\n: : broken: [[[\n```\n"
    assert parse_yaml_block(bad) is None


def test_chunk_chest_md_has_pushup():
    path = Path("data/knowledge_base/Volume1-ExerciseLibrary/Chest.md")
    if not path.exists():
        return
    chunks = chunk_kb_markdown(path)
    ids = {c.kb_id for c in chunks}
    assert "chest_010" in ids
    assert all(c.doc_type == "kb_exercise" for c in chunks)


def test_get_substitutions_home_only():
    subs = get_substitutions("chest_001", "home_only")
    ids = {s["id"] for s in subs}
    assert "chest_010" in ids
    assert "chest_011" in ids


def test_find_exercises_hotel_excludes_barbell():
    hits = find_exercises(muscle="chest", modality="hotel", difficulty_max="advanced", equipment_available=[])
    ids = {h["id"] for h in hits}
    assert "chest_010" in ids
    assert "chest_001" not in ids
