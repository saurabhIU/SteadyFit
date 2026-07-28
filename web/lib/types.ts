export type CoachingTeamChip = {
  type: "proposal" | "critique" | "revision" | string;
  agent: string;
  text: string;
};

/** Legacy agent→text map, or ordered critique/revision transcript chips. */
export type CoachingTeamProposals = Record<string, string> | CoachingTeamChip[];

export type WorkoutDay = {
  day: string;
  focus: string;
  duration_min: number;
  status: "planned" | "done" | "skipped" | "moved";
};

export type WeekPlan = {
  week_start: string;
  days: WorkoutDay[];
  calorie_target?: number;
  protein_target_g?: number;
  notes?: string;
};

export type ProposedDietMeal = {
  day: string;
  meal_slot: string;
  food_description: string;
  kcal?: number | null;
  protein_g?: number | null;
  source_kb_id?: string | null;
};

export type PendingApproval = {
  type: "plan_approval";
  proposed_plan: WeekPlan | null;
  proposed_diet_plan?: ProposedDietMeal[];
  diet_plan_summary?: string[];
  tdee_targets?: {
    calorie_target?: number;
    protein_target_g?: number;
    tdee_kcal?: number;
    is_estimate?: boolean;
    notes?: string;
  };
  calorie_target?: number | null;
  protein_target_g?: number | null;
  scheduler_summary?: string;
  /** True when the user had no prior WeekPlan (first-ever draft). */
  is_first_plan?: boolean;
  headline?: string;
  subhead?: string;
};

export type Citation = {
  source_file: string;
  section: string;
  kb_id?: string | null;
  snippet?: string;
  tag?: string;
};

export type ChatResponse = {
  thread_id: string;
  reply: string;
  coaching_team: CoachingTeamProposals;
  pending_approval?: PendingApproval | null;
  quick_replies?: string[];
  citations?: Citation[];
  /** One-time soft invite to upload a personal doc (chat Upload chip). */
  offer_upload?: boolean;
};

export type ChatHistoryMessage = {
  role: "user" | "assistant";
  content: string;
  coaching_team?: CoachingTeamProposals;
};

export type ChatHistoryResponse = {
  thread_id: string;
  messages: ChatHistoryMessage[];
  pending_approval?: PendingApproval | null;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  imagePreviewUrl?: string;
  coaching_team?: CoachingTeamProposals;
  citations?: Citation[];
  /** Contextual answer chips for this assistant turn (intake / Done conflict, etc.). */
  quickReplies?: string[];
  /** True after the user answered via chip or free text — chips stay visible but inert. */
  quickRepliesAnswered?: boolean;
};

export type UserProfile = {
  name: string;
  goal: string;
  age?: number | null;
  sex?: string | null;
  preferred_workout_modes?: string[];
  food_preference?: string | null;
  sessions_per_week: number | null;
  constraints?: string[];
  onboarding_complete?: boolean;
  /** @deprecated legacy mirrors */
  injuries: string[];
  food_preferences: string[];
  workout_preferences: string[];
};

export type AdherenceStats = {
  last14d: Record<string, number>;
  adherence_pct: number | null;
  drop_off_signal: boolean;
  streak_weeks: number;
};

export type PlanResponse = {
  thread_id: string;
  profile: UserProfile;
  week_plan: WeekPlan | null;
  adherence: AdherenceStats;
};

export type FoodLogMeal = {
  id: number;
  meal_label: string | null;
  foods: Array<{ name?: string; estimated_portion?: string } | string>;
  kcal: number | null;
  protein_g: number | null;
  logged_at: string | null;
};

export type PlannedDietMeal = {
  id?: number;
  day: string;
  meal_slot: string;
  food_description: string;
  kcal?: number | null;
  protein_g?: number | null;
  status?: string;
  source_kb_id?: string | null;
};

export type TodayFoodLogResponse = {
  meals: FoodLogMeal[];
  /** Structured diet_plan_days for today (planned — not logged intake). */
  planned_meals?: PlannedDietMeal[];
  totals: {
    date: string;
    tz: string;
    kcal_consumed: number;
    protein_g_consumed: number;
    carbs_g_consumed: number;
    fat_g_consumed: number;
    entry_count: number;
  };
  targets: {
    calorie_target: number | null;
    protein_target_g: number | null;
  };
};
