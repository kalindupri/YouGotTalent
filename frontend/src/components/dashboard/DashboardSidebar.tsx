"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface DashboardNavItem {
  id: string;
  label: string;
  icon: LucideIcon;
}

const DRAWER_WIDTH = "16rem"; // matches w-64

function navButtonClass(active: boolean): string {
  return `flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-left text-sm font-semibold transition-colors ${
    active
      ? "bg-rose-600 text-white"
      : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800"
  }`;
}

export default function DashboardSidebar({
  items,
  activeId,
  onSelect,
}: {
  items: DashboardNavItem[];
  activeId: string;
  onSelect: (id: string) => void;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const activeLabel = items.find((i) => i.id === activeId)?.label ?? "";

  function select(id: string) {
    onSelect(id);
    setMobileOpen(false);
  }

  return (
    <div className="lg:w-56 lg:shrink-0">
      {/* Mobile: current section label, for orientation while the drawer is closed. */}
      <span className="block text-xs font-bold uppercase tracking-wide text-zinc-400 lg:hidden">
        {activeLabel}
      </span>

      {/* Desktop: always-visible static sidebar. */}
      <nav className="hidden flex-col gap-1 rounded-2xl border border-zinc-200 bg-white p-2 dark:border-zinc-800 dark:bg-zinc-900 lg:flex">
        {items.map((item) => (
          <button key={item.id} type="button" onClick={() => select(item.id)} className={navButtonClass(item.id === activeId)}>
            <item.icon className="h-4 w-4 shrink-0" />
            {item.label}
          </button>
        ))}
      </nav>

      {/* Mobile: backdrop, shown only while the drawer is open, tap to dismiss. */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-zinc-900/40 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile: slide-in drawer. */}
      <nav
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col gap-1 overflow-y-auto border-r border-zinc-200 bg-white p-3 pt-6 shadow-xl transition-transform duration-200 ease-out dark:border-zinc-800 dark:bg-zinc-900 lg:hidden ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {items.map((item) => (
          <button key={item.id} type="button" onClick={() => select(item.id)} className={navButtonClass(item.id === activeId)}>
            <item.icon className="h-4 w-4 shrink-0" />
            {item.label}
          </button>
        ))}
      </nav>

      {/* Mobile: edge tab that slides along with the drawer and flips direction. */}
      <button
        type="button"
        onClick={() => setMobileOpen((v) => !v)}
        aria-label={mobileOpen ? "Close dashboard menu" : "Open dashboard menu"}
        aria-expanded={mobileOpen}
        style={{ left: mobileOpen ? DRAWER_WIDTH : 0 }}
        className="fixed top-1/2 z-50 flex h-14 w-7 -translate-y-1/2 items-center justify-center rounded-r-lg border border-l-0 border-zinc-200 bg-white text-zinc-500 shadow-md transition-[left] duration-200 ease-out dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400 lg:hidden"
      >
        {mobileOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
      </button>
    </div>
  );
}
