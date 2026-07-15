# Volume 3 — Workout Templates
**SteadyFit Knowledge Base v1.0**
Tags: `templates` `programs` `weekly-plans` `periodization`

---

## Template Index

| ID | Name | Goal | Days/Week | Equipment | Population |
|---|---|---|---|---|---|
| tmpl_001 | Full Body Beginner | General fitness | 3 | Gym | Beginners |
| tmpl_002 | Full Body Intermediate | Strength + Hypertrophy | 3 | Gym | Intermediate |
| tmpl_003 | Upper/Lower Split | Hypertrophy | 4 | Gym | Intermediate |
| tmpl_004 | Push/Pull/Legs | Hypertrophy | 6 | Gym | Advanced |
| tmpl_005 | Push/Pull/Legs | Hypertrophy | 3 (PPL once) | Gym | Intermediate |
| tmpl_006 | Home Beginner | General fitness | 3 | None | Beginners |
| tmpl_007 | Hotel Traveler | Maintenance | 4 | None/Band | Traveler |
| tmpl_008 | Fat Loss Circuit | Fat loss | 3 | Gym | All |
| tmpl_009 | Elderly Foundation | Function + Health | 2 | Minimal | Elderly |
| tmpl_010 | Office Worker Antidote | Posture + Fitness | 3 | Gym | Office |
| tmpl_011 | Strength Powerlifting | Max Strength | 4 | Gym | Advanced |
| tmpl_012 | Swimming + Gym Hybrid | Cardio + Strength | 4 | Pool + Gym | All |
| tmpl_013 | Walking Program | Cardiovascular | 5 | None | All/Beginner |
| tmpl_014 | 20-Min Express | Maintenance | 3 | Gym | Busy |
| tmpl_015 | Diabetes Management | Health + Glucose | 5 | Minimal | Diabetics |

---

## tmpl_001 — Full Body Beginner (3 days/week, Gym)
```yaml
id: tmpl_001
goal: general_fitness
level: beginner
days_per_week: 3
structure: "Full body A/B alternating"
equipment: gym
duration_per_session: 45 minutes
deload_frequency: every_8_weeks

session_A:
  - {exercise: legs_002, sets: 3, reps: "10", rest: 90, note: "Goblet squat — learn pattern"}
  - {exercise: chest_010, sets: 3, reps: "max to 2 RIR", rest: 90, note: "Regress to incline if needed"}
  - {exercise: back_002, sets: 3, reps: "10", rest: 90, note: "DB RDL — hip hinge"}
  - {exercise: back_007, sets: 3, reps: "12", rest: 90, note: "Lat pulldown or assisted pull-up"}
  - {exercise: shoulders_004, sets: 3, reps: "15", rest: 60}
  - {exercise: core_001, sets: 3, reps: "30s", rest: 60}

session_B:
  - {exercise: legs_006, sets: 3, reps: "10/side", rest: 90, note: "Reverse lunge"}
  - {exercise: shoulders_002, sets: 3, reps: "10", rest: 90, note: "DB shoulder press"}
  - {exercise: back_004, sets: 3, reps: "10", rest: 90, note: "DB RDL"}
  - {exercise: back_010, sets: 3, reps: "10/side", rest: 60}
  - {exercise: arms_002, sets: 2, reps: "12", rest: 45}
  - {exercise: core_002, sets: 3, reps: "10/side", rest: 60}

progression:
  rule: "Add smallest available weight when all sets completed with 3+ RIR"
  lower_body: "+2.5kg"
  upper_body: "+1.25kg"
```

---

## tmpl_002 — Full Body Intermediate (3 days/week)
```yaml
id: tmpl_002
goal: strength_and_hypertrophy
level: intermediate
days_per_week: 3
structure: "Full body with weekly undulation"
equipment: gym
duration_per_session: 60 minutes

week_A_day1_strength_focus:
  - {exercise: legs_001, sets: 4, reps: "5", rest: 180, note: "Heavy — 1–2 RIR"}
  - {exercise: chest_001, sets: 4, reps: "5", rest: 180}
  - {exercise: back_005, sets: 4, reps: "5", rest: 180, note: "Weighted if possible"}
  - {exercise: shoulders_001, sets: 3, reps: "6", rest: 120}
  - {exercise: core_008, sets: 3, reps: "12/side", rest: 60}

week_A_day2_hypertrophy_focus:
  - {exercise: legs_004, sets: 3, reps: "12", rest: 90}
  - {exercise: chest_003, sets: 3, reps: "12", rest: 90}
  - {exercise: back_007, sets: 3, reps: "12", rest: 90}
  - {exercise: legs_012, sets: 3, reps: "12", rest: 90}
  - {exercise: arms_002, sets: 3, reps: "15", rest: 60}
  - {exercise: arms_009_cable, sets: 3, reps: "15", rest: 60}
  - {exercise: core_005, sets: 3, reps: "20/side", rest: 45}

week_A_day3_volume_focus:
  - {exercise: legs_005, sets: 3, reps: "10/side", rest: 90}
  - {exercise: chest_005, sets: 3, reps: "15", rest: 60}
  - {exercise: back_008, sets: 3, reps: "15", rest: 60}
  - {exercise: shoulders_004, sets: 4, reps: "15", rest: 60}
  - {exercise: back_013, sets: 3, reps: "20", rest: 45}
  - {exercise: core_009, sets: 3, reps: "40s/side", rest: 60}
```

