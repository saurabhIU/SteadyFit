# Volume 7 — Nutrition Science
**SteadyFit Knowledge Base v1.0**
Tags: `nutrition` `macros` `protein` `calories` `supplements` `meal-planning`

---

## Protein: The Most Important Macro for Fitness

```yaml
evidence_based_targets:
  general_fitness: "1.6 g/kg/day (Morton et al., 2018 meta-analysis)"
  hypertrophy: "1.6–2.2 g/kg/day"
  fat_loss_with_training: "2.0–2.4 g/kg/day (preserve muscle during deficit)"
  elderly: "1.6–2.2 g/kg/day (higher end to offset anabolic resistance)"
  obese: "Use goal body weight, not current weight, for target calculation"

distribution:
  optimal: "4–5 servings of 30–40g throughout the day"
  why: "Muscle protein synthesis maximised per dose at ~0.4 g/kg per meal; further doses less effective but not harmful"
  minimum: "At least 3 protein-containing meals"

sources_per_100g_cooked:
  animal:
    chicken_breast: "31g protein | 165 kcal | 3.6g fat"
    eggs_per_egg: "6g protein | 78 kcal | 5g fat"
    Greek_yogurt_full_fat: "10g protein | 97 kcal | 5g fat"
    paneer_per_100g: "18g protein | 265 kcal | 20g fat"
    fish_salmon: "20g protein | 208 kcal | 13g fat"
    tuna_canned: "26g protein | 116 kcal | 1g fat"
    whey_protein_per_scoop_30g: "24g protein | 120 kcal | 2g fat"
  plant:
    lentils_cooked: "9g protein | 116 kcal | 0.4g fat"
    chickpeas_cooked: "9g protein | 164 kcal | 2.6g fat"
    tofu_firm: "8g protein | 76 kcal | 4g fat"
    tempeh: "19g protein | 193 kcal | 11g fat"
    edamame: "11g protein | 121 kcal | 5g fat"
    soya_milk: "3.3g protein | 54 kcal | 1.8g fat"
    black_beans: "8.9g protein | 132 kcal | 0.5g fat"

leucine_threshold:
  note: "~3g leucine per meal triggers maximal MPS — whey, dairy, eggs, meat meet this. Plant proteins may need larger servings or combining"
```

---

## Caloric Targets

```yaml
TDEE_calculation:
  step_1: "Calculate BMR (Mifflin-St Jeor most accurate)"
  BMR_men: "10 × weight(kg) + 6.25 × height(cm) − 5 × age + 5"
  BMR_women: "10 × weight(kg) + 6.25 × height(cm) − 5 × age − 161"
  step_2: "Multiply by activity factor"
  activity_factors:
    sedentary: 1.2
    lightly_active_1_3_days: 1.375
    moderately_active_3_5_days: 1.55
    very_active_6_7_days: 1.725
    athlete_twice_daily: 1.9

goals:
  fat_loss:
    deficit: "300–500 kcal/day below TDEE"
    rate: "0.3–0.7 kg/week (sustainable)"
    max_rate: "1% bodyweight/week to minimise muscle loss"
    floor: "Do not go below 1500 kcal men / 1200 kcal women without medical supervision"

  muscle_gain:
    surplus: "100–250 kcal/day above TDEE"
    rate: "0.1–0.25 kg/week (lean gaining)"
    aggressive_surplus: "Not recommended — excess fat gain without proportional muscle gain beyond 250+ kcal surplus"

  recomposition:
    description: "Maintain calories; high protein; resistance training — lose fat and gain muscle simultaneously"
    works_best_for: [beginners, returning_lifters, overweight_individuals]
    patience_required: "Slower body composition change than dedicated bulk/cut"
    calories: "At maintenance TDEE"
```

---

## Carbohydrates

