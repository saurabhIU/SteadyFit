# Volume 1 — Exercise Library: Shoulders
**SteadyFit Knowledge Base v1.0**
Tags: `shoulders` `deltoids` `overhead` `rotator-cuff`

---

## Barbell Overhead Press (OHP)
```yaml
id: shoulders_001
name: Barbell Overhead Press
muscle_primary: [anterior_deltoid, lateral_deltoid]
muscle_secondary: [triceps_brachii, upper_trapezius, serratus_anterior, core]
equipment: [barbell, rack_optional]
difficulty: intermediate
movement_pattern: vertical_push
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3–5 × 3–8 (strength) | 3–4 × 8–12 (hypertrophy)"
rest_seconds: 120–180
cues:
  - "Grip just outside shoulder width; elbows slightly in front of bar at setup"
  - "Brace core hard — rib cage down; no lumbar hyperextension"
  - "Press bar in slight arc — head moves back slightly, then forward as bar passes"
  - "Bar finishes over ears at lockout, not in front of face"
  - "Full lockout at top"
common_errors:
  - error: "Lower back hyperextension (leaning back excessively)"
    fix: "Brace core, squeeze glutes; if can't maintain, reduce load"
  - error: "Bar path too far forward"
    fix: "Bar should end directly overhead; move head back as bar passes"
substitutions:
  no_barbell: [shoulders_002, shoulders_003]
  shoulder_pain: [shoulders_004, shoulders_005]
progressions: [shoulders_001_push_press]
regressions: [shoulders_002]
contraindications: [shoulder_impingement, rotator_cuff_tear, AC_joint_injury]
evidence_notes: "Standing OHP provides significant core demand; seated version reduces core demand, increases shoulder isolation"
```

---

## Dumbbell Shoulder Press
```yaml
id: shoulders_002
name: Dumbbell Shoulder Press
muscle_primary: [anterior_deltoid, lateral_deltoid]
muscle_secondary: [triceps_brachii, upper_trapezius]
equipment: [dumbbells, bench_optional]
difficulty: beginner
movement_pattern: vertical_push
force_type: push
mechanic: compound
modality: [gym, home]
sets_rep_range: "3–4 × 8–15"
rest_seconds: 60–90
cues:
  - "Start at ear height, elbows at 90°"
  - "Press to full extension overhead — slight natural arc"
  - "Can use neutral grip (palms facing) to reduce shoulder impingement"
  - "Seated: back supported reduces core demand (good for beginners)"
substitutions:
  no_dumbbells: [shoulders_001]
  home_only: [shoulders_006]
progressions: [shoulders_001]
regressions: [shoulders_006]
```

---

## Arnold Press
```yaml
id: shoulders_003
name: Arnold Press
muscle_primary: [anterior_deltoid, lateral_deltoid]
muscle_secondary: [triceps_brachii, rotator_cuff]
equipment: [dumbbells]
difficulty: intermediate
movement_pattern: vertical_push_with_rotation
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3 × 10–15"
rest_seconds: 60–90
cues:
  - "Start with palms facing you at chin level"
  - "Rotate palms out as you press up — finish palms forward overhead"
  - "Reverse on descent"
  - "Increased ROM and rotator cuff recruitment vs standard press"
substitutions:
  no_dumbbells: [shoulders_002]
progressions: [shoulders_001]
regressions: [shoulders_002]
```

---

## Lateral Raise
```yaml
id: shoulders_004
name: Lateral Raise
muscle_primary: [lateral_deltoid]
muscle_secondary: [anterior_deltoid, supraspinatus]
equipment: [dumbbells_or_cables]
difficulty: beginner
movement_pattern: shoulder_abduction
force_type: pull
mechanic: isolation
modality: [gym, home]
sets_rep_range: "3–4 × 12–20"
rest_seconds: 45–60
cues:
  - "Slight forward lean at hips (15–20°) increases lateral delt recruitment"
  - "Slight elbow bend — elbows slightly higher than wrists at top"
  - "Raise to shoulder height only — above shoulder = upper trap takes over"
  - "Slow eccentric — 3 seconds down"
  - "Think: pour water from a jug — pinky slightly higher than thumb"
common_errors:
  - error: "Using momentum and swinging"
    fix: "Reduce weight significantly; this is a small muscle"
  - error: "Raising above shoulder height"
    fix: "Stop at parallel; anything above primarily loads upper trap"
substitutions:
  no_equipment: [shoulders_006]
evidence_notes: "Cable version maintains tension at bottom (arm hanging) unlike dumbbells; cable preferred for full ROM loading"
```

