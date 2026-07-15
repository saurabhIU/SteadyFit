# Volume 1 — Exercise Library: Chest
**SteadyFit Knowledge Base v1.0**
Tags: `chest` `push` `upper-body`

---

## Barbell Bench Press
```yaml
id: chest_001
name: Barbell Bench Press
muscle_primary: [pectoralis_major_sternal, pectoralis_major_clavicular]
muscle_secondary: [anterior_deltoid, triceps_brachii]
equipment: [barbell, bench]
difficulty: intermediate
movement_pattern: horizontal_push
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3–5 × 3–8 (strength) | 3–4 × 8–12 (hypertrophy)"
rest_seconds: 120–180
rir_guidance: "2 RIR for strength blocks; 0–1 RIR for hypertrophy sets"
tempo: "2-0-1-0 (hypertrophy) | 1-0-X-0 (strength)"
cues:
  - "Retract and depress scapulae — pinch a pencil between your shoulder blades"
  - "Feet flat, slight arch in lower back, glutes on bench"
  - "Bar path arcs from lower chest to directly over the shoulder joint at lockout"
  - "Elbows 45–60° from torso — not flared, not tucked"
  - "Wrists neutral, bar in base of palm not fingers"
common_errors:
  - error: "Elbow flare > 75°"
    fix: "Increases shoulder impingement risk; cue 45–60° angle"
  - error: "Bouncing bar off chest"
    fix: "Brief pause on chest; touch-and-go only for experienced lifters"
  - error: "Wrist hyperextension"
    fix: "Neutral wrist; use wrist wraps if needed"
substitutions:
  no_barbell: [chest_002, chest_004, chest_009]
  home_only: [chest_010, chest_011]
  shoulder_pain: [chest_007, chest_003]
  beginner: [chest_010, chest_004]
progressions: [chest_001_paused, chest_001_competition_pause]
regressions: [chest_004, chest_010]
contraindications: [acute_shoulder_impingement, AC_joint_injury]
evidence_notes: "Primary horizontal push pattern; 1-2 sets within 5% of 1RM produce equivalent hypertrophy to higher volumes when effort is matched (Schoenfeld et al., 2017)"
```

---

## Incline Barbell Bench Press
```yaml
id: chest_002
name: Incline Barbell Bench Press
muscle_primary: [pectoralis_major_clavicular, anterior_deltoid]
muscle_secondary: [triceps_brachii, pectoralis_major_sternal]
equipment: [barbell, incline_bench]
difficulty: intermediate
movement_pattern: incline_push
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 6–10"
rest_seconds: 90–120
cues:
  - "Set bench 30–45°; above 60° shifts load to anterior deltoid"
  - "Same scapular retraction as flat bench"
  - "Bar lands at upper chest, not chin or collarbone"
  - "Control the descent — 2 second eccentric minimum"
common_errors:
  - error: "Bench angle too steep (>50°)"
    fix: "Loads anterior deltoid excessively, defeating purpose"
  - error: "Losing upper-back tightness"
    fix: "Re-cue scapular retraction before each set"
substitutions:
  no_barbell: [chest_003, chest_005]
  home_only: [chest_011]
  shoulder_pain: [chest_003]
progressions: [chest_002_paused]
regressions: [chest_003, chest_005]
evidence_notes: "Incline angle of 30–45° maximises clavicular head activation (Trebs et al., 2016)"
```

---

## Incline Dumbbell Press
```yaml
id: chest_003
name: Incline Dumbbell Press
muscle_primary: [pectoralis_major_clavicular]
muscle_secondary: [anterior_deltoid, triceps_brachii]
equipment: [dumbbells, incline_bench]
difficulty: beginner
movement_pattern: incline_push
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 8–15"
rest_seconds: 60–90
cues:
  - "Neutral grip option reduces shoulder stress"
  - "Dumbbells slightly outside chest at bottom — wrists over elbows"
  - "Press to near-lockout but don't clang dumbbells at top"
  - "Each arm works independently — great for correcting side-to-side imbalance"
common_errors:
  - error: "Dumbbells too wide at bottom"
    fix: "Excessive chest stretch with less power — keep elbows at 45°"
substitutions:
  no_dumbbells: [chest_002, chest_005]
  home_only: [chest_011]
  shoulder_pain: [chest_007]
progressions: [chest_003_single_arm]
regressions: [chest_013]
```

