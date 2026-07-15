# Volume 1 — Exercise Library: Core
**SteadyFit Knowledge Base v1.0**
Tags: `core` `abs` `stability` `anti-rotation` `plank`

---

## Plank
```yaml
id: core_001
name: Plank (Forearm)
muscle_primary: [transverse_abdominis, rectus_abdominis]
muscle_secondary: [erector_spinae, gluteus_maximus, shoulder_stabilisers]
equipment: []
difficulty: beginner
movement_pattern: isometric_spinal_stability
mechanic: isolation
modality: [home, hotel, gym, elderly, rehabilitation, office]
sets_rep_range: "3 × 20–60 seconds"
rest_seconds: 60
cues:
  - "Forearms on floor; body straight from head to heels"
  - "Brace core: imagine bracing for a punch"
  - "Squeeze glutes; push floor away through forearms"
  - "Neutral spine — no hips sagging or piking"
  - "Breathe steadily — don't hold breath"
common_errors:
  - error: "Hips sagging"
    fix: "Reduce hold time; squeeze glutes"
  - error: "Hips too high"
    fix: "Lower until spine neutral — use mirror or partner"
substitutions: null
progressions: [core_002, core_003, core_008]
regressions: [core_001_knees]
evidence_notes: "Anti-extension pattern; superior for lumbar safety vs crunch (McGill, 2010)"
population_notes: "Safe for elderly, lower back pain, pregnancy (first trimester). Modify to knees if needed"
```

---

## Dead Bug
```yaml
id: core_002
name: Dead Bug
muscle_primary: [transverse_abdominis, rectus_abdominis]
muscle_secondary: [hip_flexors, erector_spinae, shoulder_stabilisers]
equipment: []
difficulty: beginner
movement_pattern: anti_extension_contralateral
mechanic: isolation
modality: [home, hotel, gym, rehabilitation]
sets_rep_range: "3 × 8–12 per side"
rest_seconds: 60
cues:
  - "Lie on back; lower back pressed into floor throughout"
  - "Arms vertical; knees at 90° table-top"
  - "Extend opposite arm and leg toward floor simultaneously"
  - "The moment your lower back lifts — stop and return"
  - "Breathe out as you extend"
evidence_notes: "Best anti-extension + contralateral loading pattern; highly recommended for lower back rehabilitation"
population_notes: "Excellent for lower back pain, elderly, rehabilitation — zero spinal loading"
substitutions: null
progressions: [core_003, core_008]
regressions: [core_001]
```

---

## Bird Dog
```yaml
id: core_003
name: Bird Dog
muscle_primary: [erector_spinae, gluteus_maximus, transverse_abdominis]
muscle_secondary: [rhomboids, hamstrings, shoulder_stabilisers]
equipment: []
difficulty: beginner
movement_pattern: contralateral_stability
mechanic: compound
modality: [home, hotel, gym, elderly, rehabilitation]
sets_rep_range: "3 × 10 per side (2s hold)"
rest_seconds: 45–60
cues:
  - "On hands and knees (quadruped); neutral spine"
  - "Extend opposite arm and leg — reach long, not high"
  - "Don't let hips rotate or drop"
  - "Hold 2 seconds at end range"
  - "Return under control; don't drop limbs"
population_notes: "McGill's Big 3 core exercise — appropriate for all populations including lower back pain"
evidence_notes: "Part of McGill's Big 3 (plank, bird dog, side bridge); evidence base for LBP prevention"
substitutions: null
progressions: [core_002]
```

---

## Hollow Body Hold
```yaml
id: core_004
name: Hollow Body Hold
muscle_primary: [rectus_abdominis, transverse_abdominis, hip_flexors]
muscle_secondary: [serratus_anterior]
equipment: []
difficulty: intermediate
movement_pattern: anti_extension_supine
mechanic: isolation
modality: [home, hotel, gym]
sets_rep_range: "3 × 20–40 seconds"
rest_seconds: 60
cues:
  - "Lie on back; press lower back into floor"
  - "Arms overhead, legs extended — lift both slightly off floor"
  - "Lower back MUST stay pressed to floor throughout"
  - "The flatter your position, the harder it is"
common_errors:
  - error: "Lower back arching off floor"
    fix: "Bend knees or raise legs higher to reduce demand"
substitutions:
  too_hard: [core_001, core_002]
progressions: [core_004_rocks]
regressions: [core_002]
```

---

## Bicycle Crunch
```yaml
id: core_005
name: Bicycle Crunch
muscle_primary: [obliques, rectus_abdominis]
muscle_secondary: [hip_flexors]
equipment: []
difficulty: beginner
movement_pattern: rotation_with_flexion
mechanic: isolation
modality: [home, hotel, gym]
sets_rep_range: "3 × 20–30 per side"
rest_seconds: 45
cues:
  - "Hands behind head — don't pull neck"
  - "Opposite elbow to opposite knee; crunch and rotate"
  - "Other leg extends long"
  - "Slow and controlled — not a speed exercise"
common_errors:
  - error: "Pulling neck forward"
    fix: "Hands behind head — only skull contact, not pulling"
substitutions: null
progressions: [core_006]
regressions: [core_001]
```

