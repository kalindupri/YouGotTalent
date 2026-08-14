"use client";

import { useCallback, useRef, useState } from "react";

// A simple rotary "knob" control: drag vertically to adjust (drag up = increase, drag down =
// decrease), which is the standard convention in audio software -- there's no natural
// "horizontal" direction for a dial, and vertical drag doesn't get obscured by the finger/cursor
// the way dragging directly on the dial's arc would.
export default function Knob({
  label,
  value,
  min,
  max,
  step = 1,
  unit = "",
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  onChange: (value: number) => void;
}) {
  const [dragging, setDragging] = useState(false);
  const dragStartRef = useRef<{ y: number; value: number } | null>(null);

  const clamp = useCallback((v: number) => Math.min(max, Math.max(min, v)), [min, max]);

  function handlePointerDown(e: React.PointerEvent) {
    e.preventDefault();
    (e.target as Element).setPointerCapture(e.pointerId);
    dragStartRef.current = { y: e.clientY, value };
    setDragging(true);
  }

  function handlePointerMove(e: React.PointerEvent) {
    if (!dragStartRef.current) return;
    const deltaY = dragStartRef.current.y - e.clientY;
    // Full range over a ~150px drag.
    const deltaValue = (deltaY / 150) * (max - min);
    const next = Math.round(clamp(dragStartRef.current.value + deltaValue) / step) * step;
    onChange(next);
  }

  function handlePointerUp(e: React.PointerEvent) {
    (e.target as Element).releasePointerCapture(e.pointerId);
    dragStartRef.current = null;
    setDragging(false);
  }

  // Map value to a -135deg..135deg rotation, matching a typical hardware knob's sweep.
  const fraction = (value - min) / (max - min);
  const angle = -135 + fraction * 270;

  return (
    <div className="flex flex-col items-center gap-1">
      <div
        role="slider"
        aria-label={label}
        aria-valuemin={min}
        aria-valuemax={max}
        aria-valuenow={value}
        tabIndex={0}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onKeyDown={(e) => {
          if (e.key === "ArrowUp" || e.key === "ArrowRight") onChange(clamp(value + step));
          if (e.key === "ArrowDown" || e.key === "ArrowLeft") onChange(clamp(value - step));
        }}
        className={`relative flex h-12 w-12 cursor-ns-resize touch-none select-none items-center justify-center rounded-full border-2 bg-white shadow-sm transition-colors dark:bg-zinc-900 ${
          dragging ? "border-rose-600" : "border-zinc-300 dark:border-zinc-700"
        }`}
      >
        <div
          className="absolute top-1 h-4 w-0.5 rounded-full bg-rose-600"
          style={{ transform: `rotate(${angle}deg)`, transformOrigin: "50% 22px" }}
        />
      </div>
      <span className="text-[10px] font-bold uppercase tracking-wide text-zinc-500">{label}</span>
      <span className="text-[10px] text-zinc-400">
        {value > 0 && unit === "dB" ? "+" : ""}
        {value}
        {unit}
      </span>
    </div>
  );
}