```yaml
function: [primary_fuel_for_high_intensity_exercise, glycogen_storage, brain_fuel]

targets:
  general_fitness: "3–5 g/kg/day"
  endurance_athlete: "5–7 g/kg/day"
  strength_training: "3–5 g/kg/day"
  fat_loss: "No minimum required; reduce calories via carbs while keeping protein high"

quality:
  prioritise:
    - Oats, rice, sweet potato, quinoa
    - Fruits (all varieties)
    - Legumes (also high protein)
    - Vegetables (low calorie, high micronutrient)
  limit:
    - Ultra-processed carbohydrates
    - Refined sugar-sweetened beverages
    - White bread, pastries

glycaemic_index:
  note: "GI matters less than total carbohydrate and overall dietary pattern"
  practical: "Context matters — high-GI food post-workout is appropriate; less so at rest"

timing:
  pre_workout: "Carbs 1–2 hours before for energy availability"
  post_workout: "Carbs + protein within 2 hours to replenish glycogen"
  if_fat_loss_goal: "Total daily intake > timing; don't overthink timing"
```

---

## Fats

```yaml
function: [hormone_production_including_testosterone, fat_soluble_vitamin_absorption, cellular_health]

minimum: "0.5–1 g/kg/day minimum for hormonal health — do not drop below"

targets:
  general: "20–35% of total calories from fat"

quality:
  prioritise:
    - Olive oil, avocado oil
    - Avocados
    - Nuts and seeds
    - Fatty fish (omega-3)
  limit:
    - Trans fats (partially hydrogenated oils)
    - Excessive saturated fat

omega_3:
  target: "1–3g EPA+DHA per day"
  sources: [fatty_fish, fish_oil_supplement, algae_oil_vegan]
  benefits: [anti_inflammatory, cardiovascular_health, muscle_protein_synthesis_support]
```

---

## Hydration

```yaml
daily_target:
  general: "3.5–4L for active adults (including food water)"
  training_days: "Add 500–750ml per hour of exercise"
  urine_colour_guide: "Pale yellow = adequate; dark yellow = dehydrated; clear = overhydrated"

performance_impact:
  2_percent_dehydration: "Up to 5% reduction in strength; up to 10% aerobic performance"
  practical: "Don't train thirsty"

electrolytes:
  sodium: "Key electrolyte; lost in sweat — increase on heavy sweat days"
  potassium: "From fruits and vegetables"
  magnesium: "From nuts, seeds, dark chocolate; supports sleep and recovery"
```

---

## Evidence-Based Supplements

```yaml
tier_1_strong_evidence:
  creatine_monohydrate:
    dose: "3–5g/day; no loading protocol needed"
    timing: "Any time — consistency matters; post-workout with protein convenient"
    benefits: [strength_increase_5_10_percent, lean_mass, power_output, possible_cognitive_benefits]
    safety: "Extensively studied; safe for healthy adults; mild water retention in first weeks"
    form: "Monohydrate — no benefit to more expensive forms (creatine HCL, buffered)"

  protein_powder:
    dose: "Supplement diet to reach daily protein target — not a replacement for whole foods"
    types:
      whey: "Fast-absorbing; highest leucine; best post-workout"
      casein: "Slow-release; good pre-sleep"
      plant_blend: "Combine pea + rice for complete amino acid profile"
    note: "Whole food protein equally effective; powder is convenience"

  caffeine:
    dose: "3–6 mg/kg bodyweight (150–400mg typical) 30–60 min pre-workout"
    benefits: [strength_increase_3_7_percent, endurance, focus, pain_perception_reduction]
    caution: "Half-life 5–6 hours — avoid within 6 hours of sleep"
    tolerance: "Develops with daily use; cycle off periodically or use strategically"

tier_2_moderate_evidence:
  beta_alanine:
    dose: "3.2–6.4g/day (split doses)"
    benefit: "Buffers lactic acid — most useful for 1–4 minute high-intensity efforts"
    side_effect: "Tingling (paraesthesia) — harmless; reduced with split dosing"
    note: "Less relevant for pure strength training; more for endurance or CrossFit"

  omega_3:
    dose: "2–3g EPA+DHA/day"
    benefit: [anti_inflammatory, cardiovascular, mild_MPS_support]
    safe: true

tier_3_insufficient_evidence:
  BCAAs: "Redundant if protein intake is adequate — save your money"
  glutamine: "No benefit beyond adequate protein intake in healthy people"
  testosterone_boosters: "No peer-reviewed evidence for marketed products"
  most_fat_burners: "Proprietary blends with ineffective dosing; evidence weak"

supplements_to_avoid:
  - Unverified proprietary blends
  - Products making extreme claims
  - Anything not NSF or Informed Sport certified if tested athlete
```

