# Volume 1 — Exercise Library: Legs
**SteadyFit Knowledge Base v1.0**
Tags: `legs` `lower-body` `squat` `hinge` `posterior-chain`

---

## Barbell Back Squat
```yaml
id: legs_001
name: Barbell Back Squat
muscle_primary: [quadriceps, gluteus_maximus]
muscle_secondary: [hamstrings, adductors, erector_spinae, core]
equipment: [barbell, squat_rack]
difficulty: intermediate
movement_pattern: squat
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3–5 × 3–6 (strength) | 3–4 × 6–12 (hypertrophy)"
rest_seconds: 180–300
cues:
  - "High bar: bar on upper traps, more upright torso, more quad emphasis"
  - "Low bar: bar on rear delts, more forward lean, more hip/glute emphasis"
  - "Brace 360°; valsalva before descent"
  - "Break hips and knees simultaneously"
  - "Knees track over toes — don't cave in"
  - "Depth: crease of hip at or below top of knee ('parallel')"
  - "Drive knees out on ascent; push floor away"
common_errors:
  - error: "Knee cave (valgus collapse)"
    fix: "Cue 'spread the floor'; strengthen glute medius; check foot position"
  - error: "Butt wink (lumbar flexion at depth)"
    fix: "May need mobility work; reduce depth until mobility improves"
  - error: "Forward lean excessive"
    fix: "Check ankle mobility; use heel elevation; consider front squat"
substitutions:
  no_rack: [legs_002, legs_003, legs_007]
  knee_pain: [legs_004, legs_007, legs_010]
  beginner: [legs_007, legs_002]
progressions: [legs_001_pause, legs_001_tempo, legs_001_front_squat]
regressions: [legs_007, legs_002]
contraindications: [acute_knee_injury, acute_lumbar_strain]
evidence_notes: "Highest absolute quad and glute loading; mechanical loading superior to leg press for bone density (Sherk et al., 2011)"
```

---

## Goblet Squat
```yaml
id: legs_002
name: Goblet Squat
muscle_primary: [quadriceps, gluteus_maximus]
muscle_secondary: [core, adductors, hamstrings]
equipment: [dumbbell_or_kettlebell]
difficulty: beginner
movement_pattern: squat
force_type: push
mechanic: compound
modality: [gym, home, hotel]
sets_rep_range: "3–4 × 10–20"
rest_seconds: 60–90
cues:
  - "Hold weight at chest with both hands — counterbalance aids upright torso"
  - "Feet shoulder-width, toes slightly out"
  - "Elbows track inside knees at depth — pushes knees out"
  - "Deep squat: hips well below parallel typically achievable"
common_errors:
  - error: "Weight too heavy — compensating with forward lean"
    fix: "Lighter weight; the counterbalance effect is the point"
substitutions:
  no_equipment: [legs_007]
progressions: [legs_001, legs_003]
regressions: [legs_007]
population_notes: "Best squat teaching tool for all populations; safe for beginners, elderly, overweight"
```

---

## Dumbbell Front Squat
```yaml
id: legs_003
name: Dumbbell Front Squat
muscle_primary: [quadriceps]
muscle_secondary: [gluteus_maximus, core, adductors]
equipment: [dumbbells]
difficulty: intermediate
movement_pattern: squat
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 8–15"
rest_seconds: 90
cues:
  - "Dumbbells at shoulders, elbows high"
  - "Very upright torso — front-loaded forces anterior counterbalance"
  - "Knees track over toes; depth as mobility allows"
substitutions:
  no_dumbbells: [legs_002, legs_007]
progressions: [legs_001]
regressions: [legs_002]
```

---

