# Volume 1 — Exercise Library: Back
**SteadyFit Knowledge Base v1.0**
Tags: `back` `pull` `upper-body` `posterior-chain`

---

## Barbell Deadlift
```yaml
id: back_001
name: Barbell Deadlift
muscle_primary: [erector_spinae, gluteus_maximus, hamstrings]
muscle_secondary: [trapezius, rhomboids, latissimus_dorsi, quadriceps, forearms]
equipment: [barbell, plates]
difficulty: intermediate
movement_pattern: hip_hinge
force_type: pull
mechanic: compound
modality: gym
sets_rep_range: "1–3 × 1–5 (strength) | 3–4 × 4–8 (hypertrophy)"
rest_seconds: 180–300
cues:
  - "Bar over mid-foot (~2.5cm from shins) before initiating"
  - "Hip hinge to reach bar — do not squat down to it"
  - "Shoulders just in front of or over the bar at setup"
  - "Brace 360° into belt or imaginary belt — valsalva before lift"
  - "Push floor away rather than thinking pull"
  - "Bar stays in contact with legs entire way up"
  - "Lock out by squeezing glutes — not hyperextending lumbar"
common_errors:
  - error: "Bar drifting forward off legs"
    fix: "Skin the shins; if bar drifts, lat activation cue: 'protect your armpits'"
  - error: "Rounding lumbar under load"
    fix: "Reduce weight; brace harder; address hip flexor/hamstring mobility"
  - error: "Jerking the bar off floor"
    fix: "Take slack out of bar first; controlled initiation"
  - error: "Hyperextending at lockout"
    fix: "Squeeze glutes; ribs down; neutral spine at top"
substitutions:
  no_barbell: [back_002, back_003]
  lower_back_pain: [back_004, back_015]
  beginner: [back_015, back_004]
progressions: [back_001_sumo, back_001_deficit, back_001_rack_pull]
regressions: [back_004, back_015]
contraindications: [acute_lumbar_disc_herniation, acute_lower_back_strain]
evidence_notes: "Greatest absolute posterior chain loading; 1 set near 1RM produces significant neuromuscular adaptation (Schoenfeld, 2010)"
```

---

## Romanian Deadlift (RDL)
```yaml
id: back_002
name: Romanian Deadlift
muscle_primary: [hamstrings, gluteus_maximus]
muscle_secondary: [erector_spinae, trapezius, forearms]
equipment: [barbell_or_dumbbells]
difficulty: beginner
movement_pattern: hip_hinge
force_type: pull
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 8–12"
rest_seconds: 90–120
cues:
  - "Start from standing — hip hinge by pushing hips back"
  - "Soft knee bend throughout — this is not a squat"
  - "Bar/dumbbells slide down legs — maintain contact"
  - "Stop when you feel hamstring stretch (usually shin level)"
  - "Drive hips forward to return — squeeze glutes at top"
common_errors:
  - error: "Bending knees excessively (turning into a squat)"
    fix: "Hinge at hip; knees slightly bent but fixed"
  - error: "Rounding upper back"
    fix: "Retract scapulae; maintain proud chest"
substitutions:
  no_equipment: [back_015]
  home_only: [back_015]
progressions: [back_001, back_002_single_leg]
regressions: [back_015]
```

---

## Single-Leg Romanian Deadlift
```yaml
id: back_003
name: Single-Leg Romanian Deadlift
muscle_primary: [hamstrings, gluteus_maximus, gluteus_medius]
muscle_secondary: [erector_spinae, core, peroneals]
equipment: [dumbbell_or_kettlebell]
difficulty: intermediate
movement_pattern: hip_hinge_unilateral
force_type: pull
mechanic: compound
modality: [gym, home]
sets_rep_range: "3 × 8–12 per side"
rest_seconds: 60–90
cues:
  - "Hinge on one leg — trail leg floats back for counterbalance"
  - "Hips stay square to floor — don't let trail hip open"
  - "Slight bend in standing knee"
  - "Weight in ipsilateral or contralateral hand — both have merit"
common_errors:
  - error: "Hip rotation (piking open)"
    fix: "Square hips; keep trail leg in line with spine"
substitutions:
  balance_issues: [back_002]
progressions: [back_003_barbell]
regressions: [back_002]
population_notes: "Excellent for elderly populations to address balance and hip stability"
```