---

## Indian Food Macro Reference
*Given the likely user base — practical application with common Indian foods*

```yaml
high_protein_Indian_foods:
  paneer_100g: {protein: 18, carbs: 1.2, fat: 20, kcal: 265}
  dal_cooked_100g: {protein: 9, carbs: 20, fat: 0.4, kcal: 116}
  chicken_curry_100g: {protein: 17, carbs: 5, fat: 8, kcal: 165}
  eggs_per_egg: {protein: 6, carbs: 0.6, fat: 5, kcal: 78}
  Greek_dahi_100g: {protein: 10, carbs: 4, fat: 5, kcal: 97}
  rajma_cooked_100g: {protein: 8.7, carbs: 22, fat: 0.5, kcal: 127}
  chole_cooked_100g: {protein: 9, carbs: 27, fat: 2.6, kcal: 164}
  soya_chunks_30g_dry: {protein: 15, carbs: 9, fat: 0.5, kcal: 100}
  tofu_100g: {protein: 8, carbs: 2, fat: 4, kcal: 76}
  fish_rohu_100g: {protein: 16, carbs: 0, fat: 1.4, kcal: 97}

common_meals:
  dal_rice_200g: {protein: 12, carbs: 58, fat: 2, kcal: 302}
  chicken_biryani_300g: {protein: 22, carbs: 55, fat: 12, kcal: 420}
  paneer_sabzi_150g: {protein: 14, carbs: 8, fat: 16, kcal: 230}
  2_roti_no_butter: {protein: 5, carbs: 30, fat: 1, kcal: 150}
  oats_40g_with_milk: {protein: 8, carbs: 30, fat: 4, kcal: 185}

high_protein_meal_ideas_Indian:
  breakfast:
    - "Egg white omelette (4 whites + 1 yolk) + 2 roti — 28g protein"
    - "Greek dahi + handful almonds + banana — 14g protein"
    - "Oats with milk + 2 boiled eggs — 22g protein"
  lunch:
    - "Dal + rice + 150g chicken — 35g protein"
    - "Rajma + brown rice + dahi — 20g protein"
    - "Paneer bhurji + 3 roti — 25g protein"
  dinner:
    - "Grilled fish + salad + 2 roti — 28g protein"
    - "Soya chunks curry + dal + rice — 22g protein"
    - "Chicken curry + 2 roti + dahi — 30g protein"
  snacks:
    - "Roasted chana 30g — 8g protein"
    - "Paneer cubes 50g — 9g protein"
    - "Boiled eggs × 2 — 12g protein"
    - "Protein shake in water — 24g protein"
```

---

## Eating Out Survival Guide

```yaml
general_principles:
  protein_first: "Order a protein source at every meal — anchor the meal around it"
  control_what_you_can: "Can't control oil in restaurant — control protein, carbs, alcohol"
  don't_skip_meals_to_compensate: "Increases hunger; leads to overeating later"

situations:
  work_lunch_restaurant:
    strategy: "Grilled/tandoori > fried; dal or paneer > naan; skip the starter"
    practical: "Dal + chawal + tandoori chicken = ~35g protein, ~450 kcal"

  biryani_order:
    estimate: "300g chicken biryani ≈ 22g protein, 420 kcal"
    strategy: "Eat slowly; pair with raita (5g more protein); skip the bread"

  fast_food:
    best_options: ["Grilled chicken burger without sauce", "Egg-based options", "Skip fries — not worth the calories"]

  alcohol:
    impact: "7 kcal/g; impairs MPS for ~24 hours; disrupts sleep"
    if_drinking: "Prioritise protein that day; minimise liquid calories from sugary mixers"
    practical: "1–2 standard drinks causes minimal impact; 4+ significantly impairs recovery"
```
