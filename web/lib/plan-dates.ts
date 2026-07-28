/**
 * Single source of truth for Plan page week dates.
 * Header range and day-tile day-of-month both derive from week_start (Monday ISO).
 */

const WEEKDAY_OFFSET: Record<string, number> = {
  monday: 0,
  mon: 0,
  tuesday: 1,
  tue: 1,
  wednesday: 2,
  wed: 2,
  thursday: 3,
  thu: 3,
  friday: 4,
  fri: 4,
  saturday: 5,
  sat: 5,
  sunday: 6,
  sun: 6,
};

/** Parse YYYY-MM-DD as local noon to avoid DST/UTC day shifts. */
export function parseWeekStart(weekStart: string): Date | null {
  const d = new Date(`${weekStart}T12:00:00`);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function weekdayOffset(dayName: string): number | null {
  const key = dayName.trim().toLowerCase();
  if (key in WEEKDAY_OFFSET) return WEEKDAY_OFFSET[key];
  return null;
}

/** Calendar Date for a named weekday within the week that starts on weekStart (Mon). */
export function dateForWeekday(weekStart: string, dayName: string): Date | null {
  const start = parseWeekStart(weekStart);
  if (!start) return null;
  const offset = weekdayOffset(dayName);
  if (offset == null) return null;
  const d = new Date(start);
  d.setDate(d.getDate() + offset);
  return d;
}

/** Day-of-month string for a tile, e.g. "28" (not zero-padded index). */
export function dayOfMonthLabel(weekStart: string, dayName: string): string {
  const d = dateForWeekday(weekStart, dayName);
  if (!d) return "—";
  return String(d.getDate());
}

/** Header range from the same week_start, e.g. "Jul 27 – Aug 2". */
export function formatWeekRange(weekStart: string): string {
  const start = parseWeekStart(weekStart);
  if (!start) return weekStart;
  const end = new Date(start);
  end.setDate(end.getDate() + 6);
  const fmt = (d: Date) =>
    d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return `${fmt(start)} – ${fmt(end)}`;
}

/**
 * All seven day-of-month labels Mon→Sun for a week_start.
 * Used by tests to assert header/tiles share one source of truth.
 */
export function weekDayOfMonthLabels(weekStart: string): string[] {
  const names = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ];
  return names.map((name) => dayOfMonthLabel(weekStart, name));
}