---

## Dumbbell Romanian Deadlift
```yaml
id: back_004
name: Dumbbell Romanian Deadlift
muscle_primary: [hamstrings, gluteus_maximus]
muscle_secondary: [erector_spinae, forearms]
equipment: [dumbbells]
difficulty: beginner
movement_pattern: hip_hinge
force_type: pull
mechanic: compound
modality: [gym, home]
sets_rep_range: "3 × 10–15"
rest_seconds: 60–90
cues:
  - "Same mechanics as barbell RDL — dumbbells outside legs"
  - "More freedom for hip-width variation vs barbell"
  - "Great for learning hinge pattern before loading barbell"
substitutions:
  no_dumbbells: [back_015]
progressions: [back_002]
regressions: [back_015]
```

---

## Pull-Up / Chin-Up
```yaml
id: back_005
name: Pull-Up
muscle_primary: [latissimus_dorsi, teres_major]
muscle_secondary: [biceps_brachii, rhomboids, lower_trapezius, infraspinatus]
equipment: [pull_up_bar]
difficulty: intermediate
movement_pattern: vertical_pull
force_type: pull
mechanic: compound
modality: [gym, home, outdoor]
sets_rep_range: "3–5 × max or 5–10 (weighted)"
rest_seconds: 90–180
cues:
  - "Grip slightly wider than shoulder width (pull-up) or shoulder-width supinated (chin-up)"
  - "Dead hang start — depress scapulae before pulling"
  - "Drive elbows to hips — not just pulling with arms"
  - "Chin clears bar at top; full hang at bottom"
  - "No kipping unless trained for it — strict for hypertrophy"
common_errors:
  - error: "Partial reps (not reaching full hang)"
    fix: "Full ROM builds more lat length tension"
  - error: "Shrugging shoulders up at top"
    fix: "Keep scapulae depressed; pack the neck"
substitutions:
  cant_do_pullup: [back_006, back_007]
  no_bar: [back_008, back_012]
progressions: [back_005_weighted, back_005_archer]
regressions: [back_006, back_007]
evidence_notes: "Chin-up grip activates more biceps; pull-up grip activates more lower trapezius (Lehman et al., 2004)"
```

---

## Assisted Pull-Up (Band or Machine)
```yaml
id: back_006
name: Assisted Pull-Up
muscle_primary: [latissimus_dorsi, teres_major]
muscle_secondary: [biceps_brachii, rhomboids]
equipment: [pull_up_bar, resistance_band_or_assisted_machine]
difficulty: beginner
movement_pattern: vertical_pull
force_type: pull
mechanic: compound
modality: [gym, home]
sets_rep_range: "3–4 × 6–12"
rest_seconds: 60–90
cues:
  - "Band: loop around bar, knee or foot in band — provides ascending assistance"
  - "Machine: select counterweight; decrease over time as strength builds"
  - "Same technique cues as full pull-up"
substitutions: null
progressions: [back_005]
regressions: [back_007]
population_notes: "Primary progression tool for beginners and those unable to perform full pull-up"
```

---

## Lat Pulldown
```yaml
id: back_007
name: Lat Pulldown
muscle_primary: [latissimus_dorsi, teres_major]
muscle_secondary: [biceps_brachii, rhomboids, lower_trapezius]
equipment: [cable_machine, lat_bar]
difficulty: beginner
movement_pattern: vertical_pull
force_type: pull
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 8–15"
rest_seconds: 60–90
cues:
  - "Grip slightly wider than shoulder width; slight lean back (~15–20°)"
  - "Pull to upper chest — not behind the neck"
  - "Initiate with scapular depression before elbow flexion"
  - "Full stretch at top — don't shorten ROM"
common_errors:
  - error: "Pulling behind neck"
    fix: "Cervical spine risk; always pull to upper chest"
  - error: "Using momentum and leaning too far back"
    fix: "Moderate lean; control the eccentric"
substitutions:
  no_machine: [back_005, back_006]
progressions: [back_005]
regressions: null
```

