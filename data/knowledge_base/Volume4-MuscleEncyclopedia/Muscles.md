# Volume 4 — Muscle Encyclopedia
**SteadyFit Knowledge Base v1.0**
Tags: `anatomy` `muscles` `function` `training`

---

## Pectoralis Major
```yaml
id: muscle_001
name: Pectoralis Major
common_name: "Chest"
heads: [sternal_head, clavicular_head]
origin: "Sternum, ribs 2–6, clavicle"
insertion: "Greater tubercle of humerus"
function: [horizontal_adduction, internal_rotation, shoulder_flexion_clavicular]
best_exercises_sternal: [chest_001, chest_004, chest_006]
best_exercises_clavicular: [chest_002, chest_003, chest_005]
volume_mev: "10 sets/week"
volume_mav: "16 sets/week"
volume_mrv: "22+ sets/week"
optimal_rep_range: "8–20 reps"
frequency: "2x/week minimum"
common_weakness: "Clavicular head often underdeveloped due to lack of incline work"
```

---

## Latissimus Dorsi
```yaml
id: muscle_002
name: Latissimus Dorsi
common_name: "Lats"
origin: "Thoracolumbar fascia, spinous processes T6–T12, iliac crest, lower ribs"
insertion: "Bicipital groove of humerus"
function: [shoulder_extension, shoulder_adduction, internal_rotation, depression_of_scapula]
best_exercises: [back_005, back_007, back_009, back_008]
volume_mev: "10 sets/week"
volume_mav: "16 sets/week"
optimal_rep_range: "8–15 reps"
frequency: "2x/week minimum"
coaching_cue: "Think: protect your armpits from tickling / drive elbows to hip pockets"
note: "Width of back appearance primarily determined by lat development"
```

---

## Gluteus Maximus
```yaml
id: muscle_003
name: Gluteus Maximus
common_name: "Glutes"
origin: "Posterior ilium, sacrum, coccyx"
insertion: "Iliotibial band, gluteal tuberosity of femur"
function: [hip_extension, external_rotation, hip_abduction_upper_fibres]
best_exercises: [legs_012, legs_001, legs_005, legs_013, back_002]
volume_mev: "10 sets/week"
volume_mav: "20 sets/week"
optimal_rep_range: "8–20 reps"
frequency: "2–3x/week"
peak_activation_exercise: "Hip thrust (Contreras et al., 2015)"
common_weakness: "Gluteal amnesia from prolonged sitting — requires conscious activation cues"
coaching_cue: "Squeeze glutes at top of hip thrust — don't just extend the spine"
```

---

## Quadriceps
```yaml
id: muscle_004
name: Quadriceps (4 heads)
heads: [rectus_femoris, vastus_lateralis, vastus_medialis, vastus_intermedius]
function: [knee_extension, hip_flexion_rectus_femoris_only]
best_exercises: [legs_001, legs_004, legs_009, legs_002, legs_005]
volume_mev: "10 sets/week"
volume_mav: "20 sets/week"
optimal_rep_range: "8–20 reps"
note: "Rectus femoris biarticular — best trained with hip extended AND knee flexed (not fully addressed by squat alone — leg curl + squat covers all heads)"
```

---

## Hamstrings
```yaml
id: muscle_005
name: Hamstrings (3 heads)
heads: [biceps_femoris_long, biceps_femoris_short, semimembranosus, semitendinosus]
function: [knee_flexion, hip_extension]
best_exercises: [back_002, legs_010, legs_011, legs_001]
volume_mev: "8 sets/week"
volume_mav: "16 sets/week"
injury_risk: "Most common muscle strain in sport — eccentric emphasis critical"
key_exercise: "Nordic curl for injury prevention"
evidence: "Biceps femoris long head most commonly injured; peak risk during late swing phase running"
```

---

## Deltoids (3 Heads)
```yaml
id: muscle_006
name: Deltoids
heads:
  anterior_deltoid:
    function: [shoulder_flexion, horizontal_adduction, internal_rotation]
    best_exercises: [shoulders_001, shoulders_002, chest_001]
    note: "Often overdeveloped in pressing-heavy programs"
  lateral_deltoid:
    function: [shoulder_abduction]
    best_exercises: [shoulders_004]
    note: "Creates shoulder width; needs dedicated isolation work"
  posterior_deltoid:
    function: [horizontal_abduction, external_rotation, extension]
    best_exercises: [shoulders_005, shoulders_007, back_013]
    note: "Chronically underdeveloped in most gym-goers; critical for posture and shoulder health"
volume_mev: "8 sets/week lateral + 8 rear"
volume_mav: "16 sets/week each head"
imbalance_warning: "Anterior:posterior ratio should be close to 1:1; most lifters are 2:1 or worse"
```

---

## Triceps Brachii
```yaml
id: muscle_007
name: Triceps Brachii
heads: [long_head, lateral_head, medial_head]
function: [elbow_extension, shoulder_extension_long_head]
best_exercises_compound: [arms_006, arms_007, chest_001]
best_exercises_isolation: [arms_008, arms_009_cable, arms_010]
note: "Long head (largest) is best stretched with arm overhead — overhead extensions or skull crusher with shoulder extension component"
volume_mev: "6 sets/week isolation (compound presses provide additional volume)"
volume_mav: "14 sets/week"
```

---

## Biceps Brachii
```yaml
id: muscle_008
name: Biceps Brachii
heads: [long_head, short_head]
function: [elbow_flexion, supination, shoulder_flexion_minor]
best_exercises: [arms_001, arms_002, arms_005, back_005]
volume_mev: "6 sets/week (compound rows/pulldowns provide additional stimulus)"
volume_mav: "14 sets/week"
note: "Long head creates bicep peak; short head creates bicep width — both curls and supination needed"
```

---

## Core Muscles
```yaml
id: muscle_009
name: Core Muscle Group
muscles:
  rectus_abdominis:
    function: "Spinal flexion; resists extension"
    best_exercises: [core_004, core_007, core_010]
  transverse_abdominis:
    function: "360° intra-abdominal pressure; spinal stability"
    best_exercises: [core_001, core_002, core_003]
    note: "The 'corset' muscle — trained through bracing, not crunching"
  obliques:
    function: "Rotation; lateral flexion; anti-rotation"
    best_exercises: [core_005, core_006, core_008, core_009]
  erector_spinae:
    function: "Spinal extension; posture"
    best_exercises: [back_001, back_002, core_003, back_014]

mcgill_insight: "Core function is primarily stabilisation, not movement production — train accordingly (McGill, 2010)"
volume_mev: "8 direct sets/week (compounds provide indirect stimulus)"
```
