import type { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "YouGotTalent — Coming Soon",
  description: "Sri Lanka's talent marketplace. Every skill, one stage. Coming soon to yougottalent.lk.",
};

const CATEGORIES = ["Acting", "Singing", "Dancing", "Music", "Photography", "Script Writing", "Comedy", "Modeling", "and more"];

export default function ComingSoonPage() {
  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-zinc-950 text-white">
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:48px_48px]"
      />
      <div
        aria-hidden
        className="pointer-events-none fixed inset-y-0 -right-32 w-1/2 bg-[linear-gradient(to_left,rgba(225,29,72,0.18),transparent)]"
      />

      <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-7">
        <div className="font-heading flex items-center gap-2 text-lg font-black uppercase tracking-tight">
          <span className="flex h-8 w-8 items-center justify-center rounded bg-rose-600 text-sm">Y</span>
          YouGotTalent
        </div>
      </header>

      <main className="relative z-10 mx-auto flex max-w-2xl flex-1 flex-col items-center justify-center px-6 pb-16 pt-8 text-center">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-zinc-800 px-3.5 py-1.5 text-xs font-semibold uppercase tracking-widest text-zinc-400">
          Sri Lanka&apos;s talent marketplace
        </span>
        <h1 className="font-heading mt-7 text-5xl font-black uppercase leading-[1.02] tracking-tight sm:text-7xl">
          Every skill.
          <br />
          <span className="text-rose-400">One stage.</span>
        </h1>
        <p className="mt-6 max-w-lg text-balance text-base leading-relaxed text-zinc-400">
          Acting, singing, dancing, script writing, music, comedy, and more — YouGotTalent is
          where Sri Lankan talent gets discovered and talent hunts find exactly who they&apos;re
          looking for. We&apos;re putting the finishing touches on things.
        </p>
        <span className="mt-10 inline-flex items-center gap-2.5 rounded-full border border-zinc-800 px-5 py-2.5 text-sm font-semibold">
          <span className="h-2 w-2 animate-pulse rounded-full bg-rose-400" />
          Launching soon at yougottalent.lk
        </span>
        <div className="mt-11 flex max-w-lg flex-wrap justify-center gap-2">
          {CATEGORIES.map((c) => (
            <span
              key={c}
              className="rounded-full border border-zinc-800 bg-zinc-900 px-3.5 py-1.5 text-xs text-zinc-400"
            >
              {c}
            </span>
          ))}
        </div>
      </main>

      <footer className="relative z-10 px-6 pb-9 pt-7 text-center text-sm text-zinc-600">
        &copy; 2026 YouGotTalent &middot;{" "}
        <a href="mailto:hello@yougottalent.lk" className="text-zinc-400 hover:text-white">
          hello@yougottalent.lk
        </a>
      </footer>
    </div>
  );
}
