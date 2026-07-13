export type CouncilProposals = Record<string, string>;

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

export type ChatResponse = {
  thread_id: string;
  reply: string;
  council: CouncilProposals;
  pending_approval?: PendingApproval | null;
};

export type ChatHistoryMessage = {
  role: "user" | "assistant";
  content: string;
  council?: CouncilProposals;
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
  council?: CouncilProposals;
};

export type UserProfile = {
  name: string;
  goal: string;
  sessions_per_week: number;
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
