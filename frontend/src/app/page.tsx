"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CastingCall, TALENT_CATEGORIES, TalentProfile, Title, api } from "@/lib/api";
import { MapPin, Star } from "lucide-react";
import { btnPrimary, btnSecondary, categoryBadgeClass, categoryColor, coverPhotoUrl, eyebrowClass, formatCategory } from "@/lib/ui";
import TalentAvatar from "@/components/TalentAvatar";
import CategoryIcon from "@/components/CategoryIcon";
import TitlePoster from "@/components/TitlePoster";

export default function Home() {
  const [talents, setTalents] = useState<TalentProfile[]>([]);
  const [calls, setCalls] = useState<CastingCall[]>([]);
  const [titles, setTitles] = useState<Title[]>([]);

  useEffect(() => {
    api.listTalents().then(setTalents).catch(() => {});
    api.listCastingCalls().then(setCalls).catch(() => {});
    api.listTitles().then(setTitles).catch(() => {});
  }, []);

  return (
    <main className="flex flex-1 flex-col overflow-hidden">
      <section className="relative overflow-hidden bg-zinc-950">
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:48px_48px]" />
        <div className="pointer-events-none absolute -right-32 top-0 h-full w-1/2 bg-gradient-to-l from-rose-600/20 to-transparent" />

        <div className="relative mx-auto flex max-w-6xl flex-col items-center px-6 py-24 text-center sm:py-32">
          <span className={eyebrowClass}>
            <MapPin className="mr-1 inline h-3 w-3" /> Sri Lanka&apos;s talent marketplace
          </span>
          <h1 className="mt-8 max-w-3xl font-heading text-5xl font-black uppercase leading-[1.05] tracking-tight text-white sm:text-6xl md:text-7xl">
            Every skill.
            <br />
            <span className="text-rose-500">One stage.</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg text-zinc-400">
            Singing, acting, script writing, painting, music, comedy and more — audition, build a
            profile, and get discovered by the talent hunts looking for exactly what you do.
          </p>
          <div className="mt-10 flex flex-col gap-3 sm:flex-row">
            <Link href="/talents" className={btnPrimary}>
              Browse talent
            </Link>
            <Link
              href="/casting-calls"
              className="inline-flex items-center justify-center gap-1.5 rounded-md border-2 border-zinc-700 bg-transparent px-6 py-3 text-sm font-bold uppercase tracking-wide text-white transition-all hover:border-white"
            >
              See talent hunts
            </Link>
          </div>

          <div className="mt-16 flex flex-wrap justify-center gap-3">
            <Stat value={talents.length} label="Talent profiles" />
            <Stat value={calls.length} label="Open opportunities" />
            <Stat value={TALENT_CATEGORIES.length} label="Skill categories" />
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-6xl px-6 py-20">
        <h2 className="text-center font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 sm:text-4xl dark:text-zinc-50">
          Browse by category
        </h2>
        <p className="mt-2 text-center text-zinc-500">Whatever your craft, there&apos;s a home for it here.</p>
        <div className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
          {TALENT_CATEGORIES.map((c) => (
            <Link
              key={c}
              href={`/talents?category=${c}`}
              className="group flex flex-col items-center gap-3 rounded-xl border border-zinc-200 bg-white p-5 text-center shadow-sm transition-all hover:-translate-y-1 hover:border-zinc-900 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-100"
            >
              <span
                className={`flex h-14 w-14 items-center justify-center rounded-sm text-white transition-transform group-hover:scale-110 ${categoryColor(c).solid}`}
              >
                <CategoryIcon category={c} className="h-6 w-6" />
              </span>
              <span className="text-sm font-bold text-zinc-800 dark:text-zinc-200">{formatCategory(c)}</span>
            </Link>
          ))}
        </div>
      </section>

      {talents.length > 0 && (
        <section className="mx-auto w-full max-w-6xl px-6 pb-20">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 sm:text-4xl dark:text-zinc-50">
              Featured talent
            </h2>
            <Link href="/talents" className="text-sm font-bold uppercase tracking-wide text-rose-600 hover:underline">
              View all →
            </Link>
          </div>
          <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3">
            {talents.slice(0, 6).map((t) => (
              <Link
                key={t.id}
                href={`/talents/${t.id}`}
                className="group overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900"
              >
                <div className="aspect-[4/3] overflow-hidden bg-zinc-100 dark:bg-zinc-800">
                  <TalentAvatar
                    name={t.display_name}
                    coverUrl={coverPhotoUrl(t.media)}
                    className="h-full w-full text-4xl transition-transform duration-300 group-hover:scale-105"
                  />
                </div>
                <div className="p-4">
                  <p className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">{t.display_name}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className={categoryBadgeClass(t.category)}>{formatCategory(t.category)}</span>
                    {t.city && <span className="text-xs text-zinc-500">{t.city}</span>}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {titles.length > 0 && (
        <section className="mx-auto w-full max-w-6xl px-6 pb-20">
          <div className="flex items-center justify-between">
            <div>
              <span className={eyebrowClass}>New</span>
              <h2 className="mt-3 font-heading text-3xl font-black uppercase tracking-tight text-zinc-900 sm:text-4xl dark:text-zinc-50">
                Rate &amp; critique
              </h2>
              <p className="mt-2 text-zinc-500">Sri Lanka's films, TV series, and songs — rated by the industry.</p>
            </div>
            <Link href="/community/titles" className="text-sm font-bold uppercase tracking-wide text-rose-600 hover:underline">
              View all →
            </Link>
          </div>
          <div className="mt-8 grid grid-cols-3 gap-4 sm:grid-cols-4 md:grid-cols-6">
            {titles.slice(0, 6).map((t) => (
              <Link key={t.id} href={`/community/titles/${t.id}`} className="group flex flex-col gap-2">
                <div className="relative aspect-[2/3] overflow-hidden rounded-lg shadow-sm transition-all group-hover:-translate-y-1 group-hover:shadow-xl">
                  <TitlePoster
                    name={t.name}
                    workType={t.work_type}
                    posterUrl={t.poster_url}
                    className="h-full w-full transition-transform duration-300 group-hover:scale-105"
                  />
                  {t.average_rating != null && (
                    <span className="absolute left-1.5 top-1.5 flex items-center gap-0.5 rounded-sm bg-black/75 px-1.5 py-0.5 text-xs font-bold text-amber-400 backdrop-blur-sm">
                      <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                      {t.average_rating.toFixed(1)}
                    </span>
                  )}
                </div>
                <p className="truncate text-sm font-bold text-zinc-900 dark:text-zinc-50">{t.name}</p>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="bg-zinc-950">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <h2 className="text-center font-heading text-3xl font-black uppercase tracking-tight text-white sm:text-4xl">
            How it works
          </h2>
          <div className="mt-12 grid grid-cols-1 gap-8 sm:grid-cols-3">
            <HowItWorksStep
              step="1"
              title="Audition your talent"
              body="Upload photos, video, audio, or writing samples — whatever shows your skill best, in any category. Organizers set up a profile too."
            />
            <HowItWorksStep
              step="2"
              title="Get discovered"
              body="Talent hunt organizers search by skill, category, and keyword to find exactly the talent they need — or post an open call."
            />
            <HowItWorksStep
              step="3"
              title="Get picked"
              body="Organizers review applicants, shortlist favorites, and manage the whole process in one place."
            />
          </div>
          <div className="mt-14 flex justify-center">
            <Link href="/register" className={btnPrimary}>
              Create your account
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex items-center gap-2 rounded-md border border-zinc-700 px-4 py-2 text-sm font-semibold text-zinc-200">
      <span className="font-heading text-lg font-black text-rose-500">{value}</span>
      {label}
    </div>
  );
}

function HowItWorksStep({ step, title, body }: { step: string; title: string; body: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-center">
      <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-sm bg-rose-600 text-lg font-black text-white">
        {step}
      </span>
      <h3 className="mt-4 font-heading text-xl font-bold text-white">{title}</h3>
      <p className="mt-2 text-sm text-zinc-400">{body}</p>
    </div>
  );
}
