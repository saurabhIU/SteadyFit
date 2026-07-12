export const PLAN_UPDATED = "steadyfit:plan-updated";

export function notifyPlanUpdated() {
  window.dispatchEvent(new Event(PLAN_UPDATED));
}
