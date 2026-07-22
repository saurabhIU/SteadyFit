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

export type PendingApproval = {
  type: "plan_approval";
  proposed_plan: WeekPlan | null;
  scheduler_summary?: string;
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