---

## Flat Dumbbell Press
```yaml
id: chest_004
name: Flat Dumbbell Press
muscle_primary: [pectoralis_major_sternal]
muscle_secondary: [anterior_deltoid, triceps_brachii]
equipment: [dumbbells, flat_bench]
difficulty: beginner
movement_pattern: horizontal_push
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 8–15"
rest_seconds: 60–90
cues:
  - "Greater ROM than barbell — dumbbells can descend below chest level"
  - "Rotate to neutral grip (palms facing) to reduce shoulder strain"
  - "Control descent over 2 seconds"
common_errors:
  - error: "Elbows fully flared"
    fix: "45–60° from torso to protect the shoulder"
substitutions:
  no_dumbbells: [chest_001]
  home_only: [chest_010, chest_011]
progressions: [chest_001]
regressions: [chest_013]
```

---

## Cable Chest Fly (Low-to-High)
```yaml
id: chest_005
name: Cable Chest Fly Low-to-High
muscle_primary: [pectoralis_major_clavicular]
muscle_secondary: [anterior_deltoid, serratus_anterior]
equipment: [cable_machine]
difficulty: beginner
movement_pattern: horizontal_adduction
force_type: pull
mechanic: isolation
modality: gym
sets_rep_range: "3 × 12–20"
rest_seconds: 45–60
cues:
  - "Cables set low (near floor); hands meet at forehead height"
  - "Slight elbow bend — not a press; keep elbow angle constant"
  - "Squeeze at top — 1 second pause"
  - "Constant tension through full arc unlike dumbbells"
common_errors:
  - error: "Bending arms into a press"
    fix: "Isolate adduction; if you can't, reduce weight"
substitutions:
  no_cable: [chest_006, chest_008]
  home_only: [chest_012]
progressions: [chest_005_single_arm]
regressions: [chest_006]
evidence_notes: "Cable maintains peak tension at peak contraction unlike dumbbell fly which peaks at stretch"
```

---

## Dumbbell Chest Fly
```yaml
id: chest_006
name: Dumbbell Chest Fly
muscle_primary: [pectoralis_major_sternal]
muscle_secondary: [anterior_deltoid, biceps_brachii_short_head]
equipment: [dumbbells, flat_bench]
difficulty: beginner
movement_pattern: horizontal_adduction
force_type: pull
mechanic: isolation
modality: gym
sets_rep_range: "3 × 12–20"
rest_seconds: 45–60
cues:
  - "Slight, fixed elbow bend — elbows soft, not bent into a press"
  - "Lower until upper arms parallel to floor — no deeper"
  - "Imagine hugging a large barrel"
  - "Light weight, high feel — this is an isolation movement"
common_errors:
  - error: "Going too deep"
    fix: "Risk of pec/bicep tendon strain below parallel; stop at upper arm = floor"
  - error: "Using too much weight and turning it into a press"
    fix: "Reduce load; isolate the fly pattern"
substitutions:
  no_dumbbells: [chest_005]
  home_only: [chest_012]
progressions: [chest_005]
regressions: [chest_013]
```

---

## Machine Chest Press
```yaml
id: chest_007
name: Machine Chest Press
muscle_primary: [pectoralis_major_sternal]
muscle_secondary: [anterior_deltoid, triceps_brachii]
equipment: [chest_press_machine]
difficulty: beginner
movement_pattern: horizontal_push
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3–4 × 10–15"
rest_seconds: 60–90
cues:
  - "Seat height: handles at mid-chest level"
  - "Keep head and upper back in contact with pad"
  - "Great for beginners, rehab, or finisher sets — guided path reduces stabilizer demand"
  - "Pause briefly at full extension without locking out"
common_errors:
  - error: "Seat too high or low"
    fix: "Adjust so handles align with mid-chest at the press position"
substitutions:
  no_machine: [chest_004, chest_001]
progressions: [chest_004, chest_001]
regressions: null
population_notes: "Preferred for elderly, rehab populations, and absolute beginners due to guided ROM"
```

---

