# Volume 6 — Exercise Science
**SteadyFit Knowledge Base v1.0**
Tags: `exercise-science` `principles` `periodization` `recovery` `adaptation`

---

## Hypertrophy: Evidence-Based Principles

```yaml
topic: muscle_hypertrophy
definition: "Increase in muscle cross-sectional area through increased myofibrillar protein content"

key_drivers:
  mechanical_tension:
    definition: "Force × time under tension; primary driver"
    implication: "Load matters; controlled eccentrics matter"
  metabolic_stress:
    definition: "Metabolite accumulation (lactate, hydrogen ions)"
    implication: "Moderate rep ranges (10–20), short rests, pump work"
  muscle_damage:
    definition: "Microtrauma to muscle fibres; least important of the three"
    implication: "Don't chase soreness; eccentric loading sufficient"

optimal_parameters:
  sets_per_muscle_per_week: "10–20 hard sets (Schoenfeld meta-analysis, 2017)"
  rep_range: "6–30 reps all produce hypertrophy when taken near failure"
  intensity: "Reps-in-Reserve (RIR) 0–3 — proximity to failure is key"
  frequency: "2x/week per muscle group minimum; 3x acceptable"
  progressive_overload: "Non-negotiable — must increase stimulus over time"
  protein: "1.6–2.2 g/kg/day (Morton et al., 2018)"
  sleep: "7–9 hours — majority of muscle protein synthesis occurs during sleep"

evidence_hierarchy:
  grade_A: [Schoenfeld_2017_meta_analysis, Morton_2018_protein_meta, Krieger_2010_sets_meta]
  key_finding: "Volume (total sets) is the primary driver of hypertrophy across all rep ranges"
```

---

## Progressive Overload

```yaml
definition: "Systematic increase in training stimulus over time to force continued adaptation"

methods:
  load_progression:
    description: "Increase weight when target reps achieved with 2+ RIR"
    frequency: "As often as possible for beginners; weekly for intermediate; monthly for advanced"
    increments: {lower_body: "2.5kg", upper_body: "1.25kg", isolation: "0.5–1kg"}

  rep_progression:
    description: "Work within a rep range; progress load when top of range achieved"
    example: "Target 3×8–12: when hitting 3×12 consistently, increase load and restart at 8"

  volume_progression:
    description: "Add sets over a mesocycle (4–6 weeks)"
    example: "Week 1: 3 sets → Week 2: 4 sets → Week 3: 4 sets → Week 4: deload 2 sets"

  technique_progression:
    description: "Improving movement quality allows more effective load"

  density_progression:
    description: "Same volume in less time (reduce rest periods)"

deload_protocol:
  when: "Every 4–8 weeks, or when performance stalls 2–3 sessions in a row"
  method: "Reduce volume by 40–50%; maintain or slightly reduce intensity"
  duration: "1 week"
  why: "Allows connective tissue, joints, and CNS to recover; performance typically rebounds above pre-deload"
```

---

## Strength Development

```yaml
definition: "Maximal force production; primarily neural adaptation initially"

key_parameters:
  intensity: "85–95% 1RM (1–5 reps per set)"
  sets: "3–6 per exercise (high specificity)"
  rest: "3–5 minutes between working sets"
  frequency: "2–4x/week per movement pattern"

neural_adaptation:
  timeline: "First 6–12 weeks of training"
  mechanisms: [increased_motor_unit_recruitment, improved_firing_rate, intermuscular_coordination]
  implication: "Beginners can get very strong before building much visible muscle"

periodization:
  linear: "Add weight each session — suitable for beginners"
  undulating: "Vary rep ranges across sessions/weeks — suitable for intermediate"
  block: "Accumulation → intensification → realization phases — advanced"
```

---

## Recovery Science