---

## Face Pull
```yaml
id: shoulders_005
name: Face Pull
muscle_primary: [rear_deltoid, infraspinatus, teres_minor]
muscle_secondary: [rhomboids, middle_trapezius]
equipment: [cable_machine, rope]
difficulty: beginner
movement_pattern: horizontal_pull_external_rotation
force_type: pull
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 15–20"
rest_seconds: 45–60
cues:
  - "Cable at eye level or just above"
  - "Pull rope to face — split the rope at end; hands beside ears"
  - "Elbows high — at or above shoulder line"
  - "External rotation at end: elbows drive back, hands pull apart"
substitutions:
  no_cable: [shoulders_005_band]
evidence_notes: "Critical for rotator cuff health and shoulder longevity; programme 2x/week minimum for desk workers"
population_notes: "Recommended for all populations; especially office workers and those with anterior shoulder dominance"
```

---

## Pike Push-Up
```yaml
id: shoulders_006
name: Pike Push-Up
muscle_primary: [anterior_deltoid, lateral_deltoid]
muscle_secondary: [triceps_brachii, upper_trapezius]
equipment: []
difficulty: beginner
movement_pattern: vertical_push
force_type: push
mechanic: compound
modality: [home, hotel]
sets_rep_range: "3 × 8–15"
rest_seconds: 60
cues:
  - "Inverted V position — hips high, head through arms"
  - "Lower head toward floor between hands"
  - "The more vertical your body, the more shoulder demand"
  - "Elevate feet for greater shoulder emphasis"
substitutions:
  too_hard: [shoulders_002]
progressions: [shoulders_006_elevated, shoulders_006_headstand]
regressions: [shoulders_002]
population_notes: "Best home-based shoulder pressing option; no equipment needed"
```

---

## Rear Delt Fly
```yaml
id: shoulders_007
name: Rear Delt Fly (Dumbbell)
muscle_primary: [rear_deltoid, infraspinatus]
muscle_secondary: [rhomboids, middle_trapezius]
equipment: [dumbbells]
difficulty: beginner
movement_pattern: horizontal_abduction
force_type: pull
mechanic: isolation
modality: [gym, home]
sets_rep_range: "3–4 × 12–20"
rest_seconds: 45–60
cues:
  - "Hinge to ~45° or lie face-down on incline bench"
  - "Arms hang down; slight elbow bend"
  - "Raise arms to sides — squeeze rear delts at top"
  - "Pinky slightly higher than thumb at top"
common_errors:
  - error: "Using upper traps instead of rear delts"
    fix: "Keep neck long; don't shrug; think horizontal spread"
substitutions:
  no_dumbbells: [shoulders_005]
progressions: [shoulders_005]
```

---

## Band Pull-Apart
```yaml
id: shoulders_008
name: Band Pull-Apart
muscle_primary: [rear_deltoid, rhomboids]
muscle_secondary: [infraspinatus, middle_trapezius]
equipment: [resistance_band]
difficulty: beginner
movement_pattern: horizontal_abduction
force_type: pull
mechanic: isolation
modality: [home, hotel, office, rehab]
sets_rep_range: "3 × 15–25"
rest_seconds: 30–45
cues:
  - "Hold band at shoulder width, arms forward"
  - "Pull band apart to chest — arms go wide"
  - "Squeeze shoulder blades at full extension"
  - "Control return — don't let band snap back"
substitutions:
  no_band: [shoulders_007]
evidence_notes: "Excellent shoulder health and posture maintenance tool; low load, suitable daily"
population_notes: "Ideal for office workers, elderly, rehabilitation — zero risk, major postural benefit"
```