## Leg Press
```yaml
id: legs_004
name: Leg Press (45° Sled)
muscle_primary: [quadriceps, gluteus_maximus]
muscle_secondary: [hamstrings, adductors]
equipment: [leg_press_machine]
difficulty: beginner
movement_pattern: squat_pattern
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 10–15"
rest_seconds: 60–90
cues:
  - "Foot placement: high and wide = more glute/ham; low and narrow = more quad"
  - "Don't lock out knees at top — slight bend maintained"
  - "Lower until 90° at knee — don't round lower back off pad at depth"
  - "Back flat against pad throughout"
common_errors:
  - error: "Lowering too deep and back rounding off pad"
    fix: "Reduces lumbar safety; stop at 90° or before back leaves pad"
  - error: "Locking out knees"
    fix: "Joint stress; maintain slight bend"
substitutions:
  no_machine: [legs_002, legs_007]
  knee_pain_ok: [legs_004]
progressions: [legs_001]
regressions: null
population_notes: "Excellent for elderly and those with lower back issues — supported spine, controlled ROM"
```

---

## Bulgarian Split Squat
```yaml
id: legs_005
name: Bulgarian Split Squat
muscle_primary: [quadriceps, gluteus_maximus]
muscle_secondary: [hamstrings, adductors, core]
equipment: [bench_or_chair, dumbbells_optional]
difficulty: intermediate
movement_pattern: unilateral_squat
force_type: push
mechanic: compound
modality: [gym, home]
sets_rep_range: "3 × 8–12 per side"
rest_seconds: 90–120
cues:
  - "Rear foot elevated on bench — laces down"
  - "Front foot far enough forward that shin stays vertical at depth"
  - "Lower until rear knee near floor"
  - "Drive through front heel to stand"
  - "Torso can lean forward slightly for glute emphasis"
common_errors:
  - error: "Front foot too close — shin angles forward excessively"
    fix: "Step foot further from bench"
  - error: "Hip dropping to side"
    fix: "Core and glute med engagement"
substitutions:
  balance_issues: [legs_006]
  no_bench: [legs_006]
progressions: [legs_005_barbell, legs_005_deficit]
regressions: [legs_006]
evidence_notes: "Equivalent glute activation to barbell squat at lower spinal loading (McCurdy et al., 2010)"
population_notes: "Not recommended for beginners or elderly without support"
```

---

## Reverse Lunge
```yaml
id: legs_006
name: Reverse Lunge
muscle_primary: [quadriceps, gluteus_maximus]
muscle_secondary: [hamstrings, adductors, core]
equipment: [bodyweight_or_dumbbells]
difficulty: beginner
movement_pattern: unilateral_squat
force_type: push
mechanic: compound
modality: [gym, home, hotel]
sets_rep_range: "3 × 10–15 per side"
rest_seconds: 60–90
cues:
  - "Step backward — safer than forward lunge for knee tracking"
  - "Lower rear knee toward floor"
  - "Front knee stays behind toes"
  - "Push through front heel to return"
  - "Upright torso"
common_errors:
  - error: "Front knee caving inward"
    fix: "Drive knee out over pinky toe"
substitutions:
  no_equipment: [legs_006]
progressions: [legs_005, legs_006_walking]
regressions: [legs_007]
population_notes: "Preferred over forward lunge for beginners, knee pain, and elderly — more stable, less forward shear"
```

---

## Bodyweight Squat
```yaml
id: legs_007
name: Bodyweight Squat
muscle_primary: [quadriceps, gluteus_maximus]
muscle_secondary: [hamstrings, adductors, core]
equipment: []
difficulty: beginner
movement_pattern: squat
force_type: push
mechanic: compound
modality: [home, hotel, gym, outdoor, elderly, beginner]
sets_rep_range: "3–4 × 15–30"
rest_seconds: 45–60
cues:
  - "Feet shoulder-width, toes slightly out"
  - "Arms forward as counterbalance"
  - "Break hips and knees simultaneously"
  - "Knees track over toes — no cave"
  - "Sit to parallel or deeper"
substitutions: null
progressions: [legs_002, legs_006]
regressions: [legs_007_box]
population_notes: "Universal starting point for all populations"
```

---

