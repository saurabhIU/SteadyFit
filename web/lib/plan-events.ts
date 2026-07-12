export const PLAN_UPDATED = "onerepmax:plan-updated";

export function notifyPlanUpdated() {
  window.dispatchEvent(new Event(PLAN_UPDATED));
}