---

## tmpl_003 — Upper/Lower Split (4 days/week)
```yaml
id: tmpl_003
goal: hypertrophy
level: intermediate
days_per_week: 4
structure: "Upper A / Lower A / Upper B / Lower B"
equipment: gym
duration_per_session: 60–70 minutes
schedule: "Mon Upper A / Tue Lower A / Thu Upper B / Fri Lower B"

upper_A_strength:
  - {exercise: chest_001, sets: 4, reps: "6", rest: 180}
  - {exercise: back_009, sets: 4, reps: "6", rest: 180}
  - {exercise: shoulders_001, sets: 3, reps: "8", rest: 120}
  - {exercise: back_005, sets: 3, reps: "6–8", rest: 120}
  - {exercise: arms_001, sets: 3, reps: "10", rest: 90}
  - {exercise: arms_006, sets: 3, reps: "10", rest: 90}

lower_A_strength:
  - {exercise: legs_001, sets: 4, reps: "5", rest: 300}
  - {exercise: back_002, sets: 3, reps: "8", rest: 120}
  - {exercise: legs_009, sets: 3, reps: "12", rest: 90}
  - {exercise: legs_010, sets: 3, reps: "12", rest: 90}
  - {exercise: legs_014, sets: 4, reps: "15", rest: 60}

upper_B_hypertrophy:
  - {exercise: chest_003, sets: 4, reps: "10–12", rest: 90}
  - {exercise: back_007, sets: 4, reps: "10–12", rest: 90}
  - {exercise: shoulders_002, sets: 3, reps: "12", rest: 90}
  - {exercise: back_008, sets: 3, reps: "12–15", rest: 90}
  - {exercise: chest_005, sets: 3, reps: "15", rest: 60}
  - {exercise: shoulders_004, sets: 3, reps: "15", rest: 60}
  - {exercise: back_013, sets: 3, reps: "20", rest: 45}

lower_B_hypertrophy:
  - {exercise: legs_005, sets: 4, reps: "10/side", rest: 90}
  - {exercise: legs_012, sets: 4, reps: "12", rest: 90}
  - {exercise: legs_009, sets: 3, reps: "15", rest: 60}
  - {exercise: legs_011, sets: 3, reps: "6", rest: 120, note: "Eccentric only"}
  - {exercise: legs_014, sets: 4, reps: "20", rest: 60}
  - {exercise: core_009, sets: 3, reps: "45s/side", rest: 60}
```

---

## tmpl_006 — Home Beginner (3 days/week, No Equipment)
```yaml
id: tmpl_006
goal: general_fitness_and_fat_loss
level: beginner
days_per_week: 3
equipment: none
duration_per_session: 35 minutes

session_A:
  - {exercise: chest_010, sets: 3, reps: "max to 2 RIR", rest: 90, note: "Incline on sofa if needed"}
  - {exercise: legs_007, sets: 3, reps: "20", rest: 60}
  - {exercise: legs_013, sets: 3, reps: "15 (2s hold)", rest: 60}
  - {exercise: shoulders_006, sets: 3, reps: "10", rest: 90}
  - {exercise: core_001, sets: 3, reps: "30–45s", rest: 60}
  - {exercise: core_002, sets: 3, reps: "10/side", rest: 60}

session_B:
  - {exercise: legs_006, sets: 3, reps: "12/side", rest: 60}
  - {exercise: chest_015, sets: 3, reps: "8/side", rest: 90, note: "Archer push-up; regress to standard"}
  - {exercise: legs_015, sets: 3, reps: "45–60s", rest: 90}
  - {exercise: arms_009, sets: 3, reps: "12", rest: 60}
  - {exercise: core_009, sets: 3, reps: "30s/side", rest: 60}
  - {exercise: back_014, sets: 3, reps: "12 (3s hold)", rest: 60}
```