## Box Squat
```yaml
id: legs_008
name: Box Squat
muscle_primary: [gluteus_maximus, hamstrings]
muscle_secondary: [quadriceps, adductors, erector_spinae]
equipment: [box_or_chair, barbell_optional]
difficulty: beginner
movement_pattern: squat
force_type: push
mechanic: compound
modality: [gym, home]
sets_rep_range: "3–4 × 6–12"
rest_seconds: 90–120
cues:
  - "Box height: just below parallel to teach depth or above for limited mobility"
  - "Sit back to box — don't drop straight down"
  - "Touch and go or pause briefly on box"
  - "Drive through heels to stand"
population_notes: "Excellent teaching tool and depth governor; recommended for elderly or those with knee concerns"
substitutions:
  no_box: [legs_007]
progressions: [legs_001, legs_002]
regressions: [legs_007]
```

---

## Leg Extension
```yaml
id: legs_009
name: Leg Extension
muscle_primary: [quadriceps]
muscle_secondary: []
equipment: [leg_extension_machine]
difficulty: beginner
movement_pattern: knee_extension
force_type: push
mechanic: isolation
modality: gym
sets_rep_range: "3 × 12–20"
rest_seconds: 45–60
cues:
  - "Full extension at top; slow eccentric (3 seconds)"
  - "Foot position: neutral, turned in, or turned out shifts quad emphasis"
  - "Pause 1 second at peak contraction"
common_errors:
  - error: "Using momentum / swinging the weight"
    fix: "Control; if can't, reduce load"
contraindications: [acute_patellar_tendinopathy, post_ACL_reconstruction_early_phase]
substitutions:
  no_machine: [legs_001, legs_002]
progressions: [legs_009_single_leg]
evidence_notes: "Useful quad isolation finisher; controversy exists re: open-chain loading post-ACL — follow physio guidance"
```

---

## Leg Curl (Lying or Seated)
```yaml
id: legs_010
name: Leg Curl
muscle_primary: [hamstrings]
muscle_secondary: [gastrocnemius]
equipment: [leg_curl_machine]
difficulty: beginner
movement_pattern: knee_flexion
force_type: pull
mechanic: isolation
modality: gym
sets_rep_range: "3 × 10–15"
rest_seconds: 60
cues:
  - "Seated version: greater hamstring stretch (hip flexed)"
  - "Lying version: classic; avoid hyperextending lower back by gripping pad"
  - "Squeeze at peak contraction; 3-second eccentric"
  - "Don't let hips rise on lying version"
common_errors:
  - error: "Hips rising off pad on lying curl"
    fix: "Reduce weight; grip handles"
substitutions:
  no_machine: [legs_011, back_002]
progressions: [legs_010_nordic]
evidence_notes: "Nordic curl produces greater hamstring eccentric strength and injury prevention benefit"
```

---

## Nordic Hamstring Curl
```yaml
id: legs_011
name: Nordic Hamstring Curl
muscle_primary: [hamstrings]
muscle_secondary: [gluteus_maximus, core]
equipment: [anchor_point_for_feet]
difficulty: advanced
movement_pattern: knee_flexion_eccentric
force_type: pull
mechanic: isolation
modality: [gym, home]
sets_rep_range: "3 × 3–8 (with negatives)"
rest_seconds: 120
cues:
  - "Kneel, feet anchored under heavy object or partner holds"
  - "Lower body toward floor under control — lean torso forward"
  - "Use hands to catch yourself at bottom; push back up"
  - "Progress: reduce hand assistance over time"
evidence_notes: "Most effective hamstring injury prevention exercise; 50% reduction in hamstring strains in RCTs (Petersen et al., 2011)"
contraindications: [acute_hamstring_strain]
substitutions:
  too_hard: [legs_010]
progressions: null
```

---

## Hip Thrust
```yaml
id: legs_012
name: Barbell Hip Thrust
muscle_primary: [gluteus_maximus]
muscle_secondary: [hamstrings, adductors, quadriceps]
equipment: [barbell, bench, pad]
difficulty: beginner
movement_pattern: hip_extension
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 8–15"
rest_seconds: 60–90
cues:
  - "Upper back on bench edge; bar padded across hips"
  - "Feet flat, hip-width apart"
  - "Drive through heels — squeeze glutes hard at top"
  - "Chin tucked — don't hyperextend spine at top; full glute squeeze stops movement"
  - "Knees at 90° at lockout"
common_errors:
  - error: "Lower back extending instead of hip extending"
    fix: "Tuck chin; think about ribs staying down; the glutes should stop the movement"
substitutions:
  no_barbell: [legs_012_bodyweight, legs_013]
  home_only: [legs_012_bodyweight, legs_013]
progressions: [legs_012_single_leg, legs_012_banded]
regressions: [legs_013]
evidence_notes: "Greatest peak glute activation of any exercise (Contreras et al., 2015)"
```