```yaml
muscle_protein_synthesis:
  peak: "24–48 hours post-exercise"
  duration_elevated: "Up to 72 hours in beginners; 24–36 hours in advanced"
  implication: "Can train muscle groups every 48–72 hours for optimal MPS stimulation"

sleep:
  optimal: "7–9 hours"
  growth_hormone: "90% of daily GH secreted during slow-wave sleep"
  consequence_of_restriction: "Reduced MPS, elevated cortisol, impaired glucose metabolism"
  practical: "Sleep is the most underrated performance enhancer"

DOMS:
  definition: "Delayed Onset Muscle Soreness — peaks 24–72 hours post-exercise"
  cause: "Inflammatory response to muscle damage; primarily eccentric contractions"
  is_it_required: "No — soreness ≠ effectiveness; reduces with adaptation to same stimulus"
  management: [light_movement, heat, protein_intake, sleep]
  not_effective: "Ice baths shown to blunt hypertrophy adaptation (Roberts et al., 2015)"

HRV_and_readiness:
  definition: "Heart Rate Variability — marker of autonomic nervous system recovery"
  interpretation: "Higher HRV = better recovered; lower = under-recovered"
  tools: [Whoop, Garmin_Body_Battery, Elite_HRV_app]
  action: "Low HRV day → reduce intensity or volume; not necessarily rest"
```

---

## Cardiorespiratory Training

```yaml
zones:
  zone_1_active_recovery: "RPE 3–4 | <60% max HR | light walk, easy cycling | fat oxidation"
  zone_2_aerobic_base: "RPE 4–5 | 60–70% max HR | can speak in sentences | optimal fat loss zone | improves mitochondrial density"
  zone_3_tempo: "RPE 6–7 | 70–80% max HR | can speak in phrases"
  zone_4_threshold: "RPE 7–8 | 80–90% max HR | can speak words only | improves lactate threshold"
  zone_5_VO2max: "RPE 9–10 | 90–100% max HR | cannot speak | HIIT intervals"

fat_loss_cardio:
  most_efficient: "Zone 2 × 150+ min/week + resistance training"
  HIIT_role: "Time-efficient alternative; produces similar fat loss to LISS when total calorie burn matched"
  incline_walking: "10–12% grade, 5–6 km/h — high calorie burn, zero impact"

VO2max_development:
  most_effective: "Zone 4–5 intervals (e.g., 4 × 4 min at 90–95% max HR)"
  frequency: "1–2x/week maximum; requires significant recovery"

concurrent_training_interference:
  concern: "Heavy endurance + heavy strength may blunt adaptations"
  evidence: "Moderate aerobic (<3 sessions/week, moderate intensity) does not meaningfully impair strength/hypertrophy"
  practical: "Don't run immediately before heavy leg day; separate by time or day"
```

---

## MEV / MAV / MRV Framework

```yaml
definitions:
  MEV: "Minimum Effective Volume — least training needed to make gains"
  MAV: "Maximum Adaptive Volume — optimal range for progress"
  MRV: "Maximum Recoverable Volume — beyond this, performance declines"

practical_guidance:
  beginner: "Start at MEV; progress toward MAV over 4–8 weeks"
  intermediate: "Train at MAV; push to MRV for 2–3 weeks, then deload"
  advanced: "Periodise between MEV, MAV, and MRV over mesocycles"

muscle_specific_ranges:
  chest: {MEV: 10, MAV: 16, MRV: 22}
  back: {MEV: 10, MAV: 18, MRV: 25}
  quads: {MEV: 10, MAV: 20, MRV: 26}
  glutes: {MEV: 10, MAV: 20, MRV: 26}
  shoulders_lateral: {MEV: 8, MAV: 16, MRV: 26}
  biceps: {MEV: 6, MAV: 14, MRV: 20}
  triceps: {MEV: 6, MAV: 14, MRV: 20}
  hamstrings: {MEV: 8, MAV: 16, MRV: 20}
  calves: {MEV: 8, MAV: 16, MRV: 20}

source: "Renaissance Periodization (Dr. Mike Israetel) — widely accepted framework in sports science"
```