---

## Russian Twist
```yaml
id: core_006
name: Russian Twist
muscle_primary: [obliques]
muscle_secondary: [rectus_abdominis, hip_flexors]
equipment: [plate_or_dumbbell_optional]
difficulty: beginner
movement_pattern: rotation
mechanic: isolation
modality: [home, hotel, gym]
sets_rep_range: "3 × 20 per side"
rest_seconds: 45
cues:
  - "Sit at 45° lean; feet off floor for more challenge"
  - "Rotate thoracic spine — not just arms swinging"
  - "Touch hands/weight to floor each side"
substitutions: null
progressions: [core_006_weighted]
regressions: [core_005]
```

---

## Ab Rollout (Wheel or Barbell)
```yaml
id: core_007
name: Ab Rollout
muscle_primary: [rectus_abdominis, transverse_abdominis]
muscle_secondary: [latissimus_dorsi, shoulder_stabilisers]
equipment: [ab_wheel_or_barbell]
difficulty: intermediate
movement_pattern: anti_extension
mechanic: isolation
modality: gym
sets_rep_range: "3 × 8–12"
rest_seconds: 90
cues:
  - "Kneel; ab wheel under shoulders"
  - "Roll forward — maintain neutral spine (don't let lower back sag)"
  - "Go as far as you can with neutral spine"
  - "Pull back using abs, not lats"
common_errors:
  - error: "Lower back sagging at full extension"
    fix: "Reduce ROM; build gradually"
evidence_notes: "Anti-extension under dynamic loading — more demanding than plank for advanced trainees"
contraindications: [acute_lower_back_pain]
substitutions:
  too_hard: [core_001]
progressions: [core_007_standing]
regressions: [core_001, core_002]
```

---

## Pallof Press
```yaml
id: core_008
name: Pallof Press
muscle_primary: [transverse_abdominis, obliques]
muscle_secondary: [glutes, shoulder_stabilisers]
equipment: [cable_machine_or_resistance_band]
difficulty: beginner
movement_pattern: anti_rotation
mechanic: isolation
modality: [gym, home]
sets_rep_range: "3 × 10–15 per side"
rest_seconds: 60
cues:
  - "Stand side-on to anchor point; hold at chest"
  - "Press arms out — resist rotation toward anchor"
  - "The further from anchor, the harder the anti-rotation demand"
  - "Hold 1 second at full extension"
evidence_notes: "Only exercise that trains anti-rotation in the frontal plane — critical for athletic and spine health"
substitutions:
  no_cable_or_band: [core_006]
progressions: [core_008_kneeling, core_008_half_kneeling]
```

---

## Side Plank
```yaml
id: core_009
name: Side Plank
muscle_primary: [quadratus_lumborum, obliques]
muscle_secondary: [glutes, hip_abductors, shoulder_stabilisers]
equipment: []
difficulty: beginner
movement_pattern: lateral_anti_flexion
mechanic: isolation
modality: [home, hotel, gym, elderly, rehabilitation]
sets_rep_range: "3 × 20–45 seconds per side"
rest_seconds: 60
cues:
  - "Forearm on floor; body in straight line — feet stacked or staggered"
  - "Drive hip up — don't let it sag"
  - "Free arm on hip or raised"
evidence_notes: "McGill Big 3 — most effective QL and lateral stabiliser exercise; key for LBP prevention"
population_notes: "Regress to knee-down version for elderly, beginners, or those with shoulder issues"
substitutions: null
progressions: [core_009_star_side_plank]
regressions: [core_009_knees]
```

---

## Hanging Knee Raise
```yaml
id: core_010
name: Hanging Knee Raise
muscle_primary: [rectus_abdominis, hip_flexors]
muscle_secondary: [obliques, forearms]
equipment: [pull_up_bar]
difficulty: intermediate
movement_pattern: hip_flexion_hanging
mechanic: isolation
modality: [gym, outdoor]
sets_rep_range: "3 × 10–20"
rest_seconds: 60–90
cues:
  - "Dead hang; posterior tilt pelvis before raising knees"
  - "Drive knees up toward chest — not just hip flexion"
  - "Control descent — don't swing"
  - "Progress: straight leg raise"
common_errors:
  - error: "Swinging / using momentum"
    fix: "Pause 1 second at bottom between reps"
substitutions:
  no_bar: [core_005, core_002]
progressions: [core_010_straight_leg]
regressions: [core_005]
```