---

## tmpl_007 — Hotel / Travel Program (4 days/week)
```yaml
id: tmpl_007
goal: maintenance_and_fitness
level: intermediate
days_per_week: 4
equipment: [bodyweight, optional_resistance_band]
duration_per_session: 30–40 minutes

day_1_lower:
  - {exercise: legs_007, sets: 4, reps: "20", rest: 60, note: "Slow 3s eccentric"}
  - {exercise: legs_006, sets: 3, reps: "15/side", rest: 60}
  - {exercise: legs_013, sets: 3, reps: "20 (2s hold)", rest: 60}
  - {exercise: back_003, sets: 3, reps: "10/side", rest: 60}
  - {exercise: legs_014, sets: 3, reps: "20", rest: 60}

day_2_upper_push:
  - {exercise: chest_010, sets: 4, reps: "max", rest: 90}
  - {exercise: chest_011, sets: 3, reps: "12", rest: 90}
  - {exercise: arms_009, sets: 3, reps: "12", rest: 60}
  - {exercise: shoulders_006, sets: 3, reps: "10", rest: 60}
  - {exercise: core_004, sets: 3, reps: "30s", rest: 60}

day_3_rest_or_walk: "Active recovery — 30 min walk; mobility"

day_4_full_body:
  - {exercise: legs_006, sets: 3, reps: "12/side", rest: 60}
  - {exercise: chest_015, sets: 3, reps: "8/side", rest: 90}
  - {exercise: legs_013, sets: 3, reps: "15 (2s hold)", rest: 60}
  - {exercise: shoulders_006, sets: 3, reps: "10", rest: 60}
  - {exercise: core_001, sets: 3, reps: "45s", rest: 60}
  - {exercise: core_009, sets: 3, reps: "35s/side", rest: 60}
```

---

## tmpl_008 — Fat Loss Circuit (3 days/week, Gym)
```yaml
id: tmpl_008
goal: fat_loss
level: beginner_to_intermediate
days_per_week: 3
equipment: gym
format: "Circuit — 40s work / 20s rest; 3–4 rounds"
rest_between_rounds: "90–120 seconds"
duration: 35–45 minutes

circuit_A:
  - legs_007    # Bodyweight squat
  - chest_010   # Push-up
  - legs_013    # Glute bridge
  - back_012    # Band row
  - legs_006    # Reverse lunge
  - core_001    # Plank hold
  - shoulders_006 # Pike push-up

circuit_B:
  - legs_002    # Goblet squat
  - chest_004   # DB press
  - back_010    # DB row
  - legs_012    # Hip thrust
  - arms_002    # DB curl
  - arms_009    # Diamond push-up
  - core_005    # Bicycle crunch

calorie_burn_estimate: "200–350 kcal per 35-min session (varies by bodyweight and intensity)"
note: "Combine with 150 min/week moderate-intensity cardio for optimal fat loss"
```

---

## tmpl_013 — Walking Program (Fat Loss + Cardiovascular Health)
```yaml
id: tmpl_013
goal: cardiovascular_health_and_fat_loss
level: all
days_per_week: 5
equipment: none
note: "Most underrated fat loss tool. Preserves muscle unlike running. Zero injury risk."

week_1_2: "20 min/day brisk walk (able to speak in sentences)"
week_3_4: "30 min/day; include 5 min faster pace every 10 min"
week_5_8: "40 min/day; aim for 8,000 steps total per day"
ongoing: "10,000 steps/day + 30 min dedicated walk"

incline_walking:
  note: "Treadmill incline 10–12° at 5–6 km/h dramatically increases calorie burn without joint stress"
  calorie_estimate: "350–550 kcal/hour (bodyweight dependent)"

combine_with: "2–3 resistance sessions per week for best body composition outcome"
```

---

## tmpl_014 — 20-Minute Express (3 days/week, Gym)
```yaml
id: tmpl_014
goal: maintenance
level: intermediate
days_per_week: 3
equipment: gym
format: "Superset pairs — minimal rest; maximum efficiency"
duration: "20 minutes exact"

superset_1:
  rounds: 3
  pair:
    - {A: legs_001_or_002, reps: "8"}
    - {B: back_005, reps: "8"}
  rest: "60s between rounds"

superset_2:
  rounds: 3
  pair:
    - {A: chest_001, reps: "8"}
    - {B: legs_012, reps: "10"}
  rest: "60s between rounds"

superset_3:
  rounds: 2
  pair:
    - {A: shoulders_004, reps: "15"}
    - {B: core_001, reps: "40s"}
  rest: "45s between rounds"

note: "For busy weeks — better than skipping entirely"
```