---

## Seated Cable Row
```yaml
id: back_008
name: Seated Cable Row
muscle_primary: [rhomboids, middle_trapezius, latissimus_dorsi]
muscle_secondary: [biceps_brachii, rear_deltoid, erector_spinae]
equipment: [cable_machine, row_handle]
difficulty: beginner
movement_pattern: horizontal_pull
force_type: pull
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 8–15"
rest_seconds: 60–90
cues:
  - "Sit upright — slight forward lean at stretch, upright at contraction"
  - "Drive elbows back past torso — row to navel, not chest"
  - "Squeeze scapulae together at full contraction — 1 second pause"
  - "Control the eccentric — let cable pull arms forward slowly"
common_errors:
  - error: "Using lower back to row (rocking)"
    fix: "Isolate upper back; torso stays nearly still"
  - error: "Not fully extending arms on eccentric"
    fix: "Full stretch for full rhomboid/lat development"
substitutions:
  no_cable: [back_009, back_010]
  home_only: [back_012]
progressions: [back_008_single_arm]
regressions: [back_012]
```

---

## Barbell Bent-Over Row
```yaml
id: back_009
name: Barbell Bent-Over Row
muscle_primary: [latissimus_dorsi, rhomboids, middle_trapezius]
muscle_secondary: [biceps_brachii, rear_deltoid, erector_spinae]
equipment: [barbell]
difficulty: intermediate
movement_pattern: horizontal_pull
force_type: pull
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 5–10"
rest_seconds: 90–120
cues:
  - "Overhand grip (pronated) for more upper back; underhand for more lats"
  - "Hinge to ~45° — maintain neutral spine, brace core"
  - "Row to lower chest/navel — elbows drive back and up"
  - "Bar stays close to body throughout"
common_errors:
  - error: "Rounding lower back under load"
    fix: "Reduce weight; brace harder; this is a demanding position"
  - error: "Upright torso (turning into a shrug)"
    fix: "Maintain 45° hinge throughout"
substitutions:
  no_barbell: [back_008, back_010]
  lower_back_pain: [back_008, back_011]
progressions: [back_009_pendlay]
regressions: [back_010, back_008]
contraindications: [acute_lower_back_strain, lumbar_disc_herniation]
```

---

## Dumbbell Single-Arm Row
```yaml
id: back_010
name: Dumbbell Single-Arm Row
muscle_primary: [latissimus_dorsi, rhomboids]
muscle_secondary: [biceps_brachii, rear_deltoid, teres_major]
equipment: [dumbbell, bench]
difficulty: beginner
movement_pattern: horizontal_pull
force_type: pull
mechanic: compound
modality: [gym, home]
sets_rep_range: "3–4 × 8–15 per side"
rest_seconds: 60
cues:
  - "Knee and hand on bench for support — back flat and parallel to floor"
  - "Row dumbbell to hip — not shoulder; elbow tracks along torso"
  - "Full hang at bottom — stretch the lat"
  - "No trunk rotation — keep hips and shoulders square"
common_errors:
  - error: "Rotating torso to get range"
    fix: "Reduces lat involvement; keep square"
substitutions:
  no_bench: [back_008, back_012]
  home_only: [back_012]
progressions: [back_009]
regressions: [back_012]
```

---

## Chest-Supported Row (Machine or Incline Bench)
```yaml
id: back_011
name: Chest-Supported Row
muscle_primary: [rhomboids, middle_trapezius, latissimus_dorsi]
muscle_secondary: [biceps_brachii, rear_deltoid]
equipment: [incline_bench_or_machine, dumbbells]
difficulty: beginner
movement_pattern: horizontal_pull
force_type: pull
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 10–15"
rest_seconds: 60–90
cues:
  - "Chest supported — eliminates lower back demand completely"
  - "Ideal for lower back pain or those who struggle to maintain hinge position"
  - "Row dumbbells up toward hips with full scapular retraction"
population_notes: "Excellent for lower back pain patients, elderly, beginners"
substitutions:
  no_bench: [back_008]
progressions: [back_009, back_010]
regressions: null
```