## Pec Deck / Chest Fly Machine
```yaml
id: chest_008
name: Pec Deck Machine Fly
muscle_primary: [pectoralis_major_sternal, pectoralis_major_clavicular]
muscle_secondary: [anterior_deltoid]
equipment: [pec_deck_machine]
difficulty: beginner
movement_pattern: horizontal_adduction
force_type: pull
mechanic: isolation
modality: gym
sets_rep_range: "3 × 12–20"
rest_seconds: 45–60
cues:
  - "Forearms vertical, elbows at 90°"
  - "Slow eccentric — 3 seconds opening"
  - "Don't let weight stack touch between reps"
common_errors:
  - error: "Elbows dropping below shoulder line"
    fix: "Adjust seat height; maintain horizontal line"
substitutions:
  no_machine: [chest_005, chest_006]
progressions: [chest_005]
population_notes: "Joint-friendly isolation option; recommended for elderly and shoulder-sensitive populations"
```

---

## Chest Dips
```yaml
id: chest_009
name: Chest Dips
muscle_primary: [pectoralis_major_sternal]
muscle_secondary: [triceps_brachii, anterior_deltoid]
equipment: [dip_bars]
difficulty: intermediate
movement_pattern: vertical_push
force_type: push
mechanic: compound
modality: gym
sets_rep_range: "3 × 6–15 (bodyweight) | 3 × 5–10 (weighted)"
rest_seconds: 90–120
cues:
  - "Lean torso forward 30–45° to shift load to chest vs triceps"
  - "Elbows flare outward slightly — different to tricep dips where elbows stay close"
  - "Lower until upper arms parallel to floor — no deeper"
  - "Control the descent; don't drop"
common_errors:
  - error: "Staying too upright"
    fix: "Becomes a tricep movement; lean forward for chest emphasis"
  - error: "Going too deep"
    fix: "Stress on shoulder capsule below parallel; stop at upper arms = floor"
substitutions:
  no_dip_bars: [chest_001, chest_004]
  shoulder_pain: [chest_007, chest_004]
progressions: [chest_009_weighted]
regressions: [chest_007, chest_004]
contraindications: [shoulder_impingement, AC_joint_injury, rotator_cuff_pathology]
```

---

## Push-Up (Standard)
```yaml
id: chest_010
name: Push-Up Standard
muscle_primary: [pectoralis_major_sternal]
muscle_secondary: [anterior_deltoid, triceps_brachii, serratus_anterior]
equipment: []
difficulty: beginner
movement_pattern: horizontal_push
force_type: push
mechanic: compound
modality: [home, hotel, gym, outdoor]
sets_rep_range: "3–4 × 8–30"
rest_seconds: 60
cues:
  - "Hands slightly wider than shoulders, fingers forward or slightly out"
  - "Rigid plank — neutral spine, glutes and core braced"
  - "Lower chest to fist-height from floor"
  - "Elbows 45° from torso"
  - "Full lockout at top — protract scapulae (push floor away)"
common_errors:
  - error: "Hips sagging"
    fix: "Squeeze glutes, brace abs; if failing, regress to incline push-up"
  - error: "Head jutting forward"
    fix: "Pack neck; gaze 6 inches ahead on floor"
  - error: "Elbows flaring to 90°"
    fix: "45° angle to reduce shoulder impingement"
substitutions: null
progressions: [chest_011, chest_015, chest_016]
regressions: [chest_013, chest_014]
population_notes: "Universal entry point — can be regressed (incline) or progressed (decline, archer, plyometric) for any population"
```

---

## Decline Push-Up
```yaml
id: chest_011
name: Decline Push-Up
muscle_primary: [pectoralis_major_sternal, anterior_deltoid]
muscle_secondary: [triceps_brachii, serratus_anterior]
equipment: [chair_or_bench]
difficulty: intermediate
movement_pattern: incline_push
force_type: push
mechanic: compound
modality: [home, hotel]
sets_rep_range: "3 × 8–20"
rest_seconds: 60–90
cues:
  - "Feet elevated on chair/bed — the higher, the more upper chest and shoulder"
  - "Same plank body position as standard push-up"
  - "Slower eccentric for increased time under tension"
substitutions:
  cant_do_decline: [chest_010]
progressions: [chest_016]
regressions: [chest_010]
```

