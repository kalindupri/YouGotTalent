"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Save, ShieldCheck } from "lucide-react";
import { ApiError, api, TALENT_CATEGORIES, TalentCategory, TalentProfile } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  btnSecondary,
  btnSmall,
  cardClass,
  categoryBadgeClass,
  coverPhotoUrl,
  formatCategory,
  inputClass,
  labelClass,
  verifiedBadgeClass,
} from "@/lib/ui";
import TalentAvatar from "@/components/TalentAvatar";

export default function TalentsPage() {
  return (
    <Suspense fallback={null}>
      <TalentsPageContent />
    </Suspense>
  );
}

function TalentsPageContent() {
  const searchParams = useSearchParams();
  const { user, token } = useAuth();

  const hasAdvancedParams =
    searchParams.has("experience_min") || searchParams.has("experience_max") || searchParams.has("verified_only");

  const [talents, setTalents] = useState<TalentProfile[]>([]);
  const [category, setCategory] = useState<TalentCategory | "">(
    (searchParams.get("category") as TalentCategory | null) ?? ""
  );
  const [city, setCity] = useState(searchParams.get("city") ?? "");
  const [q, setQ] = useState(searchParams.get("q") ?? "");
  const [showAdvanced, setShowAdvanced] = useState(hasAdvancedParams);
  const [experienceMin, setExperienceMin] = useState(searchParams.get("experience_min") ?? "");
  const [experienceMax, setExperienceMax] = useState(searchParams.get("experience_max") ?? "");
  const [verifiedOnly, setVerifiedOnly] = useState(searchParams.get("verified_only") === "true");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [savingSearch, setSavingSearch] = useState(false);
  const [saveSearchMessage, setSaveSearchMessage] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => {
      async function load() {
        setLoading(true);
        setError(null);
        try {
          setTalents(
            await api.listTalents({
              category: category || undefined,
              city: city || undefined,
              q: q || undefined,
              experience_min: experienceMin ? Number(experienceMin) : undefined,
              experience_max: experienceMax ? Number(experienceMax) : undefined,
              verified_only: verifiedOnly || undefined,
            })
          );
        } catch {
          setError("Could not load talent right now.");
        } finally {
          setLoading(false);
        }
      }
      load();
    }, 250);
    return () => clearTimeout(handle);
  }, [category, city, q, experienceMin, experienceMax, verifiedOnly]);

  async function handleSaveSearch(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setSavingSearch(true);
    setSaveSearchMessage(null);
    try {
      await api.createSavedSearch(
        {
          name: [category && formatCategory(category), city, q].filter(Boolean).join(" · ") || "My search",
          category: category || undefined,
          city: city || undefined,
          q: q || undefined,
          experience_min: experienceMin ? Number(experienceMin) : undefined,
          experience_max: experienceMax ? Number(experienceMax) : undefined,
          verified_only: verifiedOnly,
        },
        token
      );
      setSaveSearchMessage("Saved! Find it on your dashboard.");
    } catch (err) {
      setSaveSearchMessage(err instanceof ApiError ? err.message : "Could not save this search.");
    } finally {
      setSavingSearch(false);
    }
  }

  return (
    <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-14">
      <h1 className="font-heading text-4xl font-black uppercase tracking-tight text-zinc-900 sm:text-5xl dark:text-zinc-50">
        Browse talent
      </h1>
      <p className="mt-2 text-zinc-500">
        {loading ? "Loading…" : `${talents.length} talent profile${talents.length === 1 ? "" : "s"}`}
      </p>

      <div className="mt-8 flex flex-wrap gap-3">
        <input
          placeholder="Search by name, bio, or skill (e.g. 'screenplay', 'carnatic')"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className={`${inputClass} max-w-sm`}
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value as TalentCategory | "")}
          className={`${inputClass} w-auto`}
        >
          <option value="">All categories</option>
          {TALENT_CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {formatCategory(c)}
            </option>
          ))}
        </select>
        <input
          placeholder="Filter by city"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          className={`${inputClass} w-auto max-w-[10rem]`}
        />
        <button type="button" onClick={() => setShowAdvanced((v) => !v)} className={btnSmall}>
          {showAdvanced ? "Hide" : "Advanced filters"}
        </button>
      </div>

      {showAdvanced && (
        <form
          onSubmit={handleSaveSearch}
          className="mt-4 flex flex-wrap items-end gap-3 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800"
        >
          <label className={labelClass}>
            Min. experience (years)
            <input
              type="number"
              min={0}
              value={experienceMin}
              onChange={(e) => setExperienceMin(e.target.value)}
              className={`${inputClass} w-32`}
            />
          </label>
          <label className={labelClass}>
            Max. experience (years)
            <input
              type="number"
              min={0}
              value={experienceMax}
              onChange={(e) => setExperienceMax(e.target.value)}
              className={`${inputClass} w-32`}
            />
          </label>
          <label className="flex items-center gap-2 pb-2.5 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            <input
              type="checkbox"
              checked={verifiedOnly}
              onChange={(e) => setVerifiedOnly(e.target.checked)}
              className="accent-rose-600"
            />
            Verified talent only
          </label>
          {user?.role === "recruiter" && (
            <button type="submit" disabled={savingSearch} className={btnSecondary}>
              {savingSearch ? (
                "Saving…"
              ) : (
                <>
                  <Save className="h-4 w-4" /> Save this search
                </>
              )}
            </button>
          )}
          {saveSearchMessage && <p className="w-full text-sm text-zinc-500">{saveSearchMessage}</p>}
        </form>
      )}

      {error && <p className="mt-8 text-sm text-red-600">{error}</p>}
      {!loading && !error && talents.length === 0 && (
        <p className="mt-8 text-sm text-zinc-500">No talent profiles match your search yet.</p>
      )}

      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 md:grid-cols-3">
        {talents.map((t) => (
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
              <div className="flex items-center gap-1.5">
                <p className="font-heading text-lg font-bold text-zinc-900 dark:text-zinc-50">{t.display_name}</p>
                {t.is_verified && (
                  <span className={verifiedBadgeClass}>
                    <ShieldCheck className="h-3 w-3" />
                  </span>
                )}
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className={categoryBadgeClass(t.category)}>{formatCategory(t.category)}</span>
                {t.city && <span className="text-xs text-zinc-500">{t.city}</span>}
              </div>
              {t.skills && t.skills.length > 0 && (
                <p className="mt-2 truncate text-xs text-zinc-500">{t.skills.slice(0, 3).join(" · ")}</p>
              )}
            </div>
          </Link>
        ))}
        {loading &&
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className={`${cardClass} h-64 animate-pulse !p-0`}>
              <div className="aspect-[4/3] rounded-t-xl bg-zinc-100 dark:bg-zinc-800" />
            </div>
          ))}
      </div>
    </main>
  );
}