---

## Resistance Band Row
```yaml
id: back_012
name: Resistance Band Row
muscle_primary: [rhomboids, middle_trapezius]
muscle_secondary: [biceps_brachii, latissimus_dorsi]
equipment: [resistance_band, anchor_point]
difficulty: beginner
movement_pattern: horizontal_pull
force_type: pull
mechanic: compound
modality: [home, hotel, travel]
sets_rep_range: "3 × 15–20"
rest_seconds: 45–60
cues:
  - "Anchor band at waist height; sit or stand"
  - "Row elbows back past torso; squeeze shoulder blades"
  - "Control the return — band pulls arms forward"
substitutions:
  no_band: [back_014]
progressions: [back_008, back_010]
population_notes: "Best home/travel option for horizontal pulling"
```

---

## Face Pull
```yaml
id: back_013
name: Face Pull
muscle_primary: [rear_deltoid, infraspinatus, teres_minor]
muscle_secondary: [rhomboids, middle_trapezius]
equipment: [cable_machine, rope_attachment]
difficulty: beginner
movement_pattern: horizontal_pull
force_type: pull
mechanic: isolation
modality: gym
sets_rep_range: "3–4 × 15–20"
rest_seconds: 45–60
cues:
  - "Cable at or just above eye level; rope attachment"
  - "Pull to face — hands either side of head, externally rotate at end"
  - "Elbows stay high — at or above shoulder line"
  - "Squeeze rear delts and external rotators at peak contraction"
common_errors:
  - error: "Elbows dropping below shoulders"
    fix: "Keep elbows high throughout; reduces external rotation benefit"
substitutions:
  no_cable: [back_013_band]
evidence_notes: "Critical rotator cuff health exercise; recommended 2x/week for shoulder longevity regardless of program"
population_notes: "Recommended for all populations; especially important for desk workers and overhead athletes"
```

---

## Superman Hold
```yaml
id: back_014
name: Superman Hold
muscle_primary: [erector_spinae, gluteus_maximus]
muscle_secondary: [hamstrings, rhomboids, rear_deltoid]
equipment: []
difficulty: beginner
movement_pattern: spinal_extension
force_type: pull
mechanic: isolation
modality: [home, hotel, gym, rehabilitation]
sets_rep_range: "3 × 10–15 reps (2–3s hold)"
rest_seconds: 45
cues:
  - "Lie prone, arms extended overhead"
  - "Lift chest, arms, and legs simultaneously"
  - "Squeeze glutes; hold 2–3 seconds at top"
  - "Lower under control"
substitutions: null
progressions: [back_002]
population_notes: "Safe lower back activation for elderly, rehabilitation, and beginners. Builds posterior chain awareness"
```

---

## Good Morning
```yaml
id: back_015
name: Good Morning (Bodyweight or Barbell)
muscle_primary: [hamstrings, gluteus_maximus, erector_spinae]
muscle_secondary: [adductors]
equipment: [barbell_optional]
difficulty: beginner
movement_pattern: hip_hinge
force_type: pull
mechanic: compound
modality: [gym, home]
sets_rep_range: "3 × 10–15"
rest_seconds: 60–90
cues:
  - "Feet shoulder-width; hands on hips (bodyweight) or bar on upper traps (loaded)"
  - "Push hips back — hinge, don't squat"
  - "Soft knee bend; maintain throughout"
  - "Stop at horizontal or when hamstring flexibility permits"
  - "Drive hips forward to return"
substitutions:
  no_equipment: [back_015]
progressions: [back_002, back_001]
regressions: [back_014]
population_notes: "Best hip-hinge teaching tool for beginners before loading"
```