---

## Glute Bridge
```yaml
id: legs_013
name: Glute Bridge (Bodyweight)
muscle_primary: [gluteus_maximus]
muscle_secondary: [hamstrings, core]
equipment: []
difficulty: beginner
movement_pattern: hip_extension
force_type: push
mechanic: compound
modality: [home, hotel, gym, rehabilitation, elderly]
sets_rep_range: "3 × 15–25 (or 3 × 10 with 2s hold)"
rest_seconds: 45
cues:
  - "Lie on back, knees bent, feet flat"
  - "Drive hips up — squeeze glutes hard at top"
  - "Don't hyperextend lower back; posterior tilt at top"
  - "Hold 1–2 seconds for greater glute activation"
substitutions: null
progressions: [legs_012, legs_013_single_leg, legs_013_elevated]
regressions: null
population_notes: "Safest glute activation exercise; suitable for elderly, pregnancy, post-partum, rehabilitation"
```

---

## Calf Raise (Standing)
```yaml
id: legs_014
name: Standing Calf Raise
muscle_primary: [gastrocnemius]
muscle_secondary: [soleus]
equipment: [step_optional, dumbbells_optional]
difficulty: beginner
movement_pattern: plantarflexion
force_type: push
mechanic: isolation
modality: [gym, home, hotel, elderly]
sets_rep_range: "4 × 15–25"
rest_seconds: 45–60
cues:
  - "Use a step for greater ROM — full stretch at bottom (heel below step)"
  - "Pause at top and bottom — no bouncing"
  - "Knees straight to emphasise gastrocnemius"
  - "3-second eccentric for tendon adaptation"
common_errors:
  - error: "Partial ROM — not reaching full stretch"
    fix: "Use elevated surface; full range builds more muscle and tendon strength"
evidence_notes: "Slow eccentrics (3s) shown superior for Achilles tendinopathy rehabilitation and prevention"
substitutions:
  no_step: [legs_014_seated]
progressions: [legs_014_single_leg, legs_014_seated]
```

---

## Wall Sit
```yaml
id: legs_015
name: Wall Sit
muscle_primary: [quadriceps]
muscle_secondary: [gluteus_maximus, hamstrings]
equipment: [wall]
difficulty: beginner
movement_pattern: isometric_squat
force_type: push
mechanic: isolation
modality: [home, hotel, office, elderly]
sets_rep_range: "3 × 30–90 seconds"
rest_seconds: 60–90
cues:
  - "Back flat against wall; thighs parallel to floor"
  - "Knees at 90°; over feet"
  - "Arms crossed or on thighs — don't push on thighs"
  - "Breathe — don't hold breath for isometric holds"
substitutions: null
progressions: [legs_007, legs_002]
population_notes: "Excellent for elderly, rehab, office workers — zero equipment, scalable hold time"
```

---

## Step-Up
```yaml
id: legs_016
name: Step-Up
muscle_primary: [gluteus_maximus, quadriceps]
muscle_secondary: [hamstrings, adductors]
equipment: [box_or_step, dumbbells_optional]
difficulty: beginner
movement_pattern: unilateral_squat
force_type: push
mechanic: compound
modality: [gym, home, hotel, elderly]
sets_rep_range: "3 × 10–15 per side"
rest_seconds: 60
cues:
  - "Step up — drive through heel of top foot, not toe of bottom foot"
  - "Don't push off back leg — step and stand"
  - "Control descent — don't drop back foot"
  - "Box height: mid-shin to knee level"
substitutions:
  no_step: [legs_006]
progressions: [legs_005]
regressions: [legs_007]
population_notes: "Safe unilateral option for elderly; balance and functional strength benefit"
```
