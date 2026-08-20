"use client";

import { useId, useState } from "react";
import { inputClass } from "@/lib/ui";

/** Three dropdowns rather than a calendar.
 *
 * `<input type="date">` shows a locale-dependent "dd/mm/yyyy" mask that people routinely
 * misread and mistype, and its calendar popup is the wrong shape for a birth date — reaching
 * 1994 means paging back hundreds of months. Picking a year straight from a list is faster
 * and unambiguous, and native selects are good on mobile.
 *
 * Value is an ISO "YYYY-MM-DD" string (or "" when incomplete), so callers can keep sending it
 * to the API unchanged.
 *
 * The three parts are held in local state rather than derived from `value`. They have to be:
 * a birth date is only a valid ISO string once all three are chosen, so deriving them would
 * mean the first two selections round-trip through an empty `value` and visibly reset
 * themselves — the field could never be filled in at all.
 */

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const OLDEST_YEAR_OFFSET = 100;

type Parts = { d: number; m: number; y: number };

const EMPTY: Parts = { d: 0, m: 0, y: 0 };

function splitIso(iso: string): Parts {
  if (!iso) return EMPTY;
  const [y, m, d] = iso.split("-").map(Number);
  if (!y || !m || !d) return EMPTY;
  return { d, m, y };
}

function toIso({ d, m, y }: Parts): string {
  if (!d || !m || !y) return "";
  return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

function daysInMonth(year: number, month: number): number {
  if (!year || !month) return 31;
  // Day 0 of the next month is the last day of this one, which gets February and leap
  // years right without a special case.
  return new Date(year, month, 0).getDate();
}

export default function DateOfBirthInput({
  value,
  onChange,
  required = false,
  disabled = false,
}: {
  value: string;
  onChange: (isoDate: string) => void;
  required?: boolean;
  disabled?: boolean;
}) {
  const id = useId();
  const [parts, setParts] = useState<Parts>(() => splitIso(value));
  const [lastValue, setLastValue] = useState(value);

  // Adopt a complete date pushed in from outside (loading an existing profile, a form reset).
  // Adjusted during render rather than in an effect -- React's documented pattern for "reset
  // state when a prop changes", and it avoids the extra render pass an effect would cost.
  // Guarded on the round-tripped ISO so this can never fight the user's partial selections:
  // while they are mid-entry `value` is "" and this does nothing.
  if (value !== lastValue) {
    setLastValue(value);
    if (value && value !== toIso(parts)) setParts(splitIso(value));
  }

  const thisYear = new Date().getFullYear();
  const years = Array.from({ length: OLDEST_YEAR_OFFSET + 1 }, (_, i) => thisYear - i);
  const days = Array.from({ length: daysInMonth(parts.y, parts.m) }, (_, i) => i + 1);

  function update(patch: Partial<Parts>) {
    const next = { ...parts, ...patch };
    // Clamp so switching from 31 Jan to February can't leave the 31st selected.
    const max = daysInMonth(next.y, next.m);
    if (next.d > max) next.d = max;
    setParts(next);
    onChange(toIso(next));
  }

  const selectClass = `${inputClass} appearance-none`;

  return (
    <div className="grid grid-cols-3 gap-2">
      <div>
        <label htmlFor={`${id}-day`} className="mb-1 block text-xs font-normal text-zinc-500">
          Day
        </label>
        <select
          id={`${id}-day`}
          required={required}
          disabled={disabled}
          value={parts.d || ""}
          onChange={(e) => update({ d: Number(e.target.value) })}
          className={selectClass}
        >
          <option value="">Day</option>
          {days.map((day) => (
            <option key={day} value={day}>
              {day}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor={`${id}-month`} className="mb-1 block text-xs font-normal text-zinc-500">
          Month
        </label>
        <select
          id={`${id}-month`}
          required={required}
          disabled={disabled}
          value={parts.m || ""}
          onChange={(e) => update({ m: Number(e.target.value) })}
          className={selectClass}
        >
          <option value="">Month</option>
          {MONTHS.map((label, i) => (
            <option key={label} value={i + 1}>
              {label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor={`${id}-year`} className="mb-1 block text-xs font-normal text-zinc-500">
          Year
        </label>
        <select
          id={`${id}-year`}
          required={required}
          disabled={disabled}
          value={parts.y || ""}
          onChange={(e) => update({ y: Number(e.target.value) })}
          className={selectClass}
        >
          <option value="">Year</option>
          {years.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
