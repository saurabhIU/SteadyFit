# Volume 1 — Exercise Library: Arms
**SteadyFit Knowledge Base v1.0**
Tags: `arms` `biceps` `triceps` `forearms` `isolation`

---

## Barbell Curl
```yaml
id: arms_001
name: Barbell Curl
muscle_primary: [biceps_brachii]
muscle_secondary: [brachialis, brachioradialis]
equipment: [barbell_or_ez_bar]
difficulty: beginner
movement_pattern: elbow_flexion
force_type: pull
mechanic: isolation
modality: gym
sets_rep_range: "3–4 × 8–12"
rest_seconds: 60–90
cues:
  - "Shoulder-width grip; stand tall, chest up"
  - "Elbows pinned to sides — don't swing them forward"
  - "Full extension at bottom — don't shorten the range"
  - "Squeeze bicep hard at top; 1 second pause"
  - "EZ-bar reduces wrist strain vs straight bar"
common_errors:
  - error: "Swinging elbows forward / using momentum"
    fix: "Pin elbows; reduce weight"
substitutions:
  no_barbell: [arms_002, arms_003]
progressions: [arms_001_preacher]
regressions: [arms_002]
```

---

## Dumbbell Curl
```yaml
id: arms_002
name: Dumbbell Curl
muscle_primary: [biceps_brachii]
muscle_secondary: [brachialis, brachioradialis]
equipment: [dumbbells]
difficulty: beginner
movement_pattern: elbow_flexion
force_type: pull
mechanic: isolation
modality: [gym, home]
sets_rep_range: "3 × 10–15 per side"
rest_seconds: 45–60
cues:
  - "Can supinate (rotate) wrist as you curl for full bicep contraction"
  - "Alternate or simultaneous — both effective"
  - "Full extension at bottom; squeeze at top"
substitutions:
  no_dumbbells: [arms_004]
progressions: [arms_001]
```

---

## Hammer Curl
```yaml
id: arms_003
name: Hammer Curl
muscle_primary: [brachialis, brachioradialis]
muscle_secondary: [biceps_brachii]
equipment: [dumbbells]
difficulty: beginner
movement_pattern: elbow_flexion_neutral
force_type: pull
mechanic: isolation
modality: [gym, home]
sets_rep_range: "3 × 10–15 per side"
rest_seconds: 45–60
cues:
  - "Neutral (hammer) grip throughout — thumbs up"
  - "Loads brachialis more than supinated curl"
  - "Brachialis sits under bicep — developing it pushes bicep up = larger arm peak"
evidence_notes: "Superior brachialis activation vs supinated curl; include alongside standard curls for complete arm development"
substitutions:
  no_dumbbells: [arms_004]
```

---

## Resistance Band Curl
```yaml
id: arms_004
name: Resistance Band Curl
muscle_primary: [biceps_brachii]
muscle_secondary: [brachialis]
equipment: [resistance_band]
difficulty: beginner
movement_pattern: elbow_flexion
force_type: pull
mechanic: isolation
modality: [home, hotel, travel]
sets_rep_range: "3 × 15–20"
rest_seconds: 45
cues:
  - "Stand on band; hold both ends"
  - "Curl to shoulder; control descent"
  - "Band tension increases at top — different profile vs dumbbell"
substitutions:
  no_band: [arms_002]
progressions: [arms_002, arms_001]
```

---

## Preacher Curl
```yaml
id: arms_005
name: Preacher Curl (Machine or Barbell)
muscle_primary: [biceps_brachii_long_head]
muscle_secondary: [brachialis]
equipment: [preacher_bench, barbell_or_dumbbell]
difficulty: beginner
movement_pattern: elbow_flexion_supported
force_type: pull
mechanic: isolation
modality: gym
sets_rep_range: "3 × 10–15"
rest_seconds: 60
cues:
  - "Upper arm fully supported on pad — eliminates momentum completely"
  - "Full extension at bottom — don't lock out aggressively"
  - "Squeeze at top"
evidence_notes: "Supported position maximises long-head stretch and removes cheating — excellent for hypertrophy"
```

---

## Close-Grip Bench Press
```yaml
id: arms_006
name: Close-Grip Bench Press
muscle_primary: [triceps_brachii]
muscle_secondary: [pectoralis_major, anterior_deltoid]
equipment: [barbell, bench]
difficulty: intermediate
movement_pattern: horizontal_push
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 6–12"
rest_seconds: 90–120
cues:
  - "Grip shoulder-width (not super close — wrist strain)"
  - "Elbows tucked close to torso throughout"
  - "Touch lower chest; press to lockout"
  - "Biggest compound tricep loader"
substitutions:
  no_barbell: [arms_008, arms_009]
progressions: [arms_006_weighted]
regressions: [arms_008]
evidence_notes: "Highest absolute load for triceps; include as primary tricep exercise in strength programs"
```