---

## Resistance Band Chest Fly
```yaml
id: chest_012
name: Resistance Band Chest Fly
muscle_primary: [pectoralis_major]
muscle_secondary: [anterior_deltoid]
equipment: [resistance_band, anchor_point]
difficulty: beginner
movement_pattern: horizontal_adduction
force_type: pull
mechanic: isolation
modality: [home, hotel, travel]
sets_rep_range: "3 × 15–20"
rest_seconds: 45–60
cues:
  - "Anchor band at chest height behind you"
  - "Step forward to create tension — arms wide, slight elbow bend"
  - "Bring hands together in front of chest; squeeze 1 second"
  - "Slow, controlled return — band accelerates on the way back"
common_errors:
  - error: "Losing elbow angle and pressing instead of flying"
    fix: "Fix the elbow bend and maintain through full arc"
substitutions:
  no_band: [chest_010]
progressions: [chest_006, chest_005]
```

---

## Incline Push-Up
```yaml
id: chest_013
name: Incline Push-Up
muscle_primary: [pectoralis_major_sternal]
muscle_secondary: [anterior_deltoid, triceps_brachii]
equipment: [wall_or_counter_or_bench]
difficulty: beginner
movement_pattern: horizontal_push
force_type: push
mechanic: compound
modality: [home, hotel, gym, beginner]
sets_rep_range: "3 × 10–20"
rest_seconds: 45–60
cues:
  - "Hands on elevated surface — higher surface = easier"
  - "Same rigid plank position as standard push-up"
  - "Ideal first step before floor push-ups"
common_errors:
  - error: "Hips piking up"
    fix: "Maintain plank — if failing, raise hands higher"
substitutions: null
progressions: [chest_010]
regressions: [chest_014]
population_notes: "Recommended starting point for elderly, obese, or very deconditioned populations"
```

---

## Wall Push-Up
```yaml
id: chest_014
name: Wall Push-Up
muscle_primary: [pectoralis_major]
muscle_secondary: [anterior_deltoid, triceps_brachii]
equipment: [wall]
difficulty: beginner
movement_pattern: horizontal_push
force_type: push
mechanic: compound
modality: [home, hotel, elderly, rehabilitation]
sets_rep_range: "3 × 10–20"
rest_seconds: 45
cues:
  - "Hands shoulder-width on wall at chest height"
  - "Step feet back — further from wall = harder"
  - "Body straight — no bending at hips"
  - "Nose nearly touches wall at bottom"
substitutions: null
progressions: [chest_013, chest_010]
population_notes: "Safest starting point for elderly, post-surgery, very deconditioned, or obese individuals"
```

---

## Archer Push-Up
```yaml
id: chest_015
name: Archer Push-Up
muscle_primary: [pectoralis_major_sternal]
muscle_secondary: [anterior_deltoid, triceps_brachii, serratus_anterior]
equipment: []
difficulty: advanced
movement_pattern: horizontal_push
force_type: push
mechanic: compound
modality: [home, hotel, gym]
sets_rep_range: "3 × 5–10 per side"
rest_seconds: 90
cues:
  - "Hands very wide; shift weight to one arm as you lower"
  - "Opposite arm extends straight — assists and builds toward one-arm push-up"
  - "Rotate torso slightly toward working arm"
substitutions:
  too_hard: [chest_010]
progressions: [chest_016]
regressions: [chest_010]
population_notes: "Advanced; not suitable for beginners, elderly, or those with shoulder issues"
```

---

## One-Arm Push-Up
```yaml
id: chest_016
name: One-Arm Push-Up
muscle_primary: [pectoralis_major, anterior_deltoid]
muscle_secondary: [triceps_brachii, core, obliques]
equipment: []
difficulty: advanced
movement_pattern: horizontal_push
force_type: push
mechanic: compound
modality: [home, hotel, gym]
sets_rep_range: "3 × 3–8 per side"
rest_seconds: 90–120
cues:
  - "Feet wide for stability base"
  - "Free hand behind back or on thigh"
  - "Brace core hard to prevent rotation"
substitutions:
  too_hard: [chest_015, chest_010]
progressions: null
regressions: [chest_015]
population_notes: "Advanced athletes only"
```