---

## Tricep Dips
```yaml
id: arms_007
name: Tricep Dips (Bench or Parallel Bars)
muscle_primary: [triceps_brachii]
muscle_secondary: [anterior_deltoid, pectoralis_major]
equipment: [bench_or_dip_bars]
difficulty: beginner
movement_pattern: vertical_push
force_type: push
mechanic: compound
modality: [gym, home]
sets_rep_range: "3 × 10–20 (bodyweight) | 3 × 6–12 (weighted)"
rest_seconds: 60–90
cues:
  - "Stay upright — don't lean forward (becomes chest, not tricep)"
  - "Elbows point back, not flared"
  - "Lower until upper arms parallel to floor"
  - "Bench dip: easier — feet on floor; parallel bar: harder"
common_errors:
  - error: "Excessive forward lean"
    fix: "Stay upright to keep tricep emphasis"
substitutions:
  no_equipment: [arms_009]
progressions: [arms_006, arms_007_weighted]
regressions: [arms_009]
```

---

## Skull Crusher (Lying Tricep Extension)
```yaml
id: arms_008
name: Skull Crusher
muscle_primary: [triceps_brachii_long_head]
muscle_secondary: []
equipment: [barbell_or_dumbbells, bench]
difficulty: intermediate
movement_pattern: elbow_extension
force_type: push
mechanic: isolation
modality: gym
sets_rep_range: "3 × 10–15"
rest_seconds: 60–90
cues:
  - "Lie on bench; arms vertical, elbows above chest"
  - "Lower bar to forehead (not skull!) by bending elbows only"
  - "Keep upper arms vertical — elbows stationary"
  - "EZ bar more wrist-friendly than straight bar"
  - "Dumbbells: lower to beside ears"
common_errors:
  - error: "Elbows flaring out"
    fix: "Keep elbows narrow and pointing at ceiling"
contraindications: [elbow_tendinopathy_acute]
substitutions:
  no_equipment: [arms_009]
evidence_notes: "Long head is the largest tricep head and most stretched at full elbow flexion with shoulder extension — overhead position or skull crusher most effective"
```

---

## Tricep Pushdown (Cable)
```yaml
id: arms_009_cable
name: Tricep Pushdown
muscle_primary: [triceps_brachii]
muscle_secondary: []
equipment: [cable_machine]
difficulty: beginner
movement_pattern: elbow_extension
force_type: push
mechanic: isolation
modality: gym
sets_rep_range: "3 × 12–20"
rest_seconds: 45–60
cues:
  - "Cable at top; rope or bar attachment"
  - "Elbows pinned to sides throughout"
  - "Push down to full extension; squeeze"
  - "Control eccentric — cable adds constant tension"
substitutions:
  no_cable: [arms_007, arms_008]
progressions: [arms_008, arms_006]
```

---

## Diamond Push-Up
```yaml
id: arms_009
name: Diamond Push-Up
muscle_primary: [triceps_brachii]
muscle_secondary: [pectoralis_major, anterior_deltoid]
equipment: []
difficulty: intermediate
movement_pattern: horizontal_push
force_type: push
mechanic: compound
modality: [home, hotel]
sets_rep_range: "3 × 8–20"
rest_seconds: 60
cues:
  - "Hands form diamond shape under chest"
  - "Elbows track back close to ribs — not flared"
  - "Full lockout at top"
substitutions:
  too_hard: [arms_007]
progressions: [arms_006]
regressions: [arms_007]
population_notes: "Best home-based tricep isolation; no equipment"
```

---

## Overhead Tricep Extension
```yaml
id: arms_010
name: Overhead Tricep Extension
muscle_primary: [triceps_brachii_long_head]
muscle_secondary: []
equipment: [dumbbell_or_cable_or_band]
difficulty: beginner
movement_pattern: elbow_extension_overhead
force_type: push
mechanic: isolation
modality: [gym, home]
sets_rep_range: "3 × 12–15"
rest_seconds: 60
cues:
  - "Arms overhead; elbows point forward"
  - "Lower weight behind head by bending elbows"
  - "Upper arms stay vertical — elbows stationary"
  - "Overhead position maximally stretches the long head"
evidence_notes: "Long head receives greatest stretch with shoulder in flexion — overhead extensions superior for long head hypertrophy"
substitutions:
  no_equipment: [arms_009]
```
